(function (root, factory) {
    const exported = factory();

    if (typeof module === "object" && module.exports) {
        module.exports = exported;
    }

    root.ZestMartCartUtils = exported;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
    function createProductIndex(products) {
        return new Map((products || []).map((product) => [product.id, product]));
    }

    function normalizeCartEntries(cartItems) {
        if (cartItems instanceof Map) {
            return Array.from(cartItems.entries());
        }

        return Object.entries(cartItems || {});
    }

    function roundCurrency(value) {
        return Math.round((Number(value || 0) + Number.EPSILON) * 100) / 100;
    }

    function getSafeStock(product) {
        return Math.max(0, Number(product?.stock || 0));
    }

    function reconcileCartItems(cartItems, products) {
        const productIndex = createProductIndex(products);
        const nextItems = new Map();
        const adjustments = {
            removed: [],
            clamped: []
        };

        normalizeCartEntries(cartItems).forEach(([productId, item]) => {
            const product = productIndex.get(productId);
            if (!product) {
                adjustments.removed.push({ productId, reason: "missing" });
                return;
            }

            const availableStock = getSafeStock(product);
            if (availableStock < 1) {
                adjustments.removed.push({
                    productId,
                    reason: "out-of-stock",
                    name: product.name
                });
                return;
            }

            const requestedQuantity = Math.max(1, Number.parseInt(item?.quantity, 10) || 0);
            const nextQuantity = Math.min(requestedQuantity, availableStock);
            nextItems.set(productId, { quantity: nextQuantity });

            if (nextQuantity !== requestedQuantity) {
                adjustments.clamped.push({
                    productId,
                    name: product.name,
                    from: requestedQuantity,
                    to: nextQuantity
                });
            }
        });

        return { items: nextItems, adjustments };
    }

    function getCartEntries(cartItems, products) {
        const productIndex = createProductIndex(products);

        return normalizeCartEntries(cartItems)
            .map(([productId, item]) => {
                const product = productIndex.get(productId);
                if (!product) {
                    return null;
                }

                const quantity = Math.max(1, Number.parseInt(item?.quantity, 10) || 0);
                return {
                    productId,
                    quantity,
                    product,
                    subtotal: roundCurrency(quantity * Number(product.price || 0))
                };
            })
            .filter(Boolean);
    }

    function calculateCartTotal(cartItems, products) {
        return roundCurrency(
            getCartEntries(cartItems, products).reduce((total, entry) => total + entry.subtotal, 0)
        );
    }

    return {
        calculateCartTotal,
        getCartEntries,
        reconcileCartItems
    };
});
