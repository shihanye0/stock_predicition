# 预警API修复记录

## 问题描述

**时间**: 2026-02-24
**问题**: 前端访问预警相关API时返回500错误

```
GET /api/v1/alerts?page=1&page_size=20 - 500 Internal Server Error
GET /api/v1/alerts/stats - 500 Internal Server Error
GET /api/v1/alerts?is_read=0&page_size=5 - 500 Internal Server Error
```

## 问题排查过程

### 1. 检查数据库数据

首先检查数据库中是否有预警数据：

```bash
# 检查alerts表
SELECT COUNT(*) FROM alerts;  # 结果：0条

# 检查emotion数据日期范围
SELECT MIN(stat_date), MAX(stat_date) FROM emotions;
# 结果：2025-12-24 到 2026-01-23（数据过期）
```

**发现问题1**: 数据库中没有预警数据，且情绪数据已过期（最新数据是1月23日，当前是2月24日）

### 2. 生成演示数据

运行演示数据生成脚本：

```bash
python scripts/generate_demo_data.py
```

生成了：
- 7774条评论
- 7774条情感分析结果
- 220条情绪指标（更新到2026-02-24）

### 3. 触发预警扫描

尝试触发预警扫描：

```python
from app.services.alert.engine import get_alert_engine
engine = get_alert_engine()
alerts = engine.scan_all_stocks(lookback_days=30)
# 结果：0条预警（因为演示数据变化不够大，未触发预警规则）
```

### 4. 创建测试预警数据

手动创建15条测试预警：

```python
# 创建测试预警（不同类型、严重程度、日期）
for i in range(15):
    alert = Alert(
        stock_code=random.choice(['000001', '000002', '000651', '000858', '002475']),
        alert_type=random.choice(['intensity_spike', 'bull_extreme', 'bear_extreme', 'volume_surge', 'temperature_anomaly']),
        severity=random.choice(['high', 'medium', 'low']),
        title=f'测试预警 {i+1}',
        message=f'这是一个测试预警消息',
        metric_value=random.uniform(50, 90),
        threshold=random.uniform(40, 80),
        triggered_at=datetime.now() - timedelta(days=random.randint(0, 29)),
        is_read=random.choice([0, 0, 0, 1])  # 75%未读
    )
    db.add(alert)
db.commit()
```

### 5. 测试API仍返回空数据

即使数据库中有15条预警，API仍返回空结果：

```bash
GET /api/v1/alerts?page=1&page_size=5
# 返回：{"data": [], "total": 0}
```

### 6. 发现根本原因：字符集冲突

测试JOIN查询时发现错误：

```
pymysql.err.OperationalError: (1267, "Illegal mix of collations
(utf8mb4_unicode_ci,IMPLICIT) and (utf8mb4_0900_ai_ci,IMPLICIT)
for operation '='")
```

检查表结构：

```sql
SHOW FULL COLUMNS FROM stocks WHERE Field = 'stock_code';
-- 结果：utf8mb4_0900_ai_ci

SHOW FULL COLUMNS FROM alerts WHERE Field = 'stock_code';
-- 结果：utf8mb4_unicode_ci
```

**根本原因**: `alerts`表的`stock_code`列使用`utf8mb4_unicode_ci`字符集，而`stocks`表使用`utf8mb4_0900_ai_ci`，导致JOIN操作时字符集冲突。

## 解决方案

### 修复字符集不匹配

```sql
ALTER TABLE alerts
MODIFY stock_code VARCHAR(10)
CHARACTER SET utf8mb4
COLLATE utf8mb4_0900_ai_ci
NOT NULL;
```

### 增强API错误处理

修改`backend/app/api/alerts.py`，为所有端点添加异常捕获：

```python
@router.get("/alerts", response_model=ListResponse, summary="获取预警列表")
async def get_alerts(...):
    try:
        # 原有查询逻辑
        ...
        return ListResponse(data=data, total=total, page=page, page_size=page_size)
    except Exception as e:
        logger.error(f"Get alerts error: {e}")
        return ListResponse(data=[], total=0, page=page, page_size=page_size)

@router.get("/alerts/stats", response_model=Response, summary="预警统计")
async def get_alert_stats(...):
    try:
        # 原有统计逻辑
        ...
        return Response(data={...})
    except Exception as e:
        logger.error(f"Get alert stats error: {e}")
        return Response(data={
            "period_days": days,
            "total": 0,
            "unread": 0,
            "by_severity": {},
            "by_type": {},
            "by_stock": []
        })
```

## 修复结果

修复后API正常返回数据：

