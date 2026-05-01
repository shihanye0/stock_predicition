# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Transformer-based Stock Sentiment Prediction System (v2.0)** - A full-stack application for analyzing investor sentiment in Chinese A-stock markets using BERT deep learning models and multi-platform data collection.

- **Backend**: FastAPI (Python 3.9+) with PyTorch/Transformers for NLP
- **Frontend**: Vue 3 + Vite + Element Plus + ECharts
- **Database**: MySQL 8.0 + Redis 7.0
- **Task Queue**: Celery with Redis broker
- **Monitoring**: Prometheus + Grafana
- **Deployment**: Docker Compose (6 services)

## Quick Start

### One-Click Startup (Recommended)

Simply double-click `start.bat` in the project root directory. This will:
1. Kill any existing processes on ports 8000 and 3000
2. Start the backend on http://localhost:8000
3. Start the frontend on http://localhost:3000

**Note**: Requires conda environment `finance` with Python 3.10+.

### Manual Startup

If you need to start services manually:

**Backend** (in cmd):
```cmd
cd /d E:\stock_predicition\backend
C:\Users\Lenovo\anaconda3\envs\finance\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Frontend** (in another cmd):
```cmd
cd /d E:\stock_predicition\frontend
npm run dev
```

## Admin API

The system includes an admin API for data initialization:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/admin/data-status` | GET | Get current data statistics |
| `/api/v1/admin/init-demo` | POST | Generate demo data |

Example:
```bash
# Get data status
curl http://localhost:8000/api/v1/admin/data-status

# Generate demo data
curl -X POST http://localhost:8000/api/v1/admin/init-demo
```

## Development Commands

### Backend (Python/FastAPI)

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run development server (with hot reload)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest tests/ -v --cov=app

# Run specific test file
pytest tests/test_sentiment.py -v

# Run Celery worker (for async tasks)
celery -A app.celery_app worker --loglevel=info

# Run Celery beat (for scheduled tasks)
celery -A app.celery_app beat --loglevel=info
```

### Frontend (Vue 3/Vite)

```bash
cd frontend

# Install dependencies
npm install

# Run development server (port 3000 with API proxy to :8000)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Docker Deployment

```bash
# Start all services (backend, frontend, mysql, redis, prometheus, grafana)
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop all services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

### Database Management

```bash
# Initialize database schema (8 tables)
mysql -uroot -p stock_sentiment < scripts/init_db.sql

# Generate demo data
python scripts/generate_demo_data.py

# Sync market quotes from AKShare
python scripts/sync_quotes.py
```

### Utility Scripts

```bash
# Crawl comments (test mode for single stock)
python scripts/crawl_comments.py --mode test --stock 000001

# Crawl all stocks (last 7 days)
python scripts/crawl_comments.py --mode all --days 7

