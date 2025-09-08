from typing import Set, Any
from fastapi import WebSocket
import asyncio
import json

class ConnectionManager:
	def __init__(self) -> None:
		self._clients: Set[WebSocket] = set()
		self._lock = asyncio.Lock()

	async def connect(self, ws: WebSocket) -> None:
		await ws.accept()
		async with self._lock:
			self._clients.add(ws)

	async def disconnect(self, ws: WebSocket) -> None:
		async with self._lock:
			if ws in self._clients:
				self._clients.remove(ws)

	async def broadcast_json(self, payload: Any) -> None:
		message = json.dumps(payload)
		async with self._lock:
			clients = list(self._clients)
		for ws in clients:
			try:
				await ws.send_text(message)
			except Exception:
				try:
					await self.disconnect(ws)
				except Exception:
					pass

manager = ConnectionManager()
