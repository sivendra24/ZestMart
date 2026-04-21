const path = require("path");

const cartUtils = require(path.resolve(__dirname, "../../frontend/js/cart_utils.js"));

const startingProducts = [
    { id: "apple", name: "Fresh Apples", price: 120, stock: 2 },
    { id: "bread", name: "Whole Wheat Bread", price: 55, stock: 0 }
];

const staleCart = new Map([
    ["apple", { quantity: 4 }],
    ["bread", { quantity: 1 }]
]);

const { items, adjustments } = cartUtils.reconcileCartItems(staleCart, startingProducts);
if (items.get("apple").quantity !== 2) {
    throw new Error("Expected apple quantity to clamp to current stock.");
}
if (items.has("bread")) {
    throw new Error("Expected out-of-stock item to be removed from the cart.");
}
if (adjustments.clamped.length !== 1 || adjustments.removed.length !== 1) {
    throw new Error("Expected both clamp and removal adjustments.");
}

const repricedProducts = [
    { id: "apple", name: "Fresh Apples", price: 130, stock: 2 }
];

const liveEntries = cartUtils.getCartEntries(items, repricedProducts);
if (liveEntries[0].product.price !== 130) {
    throw new Error("Expected cart entries to use the latest product price.");
}

const total = cartUtils.calculateCartTotal(items, repricedProducts);
if (total !== 260) {
    throw new Error(`Expected cart total to use the live product price. Received ${total}.`);
}
