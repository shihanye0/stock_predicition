"""
管理员API - 系统数据初始化和管理
"""
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
import pymysql

from app.core.database import get_db
from app.core.config import settings
from app.models.models import Stock, Comment, Sentiment, Emotion, Quote
from app.models.schemas import Response

router = APIRouter()

# 数据库配置 - 使用配置文件中的设置
DB_CONFIG = {
    'host': settings.DB_HOST,
    'port': settings.DB_PORT,
    'user': settings.DB_USER,
    'password': settings.DB_PASSWORD,
    'database': settings.DB_NAME,
    'charset': 'utf8mb4'
}

# 模拟评论模板
POSITIVE_COMMENTS = [
    "这只股票太牛了，继续加仓！",
    "看好后市，长期持有",
    "业绩超预期，明天继续涨",
    "底部已经确认，可以进场了",
    "主力在吸筹，跟上节奏",
    "技术面很漂亮，突破在即",
    "基本面扎实，值得信赖",
    "分红不错，长线持有",
    "龙头股，稳如泰山",
    "利好消息不断，继续看涨",
    "这波调整是上车机会",
    "券商看好，目标价上调",
    "散户少见的好股票",
    "资金流入明显，后市可期",
    "行业景气度提升，受益明显"
]

NEGATIVE_COMMENTS = [
    "要跌了，赶紧跑",
    "主力在出货，小心被套",
    "业绩下滑太多了，不看好",
    "感觉还要跌，观望中",
    "高位接盘侠太多了",
    "大环境不好，谨慎为主",
    "这票已经见顶了",
    "资金在流出，不建议进场",
    "估值太高了，泡沫严重",
    "利空消息不断，小心为上",
    "机构在减仓，散户别接盘",
    "技术面走坏，跌势未止",
    "行业竞争太激烈了",
    "管理层有问题，不敢买",
    "短期风险很大，建议回避"
]

NEUTRAL_COMMENTS = [
    "继续观望，等信号",
    "横盘整理中，不急",
    "关注中，看看再说",
    "没什么特别的消息",
    "等财报出来再决定",
    "市场波动正常，平常心",
    "持仓不动，静待花开",
    "仓位不重，影响不大",
    "短线无机会，中线布局",
    "政策面不明朗，观望"
]

