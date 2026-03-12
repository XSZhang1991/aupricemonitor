"""
FastAPI route definitions.
"""
import logging
from datetime import date, datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import GoldDaily, Gold5Min, Gold1Min, GoldIndicatorsDaily

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")


# ── helpers ───────────────────────────────────────────────────────────────────

def _float(v) -> Optional[float]:
    if v is None:
        return None
    try:
        return round(float(v), 6)
    except (TypeError, ValueError):
        return None


def _pct_return(current: float, past_close: Optional[float]) -> Optional[float]:
    if past_close and past_close > 0:
        return round((current - past_close) / past_close * 100, 4)
    return None


def _price_n_days_ago(session: Session, symbol: str, n: int) -> Optional[float]:
    target = date.today() - timedelta(days=n)
    row = (
        session.query(GoldDaily.close)
        .filter(GoldDaily.symbol == symbol, GoldDaily.trade_date <= target)
        .order_by(GoldDaily.trade_date.desc())
        .first()
    )
    return float(row.close) if row and row.close else None


# ── /api/market/latest ────────────────────────────────────────────────────────

@router.get("/market/latest")
def market_latest(db: Session = Depends(get_db)):
    symbol = "Au99.99"
    # Latest daily row
    latest = (
        db.query(GoldDaily)
        .filter(GoldDaily.symbol == symbol)
        .order_by(GoldDaily.trade_date.desc())
        .first()
    )
    if not latest:
        return {"error": "No data. Please fetch history first."}

    price = float(latest.close)

    # Previous close for change calculation
    prev = (
        db.query(GoldDaily.close)
        .filter(GoldDaily.symbol == symbol, GoldDaily.trade_date < latest.trade_date)
        .order_by(GoldDaily.trade_date.desc())
        .first()
    )
    prev_close = float(prev.close) if prev and prev.close else None
    change      = round(price - prev_close, 4) if prev_close else None
    change_pct  = _pct_return(price, prev_close)

    # Volatility from indicators
    ind = (
        db.query(GoldIndicatorsDaily)
        .filter(GoldIndicatorsDaily.symbol == symbol)
        .order_by(GoldIndicatorsDaily.trade_date.desc())
        .first()
    )

    # Returns
    returns = {
        "7d":  _pct_return(price, _price_n_days_ago(db, symbol, 7)),
        "15d": _pct_return(price, _price_n_days_ago(db, symbol, 15)),
        "30d": _pct_return(price, _price_n_days_ago(db, symbol, 30)),
        "90d": _pct_return(price, _price_n_days_ago(db, symbol, 90)),
    }

    return {
        "symbol":            symbol,
        "price":             price,
        "open":              _float(latest.open),
        "high":              _float(latest.high),
        "low":               _float(latest.low),
        "change":            change,
        "change_pct":        change_pct,
        "update_time":       str(latest.trade_date),
        "volatility_daily":  _float(ind.volatility_daily)  if ind else None,
        "volatility_weekly": _float(ind.volatility_weekly) if ind else None,
        "returns":           returns,
    }


# ── /api/market/kline ─────────────────────────────────────────────────────────

@router.get("/market/kline")
def market_kline(
    interval: str = Query("daily", pattern="^(daily|5min|1min)$"),
    start:    Optional[str] = None,
    end:      Optional[str] = None,
    db: Session = Depends(get_db),
):
    symbol = "Au99.99" if interval == "daily" else "AU_MAIN"

    if interval == "daily":
        q = db.query(GoldDaily).filter(GoldDaily.symbol == "Au99.99")
        if start:
            q = q.filter(GoldDaily.trade_date >= start)
        if end:
            q = q.filter(GoldDaily.trade_date <= end)
        rows = q.order_by(GoldDaily.trade_date).all()
        data = [
            {
                "time":   str(r.trade_date),
                "open":   _float(r.open),
                "close":  _float(r.close),
                "high":   _float(r.high),
                "low":    _float(r.low),
                "volume": _float(r.volume),
            }
            for r in rows
        ]
    else:
        Model = Gold5Min if interval == "5min" else Gold1Min
        q = db.query(Model)
        if start:
            q = q.filter(Model.trade_time >= start)
        if end:
            q = q.filter(Model.trade_time <= end)
        rows = q.order_by(Model.trade_time).all()
        data = [
            {
                "time":   r.trade_time.strftime("%Y-%m-%d %H:%M:%S"),
                "open":   _float(r.open),
                "close":  _float(r.close),
                "high":   _float(r.high),
                "low":    _float(r.low),
                "volume": _float(r.volume),
            }
            for r in rows
        ]

    return {"interval": interval, "symbol": "Au99.99", "data": data}


