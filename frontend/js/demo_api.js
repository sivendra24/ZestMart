(function () {
    const DB_KEY = "zestmart-demo-db-v1";
    const SESSION_KEY = "zestmart-demo-session-v1";
    const OTP_KEY = "zestmart-demo-otp-v1";
    let active = false;

    function activate() {
        if (active) {
            return;
        }
        active = true;
        window.dispatchEvent(new CustomEvent("zestmart:demo-mode"));
    }

    function isActive() {
        return active;
    }

    function isEnabled() {
        return Boolean(window.ZestMartConfig?.allowDemoFallback);
    }

    function nowIso() {
        return new Date().toISOString();
    }

    function createId(prefix) {
        if (window.crypto?.randomUUID) {
            return `${prefix}_${window.crypto.randomUUID().replaceAll("-", "")}`;
        }
        return `${prefix}_${Date.now()}_${Math.random().toString(16).slice(2)}`;
    }

    function clone(value) {
        return JSON.parse(JSON.stringify(value));
    }

    function normalizePhone(phone) {
        return String(phone || "").replace(/\D/g, "");
    }

    function readJson(key, fallbackValue) {
        try {
            const rawValue = window.localStorage.getItem(key);
            return rawValue ? JSON.parse(rawValue) : clone(fallbackValue);
        } catch (_error) {
            return clone(fallbackValue);
        }
    }

    function writeJson(key, value) {
        window.localStorage.setItem(key, JSON.stringify(value));
    }

    function seedDatabase() {
        const existing = window.localStorage.getItem(DB_KEY);
        if (existing) {
            return;
        }

        const timestamp = nowIso();
        const adminId = createId("user");
        const deliveryId = createId("user");
        const studentId = createId("user");
        const products = [
            { id: createId("product"), name: "Fresh Apples", price: 120, category: "Fruits", stock: 40 },
            { id: createId("product"), name: "Whole Wheat Bread", price: 55, category: "Bakery", stock: 30 },
            { id: createId("product"), name: "Organic Milk", price: 68, category: "Dairy", stock: 25 },
            { id: createId("product"), name: "Energy Mix Nuts", price: 180, category: "Snacks", stock: 18 },
        ].map((product) => ({
            ...product,
            imageUrl: null,
            createdAt: timestamp,
            updatedAt: timestamp,
        }));

        writeJson(DB_KEY, {
            users: [
                {
                    id: adminId,
                    name: "ZestMart Admin",
                    userId: "admin001",
                    phone: null,
                    address: null,
                    password: "Admin@123",
                    role: "admin",
                    createdAt: timestamp,
                },
                {
                    id: deliveryId,
                    name: "Rapid Rider",
                    userId: "delivery001",
                    phone: null,
                    address: null,
                    password: "Delivery@123",
                    role: "delivery",
                    createdAt: timestamp,
                },
                {
                    id: studentId,
                    name: "Campus Shopper",
                    userId: null,
                    phone: "9876543210",
                    address: "Boys Hostel Block A, Room 204, North Campus",
                    password: "Student@123",
                    role: "student",
                    createdAt: timestamp,
                },
            ],
            products,
            orders: [],
        });
    }

    function readDb() {
        seedDatabase();
        return readJson(DB_KEY, { users: [], products: [], orders: [] });
    }

    function writeDb(db) {
        writeJson(DB_KEY, db);
    }

    function getSessionUser() {
        const session = readJson(SESSION_KEY, null);
        if (!session?.userId) {
            return null;
        }
        const db = readDb();
        return db.users.find((user) => user.id === session.userId) || null;
    }

    function setSessionUser(user) {
        if (!user) {
            window.localStorage.removeItem(SESSION_KEY);
            return;
        }
        writeJson(SESSION_KEY, { userId: user.id });
    }

    function sanitizeUser(user) {
        return {
            id: user.id,
            name: user.name,
            userId: user.userId,
            phone: user.phone,
            address: user.address,
            role: user.role,
        };
    }

    function getOtpStore() {
        return readJson(OTP_KEY, {});
    }

    function saveOtpStore(store) {
        writeJson(OTP_KEY, store);
    }

    function createResponse(message, data, status) {
        return {
            success: true,
            message,
            data: data || {},
            status: status || 200,
        };
    }

    function createError(message, status) {
        const error = new Error(message);
        error.status = status || 400;
        error.payload = { success: false, message, data: {} };
        throw error;
    }

    function requireAuth() {
        const user = getSessionUser();
        if (!user) {
            createError("Please sign in to continue.", 401);
        }
        return user;
    }

    function requireRole(user, roles) {
        if (!roles.includes(user.role)) {
            createError("You do not have permission to access this resource.", 403);
        }
    }

    function parseBody(options) {
        if (options?.formData && options.body instanceof FormData) {
            return options.body;
        }
        return options?.body || {};
    }

    async function formDataFileToDataUrl(file) {
        if (!file) {
            return null;
        }
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = () => reject(new Error("Unable to read image file."));
            reader.readAsDataURL(file);
        });
    }

    function getProductsResponse(db) {
        return db.products
            .slice()
            .sort((left, right) => new Date(right.createdAt) - new Date(left.createdAt))
            .map((product) => clone(product));
    }

    function getOrdersForUser(db, user) {
        if (user.role === "admin") {
            return db.orders.slice();
        }
        if (user.role === "delivery") {
            return db.orders.filter(
                (order) => order.deliveryPersonId === user.id || order.status === "pending"
            );
        }
        return db.orders.filter((order) => order.customerId === user.id);
    }

    function findProductOrFail(db, productId) {
        const product = db.products.find((item) => item.id === productId);
        if (!product) {
            createError("Product not found.", 404);
        }
        return product;
    }

    function findOrderOrFail(db, orderId) {
        const order = db.orders.find((item) => item.id === orderId);
        if (!order) {
            createError("Order not found.", 404);
        }
        return order;
    }

    function buildOrderItems(db, requestedProducts) {
        if (!Array.isArray(requestedProducts) || !requestedProducts.length) {
            createError("Add at least one product before placing the order.", 400);
        }

        return requestedProducts.map((item) => {
            const quantity = Number(item.quantity || 0);
            if (quantity < 1) {
                createError("Order quantity must be at least 1.", 400);
            }
            const product = findProductOrFail(db, item.productId);
            if (product.stock < quantity) {
                createError(`${product.name} does not have enough stock available.`, 400);
            }
            return {
                productId: product.id,
                name: product.name,
                price: Number(product.price),
                quantity,
            };
        });
    }

    async function handleRequest(path, options) {
        activate();
        const db = readDb();
        const body = parseBody(options);
        const currentUser = getSessionUser();

        if (path === "/auth/send-otp" && options.method === "POST") {
            const phone = normalizePhone(body.phone);
            if (phone.length < 10) {
                createError("Enter a valid mobile number.", 400);
            }

            const otp = String(Math.floor(100000 + Math.random() * 900000));
            const store = getOtpStore();
            store[phone] = {
                otp,
                verified: false,
                expiresAt: Date.now() + 5 * 60 * 1000,
            };
            saveOtpStore(store);

            return createResponse("OTP generated successfully.", {
                deliveryMode: "mock",
                maskedPhone: phone,
                expiresInMinutes: 5,
                otpPreview: otp,
            }, 201);
        }

        if (path === "/auth/verify-otp" && options.method === "POST") {
            const phone = normalizePhone(body.phone);
            const otp = String(body.otp || "");
            const store = getOtpStore();
            const record = store[phone];

            if (!record || record.expiresAt < Date.now()) {
                createError("OTP expired or not found. Request a new OTP.", 400);
            }
            if (record.otp !== otp) {
                createError("Invalid OTP.", 400);
            }

            record.verified = true;
            saveOtpStore(store);
            return createResponse("OTP verified successfully.", {});
        }

        if (path === "/auth/register" && options.method === "POST") {
            const phone = normalizePhone(body.phone);
            const store = getOtpStore();
            const otpRecord = store[phone];

            if (!otpRecord?.verified) {
                createError("Verify the OTP before registering.", 400);
            }
            if ((body.name || "").trim().length < 2) {
                createError("Name must be at least 2 characters long.", 400);
            }
            if ((body.password || "").length < 8) {
                createError("Password must be at least 8 characters long.", 400);
            }
            if ((body.address || "").trim().length < 10) {
                createError("Enter a complete delivery address.", 400);
            }
            if (db.users.some((user) => normalizePhone(user.phone) === phone)) {
                createError("An account with this phone number already exists.", 409);
            }

            const user = {
                id: createId("user"),
                name: body.name.trim(),
                userId: null,
                phone,
                address: body.address.trim(),
                password: body.password,
                role: "student",
                createdAt: nowIso(),
            };
            db.users.push(user);
            writeDb(db);
            setSessionUser(user);
            delete store[phone];
            saveOtpStore(store);

            return createResponse("Student registration completed successfully.", {
                user: sanitizeUser(user),
            }, 201);
        }

        if (path === "/auth/login/student" && options.method === "POST") {
            const phone = normalizePhone(body.phone);
            const user = db.users.find(
                (item) => item.role === "student" && normalizePhone(item.phone) === phone
            );
            if (!user || user.password !== body.password) {
                createError("Invalid phone number or password.", 401);
            }
            setSessionUser(user);
            return createResponse("Student login successful.", { user: sanitizeUser(user) });
        }

        if (path === "/auth/login/staff" && options.method === "POST") {
            const userId = String(body.userId || "").trim();
            const user = db.users.find(
                (item) => item.userId === userId && (item.role === "admin" || item.role === "delivery")
            );
            if (!user || user.password !== body.password) {
                createError("Invalid user ID or password.", 401);
            }
            setSessionUser(user);
            return createResponse("Staff login successful.", { user: sanitizeUser(user) });
        }

        if (path === "/auth/session" && options.method === "GET") {
            const user = requireAuth();
            return createResponse("Active session fetched successfully.", { user: sanitizeUser(user) });
        }

        if (path === "/auth/logout" && options.method === "POST") {
            setSessionUser(null);
            return createResponse("Signed out successfully.", {});
        }

        if (path === "/products" && options.method === "GET") {
            return createResponse("Products fetched successfully.", getProductsResponse(db));
        }

        if (path === "/orders" && options.method === "GET") {
            const user = requireAuth();
            requireRole(user, ["student", "delivery", "admin"]);

            const result = getOrdersForUser(db, user)
                .filter((order) => user.role !== "delivery" || order.deliveryPersonId === user.id || order.status === "pending")
                .map((order) => clone(order));
            return createResponse("Orders fetched successfully.", result);
        }

        if (path === "/orders" && options.method === "POST") {
            const user = requireAuth();
            requireRole(user, ["student", "delivery", "admin"]);

            const deliveryAddress = String(body.deliveryAddress || "").trim();
            if (deliveryAddress.length < 10) {
                createError("Enter a full delivery address before placing the order.", 400);
            }

            const products = buildOrderItems(db, body.products);
            products.forEach((item) => {
                const product = findProductOrFail(db, item.productId);
                product.stock -= item.quantity;
                product.updatedAt = nowIso();
            });

            const totalPrice = products.reduce((sum, item) => sum + item.price * item.quantity, 0);
            const order = {
                id: createId("order"),
                customerId: user.id,
                customerName: user.name,
                customerPhone: user.phone,
                deliveryAddress,
                products,
                totalPrice: Number(totalPrice.toFixed(2)),
                status: "pending",
                deliveryPersonId: null,
                deliveryPersonName: null,
                createdAt: nowIso(),
            };
            db.orders.unshift(order);
            writeDb(db);

            if (user.role === "student") {
                const storedUser = db.users.find((item) => item.id === user.id);
                if (storedUser) {
                    storedUser.address = deliveryAddress;
                    writeDb(db);
                }
            }

            return createResponse("Order placed successfully.", clone(order), 201);
        }

        if (path.startsWith("/orders/") && path.endsWith("/status") && options.method === "PUT") {
            const user = requireAuth();
            requireRole(user, ["delivery", "admin"]);

            const orderId = path.split("/")[2];
            const order = findOrderOrFail(db, orderId);
            const nextStatus = String(body.status || "").trim().toLowerCase();
            if (!["pending", "assigned", "delivered"].includes(nextStatus)) {
                createError("Invalid order status.", 400);
            }

            if (nextStatus === "assigned") {
                order.deliveryPersonId = user.id;
                order.deliveryPersonName = user.name;
            }
            if (nextStatus === "pending") {
                order.deliveryPersonId = null;
                order.deliveryPersonName = null;
            }
            order.status = nextStatus;
            writeDb(db);
            return createResponse("Order status updated successfully.", clone(order));
        }

        if (path === "/delivery/orders" && options.method === "GET") {
            const user = requireAuth();
            requireRole(user, ["delivery", "admin"]);

            return createResponse("Delivery orders fetched successfully.", {
                pendingOrders: db.orders.filter((order) => order.status === "pending").map(clone),
                assignedOrders: db.orders
                    .filter((order) =>
                        user.role === "admin"
                            ? order.status === "assigned" || order.status === "delivered"
                            : order.deliveryPersonId === user.id
                    )
                    .map(clone),
            });
        }

        if (path.startsWith("/delivery/orders/") && path.endsWith("/accept") && options.method === "PUT") {
            const user = requireAuth();
            requireRole(user, ["delivery"]);

            const orderId = path.split("/")[3];
            const order = findOrderOrFail(db, orderId);
            if (order.status !== "pending") {
                createError("Only pending orders can be accepted.", 400);
            }

            order.status = "assigned";
            order.deliveryPersonId = user.id;
            order.deliveryPersonName = user.name;
            writeDb(db);
            return createResponse("Order accepted successfully.", clone(order));
        }

        if (path === "/admin/products" && options.method === "POST") {
            const user = requireAuth();
            requireRole(user, ["admin"]);

            const formData = body;
            const name = String(formData.get("name") || "").trim();
            const category = String(formData.get("category") || "").trim();
            const price = Number(formData.get("price"));
            const stock = Number(formData.get("stock"));
            if (name.length < 2 || category.length < 2 || Number.isNaN(price) || Number.isNaN(stock)) {
                createError("Provide valid product details.", 400);
            }

            const imageFile = formData.get("image");
            const product = {
                id: createId("product"),
                name,
                category,
                price: Number(price.toFixed(2)),
                stock: Math.max(0, Math.trunc(stock)),
                imageUrl: imageFile instanceof File ? await formDataFileToDataUrl(imageFile) : null,
                createdAt: nowIso(),
                updatedAt: nowIso(),
            };
            db.products.unshift(product);
            writeDb(db);
            return createResponse("Product created successfully.", clone(product), 201);
        }

        if (path.startsWith("/admin/products/") && options.method === "PUT" && !path.endsWith("/image")) {
            const user = requireAuth();
            requireRole(user, ["admin"]);

            const productId = path.split("/")[3];
            const product = findProductOrFail(db, productId);
            const name = String(body.name || "").trim();
            const category = String(body.category || "").trim();
            const price = Number(body.price);
            const stock = Number(body.stock);
            if (name.length < 2 || category.length < 2 || Number.isNaN(price) || Number.isNaN(stock)) {
                createError("Provide valid product details.", 400);
            }

            product.name = name;
            product.category = category;
            product.price = Number(price.toFixed(2));
            product.stock = Math.max(0, Math.trunc(stock));
            product.updatedAt = nowIso();
            writeDb(db);
            return createResponse("Product updated successfully.", clone(product));
        }

        if (path.startsWith("/admin/products/") && path.endsWith("/image") && options.method === "PUT") {
            const user = requireAuth();
            requireRole(user, ["admin"]);

            const productId = path.split("/")[3];
            const product = findProductOrFail(db, productId);
            const imageFile = body.get("image");
            if (!(imageFile instanceof File)) {
                createError("Choose an image before uploading.", 400);
            }

            product.imageUrl = await formDataFileToDataUrl(imageFile);
            product.updatedAt = nowIso();
            writeDb(db);
            return createResponse("Product image updated successfully.", clone(product));
        }

        if (path.startsWith("/admin/products/") && options.method === "DELETE") {
            const user = requireAuth();
            requireRole(user, ["admin"]);

            const productId = path.split("/")[3];
            const productIndex = db.products.findIndex((item) => item.id === productId);
            if (productIndex === -1) {
                createError("Product not found.", 404);
            }

            db.products.splice(productIndex, 1);
            writeDb(db);
            return createResponse("Product deleted successfully.", {});
        }

        createError("The requested resource was not found.", 404);
    }

    window.ZestMartDemoApi = {
        activate,
        isActive,
        isEnabled,
        request: handleRequest,
    };
})();
