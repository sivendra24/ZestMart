
# ZestMart

ZestMart is a production-oriented role-based online mart system with OTP registration for students, JWT authentication, MongoDB persistence, admin-managed products, and delivery order handling.

## Tech Stack

- Frontend: HTML, CSS, Vanilla JavaScript
- Backend: Flask
- Database: MongoDB
- Security: bcrypt + JWT

## Features

- Student OTP registration with 5-minute expiry
- Server-side OTP rate limiting and maximum verification attempts
- Student profile address capture for delivery
- Dual login mode for students and staff
- Role-based dashboard access
- Admin product CRUD and atomic image upload
- Public product listing
- Cart-based order placement
- Delivery acceptance and delivery completion flow
- Seed data for quick testing

## Project Structure

```text
frontend/
backend/
docs/
.env
README.md
```

## Setup

1. Create and activate a Python virtual environment.
2. Install backend dependencies:

```bash
pip install -r backend/requirements.txt
```

3. Ensure MongoDB is running locally or update `.env` with your MongoDB URI.
4. Create `.env` from `.env.example` and set strong values for both `SECRET_KEY` and `JWT_SECRET_KEY`.

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

5. Seed the database:

```bash
python backend/database/seed_data.py
```

This seed script is non-destructive: it inserts missing sample data without overwriting existing users or products.

6. Start the application:

```bash
python backend/app.py
```

7. Open [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Default Seed Credentials

- Admin: `admin001` / `Admin@123`
- Delivery: `delivery001` / `Delivery@123`
- Student: `9876543210` / `Student@123`

## OTP Registration Flow

1. Open the landing page.
2. Choose `Student Register`.
3. Send OTP to the phone number.
4. Verify the OTP.
5. Add the student delivery address.
6. Create the student account.

When `MOCK_OTP_ENABLED=true`, the API returns a mock OTP in the response for local testing and does not send an SMS.
When `MOCK_OTP_ENABLED=false`, configure Twilio credentials in `.env` so OTPs can be sent to real mobile numbers.

OTP protection settings:

- `OTP_EXPIRY_MINUTES`
- `OTP_RATE_LIMIT_WINDOW_MINUTES`
- `OTP_MAX_SENDS_PER_WINDOW`
- `OTP_MAX_VERIFICATION_ATTEMPTS`

Required Twilio settings for real SMS delivery:

- `SMS_PROVIDER=twilio`
- `SMS_DEFAULT_COUNTRY_CODE=+91`
- `TWILIO_ACCOUNT_SID=...`
- `TWILIO_AUTH_TOKEN=...`
- `TWILIO_FROM_PHONE=...` or `TWILIO_MESSAGING_SERVICE_SID=...`

## Notes

- Uploaded product images are stored in `backend/uploads/products/`.
- Protected API calls require a `Bearer` token.
- Product creation now accepts metadata and an optional image in one backend-controlled request.
- Each order stores a delivery address snapshot so delivery personnel know exactly where to go.
- The frontend is served directly by Flask, so no separate frontend server is required.
- `start.bat` only auto-seeds when the database is empty, so normal restarts do not reset live data.

## Documentation

- [Architecture](docs/architecture.md)
- [API Docs](docs/api_docs.md)
- [Database Schema](docs/database_schema.md)

## Netlify Deployment

This repository can now be deployed to Netlify in two ways:

1. Demo mode:
   If no backend is attached, the site stays usable on Netlify with browser-local demo data for login, OTP, products, cart, admin, and delivery flows.
2. Live backend mode:
   Connect Netlify to a real Flask + MongoDB backend for shared production data.

Production setup:

1. Deploy the Flask backend to a Python-capable host such as Render, Railway, or a VPS.
2. Keep `JWT_COOKIE_DOMAIN` empty on the backend.
3. Set `JWT_COOKIE_SECURE=true` on the backend when using HTTPS.
4. In Netlify, set the environment variable `ZESTMART_BACKEND_URL` to your live backend URL, for example `https://your-backend.example.com`.
5. Redeploy Netlify after setting the environment variable.

Netlify now uses:

- [netlify.toml](netlify.toml) to publish the `frontend/` directory and map clean routes like `/student`
- [netlify/functions/backend-proxy.js](netlify/functions/backend-proxy.js) to proxy `/api/*` and `/uploads/*` requests to the backend

Demo credentials on a frontend-only Netlify deploy:

- Admin: `admin001` / `Admin@123`
- Delivery: `delivery001` / `Delivery@123`
- Student: `9876543210` / `Student@123`
