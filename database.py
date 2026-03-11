# -*- coding: utf-8 -*-
"""
数据库操作模块
"""

import sqlite3
from pathlib import Path
from datetime import datetime
import logging
from config import DATABASE_PATH, LOG_FILE, LOG_LEVEL

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


class Database:
    """数据库操作类"""
    
    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """初始化数据库表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 黄金价格表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS gold_price (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_date TEXT NOT NULL UNIQUE,
                    close_price REAL NOT NULL,
                    open_price REAL,
                    high_price REAL,
                    low_price REAL,
                    volume REAL,
                    change_amount REAL,
                    change_percent REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 波动率指标表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS volatility_indicator (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_date TEXT NOT NULL UNIQUE,
                    daily_return REAL,
                    daily_volatility REAL,
                    weekly_volatility REAL,
                    ma5 REAL,
                    ma10 REAL,
                    ma20 REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 数据更新日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS update_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_count INTEGER,
                    status TEXT,
                    message TEXT
                )
            ''')
            
            conn.commit()
            logger.info('数据库初始化成功')
        except Exception as e:
            logger.error(f'数据库初始化失败: {e}')
            raise
        finally:
            conn.close()
    
    def insert_price(self, trade_date, close_price, open_price=None, high_price=None, 
                     low_price=None, volume=None, change_amount=None, change_percent=None):
        """插入价格数据"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO gold_price 
                (trade_date, close_price, open_price, high_price, low_price, volume, 
                 change_amount, change_percent, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (trade_date, close_price, open_price, high_price, low_price, volume,
                  change_amount, change_percent, datetime.now()))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f'插入价格数据失败: {e}')
            return False
        finally:
            conn.close()
    
    def insert_volatility(self, trade_date, daily_return=None, daily_volatility=None,
                         weekly_volatility=None, ma5=None, ma10=None, ma20=None):
        """插入波动率数据"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO volatility_indicator
                (trade_date, daily_return, daily_volatility, weekly_volatility, ma5, ma10, ma20, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (trade_date, daily_return, daily_volatility, weekly_volatility, ma5, ma10, ma20, datetime.now()))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f'插入波动率数据失败: {e}')
            return False
        finally:
            conn.close()
    
    def get_price_data(self, start_date=None, end_date=None, limit=None):
        """获取价格数据"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            query = 'SELECT * FROM gold_price WHERE 1=1'
            params = []
            
            if start_date:
                query += ' AND trade_date >= ?'
                params.append(start_date)
            if end_date:
                query += ' AND trade_date <= ?'
                params.append(end_date)
            
            query += ' ORDER BY trade_date DESC'
            
            if limit:
                query += ' LIMIT ?'
                params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f'获取价格数据失败: {e}')
            return []
        finally:
            conn.close()
    
    def get_volatility_data(self, start_date=None, end_date=None):
        """获取波动率数据"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            query = 'SELECT * FROM volatility_indicator WHERE 1=1'
            params = []
            
            if start_date:
                query += ' AND trade_date >= ?'
                params.append(start_date)
            if end_date:
                query += ' AND trade_date <= ?'
                params.append(end_date)
            
            query += ' ORDER BY trade_date DESC'
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f'获取波动率数据失败: {e}')
            return []
        finally:
            conn.close()
    
    def get_latest_price(self):
        """获取最新价格"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM gold_price ORDER BY trade_date DESC LIMIT 1')
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f'获取最新价格失败: {e}')
            return None
        finally:
            conn.close()
    
    def delete_all_price_data(self):
        """删除所有价格数据"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM gold_price')
            cursor.execute('DELETE FROM volatility_indicator')
            conn.commit()
            logger.info('已删除所有历史数据')
            return True
        except Exception as e:
            logger.error(f'删除数据失败: {e}')
            return False
        finally:
            conn.close()
    
    def log_update(self, data_count, status='success', message=''):
        """记录数据更新日志"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO update_log (data_count, status, message)
                VALUES (?, ?, ?)
            ''', (data_count, status, message))
            conn.commit()
        except Exception as e:
            logger.error(f'记录日志失败: {e}')
        finally:
            conn.close()


# 全局数据库实例
db = Database()
