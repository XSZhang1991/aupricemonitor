-- Gold Price Monitor Database Schema
-- MySQL 8.0+

CREATE DATABASE IF NOT EXISTS gold_monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE gold_monitor;

-- Daily K-line (SGE Au99.99 spot)
CREATE TABLE IF NOT EXISTS gold_daily (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    trade_date  DATE        NOT NULL,
    symbol      VARCHAR(20) NOT NULL DEFAULT 'Au99.99',
    open        DECIMAL(10, 4),
    close       DECIMAL(10, 4) NOT NULL,
    high        DECIMAL(10, 4),
    low         DECIMAL(10, 4),
    volume      DECIMAL(20, 4),
    amount      DECIMAL(20, 4),
    created_at  TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP   DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY  uq_date_symbol (trade_date, symbol),
    INDEX       idx_trade_date (trade_date)
) ENGINE = InnoDB;

-- 5-minute K-line (SHFE AU futures proxy)
CREATE TABLE IF NOT EXISTS gold_5min (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    trade_time  DATETIME    NOT NULL,
    symbol      VARCHAR(20) NOT NULL DEFAULT 'AU_MAIN',
    open        DECIMAL(10, 4),
    close       DECIMAL(10, 4) NOT NULL,
    high        DECIMAL(10, 4),
    low         DECIMAL(10, 4),
    volume      DECIMAL(20, 4),
    hold        DECIMAL(20, 4),
    created_at  TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY  uq_time_symbol (trade_time, symbol),
    INDEX       idx_trade_time (trade_time)
) ENGINE = InnoDB;

-- 1-minute K-line (SHFE AU futures proxy)
CREATE TABLE IF NOT EXISTS gold_1min (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    trade_time  DATETIME    NOT NULL,
    symbol      VARCHAR(20) NOT NULL DEFAULT 'AU_MAIN',
    open        DECIMAL(10, 4),
    close       DECIMAL(10, 4) NOT NULL,
    high        DECIMAL(10, 4),
    low         DECIMAL(10, 4),
    volume      DECIMAL(20, 4),
    hold        DECIMAL(20, 4),
    created_at  TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY  uq_time_symbol (trade_time, symbol),
    INDEX       idx_trade_time (trade_time)
) ENGINE = InnoDB;

-- Daily technical indicators
CREATE TABLE IF NOT EXISTS gold_indicators_daily (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    trade_date        DATE        NOT NULL,
    symbol            VARCHAR(20) NOT NULL DEFAULT 'Au99.99',
    -- Moving averages
    ma5               DECIMAL(10, 4),
    ma10              DECIMAL(10, 4),
    ma20              DECIMAL(10, 4),
    ma60              DECIMAL(10, 4),
    -- MACD
    ema12             DECIMAL(10, 4),
    ema26             DECIMAL(10, 4),
    macd_dif          DECIMAL(12, 6),
    macd_dea          DECIMAL(12, 6),
    macd_hist         DECIMAL(12, 6),
    -- RSI
    rsi_6             DECIMAL(8,  4),
    rsi_12            DECIMAL(8,  4),
    rsi_24            DECIMAL(8,  4),
    -- Bollinger Bands
    boll_upper        DECIMAL(10, 4),
    boll_mid          DECIMAL(10, 4),
    boll_lower        DECIMAL(10, 4),
    -- Volatility
    volatility_daily  DECIMAL(10, 6),
    volatility_weekly DECIMAL(10, 6),
    created_at        TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP   DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY        uq_date_symbol (trade_date, symbol),
    INDEX             idx_trade_date (trade_date)
) ENGINE = InnoDB;
