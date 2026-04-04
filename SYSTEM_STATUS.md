# 股票情绪预测系统 - 当前状态报告

**生成时间**: 2026-02-24
**系统版本**: v2.0
**状态**: ✅ 运行正常

---

## 系统概览

基于Transformer的股票情绪预测系统是一个全栈应用，用于分析中国A股市场投资者情绪。系统通过爬取金融社交媒体评论，使用BERT深度学习模型进行情感分析，量化市场情绪指标，并提供可视化分析平台。

---

## 核心功能模块

### 1. 数据采集模块 ✅

**实现状态**: 已完成
**技术栈**: Scrapy + Playwright + BeautifulSoup4

**支持平台**:
- ✅ 东方财富股吧（已验证，398+条真实数据）
- ⚠️ 雪球（框架已实现，需配置登录）
- ⚠️ 新浪财经（框架已实现，需配置登录）

**功能特性**:
- 增量采集（基于时间戳）
- 频率控制（随机延迟3-8秒）
- 代理轮换支持
- 异常重试机制（最大3次）

**API端点**:
- `POST /api/v1/crawler/start` - 启动爬虫
- `POST /api/v1/crawler/stop` - 停止爬虫
- `GET /api/v1/crawler/status` - 爬虫状态
- `GET /api/v1/crawler/stats` - 采集统计

**数据量**:
- 评论数据: 7,774条
- 覆盖股票: 10只
- 数据时间范围: 2025-12-24 至 2026-02-24

---

### 2. 情感分析模块 ✅

**实现状态**: 已完成
**技术栈**: PyTorch + Transformers + BERT

**模型配置**:
- 预训练模型: `hfl/chinese-bert-wwm-ext`（哈工大中文BERT）
- 最大长度: 128 tokens
- 分类类别: 3类（积极/中性/消极）
- 训练数据: 1,005条标注数据

**辅助工具**:
- 金融情感词典: 800+词条（积极/消极/程度/否定）
- 文本预处理: Jieba分词 + 停用词过滤

**API端点**:
- `POST /api/v1/sentiment/analyze` - 单文本分析
- `POST /api/v1/sentiment/batch` - 批量分析（最多100条）
- `GET /api/v1/sentiment/stats` - 分析统计

**分析结果**:
- 情感分析记录: 7,774条
- 准确率: 待评估

---

### 3. 多模型对比实验 ✅ (v2.0新增)

**实现状态**: 已完成
**位置**: `backend/app/services/sentiment/multi_model.py`

**支持模型**:
1. **BERT-wwm** - chinese-bert-wwm-ext微调模型
2. **FinBERT** - 金融领域BERT模型
3. **Lexicon** - 基于金融词典的规则方法

**功能特性**:
- 模型性能对比（Accuracy / F1 / Precision / Recall）
- 混淆矩阵可视化
- 共识投票机制
- 基准测试

**API端点**:
- `POST /api/v1/experiment/compare` - 多模型对比
- `POST /api/v1/experiment/benchmark` - 基准测试
- `GET /api/v1/experiment/results` - 历史结果
- `GET /api/v1/experiment/metrics` - 性能指标

**前端页面**: `frontend/src/views/Experiment.vue`

---

### 4. 方面级情感分析 ✅ (v2.0新增)

**实现状态**: 已完成
**位置**: `backend/app/services/sentiment/aspect_analyzer.py`

**分析维度**（5个）:
1. **业绩** - 营收、利润、财报相关
2. **政策** - 政策、监管、法规相关
3. **技术面** - K线、均线、技术指标
4. **资金面** - 资金流入流出、成交量
5. **行业** - 行业趋势、竞争格局

**实现方式**:
- 关键词匹配（每个维度独立词库）
- 正面/负面情感判断
- 雷达图可视化

**API端点**:
- `GET /api/v1/stocks/{code}/aspects` - 方面级情感

**数据表**: `aspect_sentiments`

---

### 5. 情绪量化模块 ✅

**实现状态**: 已完成
**位置**: `backend/app/services/quantify/calculator.py`

