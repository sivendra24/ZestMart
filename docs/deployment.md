# ZestMart Deployment

## Production Runtime

- WSGI entry point: `backend/wsgi.py`
- Gunicorn config: `backend/gunicorn.conf.py`
- Docker image: `Dockerfile`
- Reverse proxy: `deploy/nginx/zestmart.conf`

## Git Setup

```bash
git init -b main
git add .
git commit -m "Prepare ZestMart for production deployment"
git remote add origin https://github.com/<your-org-or-user>/zestmart.git
git push -u origin main
```

## Local Production-Like Stack

1. Copy `.env.production.example` to `.env.production`
2. Fill every placeholder secret and Twilio credential
3. Place TLS files at:

```text
deploy/certs/fullchain.pem
deploy/certs/privkey.pem
```

4. Start the stack:

```bash
docker compose --env-file .env.production up --build -d
```

5. Check health:

```bash
curl -I https://zestmart.example.com/health
```

## Linux Host Without Docker

Install dependencies:

```bash
python -m pip install -r backend/requirements.txt
```

Run Gunicorn:

```bash
gunicorn --config backend/gunicorn.conf.py --chdir backend wsgi:app
```