# Train sentiment model
python scripts/train_sentiment.py
```

## Architecture Overview

### Backend Structure

```
backend/app/
├── api/                    # API route handlers (8 modules, 43 endpoints)
│   ├── stocks.py          # Stock list/detail/comments/quotes/aspects/profile
│   ├── sentiment.py       # Single/batch sentiment analysis
│   ├── emotion.py         # Market emotion overview/trends/ranking
│   ├── validation.py      # Correlation/accuracy/Granger causality
│   ├── crawler.py         # Crawler start/stop/status/stats
│   ├── experiment.py      # Multi-model comparison/benchmarking
│   ├── alerts.py          # Alert list/scan/stats/mark-read
│   └── auth.py            # JWT login/register/user management
│
├── core/                   # Core infrastructure
│   ├── config.py          # Settings (env-based, pydantic)
│   ├── database.py        # SQLAlchemy sync/async engines
│   ├── auth.py            # JWT token generation/validation
│   ├── cache.py           # Redis + fallback memory cache (LRU)
│   ├── logging.py         # Loguru setup (JSON + rotation)
│   ├── rate_limit.py      # Sliding window rate limiter
│   └── metrics.py         # Prometheus metrics collection
│
├── models/                 # Data layer
│   ├── models.py          # 8 SQLAlchemy ORM models
│   └── schemas.py         # Pydantic request/response models
│
├── services/               # Business logic (23 .py files)
│   ├── crawler/           # Multi-platform web scraping
│   │   ├── base.py        # BaseCrawler abstract class
│   │   ├── eastmoney.py   # East Money Guba crawler
│   │   ├── xueqiu.py      # Xueqiu crawler (framework)
│   │   ├── sina.py        # Sina Finance crawler (framework)
│   │   └── manager.py     # CrawlerManager orchestration
│   │
│   ├── sentiment/         # NLP sentiment analysis
│   │   ├── analyzer.py    # BERT-based SentimentAnalyzer
│   │   ├── lexicon.py     # FinanceLexicon (800+ words)
│   │   ├── multi_model.py # Multi-model comparison (BERT/FinBERT/Lexicon)
│   │   └── aspect_analyzer.py # Aspect-level sentiment (5 dimensions)
│   │
│   ├── quantify/          # Emotion quantification
│   │   ├── calculator.py  # EmotionCalculator (5 metrics)
│   │   └── profiler.py    # EmotionProfile (4D radar chart)
│   │
│   ├── market/            # Market validation
│   │   ├── validator.py   # Pearson/Spearman correlation
│   │   └── data_service.py # AKShare market data integration
│   │
│   ├── processor/         # Text preprocessing
│   │   └── text_processor.py # Jieba tokenization + cleaning
│   │
│   ├── alert/             # Alert engine
│   │   └── engine.py      # 5 alert detection rules
│   │
│   └── scheduler/         # Task scheduling
│       └── task_scheduler.py # APScheduler wrapper
│
├── tasks/                  # Celery async tasks
│   ├── crawler_tasks.py   # crawl_stock_comments, crawl_hot_stocks
│   ├── sentiment_tasks.py # analyze_comments, update_emotion_index
│   └── report_tasks.py    # generate_daily_report
│
├── celery_app.py          # Celery config + beat schedule
└── main.py                # FastAPI app entry point
```

### Frontend Structure

```
frontend/src/
├── views/                 # 11 page components
│   ├── Dashboard.vue     # Emotion dashboard + alert banner
│   ├── Stocks.vue        # Stock list with filters
│   ├── StockDetail.vue   # Stock detail + aspects + profile
│   ├── Trend.vue         # Emotion trend analysis
│   ├── Validation.vue    # Market validation report
│   ├── Sentiment.vue     # Sentiment analysis tester
│   ├── Experiment.vue    # Multi-model comparison UI
│   ├── Alerts.vue        # Alert management
│   ├── Settings.vue      # System settings
│   └── Login.vue         # Auth page
│
├── api/
│   ├── request.js        # Axios instance + interceptors
│   └── index.js          # API wrapper functions
│
├── router/
│   └── index.js          # Vue Router config + guards
│
├── stores/
│   └── user.js           # Pinia user store
│
└── main.js               # Vue app entry point
```

### Database Schema (8 Tables)

1. **stocks** - Stock master data (code, name, industry, market)
2. **comments** - User comments from platforms (content, author, publish_time)
3. **sentiments** - Sentiment analysis results (label, confidence, scores)
4. **emotions** - Emotion metrics (bull_index, bear_index, intensity, temperature, volatility)
5. **quotes** - Market quotes (open/close/high/low, volume, change_pct)
6. **experiment_results** - Model comparison results (accuracy, f1_score, confusion_matrix)
7. **aspect_sentiments** - Aspect-level sentiment (5 dimensions: performance/policy/technical/capital/industry)
8. **alerts** - Alert records (alert_type, severity, triggered_at, is_read)

## Key Design Patterns

### Sentiment Analysis Pipeline

```
Text Input → TextProcessor (clean/tokenize)
  → SentimentAnalyzer (BERT inference)
  → AspectAnalyzer (keyword matching)
  → MultiModelManager (consensus voting)
  → Database storage
```

**Key Classes:**
- `SentimentAnalyzer` (backend/app/services/sentiment/analyzer.py) - BERT-based sentiment analysis
- `TextProcessor` (backend/app/services/processor/text_processor.py) - Jieba tokenization + cleaning
- `AspectAnalyzer` (backend/app/services/sentiment/aspect_analyzer.py) - 5-dimension aspect analysis

### Emotion Quantification

```
Comments → EmotionCalculator
  → Bull Index (positive %)
  → Bear Index (negative %)
  → Intensity (net sentiment)
  → Temperature (activity level)
  → Volatility (std deviation)
