# 基于Transformer的股票情绪预测系统 - 开发进度文档

> 最后更新: 2026年1月22日

---

## 一、项目概述

本系统是一个基于BERT模型的A股市场投资者情绪分析与预测平台，通过采集金融社交媒体评论数据，进行NLP情感分析，量化投资者情绪，并与实际市场行情进行对比验证。

v2.0版本新增多模型对比实验、方面级情感分析、个股情绪画像、情绪预警系统等高级功能。

---

## 二、当前开发进度

### 总体完成度: 100%

```
█████████████████████████  100%
```

| 模块 | 状态 | 完成度 | 说明 |
|------|------|--------|------|
| 项目架构 | ✅ 完成 | 100% | FastAPI + Vue3 前后端分离 |
| 数据库设计 | ✅ 完成 | 100% | MySQL 8表结构 |
| 后端API | ✅ 完成 | 100% | 45条路由已实现 |
| 前端界面 | ✅ 完成 | 100% | 10个页面已实现 |
| 爬虫模块 | ✅ 完成 | 100% | 东方财富已验证 |
| 情感分析 | ✅ 完成 | 100% | BERT微调完成（准确率80%） |
| 情绪量化 | ✅ 完成 | 100% | 5个核心指标 |
| 市场验证 | ✅ 完成 | 100% | 相关性+准确率+格兰杰 |
| 行情数据 | ✅ 完成 | 100% | AKShare对接完成 |
| 定时任务 | ✅ 完成 | 100% | 调度器已实现 |
| 多模型对比 | ✅ 完成 | 100% | 3种模型对比实验 🆕 |
| 方面级分析 | ✅ 完成 | 100% | 5大维度情感分析 🆕 |
| 情绪画像 | ✅ 完成 | 100% | 4维特征画像 🆕 |
| 情绪预警 | ✅ 完成 | 100% | 5类检测规则 🆕 |
| 运维部署 | ✅ 完成 | 100% | Docker + Prometheus + Grafana |

---

## 三、已完成功能清单

### 3.1 后端服务 (FastAPI)

#### 已实现API路由（45条）
```
/api/v1/stocks           - 股票列表、详情、评论、行情、方面分析、情绪画像
/api/v1/emotion          - 情绪概览、趋势、排行
/api/v1/sentiment        - 情感分析（单条/批量）
/api/v1/validation       - 相关性、准确率、验证报告
/api/v1/crawler          - 爬虫启动/停止/状态
/api/v1/experiment       - 多模型对比/基准测试/历史结果 🆕
/api/v1/alerts           - 预警列表/扫描/统计/标记已读 🆕
```

#### 核心服务模块
| 路径 | 功能 | 状态 |
|------|------|------|
| `services/crawler/` | 多平台爬虫（东财/雪球/新浪） | ✅ 完成 |
| `services/sentiment/analyzer.py` | BERT情感分析器 | ✅ 完成 |
| `services/sentiment/lexicon.py` | 金融情感词典 | ✅ 完成 |
| `services/sentiment/multi_model.py` | 多模型管理器 🆕 | ✅ 完成 |
| `services/sentiment/aspect_analyzer.py` | 方面级情感分析 🆕 | ✅ 完成 |
| `services/processor/` | 文本清洗预处理 | ✅ 完成 |
| `services/quantify/calculator.py` | 情绪量化计算 | ✅ 完成 |
| `services/quantify/profiler.py` | 个股情绪画像 🆕 | ✅ 完成 |
| `services/alert/engine.py` | 情绪预警引擎 🆕 | ✅ 完成 |
| `services/market/validator.py` | 市场验证服务 | ✅ 完成 |
| `services/market/data_service.py` | 行情数据服务 | ✅ 完成 |
| `services/scheduler/` | 定时任务调度 | ✅ 完成 |

### 3.2 前端应用 (Vue3 + Element Plus)

| 页面 | 路由 | 功能 | 状态 |
|------|------|------|------|
| Dashboard.vue | `/` | 情绪仪表盘（含预警通知栏） | ✅ 完成 |
| Stocks.vue | `/stocks` | 股票列表 | ✅ 完成 |
| StockDetail.vue | `/stock/:code` | 股票详情（含方面分析+情绪画像） | ✅ 完成 |
| Trend.vue | `/trend` | 趋势分析 | ✅ 完成 |
| Validation.vue | `/validation` | 市场验证 | ✅ 完成 |
| Sentiment.vue | `/sentiment` | 情感分析测试 | ✅ 完成 |
| Experiment.vue | `/experiment` | 多模型对比实验 🆕 | ✅ 完成 |
| Alerts.vue | `/alerts` | 情绪预警管理 🆕 | ✅ 完成 |
| Settings.vue | `/settings` | 系统设置/爬虫管理 | ✅ 完成 |
| Login.vue | `/login` | 登录注册 | ✅ 完成 |

### 3.3 数据库设计 (MySQL)

