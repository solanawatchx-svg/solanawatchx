from __future__ import annotations
from typing import Optional, Dict, Any

def score_creator_trust(token: Dict[str, Any]) -> int:
	return 50

def score_token_viability(token: Dict[str, Any]) -> int:
	return 30

def score_community_hype(token: Dict[str, Any]) -> int:
	return 20

def aggregate_sws(phase: str, cts: int, tvs: int, chs: int) -> int:
	if phase == "launch":
		w_cts, w_tvs, w_chs = 0.7, 0.1, 0.2
	elif phase == "growth":
		w_cts, w_tvs, w_chs = 0.4, 0.3, 0.3
	else:
		w_cts, w_tvs, w_chs = 0.2, 0.5, 0.3
	score = w_cts * cts + w_tvs * tvs + w_chs * chs
	return int(round(score))
