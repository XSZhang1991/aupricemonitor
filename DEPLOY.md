# 项目部署指南

## 概述

黄金价格与波动率监控系统已经完全实现，包括：
- ✅ 数据抓取模块（使用akshare）
- ✅ 数据计算模块（波动率、技术指标）
- ✅ SQLite3数据库
- ✅ Streamlit Web界面
- ✅ 后台自动更新线程
- ✅ 完整的日志系统

## 本地运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行程序

```bash
python main.py
```

程序会自动：
- 初始化数据库
- 加载30天的历史黄金数据
- 计算所有技术指标
- 启动Streamlit Web服务

然后在浏览器中打开：`http://localhost:8501`

## GitHub推送

### 问题排除

如果遇到GitHub推送的403错误，请按以下步骤解决：

#### 步骤1：确保仓库存在

在GitHub上创建新仓库：
1. 访问 https://github.com/new
2. Repository name: `aupricemonitor`
3. 勾选 "Initialize this repository with a README" (可选)
4. 点击 "Create repository"

#### 步骤2：生成新的Personal Access Token

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token"
3. 选择以下权限：
   - repo (完全控制仓库权限)
   - workflow (GitHub Actions权限，可选)
4. 点击 "Generate token" 并复制显示的Token

#### 步骤3：使用新Token推送

在项目目录运行：

```bash
git remote set-url origin "https://USERNAME:YOUR_TOKEN@github.com/USERNAME/aupricemonitor.git"
git push -u origin master
```

将以下部分替换为你的信息：
- `USERNAME`: 你的GitHub用户名
- `YOUR_TOKEN`: 刚刚生成的Token

或者直接双击运行 `push.bat` 脚本。

### 快速推送脚本

如果使用Windows，可以直接双击 `push.bat` 执行推送：

```batch
@REM push.bat 会自动执行推送命令
```

### 验证推送成功

推送成功后，访问 https://github.com/USERNAME/aupricemonitor 查看你的仓库

## 服务器部署

### Linux/macOS部署

1. **克隆仓库**
```bash
git clone https://github.com/username/aupricemonitor.git
cd aupricemonitor
```

2. **创建虚拟环境**
```bash
python3.9 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **运行程序**
```bash
python main.py
```

### Docker部署（可选）

创建 `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

构建和运行：

```bash
docker build -t gold-monitor .
docker run -p 8501:8501 gold-monitor
```

### 使用Systemd服务（Linux）

创建 `/etc/systemd/system/gold-monitor.service`:

```ini
[Unit]
Description=Gold Monitor Service
After=network.target

[Service]
Type=simple
User=goldmonitor
WorkingDirectory=/home/goldmonitor/aupricemonitor
ExecStart=/home/goldmonitor/aupricemonitor/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用和启动服务：

```bash
sudo systemctl enable gold-monitor
sudo systemctl start gold-monitor
systemctl status gold-monitor
```

## 项目文件结构

```
aupricemonitor/
├── main.py              # 程序入口
├── config.py            # 配置管理
├── database.py          # 数据库操作
├── data_fetcher.py      # 数据抓取模块
├── data_calculator.py   # 波动率计算
├── app.py               # Streamlit前端
├── requirements.txt     # Python依赖
├── .gitignore          # Git忽略文件
├── README.md           # 项目说明
├── DEPLOY.md           # 本文件
├── push.bat            # Windows推送脚本
├── data/               # 数据库文件目录
├── logs/               # 日志文件目录
└── templates/          # HTML模板（保留以供扩展）
```

## 功能清单

### 核心功能
- [x] 实时黄金价格监控
- [x] 日波动率计算
- [x] 周波动率计算
- [x] 技术指标（MA5/10/20）
- [x] 历史数据存储
- [x] Web实时可视化
- [x] 数据导出（Excel/CSV）

### 后端功能
- [x] 自动数据抓取（每5分钟）
- [x] 数据验证和异常处理
- [x] SQLite3数据管理
- [x] 日志记录系统
- [x] 错误重试机制

### 前端功能
- [x] 实时数据展示
- [x] K线图表
- [x] 波动率走势图
- [x] 历史数据查询
- [x] 数据导出功能
- [x] 响应式界面设计

## 常见问题

### Q: 如何更改数据更新频率？
A: 编辑 `config.py` 中的 `FETCH_INTERVAL`（单位：秒）

### Q: 数据库文件位置在哪？
A: `data/gold_monitor.db`

### Q: 如何清空所有数据？
A: 在Web界面点击侧边栏的"清空所有数据"按钮

### Q: 如何修改Web服务端口？
A: 编辑 `config.py` 中的 `WEB_PORT`

### Q: 如何获取更多历史数据？
A: 编辑 `config.py` 中的 `HISTORICAL_DAYS`

## 相关资源

- Akshare文档: https://akshare.akfamily.xyz/
- Streamlit文档: https://docs.streamlit.io/
- SQLite文档: https://www.sqlite.org/docs.html

## 技术支持

如遇问题，请检查：
1. `logs/gold_monitor.log` - 系统日志
2. 网络连接 - 确保能访问数据源
3. Python版本 - 建议使用3.9+

## 更新日志

### v1.0.0 (2026-03-11)
- 初始版本发布
- 完整实现所有核心功能
- 提供Web界面
- 支持数据导出
