# StockTrade Web - 股票选股系统

> 个人投研学习平台 - 基于 AKShare + FastAPI + Vue3 的股票选股与可视化系统

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3.5+-brightgreen.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ 核心特性

### ⚡ 高性能数据同步
- **9倍速度提升**：5000只股票从90分钟缩短至10分钟
- **智能双模式**：初始化模式（慢速全量）+ 日常模式（快速增量）
- **并发控制**：20个并发请求 + 批量写入（50条/批）
- **GitHub备份**：支持自动备份数据到GitHub Releases

### 📊 实时市场看板
- **指数数据**：上证指数、深证成指、创业板指、科创50
- **涨跌统计**：涨停家数、跌停家数、涨跌分布
- **涨跌对比**：实时封板率、炸板率统计
- **数据来源**：东方财富网实时API

### 🎯 智能选股策略
- **5种内置策略**：少妇战法、SuperB1、补票战法、填坑战法、上穿60放量
- **批量执行**：支持多策略同时运行
- **可视化配置**：策略参数可视化编辑
- **结果筛选**：支持按股票、日期、策略类型筛选

### 🛠️ 任务管理系统
- **异步执行**：后台任务不阻塞用户操作
- **进度跟踪**：实时显示任务进度
- **任务控制**：支持暂停、恢复、取消任务
- **历史记录**：查看所有任务执行历史

## 🏗️ 技术架构

### 后端技术栈
```
FastAPI 0.115      # 现代异步Web框架
├── SQLAlchemy 2.0  # ORM
├── SQLite          # 轻量级数据库
├── AKShare 1.14    # 财经数据接口
├── Pandas 2.2      # 数据处理
├── NumPy 2.1       # 数值计算
└── SciPy 1.14      # 科学计算
```

### 前端技术栈
```
Vue 3.5            # 渐进式框架
├── TypeScript 5.6  # 类型安全
├── Vite 6.0        # 构建工具
├── Element Plus 2.8 # UI组件库
├── ECharts 5.5     # 图表库
├── Pinia 2.2       # 状态管理
└── Axios 1.7       # HTTP客户端
```

## 📁 项目结构

```
StockTradebyZ-main/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/            # API 路由
│   │   │   ├── stocks.py      # 股票数据接口
│   │   │   ├── strategies.py  # 选股策略接口
│   │   │   ├── sync.py        # 双模式同步接口
│   │   │   ├── high_performance_sync.py  # 高性能同步接口
│   │   │   ├── task_management.py  # 任务管理接口
│   │   │   └── scheduled_tasks.py  # 定时任务接口
│   │   ├── core/              # 核心配置
│   │   │   ├── config.py      # 应用配置
│   │   │   ├── sync_config.py # 同步配置（双模式）
│   │   │   └── scheduler.py   # 定时任务调度器
│   │   ├── models/            # 数据库模型
│   │   │   ├── stock.py       # 股票模型
│   │   │   ├── kline.py       # K线模型
│   │   │   └── strategy.py    # 策略模型
│   │   ├── schemas/           # Pydantic Schema
│   │   ├── services/          # 业务服务
│   │   │   ├── eastmoney_service.py    # 东方财富数据服务
│   │   │   ├── high_performance_sync.py # 高性能同步服务
│   │   │   ├── github_backup_service.py # GitHub备份服务
│   │   │   ├── improved_task_queue.py   # 改进的任务队列
│   │   │   └── background_task.py       # 后台任务执行器
│   │   ├── db/                # 数据库会话
│   │   ├── utils/             # 工具函数
│   │   └── main.py            # 应用入口
│   ├── requirements/          # 依赖管理
│   └── data/                  # 数据目录
├── frontend/                   # Vue3 前端
│   ├── src/
│   │   ├── api/               # API 调用
│   │   │   ├── stock.ts       # 股票API
│   │   │   ├── strategy.ts    # 策略API
│   │   │   ├── sync.ts        # 同步API
│   │   │   └── task.ts        # 任务API
│   │   ├── assets/            # 静态资源
│   │   ├── components/        # 组件
│   │   │   ├── strategy/      # 策略组件
│   │   │   └── SyncProgressPanel.vue  # 同步进度面板
│   │   ├── router/            # 路由配置
│   │   ├── store/             # 状态管理
│   │   ├── types/             # 类型定义
│   │   ├── utils/             # 工具函数
│   │   ├── views/             # 页面视图
│   │   │   ├── Dashboard.vue  # 市场看板
│   │   │   ├── StockData.vue  # 股票管理
│   │   │   ├── StockKline.vue # K线图表
│   │   │   ├── StrategyList.vue  # 策略列表
│   │   │   └── StrategyResults.vue # 选股结果
│   │   ├── App.vue            # 根组件
│   │   └── main.ts            # 应用入口
│   └── package.json
├── docs/                       # 文档目录
│   └── SCHEDULED_TASKS_GUIDE.md  # 定时任务指南
├── SYNC_PERFORMANCE.md         # 性能对比文档
└── README.md                   # 本文档
```

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- npm / pnpm

