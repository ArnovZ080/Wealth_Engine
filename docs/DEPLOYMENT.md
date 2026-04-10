# Wealth Engine Production Deployment Guide

This guide outlines the steps to deploy the Recursive Fractal Wealth Engine in a production-hardened environment using Docker Compose and Nginx.

## Prerequisites
- Docker & Docker Compose
- Domain name (with A records pointing to your server)
- SSL Certificates (optional, but recommended)
- API Keys:
  - `INVESTEC_CLIENT_ID` / `CLIENT_SECRET` (Programmable Banking)
  - `TELEGRAM_BOT_TOKEN` / `MASTER_CHAT_ID`
  - `GEMINI_API_KEY` (Alpha Hunter)
  - `CLAUDE_API_KEY` (Shadow Agent)

## 1. Environment Setup
Copy `.env.example` to `.env` and fill in the production secrets.

```bash
cp .env.example .env
# Edit .env with your real credentials
```

## 2. Infrastructure Configuration
Nginx is configured to serve the frontend on `/` and proxy API requests to `/api`.

- **Backups**: A dedicated `backup` container runs daily pg_dumps into `./infra/postgres/backups`.
- **Health Checks**: The system monitors DB and API vitals via `docker-compose` healthchecks.

## 3. Launching the Engine
Deploy the stack using Docker Compose:

```bash
docker-compose up -d --build
```

Verify services are running:
```bash
docker-compose ps
```

## 4. Initial Database Migration
Once the DB is up, run the migrations:

```bash
docker-compose exec backend alembic upgrade head
```

## 5. Security Notes
- **JWT**: Ensure `JWT_SECRET_KEY` is a long, random string.
- **Encryption**: `CREDENTIAL_ENCRYPTION_KEY` must be a valid Fernet key.
- **CORS**: Update `app/main.py` CORS settings to your production domain.

## Monitoring
Check system health via the `/api/v1/health` endpoint.
Trade alerts will be sent to your configured Telegram Master Chat ID.