# ── /api/market/indicators ────────────────────────────────────────────────────

@router.get("/market/indicators")
def market_indicators(
    start: Optional[str] = None,
    end:   Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(GoldIndicatorsDaily).filter(GoldIndicatorsDaily.symbol == "Au99.99")
    if start:
        q = q.filter(GoldIndicatorsDaily.trade_date >= start)
    if end:
        q = q.filter(GoldIndicatorsDaily.trade_date <= end)
    rows = q.order_by(GoldIndicatorsDaily.trade_date).all()

    data = [
        {
            "time":              str(r.trade_date),
            "ma5":               _float(r.ma5),
            "ma10":              _float(r.ma10),
            "ma20":              _float(r.ma20),
            "ma60":              _float(r.ma60),
            "macd_dif":          _float(r.macd_dif),
            "macd_dea":          _float(r.macd_dea),
            "macd_hist":         _float(r.macd_hist),
            "rsi_6":             _float(r.rsi_6),
            "rsi_12":            _float(r.rsi_12),
            "rsi_24":            _float(r.rsi_24),
            "boll_upper":        _float(r.boll_upper),
            "boll_mid":          _float(r.boll_mid),
            "boll_lower":        _float(r.boll_lower),
            "volatility_daily":  _float(r.volatility_daily),
            "volatility_weekly": _float(r.volatility_weekly),
        }
        for r in rows
    ]
    return {"data": data}


# ── /api/market/fetch_history ─────────────────────────────────────────────────

def _do_fetch_history():
    from backend.db.database import SessionLocal
    from backend.services.fetcher import fetch_and_save_daily, fetch_realtime_tanshu
    from backend.services.calculator import update_indicators
    with SessionLocal() as s:
        n_daily = fetch_and_save_daily(s)
        logger.info("History: %d daily rows saved", n_daily)
        if n_daily > 0:
            update_indicators(s)
    # Also fetch real-time snapshot so today's data appears immediately
    with SessionLocal() as s:
        fetch_realtime_tanshu(s)
    logger.info("fetch_history background task complete")


@router.post("/market/fetch_history")
def fetch_history(background_tasks: BackgroundTasks):
    background_tasks.add_task(_do_fetch_history)
    return {"status": "started", "message": "Historical data fetch started in background"}


# ── /api/system/status ────────────────────────────────────────────────────────

@router.get("/system/status")
def system_status(db: Session = Depends(get_db)):
    try:
        daily_count = db.query(GoldDaily).count()
        min5_count  = db.query(Gold5Min).count()
        min1_count  = db.query(Gold1Min).count()
        ind_count   = db.query(GoldIndicatorsDaily).count()

        last_daily = (
            db.query(GoldDaily.trade_date)
            .order_by(GoldDaily.trade_date.desc())
            .first()
        )
        last_update = str(last_daily.trade_date) if last_daily else None

        return {
            "status": "ok",
            "db_connected": True,
            "last_update": last_update,
            "data_counts": {
                "daily":      daily_count,
                "5min":       min5_count,
                "1min":       min1_count,
                "indicators": ind_count,
            },
        }
    except Exception as exc:
        logger.error("system_status error: %s", exc)
        return {"status": "error", "db_connected": False, "error": str(exc)}
