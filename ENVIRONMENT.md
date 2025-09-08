# Environment Variables

Create `.env` files locally (do not commit). Example keys:

Root (optional for compose):
- POSTGRES_USER=swx
- POSTGRES_PASSWORD=swxpassword
- POSTGRES_DB=swx
- RABBITMQ_DEFAULT_USER=guest
- RABBITMQ_DEFAULT_PASS=guest
- QUEUE_NEW_TOKEN=new_token_unprocessed
- QUEUE_TRADES=pumpfun_trades

Ingestion (.env):
- RPC_WSS_ENDPOINT=wss://mainnet.helius-rpc.com/?api-key=YOUR_KEY
- PUMPFUN_PROGRAM_ID=6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P
- RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
- QUEUE_NEW_TOKEN=new_token_unprocessed
- QUEUE_TRADES=pumpfun_trades
- RECONNECT_MAX_BACKOFF_MS=30000
- HELIUS_API_KEY=YOUR_KEY

Analytics (.env):
- DATABASE_URL=postgresql+asyncpg://swx:swxpassword@postgres:5432/swx
- RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
- QUEUE_NEW_TOKEN=new_token_unprocessed
- QUEUE_TRADES=pumpfun_trades
- HELIUS_API_KEY=
- SOLANATRACKER_DATA_API_KEY=
- BITQUERY_API_KEY=
- TWITTER_BEARER_TOKEN=
- APIVOID_API_KEY=
- TELEGRAM_API_ID=
- TELEGRAM_API_HASH=
- TELEGRAM_SESSION=
- RPC_HTTP_ENDPOINT=https://api.mainnet-beta.solana.com

Frontend (.env):
- NEXT_PUBLIC_WS_API_URL=ws://localhost:8000/ws
- NEXT_PUBLIC_API_BASE=http://localhost:8000
- NEXT_PUBLIC_ADMIN_USER=admin
- NEXT_PUBLIC_ADMIN_PASS=changeme