# A股热门股票列表 (目标: 100只，覆盖主要行业)
POPULAR_STOCKS = [
    # 银行
    ('600000', '浦发银行', '银行', 'SH'),
    ('600015', '华夏银行', '银行', 'SH'),
    ('600016', '民生银行', '银行', 'SH'),
    ('600036', '招商银行', '银行', 'SH'),
    ('601009', '南京银行', '银行', 'SH'),
    ('601166', '兴业银行', '银行', 'SH'),
    ('601169', '北京银行', '银行', 'SH'),
    ('601229', '上海银行', '银行', 'SH'),
    ('601288', '农业银行', '银行', 'SH'),
    ('601328', '交通银行', '银行', 'SH'),
    ('601398', '工商银行', '银行', 'SH'),
    ('601818', '光大银行', '银行', 'SH'),
    ('601939', '建设银行', '银行', 'SH'),
    ('601988', '中国银行', '银行', 'SH'),
    ('601998', '中信银行', '银行', 'SH'),
    # 白酒
    ('000568', '泸州老窖', '白酒', 'SZ'),
    ('000596', '古井贡酒', '白酒', 'SZ'),
    ('000799', '酒鬼酒', '白酒', 'SZ'),
    ('000858', '五粮液', '白酒', 'SZ'),
    ('002304', '洋河股份', '白酒', 'SZ'),
    ('600059', '古越龙山', '白酒', 'SH'),
    ('600084', '*ST中葡', '白酒', 'SH'),
    ('600199', '金种子酒', '白酒', 'SH'),
    ('600519', '贵州茅台', '白酒', 'SH'),
    ('600702', '舍得酒业', '白酒', 'SH'),
    ('600779', '水井坊', '白酒', 'SH'),
    ('603369', '今世缘', '白酒', 'SH'),
    ('603589', '口子窖', '白酒', 'SH'),
    # 半导体/科技
    ('002049', '紫光国微', '半导体', 'SZ'),
    ('002156', '通富微电', '半导体', 'SZ'),
    ('002230', '科大讯飞', '人工智能', 'SZ'),
    ('002371', '北方华创', '半导体设备', 'SZ'),
    ('002459', '晶澳科技', '光伏', 'SZ'),
    ('002475', '立讯精密', '消费电子', 'SZ'),
    ('002594', '比亚迪', '新能源汽车', 'SZ'),
    ('002601', '龙佰集团', '化工', 'SZ'),
    ('300033', '同花顺', '软件', 'SZ'),
    ('300059', '东方财富', '互联网金融', 'SZ'),
    ('300124', '汇川技术', '工业自动化', 'SZ'),
    ('300223', '北京君正', '半导体', 'SZ'),
    ('300274', '阳光电源', '光伏', 'SZ'),
    ('300450', '先导智能', '锂电设备', 'SZ'),
    ('300496', '中科创达', '软件', 'SZ'),
    ('300661', '圣邦股份', '半导体', 'SZ'),
    ('300750', '宁德时代', '锂电池', 'SZ'),
    ('300896', '爱美客', '医美', 'SZ'),
    ('600703', '三安光电', 'LED', 'SH'),
    ('600745', '闻泰科技', '半导体', 'SH'),
    ('603986', '兆易创新', '半导体', 'SH'),
    # 医药
    ('000513', '丽珠集团', '医药', 'SZ'),
    ('000538', '云南白药', '中药', 'SZ'),
    ('000661', '长春高新', '生物制药', 'SZ'),
    ('000739', '普洛药业', '医药', 'SZ'),
    ('000999', '华润三九', '医药', 'SZ'),
    ('002001', '新和成', '医药', 'SZ'),
    ('002007', '华兰生物', '生物制药', 'SZ'),
    ('002252', '上海莱士', '生物制药', 'SZ'),
    ('002275', '桂林三金', '中药', 'SZ'),
    ('002287', '奇正藏药', '中药', 'SZ'),
    ('002294', '信立泰', '医药', 'SZ'),
    ('002349', '精华制药', '中药', 'SZ'),
    ('002422', '科伦药业', '医药', 'SZ'),
    ('002603', '以岭药业', '中药', 'SZ'),
    ('002727', '一心堂', '医药零售', 'SZ'),
    ('300003', '乐普医疗', '医疗器械', 'SZ'),
    ('300015', '爱尔眼科', '医疗服务', 'SZ'),
    ('300142', '沃森生物', '疫苗', 'SZ'),
    ('300347', '泰格医药', '医疗服务', 'SZ'),
    ('300529', '健帆生物', '医疗器械', 'SZ'),
    ('600056', '中国医药', '医药', 'SH'),
    ('600079', '人福医药', '医药', 'SH'),
    ('600161', '天坛生物', '生物制药', 'SH'),
    ('600196', '复星医药', '医药', 'SH'),
    ('600211', '西藏药业', '医药', 'SH'),
    ('600216', '浙江医药', '医药', 'SH'),
    ('600276', '恒瑞医药', '医药', 'SH'),
    ('600329', '达仁堂', '中药', 'SH'),
    ('600332', '白云山', '医药', 'SH'),
    ('600436', '片仔癀', '中药', 'SH'),
    ('600529', '山东药玻', '医疗器械', 'SH'),
    ('600535', '天士力', '中药', 'SH'),
    ('600566', '济川药业', '医药', 'SH'),
    ('600867', '通化东宝', '医药', 'SH'),
    ('603259', '药明康德', '医疗服务', 'SH'),
    ('603456', '九洲药业', '医药', 'SH'),
    ('603707', '健友股份', '医药', 'SH'),
    # 新能源
    ('002074', '国轩高科', '锂电池', 'SZ'),
    ('002129', '中环股份', '光伏', 'SZ'),
    ('002709', '天赐材料', '锂电池材料', 'SZ'),
    ('300014', '亿纬锂能', '锂电池', 'SZ'),
    ('300750', '宁德时代', '锂电池', 'SZ'),
    ('600438', '通威股份', '光伏', 'SH'),
    ('601012', '隆基绿能', '光伏', 'SH'),
    ('601615', '明阳智能', '风电', 'SH'),
    ('603806', '福斯特', '光伏材料', 'SH'),
    # 消费
    ('000333', '美的集团', '家电', 'SZ'),
    ('000651', '格力电器', '家电', 'SZ'),
    ('000876', '新希望', '农牧', 'SZ'),
    ('002024', '苏宁易购', '零售', 'SZ'),
    ('002032', '苏泊尔', '家电', 'SZ'),
    ('002127', '南极电商', '电商', 'SZ'),
    ('002236', '大华股份', '安防', 'SZ'),
    ('002241', '歌尔股份', '消费电子', 'SZ'),
    ('002252', '上海莱士', '生物制药', 'SZ'),
    ('002263', '大东方', '零售', 'SZ'),
    ('002291', '星期六', '服装', 'SZ'),
    ('002352', '顺丰控股', '物流', 'SZ'),
    ('002415', '海康威视', '安防', 'SZ'),
    ('002420', '毅昌科技', '家电', 'SZ'),
    ('002501', '*ST利源', '汽车零部件', 'SZ'),
    ('002507', '涪陵榨菜', '食品', 'SZ'),
    ('002511', '中顺洁柔', '造纸', 'SZ'),
    ('002557', '洽洽食品', '食品', 'SZ'),
    ('002558', '巨人网络', '游戏', 'SZ'),
    ('002607', '亚玛顿', '光伏', 'SZ'),
    ('002705', '新宝股份', '家电', 'SZ'),
    ('002920', '港中旅', '旅游', 'SZ'),
    ('300413', '芒果超媒', '传媒', 'SZ'),
    ('300498', '温氏股份', '农牧', 'SZ'),
    ('600019', '宝钢股份', '钢铁', 'SH'),
    ('600104', '上汽集团', '汽车', 'SH'),
    ('600132', '重庆啤酒', '啤酒', 'SH'),
    ('600185', '格力地产', '房地产', 'SH'),
    ('600276', '恒瑞医药', '医药', 'SH'),
    ('600519', '贵州茅台', '白酒', 'SH'),
    ('600690', '海尔智家', '家电', 'SH'),
    ('600887', '伊利股份', '乳业', 'SH'),
    ('603605', '珀莱雅', '化妆品', 'SH'),
    ('603816', '顾家家居', '家居', 'SH'),
    # 券商
    ('000686', '东北证券', '证券', 'SZ'),
    ('000712', '锦龙股份', '证券', 'SZ'),
    ('000728', '国元证券', '证券', 'SZ'),
    ('000776', '广发证券', '证券', 'SZ'),
    ('000783', '长江证券', '证券', 'SZ'),
    ('002500', '山西证券', '证券', 'SZ'),
    ('002673', '西部证券', '证券', 'SZ'),
    ('002736', '国信证券', '证券', 'SZ'),
    ('002797', '第一创业', '证券', 'SZ'),
    ('300059', '东方财富', '互联网券商', 'SZ'),
    ('600030', '中信证券', '证券', 'SH'),
    ('600061', '国投资本', '证券', 'SH'),
    ('600109', '国金证券', '证券', 'SH'),
    ('600155', '华创阳安', '证券', 'SH'),
    ('600369', '西南证券', '证券', 'SH'),
    ('600837', '海通证券', '证券', 'SH'),
    ('600958', '东方证券', '证券', 'SH'),
    ('600999', '招商证券', '证券', 'SH'),
    ('601066', '中信建投', '证券', 'SH'),
    ('601108', '财通证券', '证券', 'SH'),
    ('601155', '新城控股', '房地产', 'SH'),
    ('601198', '东兴证券', '证券', 'SH'),
    ('601211', '国泰君安', '证券', 'SH'),
    ('601377', '兴业证券', '证券', 'SH'),
    ('601555', '东吴证券', '证券', 'SH'),
    ('601688', '华泰证券', '证券', 'SH'),
    ('601788', '光大证券', '证券', 'SH'),
    ('601878', '浙商证券', '证券', 'SH'),
    ('601881', '中国银河', '证券', 'SH'),
    ('601990', '南京证券', '证券', 'SH'),
    # 房地产
    ('000002', '万科A', '房地产', 'SZ'),
    ('000402', '金融街', '房地产', 'SZ'),
    ('000961', '中南建设', '房地产', 'SZ'),
    ('001979', '招商蛇口', '房地产', 'SZ'),
    ('002146', '荣盛发展', '房地产', 'SZ'),
    ('002244', '滨江集团', '房地产', 'SZ'),
    ('600048', '保利发展', '房地产', 'SH'),
    ('600052', '浙江广厦', '房地产', 'SH'),
    ('600077', '宋都股份', '房地产', 'SH'),
    ('600094', '大名城', '房地产', 'SH'),
    ('600162', '香江控股', '房地产', 'SH'),
    ('600185', '格力地产', '房地产', 'SH'),
    ('600246', '万通发展', '房地产', 'SH'),
    ('600340', '华夏幸福', '房地产', 'SH'),
    ('600383', '金地集团', '房地产', 'SH'),
    ('600606', '绿地控股', '房地产', 'SH'),
    ('600657', '信达地产', '房地产', 'SH'),
    ('600675', '中华企业', '房地产', 'SH'),
    ('600708', '光明地产', '房地产', 'SH'),
    ('600743', '华远地产', '房地产', 'SH'),
    ('600748', '上实发展', '房地产', 'SH'),
    ('600773', '西藏城投', '房地产', 'SH'),
    ('600846', '同济科技', '房地产', 'SH'),
    ('600848', '上海临港', '房地产', 'SH'),
    ('600867', '通化东宝', '医药', 'SH'),
    ('600890', '*ST中房', '房地产', 'SH'),
    ('601155', '新城控股', '房地产', 'SH'),
    # 基建
    ('000498', '山东路桥', '基建', 'SZ'),
    ('002051', '中工国际', '基建', 'SZ'),
    ('002062', '宏润建设', '基建', 'SZ'),
    ('002140', '东华科技', '基建', 'SZ'),
    ('002146', '荣盛发展', '房地产', 'SZ'),
    ('002271', '东方雨虹', '建材', 'SZ'),
    ('002310', '东方园林', '基建', 'SZ'),
    ('002482', '广田集团', '装修', 'SZ'),
    ('002524', '光正眼科', '医疗', 'SZ'),
    ('002789', '建艺集团', '装修', 'SZ'),
    ('300212', '易华录', 'IT', 'SZ'),
    ('600039', '四川路桥', '基建', 'SH'),
    ('600170', '上海建工', '基建', 'SH'),
    ('600320', '振华重工', '机械', 'SH'),
    ('600378', '昊华科技', '化工', 'SH'),
    ('600502', '安徽建工', '基建', 'SH'),
    ('600528', '中铁工业', '基建', 'SH'),
    ('600662', '外服控股', '人力资源', 'SH'),
    ('600668', '尖峰集团', '水泥', 'SH'),
    ('600717', '天津港', '港口', 'SH'),
    ('600720', '祁连山', '水泥', 'SH'),
    ('600801', '华新水泥', '水泥', 'SH'),
    ('600823', '世茂股份', '房地产', 'SH'),
    ('600854', '春兰股份', '家电', 'SH'),
    ('601186', '中国铁建', '基建', 'SH'),
    ('601390', '中国中铁', '基建', 'SH'),
    ('601618', '中国中冶', '基建', 'SH'),
    ('601668', '中国建筑', '基建', 'SH'),
    ('601669', '中国电建', '基建', 'SH'),
    ('601789', '宁波建工', '基建', 'SH'),
    ('601800', '中国交建', '基建', 'SH'),
    ('601618', '中国中冶', '基建', 'SH'),
]


