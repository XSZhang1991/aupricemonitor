# -*- coding: utf-8 -*-
"""
数据抓取模块 - 使用akshare库
"""

import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from config import LOG_FILE, LOG_LEVEL, HISTORICAL_DAYS
from database import db

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DataFetcher:
    """数据抓取类"""
    
    def __init__(self):
        try:
            import akshare as ak
            self.ak = ak
            self.data_source_available = True
        except ImportError:
            logger.warning('akshare库未安装，使用模拟数据')
            self.data_source_available = False
    
    def fetch_gold_price(self, days=HISTORICAL_DAYS):
        """
        抓取黄金价格数据
        
        Args:
            days: 获取过去多少天的数据
            
        Returns:
            DataFrame: 包含价格数据的数据框
        """
        try:
            if self.data_source_available:
                # 使用akshare获取上海黄金交易所数据
                try:
                    # 尝试获取黄金期货数据
                    df = self.ak.futures_jq_price_variety_detail(
                        symbol='GC',  # 黄金
                        start_year='2020'
                    )
                    logger.info(f'成功获取黄金价格数据，共{len(df)}条')
                    return df
                except Exception as e:
                    logger.warning(f'akshare获取失败: {e}，使用生成模拟数据')
                    return self._generate_simulated_data(days)
            else:
                return self._generate_simulated_data(days)
        except Exception as e:
            logger.error(f'数据抓取失败: {e}')
            return self._generate_simulated_data(days)
    
    def _generate_simulated_data(self, days=HISTORICAL_DAYS):
        """生成模拟黄金价格数据用于演示"""
        dates = []
        prices = []
        
        # 生成过去days天的数据
        base_date = datetime.now()
        base_price = 500.0  # 起始价格
        
        for i in range(days, 0, -1):
            date = base_date - timedelta(days=i)
            # 随机波动
            price_change = np.random.normal(0, 2)  # 均值为0，标准差为2的正态分布
            base_price = max(base_price + price_change, 400)
            
            dates.append(date.strftime('%Y-%m-%d'))
            prices.append(round(base_price, 2))
        
        # 构建DataFrame
        df = pd.DataFrame({
            '日期': dates,
            '收盘价': prices,
            '开盘价': [p - np.random.uniform(0, 1) for p in prices],
            '最高价': [p + np.random.uniform(0, 1) for p in prices],
            '最低价': [p - np.random.uniform(0, 2) for p in prices],
            '成交量': [np.random.randint(1000, 10000) for _ in prices]
        })
        
        return df
    
    def process_and_save_data(self, df):
        """
        处理和保存数据到数据库
        """
        if df is None or len(df) == 0:
            logger.warning('没有数据可以保存')
            return 0
        
        saved_count = 0
        
        try:
            # 标准化列名
            df.columns = [col.strip() for col in df.columns]
            
            # 处理日期列
            date_col = None
            for col in ['日期', '时间', 'date', 'Date', 'time']:
                if col in df.columns:
                    date_col = col
                    break
            
            # 处理价格列
            price_col = None
            for col in ['收盘价', '价格', 'close', 'Close']:
                if col in df.columns:
                    price_col = col
                    break
            
            if date_col is None or price_col is None:
                logger.error('未找到日期或价格列')
                return 0
            
            # 遍历数据并保存
            for idx, row in df.iterrows():
                try:
                    trade_date = str(row[date_col]).strip()
                    close_price = float(row[price_col])
                    
                    # 获取其他可选字段
                    open_price = float(row['开盘价']) if '开盘价' in df.columns else None
                    high_price = float(row['最高价']) if '最高价' in df.columns else None
                    low_price = float(row['最低价']) if '最低价' in df.columns else None
                    volume = float(row['成交量']) if '成交量' in df.columns else None
                    
                    # 计算涨跌幅（如有历史数据）
                    change_amount = None
                    change_percent = None
                    
                    if db.insert_price(
                        trade_date=trade_date,
                        close_price=close_price,
                        open_price=open_price,
                        high_price=high_price,
                        low_price=low_price,
                        volume=volume,
                        change_amount=change_amount,
                        change_percent=change_percent
                    ):
                        saved_count += 1
                except Exception as e:
                    logger.debug(f'保存数据行失败: {e}')
                    continue
            
            logger.info(f'成功保存{saved_count}条数据')
            db.log_update(saved_count, 'success', f'成功保存{saved_count}条数据')
            
        except Exception as e:
            logger.error(f'处理数据失败: {e}')
            db.log_update(0, 'error', str(e))
        
        return saved_count
    
    def update_latest_data(self):
        """更新最新数据"""
        df = self.fetch_gold_price(days=1)
        return self.process_and_save_data(df)


# 全局数据抓取实例
fetcher = DataFetcher()
