"""
APScheduler-based background task scheduler.
Real-time fetch (Tanshu API) every 5 minutes during SGE trading hours.
Daily AKShare history + indicators recalc once at 16:30.
"""
import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.db.database import SessionLocal

logger = logging.getLogger(__name__)
_scheduler = BackgroundScheduler(timezone="Asia/Shanghai")


# ── SGE trading-hours guard ───────────────────────────────────────────────────

def is_trading_time() -> bool:
    """
    SGE gold day sessions: 09:00–11:30, 13:30–15:30 (weekdays only).
    """
    now = datetime.now()
    if now.weekday() >= 5:   # Saturday=5, Sunday=6
        return False
    t = now.hour * 60 + now.minute
    return (9*60 <= t <= 11*60+30) or (13*60+30 <= t <= 15*60+30)


# ── Jobs ──────────────────────────────────────────────────────────────────────

def _job_realtime():
    """Fetch real-time price from Tanshu API and update DB."""
    if not is_trading_time():
        return
    from backend.services.fetcher import fetch_realtime_tanshu
    with SessionLocal() as s:
        fetch_realtime_tanshu(s)


def _job_daily():
    """After market close: refresh historical data via AKShare, recalc indicators."""
    from backend.services.fetcher import fetch_and_save_daily
    from backend.services.calculator import update_indicators
    with SessionLocal() as s:
        n = fetch_and_save_daily(s)
        logger.info("Daily AKShare fetch: %d rows", n)
        update_indicators(s)
    logger.info("Daily fetch+indicators done")


# ── Lifecycle ─────────────────────────────────────────────────────────────────

def start_scheduler():
    # Every 5 minutes during trading hours (guard is inside the job)
    _scheduler.add_job(_job_realtime, "interval", minutes=5,
                       id="fetch_realtime", replace_existing=True)
    # 16:30 daily — after SGE closes, pull complete historical data
    _scheduler.add_job(_job_daily, CronTrigger(hour=16, minute=30),
                       id="fetch_daily", replace_existing=True)
    _scheduler.start()
    logger.info("Scheduler started (5-min realtime + 16:30 daily)")


def stop_scheduler():
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