```

**Key Classes:**
- `EmotionCalculator` (backend/app/services/quantify/calculator.py) - 5 emotion metrics
- `EmotionProfile` (backend/app/services/quantify/profiler.py) - 4D radar chart (volatility/bias/activity/consistency)

### Caching Strategy

- **Redis primary** (TTL-based, connection pooling)
- **Memory LRU fallback** (1000 items max when Redis unavailable)
- **Cache keys**: `stock:{code}:emotion`, `sentiment:stats`, `crawler:status`
- **Implementation**: `backend/app/core/cache.py`

### Rate Limiting

- **Sliding window algorithm** (Redis-backed)
- **Route-specific limits**: auth (10/min), sentiment (30/min), stocks (60/min)
- **IP + token-based identification**
- **Implementation**: `backend/app/core/rate_limit.py`

### Alert Detection Rules

1. **Intensity spike** - Emotion intensity change > 2σ
2. **Extreme values** - Bull index > 85 or Bear index < 15
3. **Volume surge** - Comment count > 3x average
4. **Temperature anomaly** - Temperature change > 2σ
5. **Custom thresholds** - User-defined rules

**Implementation**: `backend/app/services/alert/engine.py`

## Configuration

### Environment Variables (backend/.env)

```env
# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=yourpassword
DB_NAME=stock_sentiment

# Redis (optional, falls back to memory cache)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Model
MODEL_NAME=hfl/chinese-bert-wwm-ext
MODEL_MAX_LENGTH=128
MODEL_CACHE_DIR=./data/models

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
```

### API Proxy (frontend/vite.config.js)

Frontend dev server (port 3000) proxies `/api` requests to backend (port 8000).

## Testing

### Backend Tests (49 tests)

```bash
cd backend

# Run all tests with coverage
pytest tests/ -v --cov=app

