# 基于Transformer的股票情绪预测系统 - 系统规格说明文档

## 1. 系统概述

### 1.1 项目背景

随着社交媒体在金融投资领域的广泛应用，投资者在东方财富股吧、雪球、新浪财经等平台上发表的评论已成为反映市场情绪的重要信息源。传统的情感分析方法难以准确捕捉金融文本中的复杂情感表达，而基于Transformer架构的预训练语言模型（如BERT）在自然语言理解任务上展现了卓越的性能。

本项目旨在构建一个基于Transformer的股票情绪预测系统，通过采集金融社交媒体评论数据，利用深度学习模型进行情感分析，量化市场投资情绪，为投资者提供情绪参考和决策支持。

### 1.2 项目目标

1. 构建多平台金融社交媒体数据采集系统
2. 实现基于BERT的金融文本情感分析模型
3. 建立金融领域专用情感词典
4. 开发投资情绪量化分析模块
5. 提供可视化的情绪监控与分析平台
6. 验证情绪指标与市场走势的相关性

### 1.3 功能范围

| 功能模块 | 功能描述 | 优先级 |
|---------|---------|-------|
| 数据采集 | 多平台评论数据爬取 | P0 |
| 数据预处理 | 文本清洗、分词、标准化 | P0 |
| 情感分析 | BERT模型情感预测 | P0 |
| 情感词典 | 金融词典构建与优化 | P1 |
| 情绪量化 | 情绪指标计算与趋势分析 | P0 |
| 市场验证 | 情绪与行情相关性分析 | P1 |
| 可视化展示 | 情绪仪表盘与报告 | P0 |

### 1.4 目标用户

- 个人投资者：获取市场情绪参考
- 量化研究员：情绪因子研究
- 金融分析师：辅助投资决策

---

## 2. 系统架构设计

### 2.1 整体架构

```
┌────────────────────────────────────────────────────────────────────────┐
│                         前端展示层 (Vue3 + ECharts)                     │
│    ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐     │
│    │ 情绪仪表盘 │  │ 股票详情页 │  │ 趋势分析页 │  │ 市场验证报告页    │     │
│    └──────────┘  └──────────┘  └──────────┘  └──────────────────┘     │
├────────────────────────────────────────────────────────────────────────┤
│                         API网关层 (FastAPI)                             │
│    ┌──────────────────────────────────────────────────────────────┐   │
│    │  RESTful API  │  WebSocket  │  认证授权  │  请求限流  │  日志   │   │
│    └──────────────────────────────────────────────────────────────┘   │
├────────────────────────────────────────────────────────────────────────┤
│                         业务服务层 (Python Services)                    │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────────┐  │
│  │ 爬虫服务 │ │数据处理  │ │情感分析  │ │情绪量化  │ │  市场验证服务    │  │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────────────┘  │
├────────────────────────────────────────────────────────────────────────┤
│                         数据存储层                                       │
│    ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐       │
│    │  MySQL 8.0   │    │    Redis     │    │   文件存储        │       │
│    │  (结构化数据) │    │   (缓存)     │    │  (模型/词典)      │       │
│    └──────────────┘    └──────────────┘    └──────────────────┘       │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈选型

| 层级 | 技术选型 | 版本 | 说明 |
|------|---------|------|------|
| 前端框架 | Vue.js | 3.x | 响应式前端框架 |
| 构建工具 | Vite | 5.x | 快速构建工具 |
| UI组件库 | Element Plus | 2.x | 企业级UI组件 |
| 图表库 | ECharts | 5.x | 数据可视化 |
| 后端框架 | FastAPI | 0.100+ | 高性能API框架 |
| 爬虫框架 | Scrapy | 2.x | 分布式爬虫 |
| 浏览器自动化 | Playwright | 1.x | 动态页面渲染 |
| NLP框架 | Transformers | 4.x | Hugging Face |
| 预训练模型 | chinese-bert-wwm | - | 中文BERT |
| 分词工具 | jieba | 0.42+ | 中文分词 |
| 数据库 | MySQL | 8.0 | 关系型数据库 |
| 缓存 | Redis | 7.x | 内存缓存 |
| 行情数据 | AKShare | 1.x | A股数据接口 |
| 任务调度 | APScheduler | 3.x | 定时任务 |

---

## 3. 模块详细设计

### 3.1 数据采集模块

#### 3.1.1 功能描述

从东方财富股吧、雪球、新浪财经三大平台采集股票评论数据。

#### 3.1.2 数据源分析

| 平台 | URL模式 | 数据特点 | 采集难度 |
|------|---------|---------|---------|
| 东方财富股吧 | guba.eastmoney.com | 数据量大，实时性强 | 中 |
| 雪球 | xueqiu.com | 质量高，专业性强 | 高（需登录） |
| 新浪财经 | finance.sina.com.cn | 新闻评论丰富 | 中 |

#### 3.1.3 采集字段

```python
class CommentData:
    comment_id: str        # 评论唯一ID
    platform: str          # 来源平台
    stock_code: str        # 股票代码
    stock_name: str        # 股票名称
    content: str           # 评论内容
    author: str            # 作者
    publish_time: datetime # 发布时间
    likes: int             # 点赞数
    replies: int           # 回复数
    crawl_time: datetime   # 采集时间
