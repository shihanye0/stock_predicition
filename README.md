# 基于 Transformer 的股票情绪预测系统

> A-share 市场投资者情绪分析与预测平台

**当前版本：v2.0** — 全站深色主题 | 登录认证 | 多模型对比 | 情绪预警

---

## 系统概述

本系统通过采集金融社交媒体评论数据，利用 BERT 深度学习模型进行 NLP 情感分析，量化投资者情绪指标，并与实际市场行情进行对比验证，帮助投资者洞察市场情绪动向。

**核心能力：**
- 多模型对比实验（BERT-wwm / FinBERT / 词典方法）
- 方面级情感分析（业绩 / 政策 / 技术面 / 资金面 / 行业）
- 个股情绪画像（四维雷达图）
- 情绪预警系统（5 类检测规则）
- 全站深色主题 + JWT 认证

---

## 技术栈

### 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.9+ | 主语言 |
| FastAPI | 0.109+ | Web 框架 |
| SQLAlchemy | 2.0+ | ORM |
| PyMySQL | 1.1+ | MySQL 驱动 |
| Redis | 7.0+ | 缓存 & 消息队列 |
| Celery | 5.3+ | 异步任务 |
| Uvicorn | 0.27+ | ASGI 服务器 |
| Loguru | 0.7+ | 日志管理 |
| Pydantic | - | 数据验证 |
| APScheduler | - | 定时任务 |

### 前端

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue.js | 3.x | 前端框架 |
| Vite | 5.x | 构建工具 |
| Element Plus | 2.x | UI 组件库 |
| ECharts | 5.x | 数据可视化 |
| Pinia | 2.x | 状态管理 |
| Vue Router | 4.x | 路由管理 |
| Axios | - | HTTP 客户端 |

### AI / NLP

| 技术 | 用途 |
|------|------|
| PyTorch 2.x | 深度学习框架 |
| Transformers 4.x | BERT 模型 |
| hfl/chinese-bert-wwm-ext | 中文预训练模型 |
| jieba | 中文分词 |

### 运维

| 技术 | 用途 |
|------|------|
| Docker | 容器化（6 服务） |
| Nginx | 反向代理 |
| Prometheus | 监控指标 |
| Grafana | 可视化仪表板 |
| GitHub Actions | CI/CD |

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    前端 (Vue3 + Vite)                       │
│  Dashboard │ Stocks │ StockDetail │ Trend │ Validation     │
│  Sentiment │ Experiment │ Alerts │ Settings │ Login        │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP API
┌──────────────────────────┴──────────────────────────────────┐
│                      后端 (FastAPI)                          │
│  Crawler │ Sentiment │ Emotion │ Validator │ Experiment     │
│  Alerts │ Auth(JWT)                                           │
├─────────────────────────────────────────────────────────────┤
│  缓存(Redis) │ 任务队列(Celery) │ 监控(Prometheus)            │
├─────────────────────────────────────────────────────────────┤
│            MySQL │ Redis │ Prometheus │ Grafana            │
└─────────────────────────────────────────────────────────────┘
```

---

## 功能模块

### 1. 数据采集
- 东方财富股吧爬虫（增量采集 + 定时任务）
- 雪球、新浪财经爬虫（框架已实现）
- 随机延迟 + User-Agent 轮换防封禁

### 2. 情感分析
- BERT 深度学习模型（chinese-bert-wwm-ext 微调）
- 金融情感词典辅助（800+ 词条）
- 三分类：积极 / 中性 / 消极

### 3. 多模型对比实验
- **BERT-wwm**：中文预训练模型微调
- **FinBERT**：金融领域 BERT 模型
- **词典方法**：基于金融情感词典的规则分析
- 性能基准测试（Accuracy / F1 / Precision / Recall）
- 混淆矩阵可视化

### 4. 方面级情感分析
- 5 大分析维度：业绩、政策、技术面、资金面、行业
- 每个方面独立的正面/负面关键词库
- 雷达图展示各维度情感分布

### 5. 个股情绪画像
- 四维画像：波动性、偏向性、活跃度、一致性
- 趋势方向判断与行情关联度计算
- 雷达图可视化

### 6. 情绪预警系统
- 情绪强度突变检测（> 2σ 标准差）
- 看涨/看跌极端值预警（> 85 / < 15）
- 评论量暴增检测（> 3 倍均值）
- 温度异常预警
- 预警严重等级：高危 / 中等 / 低

### 7. 情绪量化
- 看涨指数 / 看跌指数
- 情绪强度、情绪温度、情绪波动率

### 8. 市场验证
- Pearson 相关性分析
- 方向准确率验证
- 格兰杰因果检验

### 9. 用户认证
- JWT Token 认证（24 小时有效期）
- 路由守卫保护（强制登录）
- bcrypt 密码加密

### 10. 系统特性
- 全站深色主题（CSS Variables）
- ECharts 深色主题统一配置
- Prometheus 指标采集
- Redis 缓存（内存 LRU 降级）
- API 速率限制（滑动窗口）

---

## 快速开始

### 方式一：Docker 一键部署（推荐）

```bash
git clone <repository-url>
cd stock_predicition
docker-compose up -d
```

访问地址：
- 前端：http://localhost
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs
- Grafana：http://localhost:3000（admin / admin123）
- Prometheus：http://localhost:19090

### 方式二：本地开发

#### 环境要求
- Python 3.9+ / Node.js 18+
- MySQL 8.0+ / Redis 7.0+（可选）
- CUDA GPU（可选，加速 BERT 推理）

#### 1. 克隆并进入项目

```bash
git clone <repository-url>
cd stock_predicition
```

#### 2. 初始化数据库

```bash
# 创建数据库
mysql -uroot -p -e "CREATE DATABASE stock_sentiment CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 初始化表结构（8 张表）
mysql -uroot -p stock_sentiment < scripts/init_db.sql
```

#### 3. 配置环境变量

```bash
cp backend/.env.example backend/.env
# 编辑 backend/.env 填入数据库密码等配置
```

#### 4. 启动后端

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# API 文档: http://localhost:8000/docs
```

