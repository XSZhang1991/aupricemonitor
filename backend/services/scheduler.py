"""
APScheduler-based background task scheduler.
Fetches intraday data during trading hours and daily data once a day.
"""
import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.db.database import SessionLocal

logger = logging.getLogger(__name__)
_scheduler = BackgroundScheduler(timezone="Asia/Shanghai")


# ── Trading-hours guard ───────────────────────────────────────────────────────

def is_trading_time() -> bool:
    """
    SHFE gold day sessions:  09:00–11:30, 13:30–15:30
    SHFE gold night session: 21:00–02:30 (next day)
    """
    now = datetime.now()
    t = now.hour * 60 + now.minute
    day   = (9*60 <= t <= 11*60+30) or (13*60+30 <= t <= 15*60+30)
    night = (21*60 <= t) or (t <= 2*60+30)
    return day or night


# ── Jobs ──────────────────────────────────────────────────────────────────────

def _job_1min():
    if not is_trading_time():
        return
    from backend.services.fetcher import fetch_and_save_minute
    with SessionLocal() as s:
        fetch_and_save_minute(s, period="1")


def _job_5min():
    if not is_trading_time():
        return
    from backend.services.fetcher import fetch_and_save_minute
    with SessionLocal() as s:
        fetch_and_save_minute(s, period="5")


def _job_daily():
    from backend.services.fetcher import fetch_and_save_daily
    from backend.services.calculator import update_indicators
    with SessionLocal() as s:
        n = fetch_and_save_daily(s)
        if n > 0:
            update_indicators(s)
    logger.info("Daily fetch+indicators done")


# ── Lifecycle ─────────────────────────────────────────────────────────────────

def start_scheduler():
    _scheduler.add_job(_job_1min,  "interval", minutes=1,  id="fetch_1min",  replace_existing=True)
    _scheduler.add_job(_job_5min,  "interval", minutes=5,  id="fetch_5min",  replace_existing=True)
    _scheduler.add_job(_job_daily, CronTrigger(hour=16, minute=30), id="fetch_daily", replace_existing=True)
    _scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler():
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
