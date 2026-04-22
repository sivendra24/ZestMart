(function () {
    const api = window.ZestMartApi;
    const utils = window.ZestMartUtils;
    const state = {
        products: [],
        orders: []
    };

    document.addEventListener("DOMContentLoaded", init);

    async function init() {
        const user = await utils.guardRoute(["admin"]);
        if (!user) {
            return;
        }

        utils.bindLogoutButtons();
        utils.fillUserBadge("admin-user-name", "admin-user-role", user);
        utils.showDemoModeNotice("admin-status");

        document.getElementById("product-form").addEventListener("submit", handleCreateProduct);
        document.getElementById("refresh-admin-products").addEventListener("click", loadProducts);
        document.getElementById("refresh-admin-orders").addEventListener("click", loadOrders);
        document.getElementById("admin-product-list").addEventListener("click", handleProductActions);
        document.getElementById("admin-order-list").addEventListener("click", handleOrderActions);

        await Promise.all([loadProducts(), loadOrders()]);
    }

    async function loadProducts() {
        try {
            const response = await api.get("/products");
            state.products = response.data || [];
            renderProducts();
            updateOverview();
        } catch (error) {
            utils.showMessage("admin-status", error.message, "error");
        }
    }

    async function loadOrders() {
        try {
            const response = await api.get("/orders", { auth: true });
            state.orders = response.data || [];
            renderOrders();
            updateOverview();
        } catch (error) {
            utils.showMessage("admin-status", error.message, "error");
        }
    }

    async function handleCreateProduct(event) {
        event.preventDefault();
        const button = event.currentTarget.querySelector('button[type="submit"]');
        const imageFile = document.getElementById("product-image").files[0];
        const formData = new FormData();
        formData.append("name", document.getElementById("product-name").value.trim());
        formData.append("category", document.getElementById("product-category").value.trim());
        formData.append("price", document.getElementById("product-price").value);
        formData.append("stock", document.getElementById("product-stock").value);
        if (imageFile) {
            formData.append("image", imageFile);
        }

        try {
            utils.setButtonBusy(button, true, "Creating...");
            await api.post("/admin/products", formData, { auth: true, formData: true });
            event.currentTarget.reset();
            await loadProducts();
            utils.showMessage("admin-status", "Product created successfully.", "success");
        } catch (error) {
            utils.showMessage("admin-status", error.message, "error");
        } finally {
            utils.setButtonBusy(button, false);
        }
    }

    function renderProducts() {
        const list = document.getElementById("admin-product-list");
        if (!state.products.length) {
            list.innerHTML = utils.emptyState("No products available to manage.");
            return;
        }

        list.innerHTML = state.products
            .map((product) => {
                const image = product.imageUrl
                    ? `<img class="inventory-image" src="${utils.escapeHtml(product.imageUrl)}" alt="${utils.escapeHtml(product.name)}">`
                    : '<div class="inventory-image"></div>';

                return `
                    <article class="inventory-card" data-product-id="${product.id}">
                        ${image}
                        <div class="stack" style="margin-top: 0.95rem;">
                            <label class="inline-label">
                                Name
                                <input type="text" data-field="name" value="${utils.escapeHtml(product.name)}">
                            </label>
                            <label class="inline-label">
                                Category
                                <input type="text" data-field="category" value="${utils.escapeHtml(product.category)}">
                            </label>
                            <div class="row-2">
                                <label class="inline-label">
                                    Price
                                    <input type="number" min="0" step="0.01" data-field="price" value="${product.price}">
                                </label>
                                <label class="inline-label">
                                    Stock
                                    <input type="number" min="0" step="1" data-field="stock" value="${product.stock}">
                                </label>
                            </div>
                            <div class="image-upload">
                                <input type="file" data-role="image-input" accept="image/*">
                            </div>
                            <div class="inventory-actions">
                                <button type="button" data-action="save-product">Save Changes</button>
                                <button type="button" class="ghost-button" data-action="upload-image">Upload Image</button>
                                <button type="button" class="danger-button" data-action="delete-product">Delete</button>
                            </div>
                        </div>
                    </article>
                `;
            })
            .join("");
    }

    async function handleProductActions(event) {
        const button = event.target.closest("button[data-action]");
        if (!button) {
            return;
        }

        const card = button.closest("[data-product-id]");
        const productId = card.dataset.productId;

        try {
            if (button.dataset.action === "save-product") {
                utils.setButtonBusy(button, true, "Saving...");
                const payload = {
                    name: card.querySelector('[data-field="name"]').value.trim(),
                    category: card.querySelector('[data-field="category"]').value.trim(),
                    price: Number(card.querySelector('[data-field="price"]').value),
                    stock: Number(card.querySelector('[data-field="stock"]').value)
                };
                await api.put(`/admin/products/${productId}`, payload, { auth: true });
                utils.showMessage("admin-status", "Product updated successfully.", "success");
                await loadProducts();
            }

            if (button.dataset.action === "upload-image") {
                const imageInput = card.querySelector('[data-role="image-input"]');
                if (!imageInput.files[0]) {
                    utils.showMessage("admin-status", "Choose an image before uploading.", "error");
                    return;
                }
                utils.setButtonBusy(button, true, "Uploading...");
                await uploadProductImage(productId, imageInput.files[0]);
                utils.showMessage("admin-status", "Product image uploaded successfully.", "success");
                await loadProducts();
            }

            if (button.dataset.action === "delete-product") {
                const shouldDelete = window.confirm("Delete this product from the catalog?");
                if (!shouldDelete) {
                    return;
                }
                utils.setButtonBusy(button, true, "Deleting...");
                await api.remove(`/admin/products/${productId}`, { auth: true });
                utils.showMessage("admin-status", "Product deleted successfully.", "success");
                await loadProducts();
            }
        } catch (error) {
            utils.showMessage("admin-status", error.message, "error");
        } finally {
            utils.setButtonBusy(button, false);
        }
    }

    async function uploadProductImage(productId, file) {
        const formData = new FormData();
        formData.append("image", file);
        await api.put(`/admin/products/${productId}/image`, formData, {
            auth: true,
            formData: true
        });
    }

    function renderOrders() {
        const list = document.getElementById("admin-order-list");
        if (!state.orders.length) {
            list.innerHTML = utils.emptyState("Orders will appear here once users start buying.");
            return;
        }

        list.innerHTML = state.orders
            .map((order) => {
                const items = order.products
                    .map((item) => `${utils.escapeHtml(item.name)} x ${item.quantity}`)
                    .join(", ");

                let actions = '<div class="muted">Pending orders are accepted from the delivery dashboard.</div>';
                if (order.status === "assigned") {
                    actions = `
                        <div class="button-row">
                            <button type="button" data-action="deliver-order" data-order-id="${order.id}">Mark Delivered</button>
                            <button type="button" class="ghost-button" data-action="reset-order" data-order-id="${order.id}">Reset to Pending</button>
                        </div>
                    `;
                } else if (order.status === "delivered") {
                    actions = `
                        <div class="button-row">
                            <button type="button" class="ghost-button" data-action="reset-order" data-order-id="${order.id}">Reset to Pending</button>
                        </div>
                    `;
                }

                return `
                    <article class="order-card">
                        <div class="card-actions">
                            <h3 class="card-title">Order #${utils.escapeHtml(order.id.slice(-6))}</h3>
                            ${utils.statusPill(order.status)}
                        </div>
                        <div class="stack" style="margin-top: 0.85rem;">
                            <div class="detail-row"><span>Customer</span><strong>${utils.escapeHtml(order.customerName || "Unknown")}</strong></div>
                            <div class="detail-row"><span>Placed</span><strong>${utils.formatDate(order.createdAt)}</strong></div>
                            <div class="detail-row"><span>Address</span><strong>${utils.escapeHtml(order.deliveryAddress || "Not provided")}</strong></div>
                            <div class="detail-row"><span>Items</span><strong>${utils.escapeHtml(items)}</strong></div>
                            <div class="detail-row"><span>Total</span><strong>${utils.formatCurrency(order.totalPrice)}</strong></div>
                            <div class="detail-row"><span>Delivery</span><strong>${utils.escapeHtml(order.deliveryPersonName || "Unassigned")}</strong></div>
                            ${actions}
                        </div>
                    </article>
                `;
            })
            .join("");
    }

    function updateOverview() {
        setText("admin-stat-products", state.products.length);
        setText("admin-stat-low-stock", state.products.filter((product) => Number(product.stock) < 5).length);
        setText("admin-stat-pending", state.orders.filter((order) => order.status === "pending").length);
        setText("admin-stat-delivered", state.orders.filter((order) => order.status === "delivered").length);
    }

    async function handleOrderActions(event) {
        const button = event.target.closest("button[data-action]");
        if (!button) {
            return;
        }

        const orderId = button.dataset.orderId;
        const nextStatus = button.dataset.action === "deliver-order" ? "delivered" : "pending";

        try {
            utils.setButtonBusy(button, true, "Updating...");
            await api.put(`/orders/${orderId}/status`, { status: nextStatus }, { auth: true });
            utils.showMessage("admin-status", "Order status updated successfully.", "success");
            await loadOrders();
        } catch (error) {
            utils.showMessage("admin-status", error.message, "error");
        } finally {
            utils.setButtonBusy(button, false);
        }
    }

    function setText(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = String(value);
        }
    }
})();
