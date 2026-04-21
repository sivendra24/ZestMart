# ZestMart Architecture

## Overview

ZestMart is a role-based web application built with a multi-page HTML/CSS/JavaScript frontend and a Flask + MongoDB backend. The application follows a layered clean architecture:

Frontend -> Routes -> Controllers -> Services -> Models -> MongoDB

Each layer has one responsibility:

- `routes/` exposes HTTP endpoints and applies middleware.
- `controllers/` translate HTTP requests into service calls and normalize responses.
- `services/` contain business logic and cross-collection workflows.
- `models/` define document shapes and serialization.
- `middleware/` enforces authentication, authorization, and upload validation.
- `database/` bootstraps MongoDB and collection indexes.
- `utils/` centralize reusable security and formatting helpers.

## Backend Responsibilities

### Authentication

- Students register using mobile number + password with OTP verification.
- OTP documents are stored in MongoDB with expiration and a TTL index.
- OTP send rate limits are tracked server-side per phone number.
- Passwords and OTP values are hashed with `bcrypt`.
- JWT tokens carry `sub`, `role`, `phone`, and `userId`.

### Role-Based Access

- `student`: can browse products and place/view own orders.
- `delivery`: can browse products, place/view own orders, access delivery dashboard, accept orders, and mark assigned orders as delivered.
- `admin`: can manage products and view/update all orders.

### Product Management

- Admin-only CRUD endpoints manage product catalog state.
- Product creation can persist the initial image upload in the same backend request.
- Product images are uploaded via multipart form data and stored under `backend/uploads/products/`.
- Image URLs are persisted in MongoDB and served by Flask.

### Order Flow

- Authenticated users can place orders.
- Product stock is decremented atomically during checkout.
- Delivery personnel accept pending orders from the delivery dashboard.
- Admin or assigned delivery personnel can move order status forward.

## Frontend Responsibilities

- `index.html` handles student OTP onboarding and both login modes.
- `student.html` provides shopping, cart, and order history.
- `admin.html` provides product management and order oversight.
- `delivery.html` provides pending/assigned order operations.

Client-side JavaScript is split by responsibility:

- `config.js`: runtime configuration.
- `utils.js`: session handling, formatting, and UI helpers.
- `api.js`: fetch wrapper and token injection.
- `auth.js`, `student.js`, `admin.js`, `delivery.js`: role-specific behavior.

## Security Notes

- Passwords are never stored in plain text.
- OTP values are also hashed before persistence.
- Protected endpoints require Bearer tokens.
- Role middleware prevents cross-dashboard privilege escalation.
- File uploads are extension-validated and stored with generated file names.
- Max upload size is controlled by `.env`.

## Scalability Notes

- Business logic is isolated in services, allowing easy refactoring into separate domains later.
- Collection indexes are created on startup for core query paths.
- The current implementation uses local image storage, but the `file_helper` abstraction allows migration to cloud object storage later.
- The frontend uses a clear shared utility layer so it can be upgraded to a framework without changing the API contract.
