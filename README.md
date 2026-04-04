# 基于Transformer的股票情绪预测系统

> 一个基于BERT模型的A股市场投资者情绪分析与预测平台

**系统状态：✅ 开发完成（v2.0 功能扩展版），可部署使用**

---

## 系统概述

本系统通过采集金融社交媒体评论数据，利用BERT深度学习模型进行NLP情感分析，量化投资者情绪指标，并与实际市场行情进行对比验证，帮助投资者洞察市场情绪动向。

系统支持多模型对比实验（BERT-wwm / FinBERT / 词典方法）、方面级情感分析（业绩/政策/技术面/资金面/行业）、个股情绪画像、情绪预警等高级功能。

---

## 技术栈

### 后端
| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.9+ | 主语言 |
| FastAPI | 0.109+ | Web框架 |
| SQLAlchemy | 2.0+ | ORM |
| PyMySQL | 1.1+ | MySQL驱动 |
| Redis | 5.0+ | 缓存 |
| Celery | 5.3+ | 异步任务队列 |
| Uvicorn | 0.27+ | ASGI服务器 |
| Loguru | 0.7+ | 日志管理 |

### 前端
| 技术 | 版本 | 用途 |
|------|------|------|
| Vue.js | 3.x | 前端框架 |
| Vite | 5.x | 构建工具 |
| Element Plus | 2.x | UI组件库 |
| ECharts | 5.x | 数据可视化 |
| Pinia | 2.x | 状态管理 |
| Vue Router | 4.x | 路由管理 |

### AI/NLP
| 技术 | 版本 | 用途 |
|------|------|------|
| PyTorch | 2.x | 深度学习框架 |
| Transformers | 4.x | BERT模型 |
| chinese-bert-wwm-ext | - | 中文预训练模型 |
| jieba | 0.42+ | 中文分词 |

### 运维
| 技术 | 用途 |
|------|------|
| Docker | 容器化部署 |
| Nginx | 反向代理 |
| Prometheus | 监控指标 |
| Grafana | 可视化仪表板 |
| GitHub Actions | CI/CD |

---

## 系统架构

```
┌──────────────────────────────────────────────────────────────────────┐
│                           前端 (Vue3)                                │
│  Dashboard │ Stocks │ Trend │ Validation │ Experiment │ Alerts │ .. │
└────────────────────────────┬─────────────────────────────────────────┘
                             │ HTTP API (Nginx反向代理)
┌────────────────────────────┴─────────────────────────────────────────┐
│                         后端 (FastAPI)                                │
├──────────┬──────────┬──────────┬──────────┬──────────┬───────────────┤
│ 爬虫服务  │ 情感分析  │ 情绪量化  │ 市场验证  │ 多模型对比 │  情绪预警     │
│ Crawler  │Sentiment │ Quantify │Validator │MultiModel│  AlertEngine  │
├──────────┴──────────┴──────────┴──────────┴──────────┴───────────────┤
│   认证(JWT) │ 缓存(Redis) │ 任务队列(Celery) │ 监控(Prometheus)       │
├─────────────────────────────────────────────────────────────────────┤
│                    MySQL │ Redis │ Prometheus                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 功能模块

### 1. 数据采集模块
- 东方财富股吧爬虫（已验证398+条数据）
- 雪球、新浪财经爬虫（框架已实现）
- 支持增量采集和定时任务

### 2. 情感分析模块
- BERT深度学习模型（1005条训练数据）
- 金融情感词典辅助（800+词条）
- 三分类：积极/中性/消极

### 3. 多模型对比实验 🆕
- **BERT-wwm**：chinese-bert-wwm-ext 预训练模型微调
- **FinBERT**：金融领域BERT模型
- **词典方法**：基于金融情感词典的规则分析
- 模型性能基准测试（Accuracy / F1 / Precision / Recall）
- 混淆矩阵可视化

### 4. 方面级情感分析 🆕
- 5大分析维度：业绩、政策、技术面、资金面、行业
- 每个方面独立的正面/负面关键词库
- 雷达图展示各维度情感分布

### 5. 个股情绪画像 🆕
- 波动性、偏向性、活跃度、一致性 四维画像
- 趋势方向判断与行情关联度计算
- 自动生成画像标签（如「情绪稳定型」「看涨偏向」等）
- 雷达图可视化

### 6. 情绪预警系统 🆕
- 情绪强度突变检测（>2σ标准差）
- 看涨/看跌极端值预警（>85 / <15）
- 评论量暴增检测（>3倍均值）
- 温度异常预警
- 预警严重等级：高危 / 中等 / 低

### 7. 情绪量化模块
- 看涨指数、看跌指数
- 情绪强度、情绪温度
- 情绪波动率

### 8. 市场验证模块
- Pearson相关性分析
- 方向准确率验证
- 格兰杰因果检验

### 9. 用户认证系统
- JWT Token认证
- 登录/注册页面
- 路由守卫保护

### 10. 运维监控
- Prometheus指标采集
- Grafana可视化仪表板
- 结构化日志与轮转
- API速率限制
- Redis缓存优化

---

## 快速开始

### 方式一：Docker一键部署（推荐）

```bash
# 克隆项目
git clone <repository-url>
cd stock_predicition