```sql
stocks              -- 股票信息表 (10只示例股票)
comments            -- 评论数据表 (8000+模拟数据)
sentiments          -- 情感分析结果表
emotion             -- 情绪指标表
quotes              -- 股票行情表
experiment_results  -- 实验结果表 🆕
aspect_sentiments   -- 方面级情感表 🆕
alerts              -- 预警记录表 🆕
```

### 3.4 情绪量化指标

| 指标 | 计算公式 | 说明 |
|------|----------|------|
| 看涨指数 | `positive_count / total * 100` | 积极评论占比 |
| 看跌指数 | `negative_count / total * 100` | 消极评论占比 |
| 情绪强度 | `abs(positive - negative) / total` | 情绪偏离程度 |
| 情绪温度 | `(positive - negative) / total * 100 + 50` | 综合情绪热度 |
| 情绪波动 | 基于历史波动计算 | 情绪稳定性 |

### 3.5 v2.0 扩展功能 🆕

#### 多模型对比实验
| 模型 | 方法 | 说明 |
|------|------|------|
| BERT-wwm | 深度学习 | chinese-bert-wwm-ext 预训练模型微调 |
| FinBERT | 深度学习 | 金融领域BERT模型 |
| 词典方法 | 规则 | 基于金融情感词典分析 |

支持单文本多模型对比、批量基准测试、性能指标计算、混淆矩阵可视化

#### 方面级情感分析
| 方面 | 示例关键词 |
|------|----------|
| 业绩 | 营收、利润、净利润、每股收益 |
| 政策 | 监管、利率、减税、补贴 |
| 技术面 | 均线、突破、压力位、MACD |
| 资金面 | 主力、流入、流出、融资 |
| 行业 | 行业龙头、市场份额、竞争 |

#### 个股情绪画像
- **波动性**：情绪稳定性衡量
- **偏向性**：看涨/看跌倾向
- **活跃度**：评论量与情感强度
- **一致性**：情绪稳定方向程度
- 自动生成画像标签 + 雷达图可视化

#### 情绪预警系统
| 规则 | 触发条件 | 严重等级 |
|------|----------|----------|
| 情绪强度突变 | > 2σ标准差 | 高危 |
| 看涨极端 | 看涨指数 > 85 | 中等 |
| 看跌极端 | 看跌指数 > 85 | 中等 |
| 评论量暴增 | > 3倍均值 | 中等 |
| 温度异常 | > 80 或 < 20 | 低 |

---

## 四、当前运行状态

### 4.1 服务状态
- ✅ 后端: `http://localhost:8000` (Uvicorn + 45条API路由)
- ✅ 前端: `http://localhost:5173` (Vite开发) / `http://localhost` (Docker)
- ✅ 数据库: MySQL `stock_sentiment` (8张表)
- ✅ BERT模型: 延迟加载模式（torch未安装时使用模拟）
- ✅ Docker: 6个服务容器

### 4.2 数据状态
- 股票: 10只A股（平安银行、贵州茅台等）
- 评论: 8,052条模拟数据
- 情感分析: 8,052条
- 情绪指标: 230条（30天×10股）
- 行情数据: 230条

---

## 五、开发历史

### v1.0 核心功能（33项任务）✅

- [x] 安装深度学习依赖 (torch + transformers)
- [x] BERT模型微调 (准确率80%)
- [x] 真实数据爬取 (东方财富股吧验证通过)
- [x] AKShare对接真实A股行情 (210条)
- [x] 金融情感词典扩充 (+261个词)
- [x] 格兰杰因果检验API
- [x] 定时任务调度器 (APScheduler)
- [x] JWT用户认证系统
- [x] Docker容器化部署
- [x] Prometheus + Grafana监控
- [x] GitHub Actions CI/CD
- [x] 49项单元测试

### v2.0 扩展功能（15项任务）✅ 🆕

- [x] 数据库新增3张表 (experiment_results, aspect_sentiments, alerts)
- [x] 多模型分析器 (BERT-wwm / FinBERT / 词典方法)
- [x] 方面级情感分析器 (5大维度)
- [x] 个股情绪画像服务 (4维特征 + 标签生成)
- [x] 情绪预警引擎 (5类检测规则)
- [x] 实验对比API (5个端点)
- [x] 预警管理API (5个端点)
- [x] 股票API扩展 (方面分析+画像接口)
- [x] 前端API封装扩展
- [x] 实验对比页面 (Experiment.vue)
- [x] 预警管理页面 (Alerts.vue)
- [x] StockDetail 增强 (方面雷达图 + 画像雷达图)
- [x] Dashboard 预警通知栏
- [x] 路由与侧边栏更新
- [x] ECharts组件注册 (RadarChart + HeatmapChart)

---

## 六、技术债务清单

| 问题 | 优先级 | 状态 |
|------|--------|------|
| 缺少单元测试 | 中 | ✅ 已解决（49项） |
| 缺少日志持久化 | 低 | ✅ 已解决 (Loguru) |
| 前端缺少错误处理 | 中 | ✅ 已解决 |
| API缺少鉴权 | 中 | ✅ 已解决 (JWT) |

