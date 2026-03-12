"""
Data fetcher using AKShare.
Daily spot data: ak.spot_hist_sge (SGE Au99.99)
Real-time spot:  ak.spot_quotations_sge
Intraday K-line: ak.futures_zh_minute_sina (SHFE AU futures, period '1' or '5')
"""
import logging
from datetime import datetime
from typing import Optional

import akshare as ak
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.dialects.mysql import insert as mysql_insert

from backend.config import GOLD_SYMBOL_SGE
from backend.db.models import GoldDaily, Gold5Min, Gold1Min

logger = logging.getLogger(__name__)

# ── Contract helpers ──────────────────────────────────────────────────────────

# Gold futures trade months on SHFE
_MONTHS = [2, 4, 6, 8, 10, 12]


def _candidate_contracts():
    """Yield SHFE gold contract codes starting from the nearest live one."""
    now = datetime.now()
    y2 = now.year % 100
    m = now.month
    # Build ordered list: current year first, then next year if needed
    for year in (y2, y2 + 1):
        for mo in _MONTHS:
            if year == y2 and (mo < m or (mo == m and now.day >= 20)):
                continue  # likely expired
            yield f"AU{year:02d}{mo:02d}"


def get_main_contract() -> str:
    """Return the SHFE gold main contract code, e.g. 'AU2604'."""
    for sym in _candidate_contracts():
        try:
            df = ak.futures_zh_minute_sina(symbol=sym, period="5")
            if df is not None and not df.empty:
                last = pd.to_datetime(df["datetime"].iloc[-1])
                if (datetime.now() - last).days <= 14:
                    logger.info("Main contract resolved: %s", sym)
                    return sym
        except Exception as exc:
            logger.debug("Contract %s probe failed: %s", sym, exc)
    # fallback: first candidate
    for sym in _candidate_contracts():
        return sym
    return "AU2604"


# ── Daily data ────────────────────────────────────────────────────────────────

def fetch_and_save_daily(session: Session) -> int:
    """Fetch SGE Au99.99 full daily history and upsert into gold_daily."""
    try:
        df = ak.spot_hist_sge(symbol=GOLD_SYMBOL_SGE)
        # Columns: date, open, close, low, high  (no volume in SGE spot)
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


# ── Minute data ───────────────────────────────────────────────────────────────

def fetch_and_save_minute(session: Session, period: str = "5") -> int:
    """Fetch SHFE futures minute K-line and upsert into gold_5min / gold_1min."""
    assert period in ("1", "5"), "period must be '1' or '5'"
    Model = Gold5Min if period == "5" else Gold1Min
    try:
        contract = get_main_contract()
        df = ak.futures_zh_minute_sina(symbol=contract, period=period)
        # Columns: datetime, open, high, low, close, volume, hold
        if df is None or df.empty:
            logger.warning("futures_zh_minute_sina(%s, %s) empty", contract, period)
            return 0

        df = df.rename(columns={"datetime": "trade_time"})
        df["trade_time"] = pd.to_datetime(df["trade_time"])
        df["symbol"] = contract

        records = (
            df[["trade_time", "symbol", "open", "high", "low", "close", "volume", "hold"]]
            .to_dict("records")
        )

        stmt = mysql_insert(Model).values(records)
        stmt = stmt.on_duplicate_key_update(
            open=stmt.inserted.open,
            close=stmt.inserted.close,
            high=stmt.inserted.high,
            low=stmt.inserted.low,
            volume=stmt.inserted.volume,
        )
        session.execute(stmt)
        session.commit()
        logger.info("fetch_and_save_minute(%s, %s): upserted %d rows", contract, period, len(records))
        return len(records)
    except Exception as exc:
        session.rollback()
        logger.error("fetch_and_save_minute(%s) error: %s", period, exc, exc_info=True)
        return 0


# ── Real-time quote ───────────────────────────────────────────────────────────

def get_current_price() -> dict:
    """Return the latest SGE spot real-time quote as a plain dict."""
    try:
        df = ak.spot_quotations_sge(symbol=GOLD_SYMBOL_SGE)
        # Columns: 品种, 时间, 现价, 更新时间
        if df is not None and not df.empty:
            row = df.iloc[0]
            return {
                "price": float(row.get("现价", 0) or 0),
                "time": str(row.get("时间", "")),
                "update_time": str(row.get("更新时间", "")),
            }
    except Exception as exc:
        logger.warning("get_current_price error: %s", exc)
    return {}