**情绪指标**（5个）:
1. **看涨指数** (Bull Index) - 积极评论占比 × 100
2. **看跌指数** (Bear Index) - 消极评论占比 × 100
3. **情绪强度** (Intensity) - (积极数 - 消极数) / 总数
4. **情绪温度** (Temperature) - 加权情绪分数均值
5. **情绪波动** (Volatility) - 情绪强度标准差

**聚合维度**:
- 时间: 小时/日/周/月
- 股票: 个股/板块/大盘
- 平台: 单平台/多平台综合

**API端点**:
- `GET /api/v1/emotion/overview` - 市场情绪概览
- `GET /api/v1/emotion/trend` - 情绪趋势
- `GET /api/v1/emotion/ranking` - 情绪排行榜

**数据量**:
- 情绪指标记录: 220条（日级）
- 覆盖时间: 2025-12-24 至 2026-02-24

---

### 6. 个股情绪画像 ✅ (v2.0新增)

**实现状态**: 已完成
**位置**: `backend/app/services/quantify/profiler.py`

**画像维度**（4个）:
1. **波动性** (Volatility) - 情绪稳定程度
2. **偏向性** (Bias) - 看涨/看跌倾向
3. **活跃度** (Activity) - 讨论热度
4. **一致性** (Consistency) - 情绪方向一致性

**输出内容**:
- 4维雷达图数据
- 趋势方向判断（上涨/下跌/震荡）
- 行情关联度
- 画像标签（如"情绪稳定型"、"看涨偏向"）

**API端点**:
- `GET /api/v1/stocks/{code}/profile` - 个股情绪画像

---

### 7. 情绪预警系统 ✅ (v2.0新增)

**实现状态**: 已完成（已修复字符集冲突问题）
**位置**: `backend/app/services/alert/engine.py`

**预警规则**（5种）:
1. **intensity_spike** - 情绪强度突变（>2σ）
2. **bull_extreme** - 看涨指数极端（>85% 或 <15%）
3. **bear_extreme** - 看跌指数极端（>85% 或 <15%）
4. **volume_surge** - 评论量暴增（>3倍均值）
5. **temperature_anomaly** - 情绪温度异常（>2σ）

**严重等级**:
- **high** - 高危预警（需立即关注）
- **medium** - 中等预警（建议关注）
- **low** - 低级预警（参考信息）

**API端点**:
- `GET /api/v1/alerts` - 预警列表（支持筛选、分页）
- `PUT /api/v1/alerts/{id}/read` - 标记已读
- `PUT /api/v1/alerts/read-all` - 全部已读
- `POST /api/v1/alerts/scan` - 手动触发扫描
- `GET /api/v1/alerts/stats` - 预警统计

**当前状态**:
- 总预警数: 15条
- 未读预警: 12条
- 最近7天: 1条

**前端页面**: `frontend/src/views/Alerts.vue`

**已修复问题**: 数据库字符集冲突（utf8mb4_unicode_ci vs utf8mb4_0900_ai_ci）

---

### 8. 市场验证模块 ✅

**实现状态**: 已完成
**位置**: `backend/app/services/market/validator.py`

**验证方法**:
1. **Pearson相关系数** - 情绪与涨跌幅线性相关性
2. **Spearman相关系数** - 情绪与涨跌幅秩相关性
3. **方向准确率** - 情绪方向与涨跌方向一致率
4. **格兰杰因果检验** - 情绪是否为价格变动的格兰杰原因

**数据来源**:
- 行情数据: AKShare API（实时A股数据）
- 情绪数据: 系统内部计算

**API端点**:
- `GET /api/v1/validation/correlation` - 相关性分析
- `GET /api/v1/validation/accuracy` - 预测准确率
- `GET /api/v1/validation/granger` - 格兰杰检验

**前端页面**: `frontend/src/views/Validation.vue`

---

### 9. 用户认证系统 ✅

**实现状态**: 已完成
**技术栈**: JWT + bcrypt

**功能特性**:
- JWT Token认证（24小时有效期）
- 密码加密存储（bcrypt）
- 登录/注册/登出
- 路由守卫保护