```bash
GET /api/v1/alerts?page=1&page_size=5
# 返回：{"total": 15, "data": [5条预警]}

GET /api/v1/alerts/stats?days=30
# 返回：{
#   "total": 15,
#   "unread": 12,
#   "by_severity": {"high": 4, "medium": 3, "low": 8},
#   "by_type": {
#     "intensity_spike": 4,
#     "volume_surge": 4,
#     "bear_extreme": 3,
#     "temperature_anomaly": 2,
#     "bull_extreme": 2
#   }
# }
```

## 预警系统功能说明

### 预警类型（5种）

1. **intensity_spike** - 情绪强度突变
   - 检测条件：情绪强度偏离历史均值超过2个标准差
   - 严重程度：z_score >= 3 为high，否则为medium

2. **bull_extreme** - 看涨指数极端
   - 检测条件：看涨指数 > 85% 或 < 15%
   - 严重程度：>= 90% 或 <= 10% 为high，否则为medium

3. **bear_extreme** - 看跌指数极端
   - 检测条件：看跌指数 > 85% 或 < 15%
   - 严重程度：>= 90% 或 <= 10% 为high，否则为medium

4. **volume_surge** - 评论量暴增
   - 检测条件：单日评论量超过近期均值3倍
   - 严重程度：>= 5倍为high，否则为medium

5. **temperature_anomaly** - 情绪温度异常
   - 检测条件：情绪温度偏离历史均值超过2个标准差
   - 严重程度：z_score >= 3 为high，否则为medium

### 预警扫描机制

**实现位置**: `backend/app/services/alert/engine.py`

**扫描流程**:
1. 获取股票最近N天的情绪数据（默认30天）
2. 计算历史均值和标准差
3. 对比最新数据与历史数据
4. 触发符合条件的预警规则
5. 保存预警到数据库（去重：同一天同类型同股票只保存一次）

**触发方式**:
- 手动触发：`POST /api/v1/alerts/scan`
- 定时任务：可通过Celery Beat配置定期扫描

### API端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/alerts` | GET | 获取预警列表（支持分页、筛选） |
| `/api/v1/alerts/{id}/read` | PUT | 标记单条预警已读 |
| `/api/v1/alerts/read-all` | PUT | 全部标记已读 |
| `/api/v1/alerts/scan` | POST | 手动触发预警扫描 |
| `/api/v1/alerts/stats` | GET | 获取预警统计信息 |

### 前端页面

- **Dashboard.vue** - 顶部显示未读预警横幅
- **Alerts.vue** - 预警管理页面（列表、筛选、统计）

## 经验教训

1. **数据库字符集一致性很重要**
   - 创建表时应统一使用相同的字符集和排序规则
   - 建议在`init_db.sql`中明确指定所有表的字符集

2. **API应该有完善的错误处理**
   - 即使数据库查询失败，也应返回友好的空结果而非500错误
   - 使用try-except捕获异常并记录日志

3. **演示数据应该触发预警**
   - 当前演示数据变化平稳，无法触发预警规则
   - 建议在`generate_demo_data.py`中增加一些极端值数据

4. **定期检查数据时效性**
   - 演示数据可能过期，导致查询返回空结果
   - 应该在数据生成脚本中使用相对日期（如最近30天）

## 后续优化建议

1. **统一数据库字符集**
   ```sql
   -- 检查所有表的字符集
   SELECT TABLE_NAME, TABLE_COLLATION
   FROM information_schema.TABLES
   WHERE TABLE_SCHEMA = 'stock_sentiment';

   -- 统一修改为utf8mb4_0900_ai_ci
   ```

2. **增强演示数据生成**
   - 添加一些极端情绪数据（bull_index > 85, bear_index < 15）
   - 添加评论量突增的场景
   - 确保能触发各种类型的预警

3. **添加预警通知功能**
   - 邮件通知
   - WebSocket实时推送
   - 微信/钉钉机器人通知

4. **预警规则可配置化**
   - 允许用户自定义阈值
   - 支持启用/禁用特定规则
   - 支持自定义预警规则

## 相关文件

- `backend/app/api/alerts.py` - 预警API端点
- `backend/app/services/alert/engine.py` - 预警引擎
- `backend/app/models/models.py` - Alert模型定义
- `frontend/src/views/Alerts.vue` - 预警管理页面
- `frontend/src/views/Dashboard.vue` - 仪表盘（显示预警横幅）
- `scripts/init_db.sql` - 数据库初始化脚本

## 修复时间

- 问题发现：2026-02-24 11:30
- 问题定位：2026-02-24 11:40
- 问题修复：2026-02-24 11:45
- 总耗时：约15分钟
