(function () {
    const api = window.ZestMartApi;
    const cartUtils = window.ZestMartCartUtils;
    const utils = window.ZestMartUtils;
    const state = {
        products: [],
        orders: [],
        cart: new Map()
    };

    document.addEventListener("DOMContentLoaded", init);

    async function init() {
        const user = await utils.guardRoute(["student", "delivery", "admin"]);
        if (!user) {
            return;
        }

        utils.bindLogoutButtons();
        utils.fillUserBadge("student-user-name", "student-user-role", user);
        utils.populateRoleLinks("student-nav-links", user);
        const welcomeName = document.getElementById("student-welcome-name");
        if (welcomeName) {
            welcomeName.textContent = user.name || user.userId || user.phone || "Shopper";
        }
        const addressField = document.getElementById("delivery-address");
        if (addressField && user.address) {
            addressField.value = user.address;
        }

        document.getElementById("refresh-products-button").addEventListener("click", loadProducts);
        document.getElementById("refresh-orders-button").addEventListener("click", loadOrders);
        document.getElementById("checkout-button").addEventListener("click", placeOrder);
        document.getElementById("clear-cart-button").addEventListener("click", clearCart);
        document.getElementById("product-grid").addEventListener("click", handleProductGridClick);
        document.getElementById("cart-items").addEventListener("click", handleCartClick);
        document.getElementById("cart-items").addEventListener("change", handleCartChange);

        renderCart();
        updateOverview();
        await Promise.all([loadProducts(), loadOrders()]);
    }

    async function loadProducts(options) {
        const { notifyOnCartAdjustments = true } = options || {};

        try {
            const response = await api.get("/products");
            state.products = response.data || [];

            const adjustments = reconcileCart();
            renderProducts();
            renderCart();
            updateOverview();

            if (notifyOnCartAdjustments) {
                showCartAdjustmentMessage(adjustments);
            }

            return adjustments;
        } catch (error) {
            utils.showMessage("student-status", error.message, "error");
            return null;
        }
    }

    async function loadOrders() {
        try {
            const response = await api.get("/orders", { auth: true });
            state.orders = response.data || [];
            renderOrders();
            updateOverview();
        } catch (error) {
            utils.showMessage("student-status", error.message, "error");
        }
    }

    function renderProducts() {
        const grid = document.getElementById("product-grid");
        if (!state.products.length) {
            grid.innerHTML = utils.emptyState("No products are available right now.");
            return;
        }

        grid.innerHTML = state.products
            .map((product) => {
                const availableStock = Math.max(Number(product.stock || 0), 0);
                const image = product.imageUrl
                    ? `<img class="product-image" src="${utils.escapeHtml(product.imageUrl)}" alt="${utils.escapeHtml(product.name)}">`
                    : '<div class="product-image"></div>';
                const addButtonLabel = availableStock > 0 ? "Add to Cart" : "Out of Stock";
                const disabledAttribute = availableStock > 0 ? "" : "disabled";

                return `
                    <article class="product-card" data-product-id="${product.id}">
                        ${image}
                        <div class="stack" style="margin-top: 0.9rem;">
                            <div class="product-footer">
                                <div>
                                    <h3 class="product-title">${utils.escapeHtml(product.name)}</h3>
                                    <div class="muted">${utils.escapeHtml(product.category)}</div>
                                </div>
                                <strong>${utils.formatCurrency(product.price)}</strong>
                            </div>
                            <div class="product-footer">
                                <span class="pill">Stock: ${availableStock}</span>
                                <span class="muted">Updated ${utils.formatDate(product.updatedAt)}</span>
                            </div>
                            <div class="quantity-row">
                                <input type="number" min="1" max="${Math.max(availableStock, 1)}" value="1" data-role="quantity" ${disabledAttribute}>
                                <button type="button" data-add-to-cart ${disabledAttribute}>${addButtonLabel}</button>
                            </div>
                        </div>
                    </article>
                `;
            })
            .join("");
    }

    function handleProductGridClick(event) {
        const button = event.target.closest("[data-add-to-cart]");
        if (!button) {
            return;
        }

        const card = button.closest("[data-product-id]");
        const quantityInput = card.querySelector('[data-role="quantity"]');
        const quantity = Number(quantityInput.value);
        const productId = card.dataset.productId;
        const product = getProductById(productId);

        if (!product || Number(product.stock || 0) < 1 || quantity < 1) {
            utils.showMessage("student-status", "Choose a valid quantity before adding to cart.", "error");
            return;
        }

        const existingItem = state.cart.get(productId);
        const nextQuantity = (existingItem?.quantity || 0) + quantity;
        if (nextQuantity > Number(product.stock || 0)) {
            utils.showMessage("student-status", "Selected quantity exceeds available stock.", "error");
            return;
        }

        state.cart.set(productId, { quantity: nextQuantity });
        quantityInput.value = "1";
        renderCart();
        utils.showMessage("student-status", `${product.name} added to cart.`, "success");
    }

    function renderCart() {
        const cartItems = document.getElementById("cart-items");
        const totalElement = document.getElementById("cart-total");
        const entries = cartUtils.getCartEntries(state.cart, state.products);

        if (!entries.length) {
            cartItems.innerHTML = utils.emptyState("Your cart is empty.");
            totalElement.textContent = utils.formatCurrency(0);
            updateOverview();
            return;
        }

        cartItems.innerHTML = entries
            .map((entry) => `
                <div class="cart-item" data-product-id="${entry.productId}">
                    <div>
                        <strong>${utils.escapeHtml(entry.product.name)}</strong>
                        <div class="muted">${utils.formatCurrency(entry.product.price)} each</div>
                    </div>
                    <div class="quantity-row">
                        <input type="number" min="1" max="${Math.max(Number(entry.product.stock || 0), 1)}" value="${entry.quantity}" data-cart-quantity>
                        <button type="button" class="ghost-button" data-remove-cart>Remove</button>
                    </div>
                </div>
            `)
            .join("");

        totalElement.textContent = utils.formatCurrency(cartUtils.calculateCartTotal(state.cart, state.products));
        updateOverview();
    }

    function handleCartClick(event) {
        const removeButton = event.target.closest("[data-remove-cart]");
        if (!removeButton) {
            return;
        }

        const item = removeButton.closest("[data-product-id]");
        state.cart.delete(item.dataset.productId);
        renderCart();
    }

    function handleCartChange(event) {
        if (!event.target.matches("[data-cart-quantity]")) {
            return;
        }

        const itemElement = event.target.closest("[data-product-id]");
        const productId = itemElement.dataset.productId;
        const cartItem = state.cart.get(productId);
        const product = getProductById(productId);
        const quantity = Number(event.target.value);

        if (!cartItem || !product || quantity < 1 || quantity > Number(product.stock || 0)) {
            event.target.value = cartItem ? String(cartItem.quantity) : "1";
            utils.showMessage("student-status", "Enter a quantity within available stock.", "error");
            return;
        }

        state.cart.set(productId, { quantity });
        renderCart();
    }

    async function placeOrder() {
        const button = document.getElementById("checkout-button");
        const deliveryAddress = document.getElementById("delivery-address").value.trim();
        if (!state.cart.size) {
            utils.showMessage("student-status", "Add products to the cart before placing an order.", "error");
            return;
        }
        if (deliveryAddress.length < 10) {
            utils.showMessage("student-status", "Enter a full delivery address before placing the order.", "error");
            return;
        }

        try {
            utils.setButtonBusy(button, true, "Placing...");

            const adjustments = await loadProducts({ notifyOnCartAdjustments: false });
            if (adjustments === null) {
                return;
            }

            if (hasCartAdjustments(adjustments)) {
                showCartAdjustmentMessage(
                    adjustments,
                    "Cart updated to match the latest catalog data. Review the cart before placing the order."
                );
                return;
            }

            if (!state.cart.size) {
                utils.showMessage("student-status", "Your cart is empty after refreshing product availability.", "error");
                return;
            }

            const payload = {
                deliveryAddress,
                products: Array.from(state.cart.entries()).map(([productId, item]) => ({
                    productId,
                    quantity: item.quantity
                }))
            };

            await api.post("/orders", payload, { auth: true });
            clearCart();
            await Promise.all([loadProducts(), loadOrders()]);
            utils.showMessage("student-status", "Order placed successfully.", "success");
        } catch (error) {
            utils.showMessage("student-status", error.message, "error");
        } finally {
            utils.setButtonBusy(button, false);
        }
    }

    function clearCart() {
        state.cart.clear();
        renderCart();
    }

    function renderOrders() {
        const orderList = document.getElementById("order-list");
        if (!state.orders.length) {
            orderList.innerHTML = utils.emptyState("No orders found yet.");
            return;
        }

        orderList.innerHTML = state.orders
            .map((order) => {
                const items = order.products
                    .map((item) => `${utils.escapeHtml(item.name)} x ${item.quantity}`)
                    .join(", ");

                return `
                    <article class="order-card">
                        <div class="card-actions">
                            <h3 class="card-title">Order #${utils.escapeHtml(order.id.slice(-6))}</h3>
                            ${utils.statusPill(order.status)}
                        </div>
                        <div class="stack" style="margin-top: 0.85rem;">
                            <div class="detail-row"><span>Placed</span><strong>${utils.formatDate(order.createdAt)}</strong></div>
                            <div class="detail-row"><span>Items</span><strong>${utils.escapeHtml(items)}</strong></div>
                            <div class="detail-row"><span>Total</span><strong>${utils.formatCurrency(order.totalPrice)}</strong></div>
                            <div class="detail-row"><span>Address</span><strong>${utils.escapeHtml(order.deliveryAddress || "Not provided")}</strong></div>
                            <div class="detail-row"><span>Delivery</span><strong>${utils.escapeHtml(order.deliveryPersonName || "Awaiting assignment")}</strong></div>
                        </div>
                    </article>
                `;
            })
            .join("");

        updateOverview();
    }

    function reconcileCart() {
        const result = cartUtils.reconcileCartItems(state.cart, state.products);
        state.cart = result.items;
        return result.adjustments;
    }

    function hasCartAdjustments(adjustments) {
        return Boolean(adjustments && (adjustments.removed.length || adjustments.clamped.length));
    }

    function showCartAdjustmentMessage(adjustments, prefixMessage) {
        if (!hasCartAdjustments(adjustments)) {
            return;
        }

        const fragments = [];
        if (prefixMessage) {
            fragments.push(prefixMessage);
        }
        if (adjustments.clamped.length) {
            fragments.push(`${adjustments.clamped.length} item(s) had their quantity reduced to match current stock.`);
        }
        if (adjustments.removed.length) {
            fragments.push(`${adjustments.removed.length} item(s) were removed because they are no longer available.`);
        }

        utils.showMessage("student-status", fragments.join(" "), "info");
    }

    function getProductById(productId) {
        return state.products.find((item) => item.id === productId) || null;
    }

    function updateOverview() {
        setText("student-stat-products", state.products.length);
        setText("student-stat-cart-items", getCartItemCount());
        setText("student-stat-cart-value", utils.formatCurrency(getCartValue()));
        setText(
            "student-stat-active-orders",
            state.orders.filter((order) => order.status !== "delivered").length
        );
    }

    function getCartItemCount() {
        return Array.from(state.cart.values()).reduce((total, item) => total + item.quantity, 0);
    }

    function getCartValue() {
        return cartUtils.calculateCartTotal(state.cart, state.products);
    }

    function setText(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = String(value);
        }
    }
})();
