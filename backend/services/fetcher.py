"""
Data fetcher.
Historical daily data: AKShare ak.spot_hist_sge (SGE Au99.99)
Real-time intraday:    Tanshu API (shgold2) — updates today's daily candle + 5-min snapshot
"""
import logging
from datetime import datetime, date
from typing import Optional

import requests
import akshare as ak
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.dialects.mysql import insert as mysql_insert

from backend.config import GOLD_SYMBOL_SGE
from backend.db.models import GoldDaily, Gold5Min

logger = logging.getLogger(__name__)

# ── Tanshu real-time API ───────────────────────────────────────────────────────

_TANSHU_URL  = "https://api.tanshuapi.com/api/gold/v1/shgold2?key=49e4a25c90d6c1be20033d51ecd12f25"
_TANSHU_TYPE = "Au9999"   # 黄金9999 ≈ Au99.99


def _safe_float(v) -> Optional[float]:
    try:
        f = float(v)
        return f if f != 0.0 else None
    except (TypeError, ValueError):
        return None


def fetch_realtime_tanshu(session: Session) -> dict:
    """
    Call the Tanshu API, extract Au9999 real-time quote, then:
      1. Upsert today's record in gold_daily (open/high/low/close/volume).
      2. Insert a 5-min snapshot in gold_5min keyed to the rounded current time.
    Returns the parsed quote dict (empty dict on failure).
    """
    try:
        resp = requests.get(_TANSHU_URL, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("code") != 1:
            logger.warning("Tanshu API non-ok code: %s", payload.get("code"))
            return {}

        item = payload["data"]["list"].get(_TANSHU_TYPE)
        if not item:
            logger.warning("Tanshu API: %s not found in response", _TANSHU_TYPE)
            return {}

        close_price = _safe_float(item.get("price"))
        open_price  = _safe_float(item.get("openingprice"))
        high_price  = _safe_float(item.get("maxprice"))
        low_price   = _safe_float(item.get("minprice"))
        prev_close  = _safe_float(item.get("lastclosingprice"))
        volume      = _safe_float(item.get("tradeamount"))
        update_time = item.get("updatetime", "")

        if not close_price:
            logger.warning("Tanshu API: empty price for %s", _TANSHU_TYPE)
            return {}

        quote = {
            "price":       close_price,
            "open":        open_price,
            "high":        high_price,
            "low":         low_price,
            "prev_close":  prev_close,
            "volume":      volume,
            "update_time": update_time,
        }

        today = date.today()

        # ── 1. Upsert today's daily candle ────────────────────────────────────
        daily_record = {
            "trade_date": today,
            "symbol":     GOLD_SYMBOL_SGE,
            "open":       open_price,
            "close":      close_price,
            "high":       high_price,
            "low":        low_price,
            "volume":     volume,
            "amount":     None,
        }
        stmt = mysql_insert(GoldDaily).values([daily_record])
        stmt = stmt.on_duplicate_key_update(
            open=stmt.inserted.open,
            close=stmt.inserted.close,
            high=stmt.inserted.high,
            low=stmt.inserted.low,
            volume=stmt.inserted.volume,
            updated_at=datetime.now(),
        )
        session.execute(stmt)

        # ── 2. Insert 5-min snapshot (rounded down to nearest 5 minutes) ──────
        now = datetime.now()
        rounded = now.replace(second=0, microsecond=0)
        rounded = rounded.replace(minute=(rounded.minute // 5) * 5)

        min5_record = {
            "trade_time": rounded,
            "symbol":     GOLD_SYMBOL_SGE,
            "open":       close_price,
            "close":      close_price,
            "high":       close_price,
            "low":        close_price,
            "volume":     volume,
            "hold":       None,
        }
        stmt2 = mysql_insert(Gold5Min).values([min5_record])
        stmt2 = stmt2.on_duplicate_key_update(
            close=stmt2.inserted.close,
            high=stmt2.inserted.high,
            low=stmt2.inserted.low,
            volume=stmt2.inserted.volume,
        )
        session.execute(stmt2)

        session.commit()
        logger.info(
            "fetch_realtime_tanshu: close=%.2f open=%.2f high=%.2f low=%.2f vol=%.0f time=%s",
            close_price, open_price or 0, high_price or 0, low_price or 0,
            volume or 0, update_time,
        )
        return quote

    except Exception as exc:
        session.rollback()
        logger.error("fetch_realtime_tanshu error: %s", exc, exc_info=True)
        return {}


# ── Historical daily data (AKShare) ───────────────────────────────────────────

def fetch_and_save_daily(session: Session) -> int:
    """Fetch SGE Au99.99 full daily history and upsert into gold_daily."""
    try:
        df = ak.spot_hist_sge(symbol=GOLD_SYMBOL_SGE)
        if df is None or df.empty:
            logger.warning("spot_hist_sge returned empty data")
            return 0

        df = df.rename(columns={"date": "trade_date"})
        df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
        df["symbol"] = GOLD_SYMBOL_SGE
        df["volume"] = None
        df["amount"] = None

        records = (
            df[["trade_date", "symbol", "open", "close", "high", "low", "volume", "amount"]]
            .to_dict("records")
        )

        stmt = mysql_insert(GoldDaily).values(records)
        stmt = stmt.on_duplicate_key_update(
            open=stmt.inserted.open,
            close=stmt.inserted.close,
            high=stmt.inserted.high,
            low=stmt.inserted.low,
            updated_at=datetime.now(),
        )
        session.execute(stmt)
        session.commit()
        logger.info("fetch_and_save_daily: upserted %d rows", len(records))
        return len(records)
    except Exception as exc:
        session.rollback()
        logger.error("fetch_and_save_daily error: %s", exc, exc_info=True)
        return 0


# ── Compatibility stub ────────────────────────────────────────────────────────

def get_current_price() -> dict:
    """Kept for compatibility; scheduler keeps DB current via fetch_realtime_tanshu."""
    return {}
