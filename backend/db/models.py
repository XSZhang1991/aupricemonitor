from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, Numeric, TIMESTAMP, func
from backend.db.database import Base


class GoldDaily(Base):
    __tablename__ = "gold_daily"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    trade_date = Column(Date,        nullable=False)
    symbol     = Column(String(20),  nullable=False, default="Au99.99")
    open       = Column(Numeric(10, 4))
    close      = Column(Numeric(10, 4), nullable=False)
    high       = Column(Numeric(10, 4))
    low        = Column(Numeric(10, 4))
    volume     = Column(Numeric(20, 4))
    amount     = Column(Numeric(20, 4))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Gold5Min(Base):
    __tablename__ = "gold_5min"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    trade_time = Column(DateTime,    nullable=False)
    symbol     = Column(String(20),  nullable=False, default="AU_MAIN")
    open       = Column(Numeric(10, 4))
    close      = Column(Numeric(10, 4), nullable=False)
    high       = Column(Numeric(10, 4))
    low        = Column(Numeric(10, 4))
    volume     = Column(Numeric(20, 4))
    hold       = Column(Numeric(20, 4))
    created_at = Column(DateTime, default=datetime.now)


class Gold1Min(Base):
    __tablename__ = "gold_1min"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    trade_time = Column(DateTime,    nullable=False)
    symbol     = Column(String(20),  nullable=False, default="AU_MAIN")
    open       = Column(Numeric(10, 4))
    close      = Column(Numeric(10, 4), nullable=False)
    high       = Column(Numeric(10, 4))
    low        = Column(Numeric(10, 4))
    volume     = Column(Numeric(20, 4))
    hold       = Column(Numeric(20, 4))
    created_at = Column(DateTime, default=datetime.now)


class GoldIndicatorsDaily(Base):
    __tablename__ = "gold_indicators_daily"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    trade_date        = Column(Date,       nullable=False)
    symbol            = Column(String(20), nullable=False, default="Au99.99")
    ma5               = Column(Numeric(10, 4))
    ma10              = Column(Numeric(10, 4))
    ma20              = Column(Numeric(10, 4))
    ma60              = Column(Numeric(10, 4))
    ema12             = Column(Numeric(10, 4))
    ema26             = Column(Numeric(10, 4))
    macd_dif          = Column(Numeric(12, 6))
    macd_dea          = Column(Numeric(12, 6))
    macd_hist         = Column(Numeric(12, 6))
    rsi_6             = Column(Numeric(8,  4))
    rsi_12            = Column(Numeric(8,  4))
    rsi_24            = Column(Numeric(8,  4))
    boll_upper        = Column(Numeric(10, 4))
    boll_mid          = Column(Numeric(10, 4))
    boll_lower        = Column(Numeric(10, 4))
    volatility_daily  = Column(Numeric(10, 6))
    volatility_weekly = Column(Numeric(10, 6))
    created_at        = Column(DateTime, default=datetime.now)
    updated_at        = Column(DateTime, default=datetime.now, onupdate=datetime.now)
