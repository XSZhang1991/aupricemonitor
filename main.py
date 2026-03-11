# -*- coding: utf-8 -*-
"""
程序主入口
"""

import logging
import time
import sys
from threading import Thread
from datetime import datetime

# 检查关键依赖
missing = []
for pkg in ('streamlit', 'pandas', 'numpy', 'akshare', 'plotly'):
    try:
        __import__(pkg)
    except ImportError:
        missing.append(pkg)

if missing:
    msg = (
        '缺少必要的Python库: ' + ", ".join(missing) +
        "\n请运行 `pip install -r requirements.txt` 安装依赖后重试。"
    )
    print(msg)
    sys.exit(1)

from config import LOG_FILE, LOG_LEVEL, FETCH_INTERVAL
from database import db
from data_fetcher import fetcher
from data_calculator import calculator

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


def init_system():
    """系统初始化"""
    logger.info('=' * 50)
    logger.info('黄金价格与波动率监控系统启动')
    logger.info(f'启动时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    logger.info('=' * 50)
    
    # 初始化数据库
    logger.info('正在初始化数据库...')
    db.init_database()
    logger.info('数据库初始化完成')
    
    # 首次加载历史数据
    logger.info('正在加载历史数据...')
    df = fetcher.fetch_gold_price(days=30)
    count = fetcher.process_and_save_data(df)
    logger.info(f'成功加载{count}条历史数据')
    
    # 计算指标
    logger.info('正在计算技术指标...')
    indicator_count = calculator.process_and_save_indicators()
    logger.info(f'成功计算{indicator_count}条指标数据')
    
    logger.info('系统初始化完成，准备启动Web服务...')


def background_data_update():
    """后台数据更新线程"""
    logger.info('后台更新线程已启动')
    
    while True:
        try:
            time.sleep(FETCH_INTERVAL)
            
            logger.info(f'开始定时更新数据 ({datetime.now().strftime("%Y-%m-%d %H:%M:%S")})')
            
            # 更新数据
            df = fetcher.fetch_gold_price(days=1)
            fetcher.process_and_save_data(df)
            
            # 更新指标
            calculator.process_and_save_indicators()
            
            logger.info('数据更新完成')
        
        except Exception as e:
            logger.error(f'后台更新失败: {e}')
            db.log_update(0, 'error', str(e))


def main():
    """主函数"""
    try:
        # 系统初始化
        init_system()
        
        # 启动后台更新线程
        update_thread = Thread(target=background_data_update, daemon=True)
        update_thread.start()
        logger.info('后台数据更新线程已启动')
        
        # 启动Streamlit应用
        logger.info('正在启动Streamlit Web服务...')
        logger.info('请在浏览器中打开: http://localhost:8501')
        
        import streamlit.cli
        import sys
        
        sys.argv = ['streamlit', 'run', 'app.py']
        streamlit.cli.main()
    
    except KeyboardInterrupt:
        logger.info('程序被用户中断')
    except Exception as e:
        logger.error(f'系统错误: {e}')
        raise


if __name__ == '__main__':
    main()