```

#### 3.1.4 爬虫策略

- 增量采集：基于时间戳的增量更新
- 频率控制：随机延迟3-8秒
- 代理轮换：支持代理池
- 异常重试：最大重试3次

### 3.2 数据预处理模块

#### 3.2.1 处理流程

```
原始文本 → 去除HTML标签 → 去除特殊字符 → 文本去重 → 中文分词 → 停用词过滤 → 标准化文本
```

#### 3.2.2 处理规则

| 处理步骤 | 处理规则 | 示例 |
|---------|---------|------|
| HTML清洗 | 移除所有HTML标签 | `<p>看涨</p>` → `看涨` |
| 特殊字符 | 保留中英文、数字、标点 | `#涨停#` → `涨停` |
| 表情符号 | 转换为文字描述或移除 | `[笑哭]` → `笑哭` |
| 文本去重 | 基于SimHash相似度>0.9 | 去除重复评论 |
| 分词 | jieba精确模式+自定义词典 | `涨停板` 不切分 |
| 停用词 | 金融停用词表 | 移除`的`、`是`等 |

### 3.3 情感分析模块

#### 3.3.1 模型架构

```
输入文本 → Tokenizer → BERT Encoder → [CLS] → FC Layer → Softmax → 情感标签
                                                          ↓
                                               [积极, 中性, 消极]
```

#### 3.3.2 模型配置

| 参数 | 值 | 说明 |
|------|-----|------|
| 预训练模型 | hfl/chinese-bert-wwm-ext | 哈工大中文BERT |
| 最大长度 | 128 | 最大token数 |
| 分类类别 | 3 | 积极/中性/消极 |
| 学习率 | 2e-5 | 微调学习率 |
| Batch Size | 32 | 批量大小 |
| Epochs | 5 | 训练轮数 |

#### 3.3.3 输出格式

```python
class SentimentResult:
    text: str              # 原始文本
    label: str             # 情感标签: positive/neutral/negative
    confidence: float      # 置信度: 0.0-1.0
    scores: dict           # 各类别分数
```

### 3.4 情感词典模块

#### 3.4.1 词典结构

| 词典类型 | 词条数 | 说明 |
|---------|-------|------|
| 积极词典 | 500+ | 看涨、利好、突破等 |
| 消极词典 | 500+ | 看跌、利空、暴跌等 |
| 程度词典 | 100+ | 非常、极其、稍微等 |
| 否定词典 | 50+ | 不、没、未等 |
| 金融实体词典 | 1000+ | 股票名称、术语等 |

#### 3.4.2 词典格式

```
# positive.txt
涨停	1.0
利好	0.9
突破	0.8
放量	0.7

# negative.txt
跌停	-1.0
利空	-0.9
暴跌	-0.8
套牢	-0.7
```

### 3.5 情绪量化模块

#### 3.5.1 情绪指标定义

| 指标名称 | 计算公式 | 取值范围 | 说明 |
|---------|---------|---------|------|
| 看涨指数(BullIndex) | 积极评论数 / 总评论数 × 100 | 0-100 | 看涨情绪强度 |
| 看跌指数(BearIndex) | 消极评论数 / 总评论数 × 100 | 0-100 | 看跌情绪强度 |
| 情绪强度(Intensity) | (积极数-消极数) / 总数 | -1~1 | 综合情绪倾向 |
| 情绪温度(Temperature) | 加权情绪分数均值 | 0-100 | 市场热度 |
| 情绪波动(Volatility) | 情绪强度标准差 | ≥0 | 情绪稳定性 |