# 启动所有服务
docker-compose up -d

# 访问地址
# 前端: http://localhost
# 后端API: http://localhost:8000
# Grafana: http://localhost:3000 (admin/admin123)
# Prometheus: http://localhost:9090
```

### 方式二：本地开发

#### 环境要求
- Python 3.9+
- Node.js 18+
- MySQL 8.0+
- Redis（可选，用于缓存加速）
- CUDA GPU（可选，用于BERT模型加速）

#### 1. 克隆项目
```bash
git clone <repository-url>
cd stock_predicition
```

#### 2. 配置数据库
```bash
# 创建数据库
mysql -uroot -p -e "CREATE DATABASE stock_sentiment CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 初始化表结构（包含8张表：stocks, comments, sentiments, emotions, quotes, experiment_results, aspect_sentiments, alerts）
mysql -uroot -p stock_sentiment < scripts/init_db.sql
```

#### 3. 配置环境变量
编辑 `backend/.env`：
```env
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=yourpassword
DB_NAME=stock_sentiment

# Redis配置（可选）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# 模型配置
MODEL_NAME=hfl/chinese-bert-wwm-ext
MODEL_MAX_LENGTH=128
MODEL_CACHE_DIR=./data/models

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
```

#### 4. 安装并启动后端
```bash
cd backend
pip install -r requirements.txt

# 开发模式（热重载）
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或直接运行
python -m app.main

# 服务运行在 http://localhost:8000
# API文档: http://localhost:8000/docs
```

#### 5. 安装并启动前端
```bash
cd frontend
npm install
npm run dev
# 服务运行在 http://localhost:5173
```

#### 6. 生成演示数据（首次运行）
```bash
cd scripts
python generate_demo_data.py
```

#### 7. 启动Celery（可选，用于异步任务）
```bash
cd backend
celery -A app.celery_app worker --loglevel=info
```

---

## 脚本工具

### 生成演示数据
```bash
python scripts/generate_demo_data.py
```

### 爬取真实评论
```bash
# 测试单只股票
python scripts/crawl_comments.py --mode test --stock 000001

# 爬取所有股票
python scripts/crawl_comments.py --mode all --days 7
```

### 同步行情数据
```bash
python scripts/sync_quotes.py
```

### 训练情感模型
```bash
python scripts/train_sentiment.py
```

---

## 项目结构

```
stock_predicition/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── api/               # API路由
│   │   │   ├── stocks.py      # 股票相关API
│   │   │   ├── emotion.py     # 情绪分析API
│   │   │   ├── sentiment.py   # 情感分析API
│   │   │   ├── validation.py  # 市场验证API
│   │   │   ├── crawler.py     # 爬虫管理API
│   │   │   ├── auth.py        # 用户认证API
│   │   │   ├── experiment.py  # 实验对比API 🆕
│   │   │   └── alerts.py      # 情绪预警API 🆕
│   │   ├── core/              # 核心配置
│   │   ├── models/            # 数据模型（8张表ORM）
│   │   ├── services/          # 业务服务
│   │   │   ├── crawler/       # 爬虫服务
│   │   │   ├── sentiment/     # 情感分析
│   │   │   │   ├── analyzer.py       # BERT分析器
│   │   │   │   ├── lexicon.py        # 金融词典
│   │   │   │   ├── multi_model.py    # 多模型管理器 🆕
│   │   │   │   └── aspect_analyzer.py # 方面级分析 🆕
│   │   │   ├── quantify/      # 情绪量化
│   │   │   │   ├── calculator.py     # 指标计算器
│   │   │   │   └── profiler.py       # 情绪画像 🆕
│   │   │   ├── alert/         # 情绪预警 🆕
│   │   │   │   └── engine.py         # 预警引擎
│   │   │   ├── market/        # 市场验证
│   │   │   ├── processor/     # 文本处理
│   │   │   └── scheduler/     # 定时任务
│   │   └── main.py            # 入口文件
│   ├── data/                  # 数据文件
│   │   ├── lexicon/           # 情感词典
│   │   └── models/            # 训练模型
│   └── requirements.txt
│
├── frontend/                  # 前端应用
│   ├── src/
│   │   ├── api/              # API封装
│   │   ├── views/            # 页面组件（10个）
│   │   │   ├── Dashboard.vue    # 情绪仪表盘
│   │   │   ├── Stocks.vue       # 股票列表
│   │   │   ├── StockDetail.vue  # 股票详情（含方面分析+画像）
│   │   │   ├── Trend.vue        # 趋势分析
│   │   │   ├── Validation.vue   # 市场验证
│   │   │   ├── Sentiment.vue    # 情感分析测试
│   │   │   ├── Experiment.vue   # 实验对比 🆕
│   │   │   ├── Alerts.vue       # 情绪预警 🆕
│   │   │   ├── Settings.vue     # 系统设置
│   │   │   └── Login.vue        # 登录页
│   │   ├── router/           # 路由配置
│   │   └── main.js
│   └── package.json
│
├── scripts/                   # 脚本工具
│   ├── init_db.sql           # 数据库初始化（8张表）
│   ├── generate_demo_data.py # 演示数据生成
│   ├── crawl_comments.py     # 评论爬取
│   ├── sync_quotes.py        # 行情同步
│   └── train_sentiment.py    # 模型训练
│
├── deploy/                    # 部署配置
│   ├── prometheus/           # Prometheus配置
│   └── grafana/              # Grafana配置
│
├── docs/                      # 文档
│   ├── spec.md               # 系统规格说明
│   └── DEVELOPMENT_STATUS.md # 开发进度
│
├── docker-compose.yml         # Docker编排
└── README.md                  # 本文档
```

---

## API接口

### 核心业务
| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/v1/stocks` | GET | 获取股票列表 |
| `/api/v1/stocks/{code}` | GET | 获取股票详情 |
| `/api/v1/stocks/{code}/comments` | GET | 获取股票评论 |
| `/api/v1/stocks/{code}/aspects` | GET | 方面级情感分析 🆕 |
| `/api/v1/stocks/{code}/profile` | GET | 个股情绪画像 🆕 |
| `/api/v1/emotion/overview` | GET | 情绪概览 |
| `/api/v1/emotion/trend` | GET | 情绪趋势 |
| `/api/v1/sentiment/analyze` | POST | 情感分析 |
| `/api/v1/validation/correlation` | GET | 相关性分析 |
| `/api/v1/validation/granger` | GET | 格兰杰检验 |
| `/api/v1/crawler/start` | POST | 启动爬虫 |

