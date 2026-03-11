# -*- coding: utf-8 -*-
"""
程序主入口 - 直接运行Streamlit应用
"""

import subprocess
import sys
import os

def main():
    """启动Streamlit应用"""
    print("=" * 60)
    print("黄金价格与波动率监控系统")
    print("启动Streamlit服务...")
    print("=" * 60)
    print()
    
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_file = os.path.join(current_dir, 'app.py')
    
    # 运行Streamlit
    cmd = [sys.executable, '-m', 'streamlit', 'run', app_file, 
           '--server.port=8501', '--server.address=0.0.0.0']
    
    print(f"运行命令: {' '.join(cmd)}")
    print()
    print("Web服务已启动，请在浏览器中打开: http://localhost:8501")
    print("=" * 60)
    print()
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n程序已停止")
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

    main()