def add_missing_stocks(cursor) -> int:
    """添加缺失的股票到数据库"""
    added_count = 0

    # 获取现有股票代码
    cursor.execute("SELECT stock_code FROM stocks")
    existing_codes = set(row[0] for row in cursor.fetchall())

    # 添加缺失的股票
    for stock_code, stock_name, industry, market in POPULAR_STOCKS:
        if stock_code not in existing_codes:
            try:
                cursor.execute("""
                    INSERT INTO stocks (stock_code, stock_name, industry, market, status)
                    VALUES (%s, %s, %s, %s, 1)
                    ON DUPLICATE KEY UPDATE stock_name = VALUES(stock_name)
                """, (stock_code, stock_name, industry, market))
                added_count += 1
            except Exception as e:
                pass

    return added_count


def generate_demo_data() -> dict:
    """生成演示数据"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 先添加缺失的股票
    stocks_added = add_missing_stocks(cursor)
    conn.commit()
    print(f"新增 {stocks_added} 只股票")

    # 获取股票列表
    cursor.execute("SELECT stock_code, stock_name FROM stocks")
    stocks = cursor.fetchall()

    if not stocks:
        cursor.close()
        conn.close()
        return {
            "success": False,
            "message": "没有找到股票数据，请先添加股票",
            "stats": {"comments": 0, "sentiments": 0, "emotions": 0, "quotes": 0}
        }

    print(f"找到 {len(stocks)} 只股票")

    # 生成过去30天的数据
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    # 股票基础价格
    base_prices = {
        '000001': 12.5,
        '000002': 15.0,
        '600036': 35.0,
        '600519': 1800.0,
        '000651': 40.0,
        '300750': 180.0,
        '002475': 30.0,
        '600276': 45.0,
        '601318': 50.0,
        '000858': 160.0
    }

    total_comments = 0
    total_sentiments = 0
    total_emotions = 0
    total_quotes = 0

    for stock_code, stock_name in stocks:
        print(f"正在生成 {stock_name}({stock_code}) 的数据...")

        base_price = base_prices.get(stock_code, 50.0)
        current_price = base_price

        current_date = start_date
        while current_date <= end_date:
            # 跳过周末
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue

            # 每天生成20-50条评论
            daily_comments = random.randint(20, 50)

            # 决定当天的情绪倾向
            sentiment_bias = random.choice(['positive', 'negative', 'neutral'])

            pos_count, neu_count, neg_count = 0, 0, 0

            for _ in range(daily_comments):
                # 根据倾向决定情感
                r = random.random()
                if sentiment_bias == 'positive':
                    if r < 0.5:
                        sentiment = 'positive'
                    elif r < 0.8:
                        sentiment = 'neutral'
                    else:
                        sentiment = 'negative'
                elif sentiment_bias == 'negative':
                    if r < 0.5:
                        sentiment = 'negative'
                    elif r < 0.8:
                        sentiment = 'neutral'
                    else:
                        sentiment = 'positive'
                else:
                    if r < 0.4:
                        sentiment = 'neutral'
                    elif r < 0.7:
                        sentiment = 'positive'
                    else:
                        sentiment = 'negative'

                # 生成评论内容
                if sentiment == 'positive':
                    content = random.choice(POSITIVE_COMMENTS)
                elif sentiment == 'negative':
                    content = random.choice(NEGATIVE_COMMENTS)
                else:
                    content = random.choice(NEUTRAL_COMMENTS)

                content = f"[{stock_code}] {content}"

                platforms = ['eastmoney', 'xueqiu', 'sina']
                platform = random.choice(platforms)

                # 随机时间
                hour = random.randint(9, 22)
                minute = random.randint(0, 59)
                pub_time = current_date.replace(hour=hour, minute=minute)

                comment_id = f"{platform}_{stock_code}_{pub_time.strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"

                # 插入评论
                try:
                    cursor.execute("""
                        INSERT INTO comments (comment_id, platform, stock_code, content, content_clean,
                            author, publish_time, likes, replies, is_processed)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE content = VALUES(content)
                    """, (
                        comment_id, platform, stock_code,
                        content, content, f"用户{random.randint(10000, 99999)}",
                        pub_time, random.randint(0, 500), random.randint(0, 50),
                        1
                    ))
                    total_comments += 1

                    # 生成情感分析结果
                    if sentiment == 'positive':
                        positive_score = random.uniform(0.7, 0.95)
                        negative_score = random.uniform(0.02, 0.15)
                    elif sentiment == 'negative':
                        negative_score = random.uniform(0.7, 0.95)
                        positive_score = random.uniform(0.02, 0.15)
                    else:
                        positive_score = random.uniform(0.1, 0.3)
                        negative_score = random.uniform(0.1, 0.3)

                    neutral_score = 1 - positive_score - negative_score

                    cursor.execute("""
                        INSERT INTO sentiments (comment_id, label, confidence, positive_score,
                            neutral_score, negative_score, model_version)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE label = VALUES(label)
                    """, (
                        comment_id, sentiment,
                        max(positive_score, negative_score, neutral_score),
                        round(positive_score, 4),
                        round(neutral_score, 4),
                        round(negative_score, 4),
                        'bert-wwm-ext-demo'
                    ))
                    total_sentiments += 1

                    if sentiment == 'positive':
                        pos_count += 1
                    elif sentiment == 'negative':
                        neg_count += 1
                    else:
                        neu_count += 1

                except Exception as e:
                    pass

            # 生成每日情绪指标
            total_day = pos_count + neu_count + neg_count
            if total_day == 0:
                total_day = 1

            bull_index = round((pos_count / total_day) * 100, 2)
            bear_index = round((neg_count / total_day) * 100, 2)
            intensity = round(abs(pos_count - neg_count) / total_day, 4)
            temperature = round((pos_count - neg_count) / total_day * 100 + 50, 2)
            volatility = round(random.uniform(0.1, 0.5), 4)

            try:
                cursor.execute("""
                    INSERT INTO emotions (stock_code, stat_date, stat_hour, total_count,
                        positive_count, neutral_count, negative_count, bull_index, bear_index,
                        intensity, temperature, volatility)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE total_count = VALUES(total_count)
                """, (
                    stock_code, current_date.date(), None,
                    total_day, pos_count, neu_count, neg_count,
                    bull_index, bear_index, intensity, temperature, volatility
                ))
                total_emotions += 1
            except Exception as e:
                pass

            # 生成行情数据
            change_pct = random.uniform(-5, 5)
            close_price = round(current_price * (1 + change_pct / 100), 2)
            open_price = round(close_price * (1 + random.uniform(-1, 1) / 100), 2)
            high_price = round(max(open_price, close_price) * (1 + random.uniform(0, 2) / 100), 2)
            low_price = round(min(open_price, close_price) * (1 - random.uniform(0, 2) / 100), 2)

            try:
                cursor.execute("""
                    INSERT INTO quotes (stock_code, trade_date, open_price, close_price,
                        high_price, low_price, pre_close, change_amount, change_pct,
                        volume, amount, turnover_rate)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE close_price = VALUES(close_price)
                """, (
                    stock_code, current_date.date(), open_price,
                    close_price, high_price, low_price, current_price,
                    round(close_price - current_price, 2), round(change_pct, 4),
                    random.randint(100000, 5000000),
                    random.randint(1000000000, 50000000000),
                    round(random.uniform(0.5, 10), 4)
                ))
                total_quotes += 1
            except Exception as e:
                pass

            current_price = close_price
            current_date += timedelta(days=1)

        conn.commit()

    cursor.close()
    conn.close()

    return {
        "success": True,
        "message": f"演示数据生成成功，新增 {stocks_added} 只股票",
        "stats": {
            "stocks_added": stocks_added,
            "stocks_total": len(stocks),
            "comments": total_comments,
            "sentiments": total_sentiments,
            "emotions": total_emotions,
            "quotes": total_quotes
        }
    }


@router.post("/admin/init-demo", response_model=Response, summary="初始化演示数据")
async def init_demo_data(background_tasks: BackgroundTasks):
    """
    生成演示数据（模拟评论、情感分析、情绪指标）
    用于开发和测试
    """
    try:
        result = generate_demo_data()
        return Response(
            message=result["message"],
            data=result["stats"]
        )
    except Exception as e:
        return Response(code=500, message=f"生成演示数据失败: {str(e)}", data=None)


@router.get("/admin/data-status", response_model=Response, summary="获取数据状态")
async def get_data_status(db: Session = Depends(get_db)):
    """获取数据库中的数据统计"""
    try:
        # 统计各表数据量
        stock_count = db.query(Stock).count()
        comment_count = db.query(Comment).count()
        sentiment_count = db.query(Sentiment).count()
        emotion_count = db.query(Emotion).count()
        quote_count = db.query(Quote).count()

        return Response(data={
            "stocks": stock_count,
            "comments": comment_count,
            "sentiments": sentiment_count,
            "emotions": emotion_count,
            "quotes": quote_count,
            "has_data": comment_count > 0 and emotion_count > 0
        })
    except Exception as e:
        return Response(code=500, message=str(e), data=None)
