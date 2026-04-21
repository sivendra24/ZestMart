# ZestMart Database Schema

## Collections

### `users`

Fields:

- `name`
- `phone`
- `address`
- `userId`
- `password`
- `role`
- `isVerified`
- `createdAt`

Indexes:

- unique sparse index on `phone`
- unique sparse index on `userId`
- index on `role`

### `otps`

Fields:

- `phone`
- `otp` (bcrypt hash of the OTP code)
- `expiresAt`
- `verified`
- `verifiedAt`
- `attemptCount`
- `maxAttempts`
- `createdAt`
- `updatedAt`

Indexes:

- unique sparse index on `phone`
- TTL index on `expiresAt`

### `otp_rate_limits`

Fields:

- `phone`
- `requestCount`
- `windowStartedAt`
- `windowExpiresAt`
- `lastRequestedAt`

Indexes:

- unique sparse index on `phone`
- TTL index on `windowExpiresAt`

### `products`

Fields:

- `name`
- `price`
- `category`
- `stock`
- `imageUrl`
- `createdAt`
- `updatedAt`

Indexes:

- index on `name`
- index on `category`

### `orders`

Fields:

- `userId`
- `userRole`
- `customerName`
- `customerPhone`
- `deliveryAddress`
- `products[]`
- `totalPrice`
- `status`
- `deliveryPersonId`
- `deliveryPersonUserId`
- `deliveryPersonName`
- `createdAt`
- `updatedAt`

Indexes:

- index on `status`
- index on `userId`
- index on `deliveryPersonId`

## Embedded `products[]` Snapshot

Each order stores a snapshot of the ordered products:

- `productId`
- `name`
- `category`
- `price`
- `quantity`
- `subtotal`
- `imageUrl`

This prevents order history from changing when the live catalog changes.
