from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, BigInteger, JSON
from .db import Base

class Token(Base):
	__tablename__ = "tokens"
	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	mint_address: Mapped[str] = mapped_column(String(64), unique=True, index=True)
	creator_wallet: Mapped[str] = mapped_column(String(64), index=True)
	creation_ts: Mapped[int] = mapped_column(BigInteger)
	metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
	cts: Mapped[int | None] = mapped_column(Integer, nullable=True)
	tvs: Mapped[int | None] = mapped_column(Integer, nullable=True)
	chs: Mapped[int | None] = mapped_column(Integer, nullable=True)
	sws: Mapped[int | None] = mapped_column(Integer, nullable=True)
	gini: Mapped[float | None] = mapped_column(JSON, nullable=True)
	nakamoto: Mapped[int | None] = mapped_column(Integer, nullable=True)
	scores_updated_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
	chs_sources: Mapped[dict | None] = mapped_column(JSON, nullable=True)

class Trade(Base):
	__tablename__ = "trades"
	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	signature: Mapped[str] = mapped_column(String(90), unique=True, index=True)
	mint_address: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
	program: Mapped[str] = mapped_column(String(64), index=True)
	timestamp: Mapped[int] = mapped_column(BigInteger)
	payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

class HolderMetric(Base):
	__tablename__ = "holder_metrics"
	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	mint_address: Mapped[str] = mapped_column(String(64), index=True)
	taken_at: Mapped[int] = mapped_column(BigInteger)
	gini: Mapped[float] = mapped_column(JSON)
	nakamoto: Mapped[int] = mapped_column(Integer)
	data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
