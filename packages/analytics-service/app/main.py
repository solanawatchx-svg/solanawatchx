from fastapi import FastAPI, WebSocket, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc
from .db import engine, Base, get_session
from .models import Token
from .scoring import score_creator_trust, score_token_viability, score_community_hype, aggregate_sws
from .websocket_manager import manager
import os
import asyncio
import aio_pika
import time
import uuid
from typing import Optional

from .services.metrics import creator_wallet_age_seconds
from .services.holders import compute_holder_metrics
from .services.dex import derive_tvs_adjustments_from_dex
from .services.socials import simple_chs_from_sources, domain_age

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
EXCHANGE_EVENTS = os.getenv("EXCHANGE_EVENTS", "swx_events")

app = FastAPI(title="SolanaWatchX Analytics API")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

_event_task: asyncio.Task | None = None

async def event_listener() -> None:
	connection: aio_pika.RobustConnection | None = None
	try:
		connection = await aio_pika.connect_robust(RABBITMQ_URL)
		channel = await connection.channel()
		exchange = await channel.declare_exchange(EXCHANGE_EVENTS, aio_pika.ExchangeType.FANOUT, durable=True)
		queue = await channel.declare_queue(exclusive=True, auto_delete=True)
		await queue.bind(exchange)
		async with queue.iterator() as qit:
			async for msg in qit:
				async with msg.process():
					try:
						await manager.broadcast_json({"type": "event", "data": msg.body.decode()})
					except Exception:
						pass
	finally:
		if connection:
			await connection.close()

@app.on_event("startup")
async def on_startup() -> None:
	async with engine.begin() as conn:
		await conn.run_sync(Base.metadata.create_all)
	global _event_task
	_event_task = asyncio.create_task(event_listener())

@app.on_event("shutdown")
async def on_shutdown() -> None:
	global _event_task
	if _event_task:
		_event_task.cancel()
		try:
			await _event_task
		except Exception:
			pass

@app.get("/health")
async def health() -> dict:
	return {"status": "ok"}

@app.get("/tokens")
async def list_tokens(
	session: AsyncSession = Depends(get_session),
	q: Optional[str] = Query(default=None),
	min_sws: Optional[int] = Query(default=None),
	max_age_min: Optional[int] = Query(default=None),
	sort: Optional[str] = Query(default="-id"),
	page: int = Query(default=1, ge=1),
	page_size: int = Query(default=20, ge=1, le=100),
):
	stmt = select(Token)
	count_stmt = select(func.count(Token.id))
	if q:
		like = f"%{q}%"
		stmt = stmt.where((Token.mint_address.ilike(like)) | (Token.creator_wallet.ilike(like)))
		count_stmt = count_stmt.where((Token.mint_address.ilike(like)) | (Token.creator_wallet.ilike(like)))
	if min_sws is not None:
		stmt = stmt.where((Token.sws >= min_sws))
		count_stmt = count_stmt.where((Token.sws >= min_sws))
	if max_age_min is not None:
		threshold = int(time.time()) - max_age_min * 60
		stmt = stmt.where(Token.creation_ts >= threshold)
		count_stmt = count_stmt.where(Token.creation_ts >= threshold)
	order_field = Token.id
	direction = desc
	if sort:
		direction = desc if sort.startswith("-") else asc
		name = sort[1:] if sort.startswith("-") else sort
		if name == "sws":
			order_field = Token.sws
		elif name == "creation_ts":
			order_field = Token.creation_ts
		elif name == "cts":
			order_field = Token.cts
		elif name == "tvs":
			order_field = Token.tvs
		elif name == "chs":
			order_field = Token.chs
		else:
			order_field = Token.id
	stmt = stmt.order_by(direction(order_field)).offset((page - 1) * page_size).limit(page_size)
	total = (await session.execute(count_stmt)).scalar_one()
	rows = (await session.execute(stmt)).scalars().all()
	items = [
		{
			"mint_address": r.mint_address,
			"creator_wallet": r.creator_wallet,
			"creation_ts": r.creation_ts,
			"cts": r.cts,
			"tvs": r.tvs,
			"chs": r.chs,
			"sws": r.sws,
		}
		for r in rows
	]
	return {"items": items, "total": total, "page": page, "page_size": page_size}

