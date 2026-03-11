# -*- coding: utf-8 -*-
"""
Streamlit前端应用
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging
import traceback
import sys

# 首先检查依赖
try:
    from config import LOG_FILE, LOG_LEVEL
    from database import db
    from data_fetcher import fetcher
    from data_calculator import calculator
except Exception as e:
    st.error(f"❌ 导入模块失败: {str(e)}")
    st.error("详细错误:")
    st.error(traceback.format_exc())
    st.stop()

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

# Streamlit页面配置
st.set_page_config(
    page_title='黄金价格与波动率监控系统',
    page_icon='📈',
    layout='wide',
    initial_sidebar_state='expanded'
)

# 自定义CSS样式
st.markdown('''
    <style>
    .metric-container {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 8px;
        margin: 10px 0;
    }
    .price-up {
        color: #ff4444;
    }
    .price-down {
        color: #44aa44;
    }
    </style>
''', unsafe_allow_html=True)

# 页面标题
st.title('📈 黄金价格与波动率监控系统')
st.markdown('---')

# 侧边栏配置
with st.sidebar:
    st.header('⚙️ 系统控制')
    
    if st.button('🔄 刷新数据', key='refresh_btn', use_container_width=True):
        with st.spinner('正在获取最新数据...'):
            fetcher.update_latest_data()
            calculator.process_and_save_indicators()
        st.success('✅ 数据更新成功')
    
    st.divider()
    
    st.subheader('📅 查询范围')
    query_type = st.radio('选择查询类型', ['最近天数', '按日期范围'])
    
    if query_type == '最近天数':
        days = st.slider('选择天数', 1, 365, 30)
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
    else:
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input('开始日期', datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input('结束日期', datetime.now())
        start_date = start_date.strftime('%Y-%m-%d')
        end_date = end_date.strftime('%Y-%m-%d')
    
    st.divider()
    
    if st.button('📥 导出数据为Excel', key='export_btn', use_container_width=True):
        try:
            price_data = db.get_price_data(start_date, end_date)
            volatility_data = db.get_volatility_data(start_date, end_date)
            
            # 合并数据
            df_price = pd.DataFrame(price_data)
            df_volatility = pd.DataFrame(volatility_data)
            
            if not df_price.empty and not df_volatility.empty:
                df_merged = df_price.merge(df_volatility, on='trade_date', how='left')
                
                # 导出为Excel
                filename = f'gold_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
                with pd.ExcelWriter(f'data/{filename}', engine='openpyxl') as writer:
                    df_merged.to_excel(writer, index=False, sheet_name='价格数据')
                
                st.success(f'✅ 数据已导出: {filename}')
            else:
                st.warning('⚠️ 没有数据可导出')
        except Exception as e:
            st.error(f'❌ 导出失败: {e}')
    
    if st.button('🗑️ 清空所有数据', key='delete_btn', use_container_width=True):
        if st.checkbox('确认删除所有历史数据'):
            db.delete_all_price_data()
            st.success('✅ 数据已清空')
    
    st.divider()
    st.info('💡 本系统每5分钟自动更新一次数据')


# 主要内容区域
try:
    # 获取数据
    price_data = db.get_price_data(start_date, end_date)
    volatility_data = db.get_volatility_data(start_date, end_date)
    
    if not price_data:
        st.warning('⚠️ 还没有数据，请点击"刷新数据"获取最新数据')
        
        # 提供初始化选项
        if st.button('🔨 初始化数据库并加载数据'):
            with st.spinner('正在初始化...'):
                try:
                    db.init_database()
                    st.success('✅ 数据库已初始化')
                    
                    df = fetcher.fetch_gold_price(days=30)
                    if df is not None and len(df) > 0:
                        count = fetcher.process_and_save_data(df)
                        st.success(f'✅ 已加载 {count} 条历史数据')
                    else:
                        st.warning('⚠️ 无法获取历史数据')
                except Exception as e:
                    st.error(f'❌ 初始化失败: {str(e)}')
    else:
        # 转换为DataFrame
        df_price = pd.DataFrame(price_data)
        df_volatility = pd.DataFrame(volatility_data)
        df_price = df_price.sort_values('trade_date')
        
        # 第一行：关键指标
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            latest_price = df_price.iloc[-1]['close_price']
            st.metric('当前价格 (元/克)', f'{latest_price:.2f}', '💰')
        
        with col2:
            if len(df_price) > 1:
                prev_price = df_price.iloc[-2]['close_price']
                change = latest_price - prev_price
                st.metric('涨跌额', f'{change:+.2f}', '📊')
            else:
                st.metric('涨跌额', '无', '📊')
        
        with col3:
            if len(df_price) > 1:
                prev_price = df_price.iloc[-2]['close_price']
                change_pct = (change / prev_price) * 100
                st.metric('涨跌幅(%)', f'{change_pct:+.2f}%', '📈' if change_pct > 0 else '📉')
            else:
                st.metric('涨跌幅(%)', '无', '📊')
        
        with col4:
            if not df_volatility.empty and df_volatility.iloc[-1]['daily_volatility'] is not None:
                daily_vol = df_volatility.iloc[-1]['daily_volatility']
                st.metric('日波动率', f'{daily_vol:.4f}', '📊')
            else:
                st.metric('日波动率', '计算中', '⏳')
        
        with col5:
            if not df_volatility.empty and df_volatility.iloc[-1]['weekly_volatility'] is not None:
                weekly_vol = df_volatility.iloc[-1]['weekly_volatility']
                st.metric('周波动率', f'{weekly_vol:.4f}', '📊')
            else:
                st.metric('周波动率', '计算中', '⏳')
        
        st.divider()
        
        # 第二行：图表
        tab1, tab2, tab3 = st.tabs(['💹 价格走势', '📊 波动率分析', '📋 历史数据'])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                # K线图
                st.subheader('黄金价格K线图')
                try:
                    fig_candle = go.Figure(data=[go.Candlestick(
                        x=df_price['trade_date'],
                        open=df_price['open_price'],
                        high=df_price['high_price'],
                        low=df_price['low_price'],
                        close=df_price['close_price']
                    )])
                    fig_candle.update_layout(height=500, xaxis_rangeslider_visible=False)
                    st.plotly_chart(fig_candle, use_container_width=True)
                except Exception as e:
                    st.warning(f"K线图显示失败: {e}")
            
            with col2:
                # 折线图
                st.subheader('黄金价格走势')
                try:
                    fig_line = go.Figure()
                    fig_line.add_trace(go.Scatter(
                        x=df_price['trade_date'],
                        y=df_price['close_price'],
                        mode='lines+markers',
                        name='收盘价',
                        line=dict(color='#1f77b4', width=2)
                    ))
                    
                    # 添加移动平均线
                    if 'ma5' in df_volatility.columns:
                        fig_line.add_trace(go.Scatter(
                            x=df_volatility['trade_date'],
                            y=df_volatility['ma5'],
                            mode='lines',
                            name='5日MA',
                            line=dict(color='#ff7f0e', width=1, dash='dash')
                        ))
                    
                    if 'ma20' in df_volatility.columns:
                        fig_line.add_trace(go.Scatter(
                            x=df_volatility['trade_date'],
                            y=df_volatility['ma20'],
                            mode='lines',
                            name='20日MA',
                            line=dict(color='#2ca02c', width=1, dash='dash')
                        ))
                    
                    fig_line.update_layout(height=500, hovermode='x')
                    st.plotly_chart(fig_line, use_container_width=True)
                except Exception as e:
                    st.warning(f"走势图显示失败: {e}")
        
        with tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader('日波动率走势')
                try:
                    if not df_volatility.empty and df_volatility['daily_volatility'].notna().any():
                        fig_vol = go.Figure()
                        fig_vol.add_trace(go.Scatter(
                            x=df_volatility['trade_date'],
                            y=df_volatility['daily_volatility'],
                            mode='lines+markers',
                            name='日波动率',
                            fill='tozeroy',
                            line=dict(color='#d62728')
                        ))
                        fig_vol.update_layout(height=400, hovermode='x')
                        st.plotly_chart(fig_vol, use_container_width=True)
                    else:
                        st.info('暂无波动率数据')
                except Exception as e:
                    st.warning(f"日波动率图显示失败: {e}")
            
            with col2:
                st.subheader('周波动率走势')
                try:
                    if not df_volatility.empty and df_volatility['weekly_volatility'].notna().any():
                        fig_weekly = go.Figure()
                        fig_weekly.add_trace(go.Scatter(
                            x=df_volatility['trade_date'],
                            y=df_volatility['weekly_volatility'],
                            mode='lines+markers',
                            name='周波动率',
                            fill='tozeroy',
                            line=dict(color='#9467bd')
                        ))
                        fig_weekly.update_layout(height=400, hovermode='x')
                        st.plotly_chart(fig_weekly, use_container_width=True)
                    else:
                        st.info('暂无波动率数据')
                except Exception as e:
                    st.warning(f"周波动率图显示失败: {e}")
        
        with tab3:
            st.subheader('历史价格数据')
            
            try:
                # 合并显示
                if not df_volatility.empty:
                    df_display = df_price.merge(df_volatility[['trade_date', 'daily_volatility', 'weekly_volatility', 'ma5', 'ma20']], 
                                               on='trade_date', how='left')
                else:
                    df_display = df_price
                
                df_display = df_display.sort_values('trade_date', ascending=False)
                
                # 提取显示列
                display_cols = ['trade_date', 'close_price', 'high_price', 'low_price', 'volume']
                
                df_display_cols = df_display[[col for col in display_cols if col in df_display.columns]].copy()
                
                # 重命名列
                rename_map = {
                    'trade_date': '交易日期',
                    'close_price': '收盘价',
                    'high_price': '最高价',
                    'low_price': '最低价',
                    'volume': '成交量'
                }
                df_display_cols = df_display_cols.rename(columns=rename_map)
                
                st.dataframe(df_display_cols, use_container_width=True, height=400)
                
                # 统计信息
                st.subheader('📊 统计信息')
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric('数据条数', len(df_price))
                
                with col2:
                    st.metric('最高价', f'{df_price["high_price"].max():.2f}')
                
                with col3:
                    st.metric('最低价', f'{df_price["low_price"].min():.2f}')
                
                with col4:
                    st.metric('平均价', f'{df_price["close_price"].mean():.2f}')
            except Exception as e:
                st.error(f'❌ 数据显示失败: {str(e)}')

except Exception as e:
    st.error(f'❌ 应用发生错误: {str(e)}')
    st.error('详细错误信息:')
    st.error(traceback.format_exc())

st.divider()
st.markdown('---')
st.markdown('**系统信息**: 黄金价格与波动率实时监控系统 | 版本 1.0.0 | 最后更新: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