#### 3.5.2 聚合维度

- 时间维度：小时/日/周/月
- 股票维度：个股/板块/大盘
- 平台维度：单平台/多平台综合

### 3.6 市场验证模块

#### 3.6.1 验证指标

| 指标 | 计算方法 | 说明 |
|------|---------|------|
| 相关系数 | Pearson相关系数 | 情绪与涨跌幅相关性 |
| 领先性分析 | 互相关函数CCF | 情绪领先天数 |
| 预测准确率 | 情绪方向与涨跌方向一致率 | 方向预测能力 |
| 格兰杰因果检验 | Granger Causality | 因果关系验证 |

#### 3.6.2 行情数据字段

```python
class StockQuote:
    stock_code: str    # 股票代码
    trade_date: date   # 交易日期
    open_price: float  # 开盘价
    close_price: float # 收盘价
    high_price: float  # 最高价
    low_price: float   # 最低价
    volume: int        # 成交量
    amount: float      # 成交额
    change_pct: float  # 涨跌幅
```

---

## 4. 数据库设计

### 4.1 ER图

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   stocks    │     │  comments   │     │ sentiments  │
│─────────────│     │─────────────│     │─────────────│
│ stock_code  │←────│ stock_code  │────→│ comment_id  │
│ stock_name  │     │ comment_id  │     │ label       │
│ industry    │     │ content     │     │ confidence  │
└─────────────┘     │ platform    │     │ scores      │
                    │ author      │     └─────────────┘
                    │ publish_time│
                    └─────────────┘
                           │
                           ↓
                    ┌─────────────┐     ┌─────────────┐
                    │  emotions   │     │   quotes    │
                    │─────────────│     │─────────────│
                    │ stock_code  │     │ stock_code  │
                    │ date        │     │ trade_date  │
                    │ bull_index  │     │ open/close  │
                    │ bear_index  │     │ high/low    │
                    │ intensity   │     │ volume      │
                    └─────────────┘     └─────────────┘