### 实验对比 🆕
| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/v1/experiment/compare` | POST | 多模型对比分析 |
| `/api/v1/experiment/benchmark` | POST | 基准测试 |
| `/api/v1/experiment/results` | GET | 历史实验结果 |
| `/api/v1/experiment/metrics` | GET | 模型性能指标 |
| `/api/v1/experiment/models` | GET | 可用模型列表 |

### 情绪预警 🆕
| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/v1/alerts` | GET | 预警列表 |
| `/api/v1/alerts/{id}/read` | PUT | 标记已读 |
| `/api/v1/alerts/read-all` | PUT | 全部已读 |
| `/api/v1/alerts/scan` | POST | 触发预警扫描 |
| `/api/v1/alerts/stats` | GET | 预警统计 |

完整API文档：http://localhost:8000/docs （Swagger UI）

---

## 开发状态

**当前状态：✅ 开发完成（v2.0 扩展版 - 48/48项任务）**

### 核心功能（v1.0）
- [x] 项目架构搭建
- [x] 数据库设计（8张表）
- [x] 后端API开发（45条路由）
- [x] 前端页面开发（10个页面）
- [x] 爬虫模块（东方财富）
- [x] BERT情感分析
- [x] 情绪量化指标
- [x] 市场验证分析
- [x] AKShare行情对接
- [x] 定时任务调度

### 扩展功能（v2.0）🆕
- [x] 多模型对比实验（BERT-wwm / FinBERT / 词典方法）
- [x] 方面级情感分析（5大维度）
- [x] 个股情绪画像（4维特征）
- [x] 情绪预警系统（5类检测规则）
- [x] 实验对比可视化面板
- [x] 预警管理页面

### 安全认证
- [x] JWT用户认证
- [x] 登录/注册页面
- [x] 路由守卫

### 系统优化
- [x] API速率限制
- [x] 结构化日志系统
- [x] Redis缓存
- [x] 49项单元测试

### 运维部署
- [x] Docker容器化（6个服务）
- [x] Nginx反向代理
- [x] Celery异步队列
- [x] Prometheus监控
- [x] Grafana仪表板
- [x] GitHub Actions CI/CD

---

## 单元测试

```bash
cd backend
pytest tests/ -v
# 49 passed
```

---

## 数据库表结构

| 表名 | 说明 |
|------|------|
| `stocks` | 股票信息表 |
| `comments` | 评论数据表 |
| `sentiments` | 情感分析结果表 |
| `emotions` | 情绪指标表 |
| `quotes` | 股票行情表 |
| `experiment_results` | 实验结果表 🆕 |
| `aspect_sentiments` | 方面级情感表 🆕 |
| `alerts` | 预警记录表 🆕 |

---

## 监控指标

| 指标 | 说明 |
|------|------|
| `http_requests_total` | HTTP请求总数 |
| `http_request_duration_seconds` | 请求耗时 |
| `sentiment_analysis_total` | 情感分析次数 |
| `crawler_comments_collected_total` | 爬虫采集数 |
| `cache_hits_total` | 缓存命中 |
| `emotion_index` | 情绪指数 |

---

## 许可证

MIT License

---

## 联系方式

如有问题，请提交Issue或联系开发者。
