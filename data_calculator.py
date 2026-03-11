# -*- coding: utf-8 -*-
"""
数据计算模块 - 波动率、指标计算
"""

import logging
import numpy as np
import pandas as pd
from config import LOG_FILE, LOG_LEVEL, VOLATILITY_DAYS, MA_PERIODS
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


class DataCalculator:
    """数据计算类"""
    
    def __init__(self, volatility_days=VOLATILITY_DAYS):
        self.volatility_days = volatility_days
    
    def calculate_returns(self, prices):
        """
        计算对数收益率
        
        Args:
            prices: 价格数组
            
        Returns:
            numpy数组: 对数收益率序列
        """
        if len(prices) < 2:
            return np.array([])
        
        prices = np.array(prices, dtype=float)
        returns = np.log(prices[1:] / prices[:-1])
        return returns
    
    def calculate_daily_volatility(self, returns):
        """
        计算日波动率（收益率的标准差）
        
        Args:
            returns: 对数收益率数组
            
        Returns:
            float: 日波动率
        """
        if len(returns) == 0:
            return None
        
        return float(np.std(returns, ddof=1))
    
    def calculate_weekly_volatility(self, daily_volatility):
        """
        计算周波动率
        公式：周波动率 = 日波动率 × sqrt(5)
        
        Args:
            daily_volatility: 日波动率
            
        Returns:
            float: 周波动率
        """
        if daily_volatility is None or daily_volatility == 0:
            return None
        
        return float(daily_volatility * np.sqrt(self.volatility_days))
    
    def calculate_moving_average(self, prices, period):
        """
        计算移动平均线
        
        Args:
            prices: 价格数组
            period: 周期
            
        Returns:
            float: 移动平均价
        """
        if len(prices) < period:
            return None
        
        prices = np.array(prices[-period:], dtype=float)
        return float(np.mean(prices))
    
    def calculate_all_indicators(self, trade_date, prices):
        """
        计算所有指标
        
        Args:
            trade_date: 交易日期
            prices: 价格数组（按日期升序）
            
        Returns:
            dict: 包含所有指标的字典
        """
        indicators = {
            'trade_date': trade_date,
            'daily_return': None,
            'daily_volatility': None,
            'weekly_volatility': None,
        }
        
        if len(prices) < 2:
            return indicators
        
        try:
            # 计算对数收益率
            returns = self.calculate_returns(prices)
            if len(returns) > 0:
                indicators['daily_return'] = float(returns[-1])
            
            # 计算日波动率（过去5天）
            if len(prices) >= 5:
                recent_returns = returns[-5:]
                daily_vol = self.calculate_daily_volatility(recent_returns)
                indicators['daily_volatility'] = daily_vol
                
                # 计算周波动率
                if daily_vol is not None:
                    weekly_vol = self.calculate_weekly_volatility(daily_vol)
                    indicators['weekly_volatility'] = weekly_vol
            
            # 计算移动平均线
            for period in MA_PERIODS:
                if len(prices) >= period:
                    ma = self.calculate_moving_average(prices, period)
                    indicators[f'ma{period}'] = ma
        
        except Exception as e:
            logger.error(f'计算指标失败: {e}')
        
        return indicators
    
    def process_and_save_indicators(self):
        """
        处理和保存所有指标到数据库
        """
        try:
            # 获取所有价格数据
            price_data = db.get_price_data()
            
            if not price_data:
                logger.warning('没有价格数据可以计算指标')
                return 0
            
            # 转换为DataFrame便于处理
            df = pd.DataFrame(price_data)
            df = df.sort_values('trade_date')
            
            prices = df['close_price'].tolist()
            dates = df['trade_date'].tolist()
            
            saved_count = 0
            
            # 逐日期计算指标
            for i, date in enumerate(dates):
                indicators = self.calculate_all_indicators(
                    date,
                    prices[:i+1]  # 使用到当前日期的所有数据
                )
                
                # 保存到数据库
                if db.insert_volatility(
                    trade_date=indicators['trade_date'],
                    daily_return=indicators.get('daily_return'),
                    daily_volatility=indicators.get('daily_volatility'),
                    weekly_volatility=indicators.get('weekly_volatility'),
                    ma5=indicators.get('ma5'),
                    ma10=indicators.get('ma10'),
                    ma20=indicators.get('ma20')
                ):
                    saved_count += 1
            
            logger.info(f'成功保存{saved_count}条指标数据')
            return saved_count
        
        except Exception as e:
            logger.error(f'处理指标失败: {e}')
            return 0


# 全局计算器实例
calculator = DataCalculator()