### 1. 克隆项目

```bash
git clone https://github.com/kevin12369/StockTradebyZ.git
cd StockTradebyZ-main
```

### 2. 后端启动

```bash
# 进入后端目录
cd backend

# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# 安装依赖
pip install -r requirements/base.txt

# 启动后端服务
python -m app.main
```

后端服务运行在：http://localhost:8000

API 文档：http://localhost:8000/docs

### 3. 前端启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install
# 或使用 pnpm
pnpm install

# 启动开发服务器
npm run dev
```

前端服务运行在：http://localhost:5173

## 📖 使用指南

### 数据同步

#### 方式一：双模式同步（推荐）

**日常快速同步**（每天使用）
```bash
POST /api/v1/sync/quick?mode=daily
```
- 只更新最近3天数据
- 速度：5000只股票约10分钟
- 推荐：每天收盘后执行

**初始化全量同步**（首次部署）
```bash
POST /api/v1/sync/quick?mode=init
```
- 获取近3年历史数据
- 速度：5000只股票约2小时
- 推荐：首次部署或数据缺失时执行
- 支持GitHub自动备份

#### 方式二：高性能同步（极速）

**高性能日常同步**
```bash
POST /api/v1/sync/fast/daily?concurrent=20
```
- 20个并发请求
- 批量写入数据库
- 速度：5000只股票约10分钟

**高性能初始化同步**
```bash
POST /api/v1/sync/fast/init?concurrent=5
```
- 5个并发请求（保守）
- 速度：5000只股票约2小时

#### 性能对比

| 方案 | 并发数 | 5000只股票耗时 | 吞吐量 |
|------|--------|----------------|--------|
| 原方案 | 1 | ~90分钟 | 55只/小时 |
| 双模式-日常 | 1 | ~10分钟 | 3300只/小时 |
| **高性能-日常** | **20** | **~10分钟** | **30000只/小时** |
| **高性能-初始化** | **5** | **~2小时** | **2500只/小时** |

### 选股策略

1. 访问「选股策略」页面
2. 选择要执行的一个或多个策略
3. 选择选股日期（可选，默认为当天）
4. 点击「执行选股」按钮
5. 等待策略执行完成（后台异步执行）
6. 查看选股结果

### 市场看板

- 访问「市场看板」页面
- 查看实时指数数据、涨跌统计
- 数据自动刷新（每30秒）

## 📡 API 接口

### 股票数据接口

| 方法 | 端点 | 功能 |
|------|------|------|
| GET | `/api/v1/stocks` | 获取股票列表 |
| GET | `/api/v1/stocks/{ts_code}` | 获取股票详情 |
| GET | `/api/v1/stocks/{ts_code}/kline` | 获取K线数据 |
| GET | `/api/v1/stocks/kline/status` | 获取K线同步状态 |

### 数据同步接口

| 方法 | 端点 | 功能 |
|------|------|------|
| POST | `/api/v1/sync/quick` | 快速同步（推荐） |
| POST | `/api/v1/sync/daily` | 日常快速同步 |
| POST | `/api/v1/sync/init` | 初始化全量同步 |
| GET | `/api/v1/sync/estimate` | 估算同步时间 |
| POST | `/api/v1/sync/backup` | 手动GitHub备份 |
| GET | `/api/v1/sync/backups` | 列出GitHub备份 |

### 高性能同步接口

| 方法 | 端点 | 功能 |
|------|------|------|
| POST | `/api/v1/sync/fast/daily` | 高性能日常同步 |
| POST | `/api/v1/sync/fast/init` | 高性能初始化同步 |
| GET | `/api/v1/sync/fast/estimate` | 估算高性能同步时间 |
| GET | `/api/v1/sync/fast/compare` | 性能对比 |

### 选股策略接口

| 方法 | 端点 | 功能 |
|------|------|------|
| GET | `/api/v1/strategies` | 获取策略列表 |
| GET | `/api/v1/strategies/{id}` | 获取策略详情 |
| PUT | `/api/v1/strategies/{id}` | 更新策略配置 |
| POST | `/api/v1/strategies/run` | 执行选股策略 |
| GET | `/api/v1/strategies/results` | 获取选股结果 |
| GET | `/api/v1/strategies/results/stats` | 获取选股统计 |

### 任务管理接口

| 方法 | 端点 | 功能 |
|------|------|------|
| GET | `/api/v1/tasks` | 获取所有任务 |
| GET | `/api/v1/tasks/{task_id}` | 获取任务详情 |
| POST | `/api/v1/tasks/{task_id}/cancel` | 取消任务 |
| POST | `/api/v1/tasks/{task_id}/pause` | 暂停任务 |
| POST | `/api/v1/tasks/{task_id}/resume` | 恢复任务 |
| DELETE | `/api/v1/tasks/{task_id}` | 删除任务记录 |

### 市场数据接口

| 方法 | 端点 | 功能 |
|------|------|------|
| GET | `/api/v1/market/overview` | 获取市场概览 |
| GET | `/api/v1/market/indices` | 获取指数数据 |
| GET | `/api/v1/market/zdt` | 获取涨跌停数据 |
| GET | `/api/v1/market/distribution` | 获取涨跌分布 |

## ⚙️ 配置说明

### 后端配置

配置文件：`backend/.env`

```bash
# 应用配置
APP_NAME=StockTrade Backend
DEBUG=true