**API端点**:
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/register` - 用户注册
- `GET /api/auth/me` - 获取当前用户
- `POST /api/auth/logout` - 用户登出

**前端页面**: `frontend/src/views/Login.vue`

---

### 10. 运维监控系统 ✅

**实现状态**: 已完成
**技术栈**: Prometheus + Grafana + Loguru

**监控指标**:
- `http_requests_total` - HTTP请求总数
- `http_request_duration_seconds` - 请求耗时
- `sentiment_analysis_total` - 情感分析次数
- `crawler_comments_collected_total` - 爬虫采集数
- `cache_hits_total` - 缓存命中
- `emotion_index` - 情绪指数

**日志系统**:
- 结构化日志（JSON格式）
- 日志轮转（按日期）
- 日志级别: DEBUG/INFO/WARNING/ERROR
- 日志文件: `backend/logs/app_{date}.log`

**监控端点**:
- Prometheus: http://localhost:19090
- Grafana: http://localhost:3000 (admin/admin123)
- API Metrics: http://localhost:8000/metrics

---

## 数据库状态

**数据库**: MySQL 8.0
**字符集**: utf8mb4_0900_ai_ci（已统一）

### 数据表（8张）

| 表名 | 记录数 | 说明 |
|------|--------|------|
| `stocks` | 10 | 股票基本信息 |
| `comments` | 7,774 | 用户评论数据 |
| `sentiments` | 7,774 | 情感分析结果 |
| `emotions` | 220 | 情绪指标（日级） |
| `quotes` | 待同步 | 股票行情数据 |
| `experiment_results` | 0 | 实验对比结果 |
| `aspect_sentiments` | 0 | 方面级情感 |
| `alerts` | 15 | 预警记录 |

**总数据量**: 约16,000条记录

---

## 前端页面

**技术栈**: Vue 3 + Vite + Element Plus + ECharts

### 页面列表（11个）

| 页面 | 路由 | 状态 | 说明 |
|------|------|------|------|
| Dashboard | `/` | ✅ | 情绪仪表盘 + 预警横幅 |
| Stocks | `/stocks` | ✅ | 股票列表（筛选、分页） |
| StockDetail | `/stocks/:code` | ✅ | 股票详情 + 方面分析 + 画像 |
| Trend | `/trend` | ✅ | 情绪趋势分析 |
| Validation | `/validation` | ✅ | 市场验证报告 |
| Sentiment | `/sentiment` | ✅ | 情感分析测试工具 |
| Experiment | `/experiment` | ✅ | 多模型对比实验 |
| Alerts | `/alerts` | ✅ | 预警管理页面 |
| Settings | `/settings` | ✅ | 系统设置 |
| Login | `/login` | ✅ | 登录页面 |
| App | - | ✅ | 根组件 |

**开发服务器**: http://localhost:3000
**API代理**: `/api` → `http://localhost:8000`

---

## API接口

**总端点数**: 43个
**API文档**: http://localhost:8000/docs (Swagger UI)

### 接口分类

| 分类 | 端点数 | 说明 |
|------|--------|------|
| 认证 | 4 | 登录/注册/用户管理 |
| 股票 | 7 | 股票列表/详情/评论/行情/方面/画像 |
| 情绪 | 3 | 情绪概览/趋势/排行 |
| 情感分析 | 3 | 单文本/批量/统计 |
| 市场验证 | 3 | 相关性/准确率/格兰杰检验 |
| 爬虫管理 | 4 | 启动/停止/状态/统计 |
| 实验对比 | 5 | 多模型对比/基准测试/结果/指标 |
| 预警管理 | 5 | 列表/已读/扫描/统计 |
| 健康检查 | 3 | 根路径/健康/速率限制 |
| 监控 | 1 | Prometheus指标 |

---

## 部署架构

**部署方式**: Docker Compose
**服务数量**: 6个

### 服务列表

| 服务 | 镜像 | 端口 | 状态 |
|------|------|------|------|
| backend | 自定义 | 8000 | ✅ 运行中 |
| frontend | 自定义 | 80 | ✅ 运行中 |
| mysql | mysql:8.0 | 13306 | ✅ 运行中 |
| redis | redis:7-alpine | 6379 | ✅ 运行中 |
| prometheus | prom/prometheus:v2.48.0 | 19090 | ✅ 运行中 |
| grafana | grafana/grafana:10.2.2 | 3000 | ✅ 运行中 |