#### 5. 启动前端

```bash
cd frontend
npm install
npm run dev
# 前端: http://localhost:3000（API 代理到 :8000）
```

#### 6. 生成演示数据

```bash
python scripts/generate_demo_data.py
```

#### 7. 启动 Celery（可选）

```bash
cd backend
celery -A app.celery_app worker --loglevel=info
celery -A app.celery_app beat --loglevel=info
```

---

## 项目结构

```
stock_predicition/
├── backend/
│   ├── app/
│   │   ├── api/              # API 路由（8 模块）
│   │   │   ├── stocks.py     # 股票 CRUD / 评论 / 行情
│   │   │   ├── sentiment.py  # 情感分析
│   │   │   ├── emotion.py    # 情绪概览 / 趋势 / 排名
│   │   │   ├── validation.py # 相关性 / 格兰杰检验
│   │   │   ├── crawler.py    # 爬虫管理
│   │   │   ├── experiment.py # 多模型对比实验
│   │   │   ├── alerts.py     # 预警列表 / 扫描 / 统计
│   │   │   └── auth.py       # JWT 登录 / 注册
│   │   ├── core/             # 核心基础设施
│   │   │   ├── config.py     # Pydantic 配置管理
│   │   │   ├── database.py   # SQLAlchemy 引擎
│   │   │   ├── auth.py       # JWT 令牌
│   │   │   ├── cache.py      # Redis + 内存 LRU 缓存
│   │   │   ├── logging.py    # Loguru 日志
│   │   │   ├── rate_limit.py # 滑动窗口限流
│   │   │   └── metrics.py    # Prometheus 指标
│   │   ├── models/           # 数据层
│   │   │   ├── models.py     # 8 张 SQLAlchemy ORM 表
│   │   │   └── schemas.py    # Pydantic 请求/响应模型
│   │   ├── services/         # 业务逻辑（7 个子模块）
│   │   │   ├── crawler/      # 多平台爬虫
│   │   │   ├── sentiment/    # BERT 情感分析
│   │   │   ├── quantify/     # 情绪量化计算
│   │   │   ├── market/       # 市场数据验证
│   │   │   ├── processor/    # 文本预处理
│   │   │   ├── alert/        # 预警引擎
│   │   │   └── scheduler/    # 定时任务调度
│   │   └── main.py           # FastAPI 入口
│   ├── data/
│   │   ├── lexicon/          # 情感词典（800+ 词条）
│   │   └── models/           # BERT 模型文件
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── api/              # Axios 封装
│   │   │   ├── request.js    # 实例 + 拦截器
│   │   │   └── index.js      # API 函数
│   │   ├── views/            # 11 个页面组件
│   │   │   ├── Dashboard.vue    # 情绪仪表盘
│   │   │   ├── Stocks.vue       # 股票列表
│   │   │   ├── StockDetail.vue  # 个股详情
│   │   │   ├── Trend.vue        # 情绪趋势
│   │   │   ├── Validation.vue   # 市场验证
│   │   │   ├── Sentiment.vue    # 情感分析测试
│   │   │   ├── Experiment.vue   # 多模型对比
│   │   │   ├── Alerts.vue       # 预警管理
│   │   │   ├── Settings.vue     # 系统设置
│   │   │   └── Login.vue        # 登录页
│   │   ├── stores/           # Pinia 状态管理
│   │   ├── router/           # Vue Router + 路由守卫
│   │   ├── styles/           # 全局样式
│   │   │   └── dark-theme.css  # 深色主题变量
│   │   ├── utils/            # 工具函数
│   │   │   └── chart-theme.js   # ECharts 深色主题
│   │   └── main.js
│   └── package.json
│
├── scripts/
│   ├── init_db.sql           # 数据库初始化（8 张表）
│   ├── generate_demo_data.py # 演示数据生成
│   ├── crawl_comments.py    # 评论爬取
│   ├── sync_quotes.py       # 行情同步
│   ├── train_sentiment.py   # 模型训练
│   └── fix_collation.sql    # 字符集修复
│
├── deploy/
│   ├── prometheus/           # Prometheus 配置
│   └── grafana/             # Grafana 配置
│
├── docker-compose.yml         # 6 服务编排
└── README.md
```

