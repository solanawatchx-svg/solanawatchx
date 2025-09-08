import asyncio
import json
import os
from typing import Any

import aio_pika
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import time

from ..db import AsyncSessionLocal
from ..models import Token, Trade, HolderMetric
from ..services.metrics import creator_wallet_age_seconds
from ..services.holders import compute_holder_metrics
from ..services.dex import derive_tvs_adjustments_from_dex
from ..scoring import aggregate_sws
from ..services.socials import simple_chs_from_sources, domain_age

QUEUE_NEW_TOKEN = os.getenv("QUEUE_NEW_TOKEN", "new_token_unprocessed")
QUEUE_TRADES = os.getenv("QUEUE_TRADES", "pumpfun_trades")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
EXCHANGE_EVENTS = os.getenv("EXCHANGE_EVENTS", "swx_events")

async def compute_cts_basic(creator: str) -> int:
	age = await creator_wallet_age_seconds(creator)
	if age <= 72 * 3600:
		return 20
	elif age <= 7 * 24 * 3600:
		return 50
	else:
		return 80

async def emit_event(channel: aio_pika.Channel, event: dict[str, Any]) -> None:
	exchange = await channel.declare_exchange(EXCHANGE_EVENTS, aio_pika.ExchangeType.FANOUT, durable=True)
	await exchange.publish(aio_pika.Message(body=json.dumps(event).encode()), routing_key="")

async def recompute_token_scores(session: AsyncSession, token: Token) -> None:
	m = await compute_holder_metrics(token.mint_address)
	token.gini = m.get("gini")
	token.nakamoto = m.get("nakamoto")
	session.add(HolderMetric(mint_address=token.mint_address, taken_at=int(time.time()), gini=float(token.gini or 0), nakamoto=int(token.nakamoto or 0), data=m))
	tvs = 70
	if (token.gini or 0) > 0.8:
		tvs -= 30
	if (token.nakamoto or 0) < 5:
		tvs -= 20
	tvs += await derive_tvs_adjustments_from_dex(token.mint_address)
	token.tvs = max(0, min(100, tvs))
	meta = token.metadata or {}
	links_str = json.dumps(meta).lower()
	has_tw = ('twitter.com' in links_str) or ('x.com' in links_str)
	has_tg = ('t.me' in links_str) or ('telegram.me' in links_str)
	domain_days = 0
	try:
		for k in ["website", "site", "url"]:
			if isinstance(meta.get(k), str):
				host = meta[k].split('//')[-1].split('/')[0]
				domain_days = await domain_age(host)
				break
	except Exception:
		pass
	token.chs = await simple_chs_from_sources(has_tw, has_tg, domain_days)
	token.cts = await compute_cts_basic(token.creator_wallet)
	token.sws = aggregate_sws("launch", token.cts or 0, token.tvs or 0, token.chs or 0)
	token.scores_updated_at = int(time.time())

async def upsert_token(session: AsyncSession, payload: dict[str, Any]) -> Token | None:
	mint = payload.get("mint_address") or payload.get("mint") or payload.get("signature")
	creator = payload.get("creator_wallet_address") or payload.get("creator") or ''
	ts = payload.get("timestamp") or payload.get("creation_timestamp") or 0
	if not mint:
		return None
	res = await session.execute(select(Token).where(Token.mint_address == str(mint)))
	existing = res.scalar_one_or_none()
	if existing:
		existing.creation_ts = int(ts or existing.creation_ts or 0)
		existing.creator_wallet = str(creator or existing.creator_wallet or '')
		token = existing
	else:
		token = Token(mint_address=str(mint), creator_wallet=str(creator or ''), creation_ts=int(ts or 0), metadata=payload)
		session.add(token)
	await recompute_token_scores(session, token)
	return token

async def insert_trade(session: AsyncSession, payload: dict[str, Any]) -> None:
	sig = payload.get("signature") or payload.get("sig")
	mint = payload.get("mint_address") or (payload.get("payload") or {}).get("tokenTransfers", [{}])[0].get("mint")
	if not sig:
		return
	session.add(Trade(signature=str(sig), mint_address=(str(mint) if mint else None), program=str(payload.get("program") or ''), timestamp=int(payload.get("timestamp") or 0), payload=payload))

async def handle_message(msg: aio_pika.IncomingMessage) -> None:
	async with msg.process():
		try:
			payload = json.loads(msg.body)
			async with AsyncSessionLocal() as session:
				if msg.routing_key == QUEUE_NEW_TOKEN or msg.queue.name == QUEUE_NEW_TOKEN:
					token = await upsert_token(session, payload)
					await emit_event(msg.channel, {"type": "scores_updated"})
					await session.commit()
					await emit_event(msg.channel, {"type": "token_upserted"})
				else:
					await insert_trade(session, payload)
					await session.commit()
					await emit_event(msg.channel, {"type": "trade_inserted"})
		except Exception as e:
			print("[worker] error", e)

async def main() -> None:
	connection = await aio_pika.connect_robust(RABBITMQ_URL)
	channel = await connection.channel()
	await channel.set_qos(prefetch_count=16)
	q_new = await channel.declare_queue(QUEUE_NEW_TOKEN, durable=True)
	q_trd = await channel.declare_queue(QUEUE_TRADES, durable=True)
	await q_new.consume(handle_message)
	await q_trd.consume(handle_message)
	print("[worker] consuming queues:", QUEUE_NEW_TOKEN, QUEUE_TRADES)
	try:
		while True:
			await asyncio.sleep(5)
	except KeyboardInterrupt:
		pass

if __name__ == "__main__":
	asyncio.run(main())
