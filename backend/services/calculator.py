"""
Technical indicator calculator.
Computes MA, MACD, RSI, Bollinger Bands, and volatility from daily close prices.
"""
import logging
from datetime import datetime

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.dialects.mysql import insert as mysql_insert

from backend.db.models import GoldDaily, GoldIndicatorsDaily

logger = logging.getLogger(__name__)


# ── Pure pandas helpers ───────────────────────────────────────────────────────

def _ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def _macd(close: pd.Series):
    ema12 = _ema(close, 12)
    ema26 = _ema(close, 26)
    dif   = ema12 - ema26
    dea   = _ema(dif, 9)
    hist  = 2.0 * (dif - dea)
    return ema12, ema26, dif, dea, hist


def _rsi(close: pd.Series, n: int) -> pd.Series:
    delta    = close.diff()
    gain     = delta.clip(lower=0)
    loss     = (-delta).clip(lower=0)
    avg_gain = gain.ewm(com=n - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=n - 1, adjust=False).mean()
    rs       = avg_gain / avg_loss.replace(0, np.nan)
    return 100.0 - 100.0 / (1.0 + rs)


def _boll(close: pd.Series, n: int = 20, k: float = 2.0):
    mid   = close.rolling(n).mean()
    std   = close.rolling(n).std(ddof=1)
    upper = mid + k * std
    lower = mid - k * std
    return upper, mid, lower


def _vol_daily(close: pd.Series, n: int = 20) -> pd.Series:
    """Annualised daily volatility (20-day rolling)."""
    lr = np.log(close / close.shift(1))
    return lr.rolling(n).std(ddof=1) * np.sqrt(252)


def _vol_weekly(close: pd.Series, n: int = 5) -> pd.Series:
    """Annualised weekly volatility (5-day rolling)."""
    lr = np.log(close / close.shift(1))
    return lr.rolling(n).std(ddof=1) * np.sqrt(52)


# ── Main entry ────────────────────────────────────────────────────────────────

def update_indicators(session: Session) -> int:
    """
    Load all daily closes from DB, compute all indicators,
    upsert results into gold_indicators_daily.
    Returns number of rows written.
    """
    try:
        rows = (
            session.query(GoldDaily.trade_date, GoldDaily.close, GoldDaily.symbol)
            .filter(GoldDaily.symbol == "Au99.99")
            .order_by(GoldDaily.trade_date)
            .all()
        )
        if len(rows) < 5:
            logger.warning("update_indicators: not enough rows (%d)", len(rows))
            return 0

        df = pd.DataFrame(rows, columns=["trade_date", "close", "symbol"])
        df["close"] = df["close"].astype(float)
        c = df["close"]

        # Moving averages
        df["ma5"]  = c.rolling(5).mean()
        df["ma10"] = c.rolling(10).mean()
        df["ma20"] = c.rolling(20).mean()
        df["ma60"] = c.rolling(60).mean()

        # MACD
        df["ema12"], df["ema26"], df["macd_dif"], df["macd_dea"], df["macd_hist"] = _macd(c)

        # RSI
        df["rsi_6"]  = _rsi(c, 6)
        df["rsi_12"] = _rsi(c, 12)
        df["rsi_24"] = _rsi(c, 24)

        # Bollinger
        df["boll_upper"], df["boll_mid"], df["boll_lower"] = _boll(c)

        # Volatility
        df["volatility_daily"]  = _vol_daily(c)
        df["volatility_weekly"] = _vol_weekly(c)

        def _f(v):
            if pd.isna(v):
                return None
            return round(float(v), 6)

        records = [
            {
                "trade_date":        row.trade_date,
                "symbol":            row.symbol,
                "ma5":               _f(row.ma5),
                "ma10":              _f(row.ma10),
                "ma20":              _f(row.ma20),
                "ma60":              _f(row.ma60),
                "ema12":             _f(row.ema12),
                "ema26":             _f(row.ema26),
                "macd_dif":          _f(row.macd_dif),
                "macd_dea":          _f(row.macd_dea),
                "macd_hist":         _f(row.macd_hist),
                "rsi_6":             _f(row.rsi_6),
                "rsi_12":            _f(row.rsi_12),
                "rsi_24":            _f(row.rsi_24),
                "boll_upper":        _f(row.boll_upper),
                "boll_mid":          _f(row.boll_mid),
                "boll_lower":        _f(row.boll_lower),
                "volatility_daily":  _f(row.volatility_daily),
                "volatility_weekly": _f(row.volatility_weekly),
            }
            for _, row in df.iterrows()
        ]

        stmt = mysql_insert(GoldIndicatorsDaily).values(records)
        stmt = stmt.on_duplicate_key_update(
            ma5=stmt.inserted.ma5, ma10=stmt.inserted.ma10,
            ma20=stmt.inserted.ma20, ma60=stmt.inserted.ma60,
            ema12=stmt.inserted.ema12, ema26=stmt.inserted.ema26,
            macd_dif=stmt.inserted.macd_dif, macd_dea=stmt.inserted.macd_dea,
            macd_hist=stmt.inserted.macd_hist,
            rsi_6=stmt.inserted.rsi_6, rsi_12=stmt.inserted.rsi_12,
            rsi_24=stmt.inserted.rsi_24,
            boll_upper=stmt.inserted.boll_upper, boll_mid=stmt.inserted.boll_mid,
            boll_lower=stmt.inserted.boll_lower,
            volatility_daily=stmt.inserted.volatility_daily,
            volatility_weekly=stmt.inserted.volatility_weekly,
            updated_at=datetime.now(),
        )
        session.execute(stmt)
        session.commit()
        logger.info("update_indicators: wrote %d rows", len(records))
        return len(records)

    except Exception as exc:
        session.rollback()
        logger.error("update_indicators error: %s", exc, exc_info=True)
        return 0