---

## API 接口

### 认证
| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/v1/auth/login` | POST | 用户登录 |
| `/api/v1/auth/register` | POST | 用户注册 |
| `/api/v1/auth/me` | GET | 当前用户信息 |

### 股票
| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/v1/stocks` | GET | 股票列表 |
| `/api/v1/stocks/{code}` | GET | 股票详情 |
| `/api/v1/stocks/{code}/comments` | GET | 评论列表 |
| `/api/v1/stocks/{code}/quotes` | GET | 行情数据 |
| `/api/v1/stocks/{code}/aspects` | GET | 方面级情感 |
| `/api/v1/stocks/{code}/profile` | GET | 情绪画像 |

### 情绪
| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/v1/emotion/overview` | GET | 情绪概览 |
| `/api/v1/emotion/trend` | GET | 情绪趋势 |
| `/api/v1/emotion/ranking` | GET | 情绪排名 |

### 情感分析
| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/v1/sentiment/analyze` | POST | 单条文本分析 |
| `/api/v1/sentiment/batch` | POST | 批量分析 |

### 市场验证
| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/v1/validation/correlation` | GET | 相关性分析 |
| `/api/v1/validation/granger` | GET | 格兰杰因果检验 |
| `/api/v1/validation/accuracy` | GET | 方向准确率 |

### 实验对比
| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/v1/experiment/compare` | POST | 多模型对比 |
| `/api/v1/experiment/benchmark` | POST | 基准测试 |
| `/api/v1/experiment/results` | GET | 历史结果 |
| `/api/v1/experiment/models` | GET | 可用模型 |

### 预警
| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/v1/alerts` | GET | 预警列表 |
| `/api/v1/alerts/scan` | POST | 触发扫描 |
| `/api/v1/alerts/stats` | GET | 预警统计 |
| `/api/v1/alerts/{id}/read` | PUT | 标记已读 |
| `/api/v1/alerts/read-all` | PUT | 全部已读 |

### 爬虫
| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/v1/crawler/start` | POST | 启动爬虫 |
| `/api/v1/crawler/stop` | POST | 停止爬虫 |
| `/api/v1/crawler/status` | GET | 爬虫状态 |
| `/api/v1/crawler/stats` | GET | 采集统计 |

完整 API 文档：http://localhost:8000/docs

---

## 数据库表结构（8 张表）

| 表名 | 说明 |
|------|------|
| `stocks` | 股票信息 |
| `comments` | 评论数据 |
| `sentiments` | 情感分析结果 |
| `emotions` | 情绪指标 |
| `quotes` | 股票行情 |
| `experiment_results` | 实验对比结果 |
| `aspect_sentiments` | 方面级情感 |
| `alerts` | 预警记录 |

---

## 单元测试

```bash
cd backend
pytest tests/ -v --cov=app
# 49 passed
```

---

## 监控指标

| 指标 | 说明 |
|------|------|
| `http_requests_total` | HTTP 请求总数 |
| `http_request_duration_seconds` | 请求耗时 |
| `sentiment_analysis_total` | 情感分析次数 |
| `crawler_comments_collected_total` | 爬虫采集数 |
| `cache_hits_total` | 缓存命中 |

Prometheus：http://localhost:19090
Grafana：http://localhost:3000（admin / admin123）

---

## 许可证

MIT License