@app.get("/tokens/{mint}")
async def get_token(mint: str, session: AsyncSession = Depends(get_session)):
	res = await session.execute(select(Token).where(Token.mint_address == mint))
	t = res.scalar_one_or_none()
	if not t:
		return {"error": "not_found"}
	return {
		"mint_address": t.mint_address,
		"creator_wallet": t.creator_wallet,
		"creation_ts": t.creation_ts,
		"cts": t.cts,
		"tvs": t.tvs,
		"chs": t.chs,
		"sws": t.sws,
		"gini": t.gini,
		"nakamoto": t.nakamoto,
		"chs_sources": t.chs_sources or {},
	}

@app.post("/tokens/{mint}/refresh")
async def refresh_token(mint: str, session: AsyncSession = Depends(get_session)):
	res = await session.execute(select(Token).where(Token.mint_address == mint))
	t = res.scalar_one_or_none()
	if not t:
		return {"updated": 0}
	age = await creator_wallet_age_seconds(t.creator_wallet)
	cts = 20 if age <= 72*3600 else 50 if age <= 7*24*3600 else 80
	m = await compute_holder_metrics(t.mint_address)
	gini = m.get("gini") or 0
	nakamoto = m.get("nakamoto") or 0
	adj = await derive_tvs_adjustments_from_dex(t.mint_address)
	tvs = 70
	if gini > 0.8:
		tvs -= 30
	if nakamoto < 5:
		tvs -= 20
	tvs += adj
	meta = t.metadata or {}
	links_str = (str(meta)).lower()
	has_tw = ('twitter.com' in links_str) or ('x.com' in links_str)
	has_tg = ('t.me' in links_str) or ('telegram.me' in links_str)
	days = 0
	try:
		for k in ["website", "site", "url"]:
			if isinstance(meta.get(k), str):
				host = meta[k].split('//')[-1].split('/')[0]
				days = await domain_age(host)
				break
	except Exception:
		pass
	chs = await simple_chs_from_sources(has_tw, has_tg, days)
	sws = aggregate_sws("launch", cts, tvs, chs)
	t.cts, t.tvs, t.chs, t.sws = cts, tvs, chs, sws
	t.gini, t.nakamoto = gini, nakamoto
	t.chs_sources = {"has_twitter": has_tw, "has_telegram": has_tg, "domain_days": days}
	await session.commit()
	await manager.broadcast_json({"type": "scores_updated"})
	return {"updated": 1, "sws": sws}

@app.post("/scores/recompute")
async def recompute_scores(session: AsyncSession = Depends(get_session)):
	result = await session.execute(select(Token).order_by(Token.id.desc()).limit(100))
	tokens = result.scalars().all()
	for t in tokens:
		cts = score_creator_trust({
			"creator_wallet": t.creator_wallet,
			"creation_ts": t.creation_ts,
			"metadata": t.metadata or {},
		})
		tvs = score_token_viability({
			"metadata": t.metadata or {},
		})
		chs = score_community_hype({
			"metadata": t.metadata or {},
		})
		sws = aggregate_sws("launch", cts, tvs, chs)
		t.cts, t.tvs, t.chs, t.sws = cts, tvs, chs, sws
	await session.commit()
	await manager.broadcast_json({"type": "scores_updated"})
	return {"updated": len(tokens)}

@app.post("/seed/dummy")
async def seed_dummy(session: AsyncSession = Depends(get_session)):
	mint = str(uuid.uuid4()).replace('-', '')[:32]
	creator = str(uuid.uuid4()).replace('-', '')[:32]
	ts = int(time.time())
	t = Token(mint_address=mint, creator_wallet=creator, creation_ts=ts, metadata={"name": "DummyToken", "symbol": "DUM"})
	cts = score_creator_trust({"creator_wallet": creator, "creation_ts": ts, "metadata": t.metadata})
	tvs = score_token_viability({"metadata": t.metadata})
	chs = score_community_hype({"metadata": t.metadata})
	sws = aggregate_sws("launch", cts, tvs, chs)
	t.cts, t.tvs, t.chs, t.sws = cts, tvs, chs, sws
	session.add(t)
	await session.commit()
	await manager.broadcast_json({"type": "token_upserted"})
	await manager.broadcast_json({"type": "scores_updated"})
	return {"mint_address": mint, "creator_wallet": creator, "sws": sws}

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
	await manager.connect(ws)
	try:
		await ws.send_json({"type": "welcome", "msg": "SolanaWatchX stream connected"})
		while True:
			await ws.receive_text()
	except Exception:
		pass
	finally:
		await manager.disconnect(ws)