# Run specific test module
pytest tests/test_sentiment.py -v
pytest tests/test_auth.py -v
pytest tests/test_cache.py -v
pytest tests/test_rate_limit.py -v
```

**Test Coverage:**
- Sentiment analysis (BERT model, lexicon, multi-model)
- JWT authentication (login, register, token validation)
- Cache system (Redis + memory fallback)
- Rate limiting (sliding window)

## Important Notes

### BERT Model Loading

- Model files are in `backend/data/models/sentiment_model/`
- First run downloads model from Hugging Face (requires internet)
- Model is cached locally for subsequent runs
- GPU acceleration available if CUDA is installed

### Crawler Anti-Ban Strategy

- Random delay 3-8 seconds between requests
- User-Agent rotation
- Proxy pool support (configure in settings)
- Max retry 3 times with exponential backoff
- Respect robots.txt

### Celery Scheduled Tasks

Defined in `backend/app/celery_app.py`:
- **crawl-hot-stocks** - Daily at 8:00 AM
- **update-emotion-index** - Every hour
- **generate-daily-report** - Daily at 8:00 PM

### API Rate Limits

- `/api/auth/*` - 10 requests/minute
- `/api/v1/sentiment/*` - 30 requests/minute
- `/api/v1/stocks/*` - 60 requests/minute
- `/api/v1/crawler/*` - 5 requests/minute

### Monitoring Endpoints

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Prometheus Metrics**: http://localhost:8000/metrics
- **Grafana Dashboard**: http://localhost:3000 (admin/admin123)
- **Health Check**: http://localhost:8000/health

## Common Development Tasks

### Adding a New API Endpoint

1. Define route handler in `backend/app/api/{module}.py`
2. Add Pydantic schemas in `backend/app/models/schemas.py`
3. Implement business logic in `backend/app/services/{module}/`
4. Add tests in `backend/tests/test_{module}.py`
5. Update API wrapper in `frontend/src/api/index.js`

### Adding a New Database Table

1. Define ORM model in `backend/app/models/models.py`
2. Update `scripts/init_db.sql` with CREATE TABLE statement
3. Add Pydantic schemas in `backend/app/models/schemas.py`
4. Run migration: `mysql -uroot -p stock_sentiment < scripts/init_db.sql`

### Adding a New Sentiment Model

1. Implement model class in `backend/app/services/sentiment/`
2. Register in `MultiModelManager` (multi_model.py)
3. Add model config to settings
4. Update experiment comparison API

### Debugging Tips

- **Backend logs**: `backend/logs/app_{date}.log` (JSON format)
- **Frontend console**: Check browser DevTools Network tab
- **Database queries**: Enable SQLAlchemy echo in `database.py`
- **Redis cache**: Use `redis-cli` to inspect keys
- **Celery tasks**: Check worker logs with `celery -A app.celery_app worker --loglevel=debug`

## Performance Considerations

- **BERT inference** is CPU/GPU intensive - consider batch processing for large datasets
- **Redis caching** reduces database load - use for frequently accessed data
- **Celery async tasks** for long-running operations (crawling, batch analysis)
- **Database indexing** on stock_code, publish_time, stat_date for query performance
- **API pagination** for large result sets (default limit: 100)

## Security Notes

- JWT tokens expire after 24 hours (configurable)
- Passwords hashed with bcrypt
- CORS enabled for all origins (restrict in production)
- SQL injection prevented by SQLAlchemy ORM
- Rate limiting prevents API abuse
- Input validation with Pydantic schemas

## Git & GitHub 操作经验

### Git 路径配置（Windows 环境）

当前环境 Git 安装路径：`E:/Git/bin/git.exe`

使用方式：
```bash
cd E:/stock_predicition && E:/Git/bin/git.exe <command>
```

### 远程仓库 URL 协议问题

**问题**：`git://github.com/xxx` 是只读协议，无法推送。

**解决**：必须改为 `https://github.com/xxx`
```bash
E:/Git/bin/git.exe remote set-url origin https://github.com/shihanye0/stock_predicition.git
```

### GitHub 大文件限制

**限制**：GitHub 单文件限制 100MB，超出会被拒绝。

**常见大文件**：
- `.safetensors` / `.pt` / `.bin` 模型文件
- `.png` / `.jpg` 图片（超过 50MB）
- 压缩包 / 二进制文件

### 处理大文件的正确流程

1. **提交前检查**：估算文件大小，避免已提交后发现问题
2. **添加到 .gitignore**：大文件目录和扩展名应预先排除
   ```gitignore
   # 模型大文件
   bert和bilstm/**/*.safetensors
   bert和bilstm/**/*.pt
   bert和bilstm/best_model/
   backend/data/models/**/*.bin
   backend/data/models/**/*.pt
   backend/data/models/**/*.safetensors
   ```
3. **移除已提交的大文件**：
   ```bash
   E:/Git/bin/git.exe rm -r --cached <大文件目录>
   E:/Git/bin/git.exe commit --amend --no-edit
   ```
4. **推送**：
   ```bash
   E:/Git/bin/git.exe push -u origin main
   ```

### GitHub Personal Access Token 配置

**方法 1：嵌入 URL（临时方案）**
```bash
E:/Git/bin/git.exe remote set-url origin https://username:TOKEN@github.com/username/repo.git
```

**方法 2：凭证存储（推荐）**
```bash
# 1. 创建凭证文件
echo "https://username:TOKEN@github.com" > ~/.git-credentials

# 2. 启用凭证助手
E:/Git/bin/git.exe config --global credential.helper store
```

### 完整提交流程（避免踩坑）

```bash
# 1. 检查远程 URL 是否为 https
E:/Git/bin/git.exe remote -v

# 2. 检查将要提交的文件大小（避免超过 100MB）
# 特别关注 .safetensors, .pt, .bin 等模型文件

# 3. 确保 .gitignore 正确配置，排除大文件

# 4. 暂存文件
E:/Git/bin/git.exe add -A

# 5. 创建提交
E:/Git/bin/git.exe commit -m "提交消息"

# 6. 推送到 GitHub（确保 Token 已配置）
E:/Git/bin/git.exe push -u origin main
```

### 快速验证清单

- [ ] 远程 URL 是 `https://` 而非 `git://`
- [ ] 大模型文件（>100MB）已排除
- [ ] .gitignore 已更新
- [ ] 凭证（Token）已配置
- [ ] 本地已与远程同步（无落后提交）

1.称呼规则: 每次回复用中文回答我的问题，每次回复前必须使用"Boss"作为称呼。2. 决策确认: 遇到不确定的代码设计问题时，必须先询问 Boss，不得直接行动。3. 代码兼容性: 不能写兼容性代码，除非 Boss 主动要求。 4.每完成一个板块的内容后，可写一个markdown文件，命名格式为今天日期-名称；保存在根目录下。介绍当前的进度和当前模块的功能与实现方法，可以更方便的了解系统状态。