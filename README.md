# SolanaWatchX Monorepo

SolanaWatchX is a real-time intelligence and risk assessment platform for Solana pump.fun token launches.

- packages/ingestion-service (Node.js + TypeScript): WebSocket ingestion -> RabbitMQ
- packages/analytics-service (Python + FastAPI): API + workers compute CTS/TVS/CHS and SWS; persists tokens/trades/history
- packages/frontend-app (Next.js + React): Real-time dashboard, tokens view, admin page
- infra/ (Docker, Docker Compose, Kubernetes)

Quick start (Docker Compose):
1) Copy envs from ENVIRONMENT.md into .env files
- cp .env.example .env (optional if used)
- cp packages/ingestion-service/.env.example packages/ingestion-service/.env
- cp packages/analytics-service/.env.example packages/analytics-service/.env
- cp packages/frontend-app/.env.example packages/frontend-app/.env

2) Start stack
- docker compose -f infra/docker-compose.yml up --build

Access:
- Frontend: http://localhost:3000 (admin at /admin)
- Analytics API: http://localhost:8000 (docs: /docs)
- RabbitMQ: http://localhost:15672 (guest/guest)
- Postgres: localhost:5432 (user: swx, db: swx)

Security:
- Never request/handle user private keys.
- Validate and rate-limit third-party API responses.
- Keep secrets out of VCS and use K8s Secrets in prod.

