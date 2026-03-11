# -*- coding: utf-8 -*-
"""
配置文件
"""

import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent

# 数据库配置
DATABASE_PATH = BASE_DIR / 'data' / 'gold_monitor.db'
DATABASE_URL = f'sqlite:///{DATABASE_PATH}'

# 日志配置
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / 'gold_monitor.log'
LOG_LEVEL = 'INFO'

# 数据抓取配置
FETCH_INTERVAL = 300  # 5分钟更新一次（单位：秒）
HISTORICAL_DAYS = 30  # 历史数据天数

# Web服务配置
WEB_HOST = '0.0.0.0'
WEB_PORT = 8501
DEBUG = True

# Streamlit配置
STREAMLIT_CONFIG = {
    'client.showErrorDetails': True,
    'logger.level': 'info',
}

# 数据源配置
DATA_SOURCE = 'akshare'  # 数据源

# 黄金代码
GOLD_CODES = {
    'Au99.99': '上海黄金交易所现货',  # 上海黄金交易所现货
}

# 移动平均线周期
MA_PERIODS = [5, 10, 20]

# 波动率计算参数
VOLATILITY_DAYS = 5  # 用于计算周波动率的天数
