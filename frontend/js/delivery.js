(function () {
    const api = window.ZestMartApi;
    const utils = window.ZestMartUtils;
    const state = {
        currentUser: null,
        pendingOrders: [],
        assignedOrders: []
    };

    document.addEventListener("DOMContentLoaded", init);

    async function init() {
        const user = await utils.guardRoute(["delivery", "admin"]);
        if (!user) {
            return;
        }

        state.currentUser = user;

        utils.bindLogoutButtons();
        utils.fillUserBadge("delivery-user-name", "delivery-user-role", user);
        utils.populateRoleLinks("delivery-nav-links", user);

        document.getElementById("refresh-delivery-orders").addEventListener("click", loadDashboard);
        document.getElementById("pending-order-list").addEventListener("click", handlePendingActions);
        document.getElementById("assigned-order-list").addEventListener("click", handleAssignedActions);

        await loadDashboard();
    }

    async function loadDashboard() {
        try {
            const response = await api.get("/delivery/orders", { auth: true });
            state.pendingOrders = response.data.pendingOrders || [];
            state.assignedOrders = response.data.assignedOrders || [];
            renderPendingOrders();
            renderAssignedOrders();
            updateOverview();
        } catch (error) {
            utils.showMessage("delivery-status", error.message, "error");
        }
    }

    function renderPendingOrders() {
        const list = document.getElementById("pending-order-list");
        if (!state.pendingOrders.length) {
            list.innerHTML = utils.emptyState("No pending orders are waiting right now.");
            return;
        }

        list.innerHTML = state.pendingOrders
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
                            <div class="detail-row"><span>Customer</span><strong>${utils.escapeHtml(order.customerName || "Unknown")}</strong></div>
                            <div class="detail-row"><span>Phone</span><strong>${utils.escapeHtml(order.customerPhone || "Not provided")}</strong></div>
                            <div class="detail-row"><span>Address</span><strong>${utils.escapeHtml(order.deliveryAddress || "Not provided")}</strong></div>
                            <div class="detail-row"><span>Items</span><strong>${utils.escapeHtml(items)}</strong></div>
                            <div class="detail-row"><span>Total</span><strong>${utils.formatCurrency(order.totalPrice)}</strong></div>
                            ${renderPendingOrderAction(order)}
                        </div>
                    </article>
                `;
            })
            .join("");
    }

    function renderAssignedOrders() {
        const list = document.getElementById("assigned-order-list");
        if (!state.assignedOrders.length) {
            list.innerHTML = utils.emptyState("You do not have any assigned orders yet.");
            return;
        }

        list.innerHTML = state.assignedOrders
            .map((order) => {
                const items = order.products
                    .map((item) => `${utils.escapeHtml(item.name)} x ${item.quantity}`)
                    .join(", ");
                const deliverAction =
                    order.status === "assigned"
                        ? `<div class="button-row"><button type="button" data-action="deliver-order" data-order-id="${order.id}">Mark Delivered</button></div>`
                        : '<div class="muted">Delivery already completed.</div>';

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
                            ${deliverAction}
                        </div>
                    </article>
                `;
            })
            .join("");
    }

    async function handlePendingActions(event) {
        const button = event.target.closest('[data-action="accept-order"]');
        if (!button) {
            return;
        }

        if (!canAcceptOrders()) {
            utils.showMessage("delivery-status", "Only delivery personnel can accept pending orders.", "error");
            return;
        }

        try {
            utils.setButtonBusy(button, true, "Accepting...");
            await api.put(`/delivery/orders/${button.dataset.orderId}/accept`, {}, { auth: true });
            utils.showMessage("delivery-status", "Order accepted successfully.", "success");
            await loadDashboard();
        } catch (error) {
            utils.showMessage("delivery-status", error.message, "error");
        } finally {
            utils.setButtonBusy(button, false);
        }
    }

    async function handleAssignedActions(event) {
        const button = event.target.closest('[data-action="deliver-order"]');
        if (!button) {
            return;
        }

        try {
            utils.setButtonBusy(button, true, "Updating...");
            await api.put(`/orders/${button.dataset.orderId}/status`, { status: "delivered" }, { auth: true });
            utils.showMessage("delivery-status", "Order marked as delivered.", "success");
            await loadDashboard();
        } catch (error) {
            utils.showMessage("delivery-status", error.message, "error");
        } finally {
            utils.setButtonBusy(button, false);
        }
    }

    function updateOverview() {
        setText("delivery-stat-pending", state.pendingOrders.length);
        setText(
            "delivery-stat-assigned",
            state.assignedOrders.filter((order) => order.status === "assigned").length
        );
        setText(
            "delivery-stat-completed",
            state.assignedOrders.filter((order) => order.status === "delivered").length
        );
    }

    function canAcceptOrders() {
        return state.currentUser?.role === "delivery";
    }

    function renderPendingOrderAction(order) {
        if (canAcceptOrders()) {
            return `
                <div class="button-row">
                    <button type="button" data-action="accept-order" data-order-id="${order.id}">Accept Order</button>
                </div>
            `;
        }

        return '<div class="muted">Admins can review pending orders here, but only delivery users can claim them.</div>';
    }

    function setText(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = String(value);
        }
    }
})();