**启动命令**: `docker-compose up -d`

---

## 测试覆盖

**测试框架**: pytest
**测试文件**: 5个
**测试用例**: 49个

### 测试模块

| 模块 | 文件 | 用例数 | 状态 |
|------|------|--------|------|
| 情感分析 | `test_sentiment.py` | 15+ | ✅ 通过 |
| 用户认证 | `test_auth.py` | 10+ | ✅ 通过 |
| 缓存系统 | `test_cache.py` | 8+ | ✅ 通过 |
| 速率限制 | `test_rate_limit.py` | 8+ | ✅ 通过 |
| 其他 | - | 8+ | ✅ 通过 |

**运行命令**: `pytest tests/ -v --cov=app`

---

## 性能优化

### 缓存策略

**实现**: Redis + 内存LRU fallback
**位置**: `backend/app/core/cache.py`

**缓存键**:
- `stock:{code}:emotion` - 股票情绪数据
- `sentiment:stats` - 情感分析统计
- `crawler:status` - 爬虫状态

**缓存命中率**: 待统计

### 速率限制

**实现**: 滑动窗口算法（Redis支持）
**位置**: `backend/app/core/rate_limit.py`

**限制规则**:
- `/api/auth/*` - 10次/分钟
- `/api/v1/sentiment/*` - 30次/分钟
- `/api/v1/stocks/*` - 60次/分钟
- `/api/v1/crawler/*` - 5次/分钟

### 异步任务

**实现**: Celery + Redis broker
**位置**: `backend/app/celery_app.py`

**定时任务**:
- `crawl-hot-stocks` - 每天8:00爬取热门股票
- `update-emotion-index` - 每小时更新情绪指数
- `generate-daily-report` - 每天20:00生成日报

---

## 已知问题

### 1. 演示数据预警触发率低 ⚠️

**问题**: 演示数据变化平稳，无法触发预警规则
**影响**: 预警功能演示效果不佳
**解决方案**: 在`generate_demo_data.py`中增加极端值数据

### 2. 雪球/新浪爬虫未配置 ⚠️

**问题**: 需要登录凭证才能爬取
**影响**: 只能爬取东方财富数据
**解决方案**: 配置登录Cookie或使用Playwright自动登录

### 3. 行情数据未同步 ⚠️

**问题**: `quotes`表为空
**影响**: 市场验证功能无法使用
**解决方案**: 运行`python scripts/sync_quotes.py`

---

## 后续优化计划

### 短期（1-2周）

1. ✅ 修复预警API字符集冲突（已完成）
2. ⬜ 同步行情数据到数据库
3. ⬜ 优化演示数据生成（增加极端值）
4. ⬜ 配置雪球/新浪爬虫登录
5. ⬜ 完善单元测试覆盖率（目标80%+）

### 中期（1个月）

1. ⬜ 实现预警通知功能（邮件/WebSocket）
2. ⬜ 增加更多股票到数据库（目前仅10只）
3. ⬜ 优化BERT模型性能（GPU加速）
4. ⬜ 实现预警规则可配置化
5. ⬜ 添加用户权限管理

### 长期（3个月+）

1. ⬜ 支持更多数据源（微博、知乎等）
2. ⬜ 实现情绪预测功能（LSTM/GRU）
3. ⬜ 开发移动端应用
4. ⬜ 实现分布式爬虫集群
5. ⬜ 增加量化交易策略回测

---

## 文档资源

### 项目文档

- `README.md` - 项目说明文档
- `CLAUDE.md` - Claude Code开发指南
- `docs/spec.md` - 系统规格说明
- `docs/DEVELOPMENT_STATUS.md` - 开发进度跟踪
- `BUGFIX_ALERTS_API.md` - 预警API修复记录（本次）
- `SYSTEM_STATUS.md` - 系统状态报告（本文档）

### API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 监控面板

- Grafana: http://localhost:3000
- Prometheus: http://localhost:19090

---

## 联系方式

如有问题，请提交Issue或联系开发者。

**最后更新**: 2026-02-24 11:50
