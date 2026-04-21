# ZestMart API Documentation

All responses use the structure:

```json
{
  "success": true,
  "message": "Human-readable message",
  "data": {}
}
```

## Auth Routes

### `POST /auth/send-otp`

Request:

```json
{
  "phone": "9876543210"
}
```

Response data includes:

- `maskedPhone`
- `expiresInMinutes`
- `deliveryMode` as `sms` or `mock`
- `otpPreview` only when `deliveryMode` is `mock`

Rate limits:

- Maximum `OTP_MAX_SENDS_PER_WINDOW` requests per `OTP_RATE_LIMIT_WINDOW_MINUTES`
- Returns `429` when the limit is exceeded

### `POST /auth/verify-otp`

Request:

```json
{
  "phone": "9876543210",
  "otp": "123456"
}
```

Notes:

- OTP expires after `OTP_EXPIRY_MINUTES`
- Verification is locked after `OTP_MAX_VERIFICATION_ATTEMPTS`

### `POST /auth/register`

Request:

```json
{
  "name": "Campus Shopper",
  "phone": "9876543210",
  "password": "Student@123",
  "address": "Boys Hostel Block A, Room 204, North Campus"
}
```

### `POST /auth/login/student`

Request:

```json
{
  "phone": "9876543210",
  "password": "Student@123"
}
```

### `POST /auth/login/staff`

Request:

```json
{
  "userId": "admin001",
  "password": "Admin@123"
}
```

## Product Routes

### `GET /products`

Public endpoint to fetch the product catalog.

### `POST /admin/products`

Auth: `admin`

Accepted request types:

- `application/json`
- `multipart/form-data`

Request fields:

```json
{
  "name": "Citrus Juice",
  "price": 120,
  "category": "Beverages",
  "stock": 20
}
```

Optional multipart field:

- `image`

### `PUT /admin/products/:id`

Auth: `admin`

Partial or full product payload:

```json
{
  "name": "Citrus Juice",
  "price": 130,
  "category": "Beverages",
  "stock": 18
}
```

### `DELETE /admin/products/:id`

Auth: `admin`

### `PUT /admin/products/:id/image`

Auth: `admin`

Request content type: `multipart/form-data`

Field name:

- `image`

## Order Routes

### `POST /orders`

Auth: `student`, `delivery`, `admin`

Request:

```json
{
  "deliveryAddress": "Boys Hostel Block A, Room 204, North Campus",
  "products": [
    {
      "productId": "PRODUCT_ID",
      "quantity": 2
    }
  ]
}
```

### `GET /orders`

Auth: `student`, `delivery`, `admin`

- Students and delivery users receive their own orders.
- Admin receives all orders.

### `PUT /orders/:id/status`

Auth: `delivery`, `admin`

Request:

```json
{
  "status": "delivered"
}
```

Admin can also reset an order to pending:

```json
{
  "status": "pending"
}
```

## Delivery Routes

### `GET /delivery/orders`

Auth: `delivery`, `admin`

Returns:

- `pendingOrders`
- `assignedOrders`

### `PUT /delivery/orders/:id/accept`

Auth: `delivery`

Marks a pending order as assigned to the current delivery user.