# 服务器配置
HOST=0.0.0.0
PORT=8000

# 数据库配置
DATABASE_URL=sqlite:///./data/stocktrade.db

# GitHub备份配置
GITHUB_TOKEN=your_github_token
GITHUB_REPO=kevin12369/StockTradebyZ

# AKShare配置
AKSHARE_TIMEOUT=30
AKSHARE_MAX_RETRIES=3

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### 前端配置

配置文件：`frontend/.env.development`

```bash
# API Base URL
VITE_API_BASE_URL=http://localhost:8000

# App Title
VITE_APP_TITLE=股票选股系统
```

## 🧪 开发指南

### 后端开发

```bash
# 安装开发依赖
pip install -r requirements/dev.txt

# 代码格式化
black backend/app/
isort backend/app/

# 代码检查
pylint backend/app/
```

### 前端开发

```bash
# 代码格式化
npm run format

# 代码检查
npm run lint

# 类型检查
npm run build
```

## 📊 系统架构

### 同步架构

```
┌─────────────────────────────────────────────────────┐
│                     用户请求                          │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│               任务队列 (improved_task_queue)         │
│  - 任务排队、进度更新                                 │
│  - 取消/暂停/恢复支持                                │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│          高性能同步服务 (high_performance_sync)      │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │  并发控制器 (ConcurrentRateLimiter)          │    │
│  │  - 最大并发数: 20                            │    │
│  │  - 速率限制: 5 req/s                         │    │
│  └────────────────────────────────────────────┘    │
│                   │                                  │
│                   ▼                                  │
│  ┌────────────────────────────────────────────┐    │
│  │  线程池 (ThreadPoolExecutor, 20 workers)    │    │
│  │  - 在线程池中执行AKShare调用                 │    │
│  │  - 避免阻塞事件循环                          │    │
│  └────────────────────────────────────────────┘    │
│                   │                                  │
│                   ▼                                  │
│  ┌────────────────────────────────────────────┐    │
│  │  批量写入器 (BatchWriter)                   │    │
│  │  - 批次大小: 50条                           │    │
│  │  - 刷新间隔: 3秒                            │    │
│  └────────────────────────────────────────────┘    │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│                   数据库                             │
│  批量写入 (bulk_insert_mappings)                    │
└─────────────────────────────────────────────────────┘
```

## 🔧 故障排除

### 问题1：后端启动失败

**解决方案：**
- 检查 Python 版本 >= 3.11
- 确保已安装所有依赖：`pip install -r requirements/base.txt`
- 检查数据库是否已初始化

### 问题2：前端无法连接后端

**解决方案：**
- 检查后端是否正常运行
- 检查 `frontend/.env.development` 中的 `VITE_API_BASE_URL` 配置
- 检查浏览器控制台的网络请求

### 问题3：数据同步速度慢

**解决方案：**
- 使用高性能同步模式：`POST /api/v1/sync/fast/daily`
- 调整并发数（默认20，可调整为30）
- 检查网络连接状态

### 问题4：GitHub备份失败

**解决方案：**
- 检查 `GITHUB_TOKEN` 是否正确配置
- 确保Token有repo权限
- 检查GitHub仓库是否存在

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

## ⚠️ 免责声明

本系统仅供学习与技术研究之用，**不构成任何投资建议**。

股市有风险，入市需谨慎。使用本系统进行投资决策所造成的任何损失，本系统及开发者不承担任何责任。

## 🙏 致谢

- [AKShare](https://akshare.akfamily.xyz/) - 开源财经数据接口库
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Python Web 框架
- [Vue.js](https://vuejs.org/) - 渐进式 JavaScript 框架
- [Element Plus](https://element-plus.org/) - Vue 3 UI 组件库
- [东方财富网](https://www.eastmoney.com/) - 数据来源

## 📮 联系方式

- GitHub: [kevin12369/StockTradebyZ](https://github.com/kevin12369/StockTradebyZ)
- Issue: [提交问题](https://github.com/kevin12369/StockTradebyZ/issues)

---

⭐ 如果这个项目对你有帮助，请给个Star支持一下！