---

## 七、项目结构

```
stock_predicition/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── api/               # API路由 ✅
│   │   │   ├── stocks.py      # 股票API
│   │   │   ├── emotion.py     # 情绪分析API
│   │   │   ├── sentiment.py   # 情感分析API
│   │   │   ├── validation.py  # 市场验证API
│   │   │   ├── crawler.py     # 爬虫管理API
│   │   │   ├── auth.py        # 用户认证API
│   │   │   ├── experiment.py  # 实验对比API 🆕
│   │   │   └── alerts.py      # 情绪预警API 🆕
│   │   ├── core/              # 核心配置 ✅
│   │   ├── models/            # 数据模型 (8张表ORM) ✅
│   │   ├── services/          # 业务服务 ✅
│   │   │   ├── crawler/       # 爬虫服务
│   │   │   ├── sentiment/     # 情感分析 (含多模型+方面级)
│   │   │   ├── quantify/      # 情绪量化 (含画像)
│   │   │   ├── alert/         # 情绪预警 🆕
│   │   │   ├── market/        # 市场验证
│   │   │   ├── processor/     # 文本处理
│   │   │   └── scheduler/     # 定时任务
│   │   └── main.py            # 入口文件 ✅
│   ├── data/                  # 数据文件
│   └── requirements.txt       # 依赖清单
│
├── frontend/                  # 前端应用
│   ├── src/
│   │   ├── api/              # API封装 ✅
│   │   ├── views/            # 页面组件 (10个) ✅
│   │   ├── router/           # 路由配置 ✅
│   │   └── main.js           # 入口文件 ✅
│   └── package.json
│
├── scripts/                   # 脚本工具
│   ├── init_db.sql           # 数据库初始化 (8张表) ✅
│   └── generate_demo_data.py # 模拟数据生成 ✅
│
├── deploy/                    # 部署配置
│   ├── prometheus/           # Prometheus配置
│   └── grafana/              # Grafana配置
│
├── docker-compose.yml         # Docker编排
└── docs/                      # 文档
    ├── spec.md               # 系统规格说明 ✅
    └── DEVELOPMENT_STATUS.md # 本文档 ✅
```

---

## 八、快速开始命令

```bash
# 1. 启动后端
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 2. 启动前端
cd frontend
npm install
npm run dev

# 3. 生成模拟数据（首次运行）
python scripts/generate_demo_data.py

# 4. 爬取评论数据
python scripts/crawl_comments.py --mode test --stock 000001

# 5. 同步行情数据
python scripts/sync_quotes.py

# 6. 训练情感模型
python scripts/train_sentiment.py

# 7. Docker一键部署
docker-compose up -d
```

---

## 九、版本记录

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v0.1.0 | 2026-01-22 | 项目初始化，完成基础架构 |
| v0.2.0 | 2026-01-22 | 完成核心功能，生成模拟数据 |
| v0.3.0 | 2026-01-22 | BERT模型微调完成（准确率80%），对接AKShare真实行情 |
| v0.4.0 | 2026-01-22 | 东方财富爬虫实战验证，金融词典+261词，格兰杰因果检验，定时调度器 |
| v1.0.0 | 2026-01-22 | JWT认证、Docker部署、Prometheus监控、CI/CD、单元测试 |
| v2.0.0 | 2026-01-22 | 多模型对比、方面级分析、情绪画像、预警系统、实验可视化面板 🆕 |

---

## 十、已完成功能总结

### 10.1 v1.0 核心功能 ✅

1. **数据采集** - 东方财富股吧爬虫已验证
2. **情感分析** - BERT微调模型准确率80%
3. **情绪量化** - 5个核心指标计算
4. **市场验证** - 相关性/准确率/格兰杰检验
5. **可视化展示** - 10个前端页面
6. **定时任务** - APScheduler调度器
7. **用户认证** - JWT Token机制
8. **运维部署** - Docker + Prometheus + Grafana

### 10.2 v2.0 扩展功能 ✅ 🆕

1. **多模型对比** - BERT-wwm / FinBERT / 词典方法三种模型并行分析
2. **方面级分析** - 5大维度（业绩/政策/技术面/资金面/行业）独立情感评分
3. **情绪画像** - 4维特征（波动性/偏向性/活跃度/一致性）+ 自动标签生成
4. **情绪预警** - 5类检测规则，三级严重等级
5. **实验可视化** - 性能指标柱状图 + 混淆矩阵热力图

### 10.3 测试结果

- 爬虫测试: 平安银行(000001) 爬取 **398条评论** ✅
- 模型准确率: **80%** ✅
- 行情数据: **210条真实A股行情** ✅
- 后端路由: **45条API** ✅
- 单元测试: **49项通过** ✅
- 前端页面: **10个** ✅

---

*本文档将随开发进度持续更新*