```

### 4.2 表结构设计

#### 4.2.1 股票信息表 (stocks)

```sql
CREATE TABLE stocks (
    stock_code VARCHAR(10) PRIMARY KEY COMMENT '股票代码',
    stock_name VARCHAR(50) NOT NULL COMMENT '股票名称',
    industry VARCHAR(50) COMMENT '所属行业',
    market VARCHAR(10) COMMENT '市场(SH/SZ)',
    list_date DATE COMMENT '上市日期',
    status TINYINT DEFAULT 1 COMMENT '状态:1正常0退市',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_industry (industry),
    INDEX idx_market (market)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票信息表';
```

#### 4.2.2 评论数据表 (comments)

```sql
CREATE TABLE comments (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    comment_id VARCHAR(64) UNIQUE NOT NULL COMMENT '评论唯一ID',
    platform VARCHAR(20) NOT NULL COMMENT '来源平台',
    stock_code VARCHAR(10) NOT NULL COMMENT '股票代码',
    content TEXT NOT NULL COMMENT '评论内容',
    content_clean TEXT COMMENT '清洗后内容',
    author VARCHAR(100) COMMENT '作者',
    publish_time DATETIME NOT NULL COMMENT '发布时间',
    likes INT DEFAULT 0 COMMENT '点赞数',
    replies INT DEFAULT 0 COMMENT '回复数',
    crawl_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '采集时间',
    is_processed TINYINT DEFAULT 0 COMMENT '是否已处理',
    INDEX idx_stock_code (stock_code),
    INDEX idx_platform (platform),
    INDEX idx_publish_time (publish_time),
    INDEX idx_is_processed (is_processed),
    FOREIGN KEY (stock_code) REFERENCES stocks(stock_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='评论数据表';
```

#### 4.2.3 情感分析结果表 (sentiments)

```sql
CREATE TABLE sentiments (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    comment_id VARCHAR(64) UNIQUE NOT NULL COMMENT '评论ID',
    label VARCHAR(20) NOT NULL COMMENT '情感标签',
    confidence DECIMAL(5,4) NOT NULL COMMENT '置信度',
    positive_score DECIMAL(5,4) COMMENT '积极得分',
    neutral_score DECIMAL(5,4) COMMENT '中性得分',
    negative_score DECIMAL(5,4) COMMENT '消极得分',
    model_version VARCHAR(50) COMMENT '模型版本',
    analyzed_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '分析时间',
    INDEX idx_label (label),
    INDEX idx_analyzed_at (analyzed_at),
    FOREIGN KEY (comment_id) REFERENCES comments(comment_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='情感分析结果表';
```

#### 4.2.4 情绪指标表 (emotions)

```sql
CREATE TABLE emotions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL COMMENT '股票代码',
    stat_date DATE NOT NULL COMMENT '统计日期',
    stat_hour TINYINT COMMENT '统计小时(0-23,NULL表示日级)',
    total_count INT DEFAULT 0 COMMENT '总评论数',
    positive_count INT DEFAULT 0 COMMENT '积极评论数',
    neutral_count INT DEFAULT 0 COMMENT '中性评论数',
    negative_count INT DEFAULT 0 COMMENT '消极评论数',
    bull_index DECIMAL(5,2) COMMENT '看涨指数',
    bear_index DECIMAL(5,2) COMMENT '看跌指数',
    intensity DECIMAL(5,4) COMMENT '情绪强度',
    temperature DECIMAL(5,2) COMMENT '情绪温度',
    volatility DECIMAL(5,4) COMMENT '情绪波动',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_date_hour (stock_code, stat_date, stat_hour),
    INDEX idx_stat_date (stat_date),
    FOREIGN KEY (stock_code) REFERENCES stocks(stock_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='情绪指标表';
```

#### 4.2.5 股票行情表 (quotes)

```sql
CREATE TABLE quotes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL COMMENT '股票代码',
    trade_date DATE NOT NULL COMMENT '交易日期',
    open_price DECIMAL(10,2) COMMENT '开盘价',
    close_price DECIMAL(10,2) COMMENT '收盘价',
    high_price DECIMAL(10,2) COMMENT '最高价',
    low_price DECIMAL(10,2) COMMENT '最低价',
    pre_close DECIMAL(10,2) COMMENT '昨收价',
    change_amount DECIMAL(10,2) COMMENT '涨跌额',
    change_pct DECIMAL(8,4) COMMENT '涨跌幅(%)',
    volume BIGINT COMMENT '成交量(手)',
    amount DECIMAL(18,2) COMMENT '成交额(元)',
    turnover_rate DECIMAL(8,4) COMMENT '换手率(%)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_date (stock_code, trade_date),
    INDEX idx_trade_date (trade_date),
    FOREIGN KEY (stock_code) REFERENCES stocks(stock_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票行情表';
```

---

## 5. API接口设计

### 5.1 接口规范

- 基础路径: `/api/v1`
- 数据格式: JSON
- 认证方式: JWT Token
- 响应格式:

```json
{
    "code": 200,
    "message": "success",
    "data": {},
    "timestamp": 1704067200
}
```

### 5.2 接口列表

#### 5.2.1 股票相关

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /stocks | 获取股票列表 |
| GET | /stocks/{code} | 获取股票详情 |
| GET | /stocks/{code}/comments | 获取股票评论 |
| GET | /stocks/{code}/emotion | 获取股票情绪 |
| GET | /stocks/{code}/quotes | 获取股票行情 |

#### 5.2.2 情绪分析

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /sentiment/analyze | 分析单条文本情感 |
| POST | /sentiment/batch | 批量分析文本情感 |
| GET | /sentiment/stats | 获取分析统计数据 |

#### 5.2.3 情绪指标

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /emotion/overview | 获取市场情绪概览 |
| GET | /emotion/trend | 获取情绪趋势数据 |
| GET | /emotion/ranking | 获取情绪排行榜 |
| GET | /emotion/heatmap | 获取情绪热力图数据 |

#### 5.2.4 市场验证

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /validation/correlation | 获取情绪-行情相关性 |
| GET | /validation/accuracy | 获取预测准确率 |
| GET | /validation/report | 获取验证报告 |

#### 5.2.5 系统管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /crawler/start | 启动爬虫任务 |
| POST | /crawler/stop | 停止爬虫任务 |
| GET | /crawler/status | 获取爬虫状态 |
| GET | /system/stats | 获取系统统计 |

### 5.3 接口详细定义

#### GET /api/v1/stocks/{code}/emotion

获取指定股票的情绪数据

**请求参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 股票代码 |
| start_date | string | 否 | 开始日期 (YYYY-MM-DD) |
| end_date | string | 否 | 结束日期 (YYYY-MM-DD) |
| granularity | string | 否 | 粒度: hour/day/week |

**响应示例:**

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "stock_code": "000001",
        "stock_name": "平安银行",
        "period": {
            "start": "2026-01-01",
            "end": "2026-01-21"
        },
        "summary": {
            "avg_bull_index": 58.5,
            "avg_bear_index": 25.3,
            "avg_intensity": 0.32,
            "total_comments": 12580
        },
        "trend": [
            {
                "date": "2026-01-21",
                "bull_index": 62.3,
                "bear_index": 22.1,
                "intensity": 0.40,
                "temperature": 75.5,
                "comment_count": 856
            }
        ]
    }
}
```

---

## 6. 前端页面设计

### 6.1 页面结构

```
├── 首页(Dashboard)          # 情绪仪表盘
│   ├── 市场情绪概览卡片
│   ├── 情绪趋势图表
│   ├── 热门股票情绪排行
│   └── 最新评论动态
├── 股票详情页(StockDetail)  # 单股情绪分析
│   ├── 股票基本信息
│   ├── 情绪指标展示
│   ├── 情绪vs行情对比图
│   └── 相关评论列表
├── 趋势分析页(Trend)        # 情绪趋势分析
│   ├── 时间范围选择
│   ├── 多股票对比
│   └── 趋势预测展示
├── 验证报告页(Validation)   # 市场验证报告
│   ├── 相关性分析
│   ├── 预测准确率
│   └── 因果检验结果
└── 系统设置页(Settings)     # 系统配置
    ├── 爬虫任务管理
    ├── 模型参数配置
    └── 系统日志查看
```

### 6.2 核心组件

| 组件名 | 说明 | 使用页面 |
|--------|------|---------|
| EmotionGauge | 情绪仪表盘 | Dashboard |
| TrendChart | 趋势折线图 | Dashboard, StockDetail |
| SentimentPie | 情感分布饼图 | StockDetail |
| CommentList | 评论列表 | StockDetail |
| StockTable | 股票数据表格 | Dashboard, Trend |
| HeatmapChart | 热力图 | Dashboard |

---

## 7. 部署架构

### 7.1 开发环境

```
本地开发机
├── Python 3.10+ (后端)
├── Node.js 18+ (前端)
├── MySQL 8.0 (数据库)
├── Redis 7.x (缓存)
└── Git (版本控制)
```

### 7.2 生产环境建议

```
┌─────────────────────────────────────────────┐
│              Nginx (反向代理)                │
├──────────────────┬──────────────────────────┤
│   前端静态资源    │      后端API服务          │
│   (Vue Build)    │     (FastAPI + Uvicorn)  │
├──────────────────┴──────────────────────────┤
│                  MySQL                       │
│                  Redis                       │
└─────────────────────────────────────────────┘
```

---

## 8. 开发计划

### 8.1 里程碑

| 阶段 | 时间 | 交付物 |
|------|------|--------|
| M1 | 第1周 | 项目框架搭建完成 |
| M2 | 第2-3周 | 数据采集模块完成 |
| M3 | 第4-5周 | 情感分析模块完成 |
| M4 | 第6周 | 情绪量化模块完成 |
| M5 | 第7-8周 | 前端开发完成 |
| M6 | 第9周 | 系统集成测试 |

### 8.2 风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| 网站反爬限制 | 数据采集受阻 | 使用代理池、控制频率 |
| 模型精度不足 | 情感分析不准 | 扩大训练数据、优化词典 |
| 数据量过大 | 系统性能下降 | 分库分表、增加缓存 |

---

## 附录

### A. 参考资料

1. BERT: Pre-training of Deep Bidirectional Transformers
2. FinBERT: Financial Sentiment Analysis with BERT
3. Hugging Face Transformers Documentation
4. 东方财富网API分析

### B. 术语表

| 术语 | 说明 |
|------|------|
| BERT | Bidirectional Encoder Representations from Transformers |
| NLP | Natural Language Processing 自然语言处理 |
| 情绪指标 | 量化市场情绪的数值指标 |
| 看涨/看跌 | 预期股价上涨/下跌的投资情绪 |
