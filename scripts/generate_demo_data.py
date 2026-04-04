"""
生成演示数据脚本
为系统生成模拟的评论、情感分析结果和情绪指标数据
"""
import random
from datetime import datetime, timedelta
import pymysql

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'root',
    'database': 'stock_sentiment',
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

def generate_comment(stock_code: str, sentiment: str, pub_time: datetime) -> dict:
    """生成单条评论数据"""
    if sentiment == 'positive':
        content = random.choice(POSITIVE_COMMENTS)
    elif sentiment == 'negative':
        content = random.choice(NEGATIVE_COMMENTS)
    else:
        content = random.choice(NEUTRAL_COMMENTS)
    
    # 添加股票代码让评论更真实
    content = f"[{stock_code}] {content}"
    
    platforms = ['eastmoney', 'xueqiu', 'sina']
    platform = random.choice(platforms)
    
    comment_id = f"{platform}_{stock_code}_{pub_time.strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
    
    return {
        'comment_id': comment_id,
        'platform': platform,
        'stock_code': stock_code,
        'content': content,
        'content_clean': content,
        'author': f"用户{random.randint(10000, 99999)}",
        'publish_time': pub_time,
        'likes': random.randint(0, 500),
        'replies': random.randint(0, 50),
        'is_processed': 1
    }

def generate_sentiment(comment_id: str, sentiment: str) -> dict:
    """生成情感分析结果"""
    if sentiment == 'positive':
        positive_score = random.uniform(0.7, 0.95)
        negative_score = random.uniform(0.02, 0.15)
        neutral_score = 1 - positive_score - negative_score
    elif sentiment == 'negative':
        negative_score = random.uniform(0.7, 0.95)
        positive_score = random.uniform(0.02, 0.15)
        neutral_score = 1 - positive_score - negative_score
    else:
        neutral_score = random.uniform(0.5, 0.8)
        positive_score = random.uniform(0.1, (1 - neutral_score) * 0.6)
        negative_score = 1 - positive_score - neutral_score
    
    return {
        'comment_id': comment_id,
        'label': sentiment,
        'confidence': max(positive_score, negative_score, neutral_score),
        'positive_score': round(positive_score, 4),
        'neutral_score': round(neutral_score, 4),
        'negative_score': round(negative_score, 4),
        'model_version': 'bert-wwm-ext-demo'
    }

def generate_emotion(stock_code: str, stat_date: datetime.date, pos_count: int, neu_count: int, neg_count: int) -> dict:
    """生成情绪指标"""
    total = pos_count + neu_count + neg_count
    if total == 0:
        total = 1
    
    bull_index = round((pos_count / total) * 100, 2)
    bear_index = round((neg_count / total) * 100, 2)
    intensity = round(abs(pos_count - neg_count) / total, 4)
    temperature = round((pos_count - neg_count) / total * 100 + 50, 2)
    volatility = round(random.uniform(0.1, 0.5), 4)
    
    return {
        'stock_code': stock_code,
        'stat_date': stat_date,
        'stat_hour': None,  # 日级数据
        'total_count': total,
        'positive_count': pos_count,
        'neutral_count': neu_count,
        'negative_count': neg_count,
        'bull_index': bull_index,
        'bear_index': bear_index,
        'intensity': intensity,
        'temperature': temperature,
        'volatility': volatility
    }

def generate_quote(stock_code: str, trade_date: datetime.date, base_price: float) -> dict:
    """生成行情数据"""
    change_pct = random.uniform(-5, 5)
    close_price = round(base_price * (1 + change_pct / 100), 2)
    open_price = round(close_price * (1 + random.uniform(-1, 1) / 100), 2)
    high_price = round(max(open_price, close_price) * (1 + random.uniform(0, 2) / 100), 2)
    low_price = round(min(open_price, close_price) * (1 - random.uniform(0, 2) / 100), 2)
    
    return {
        'stock_code': stock_code,
        'trade_date': trade_date,
        'open_price': open_price,
        'close_price': close_price,
        'high_price': high_price,
        'low_price': low_price,
        'pre_close': base_price,
        'change_amount': round(close_price - base_price, 2),
        'change_pct': round(change_pct, 4),
        'volume': random.randint(100000, 5000000),
        'amount': random.randint(1000000000, 50000000000),
        'turnover_rate': round(random.uniform(0.5, 10), 4)
    }

def main():
    print("开始生成演示数据...")
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 获取股票列表
    cursor.execute("SELECT stock_code, stock_name FROM stocks")
    stocks = cursor.fetchall()
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
                
                # 随机时间
                hour = random.randint(9, 22)
                minute = random.randint(0, 59)
                pub_time = current_date.replace(hour=hour, minute=minute)
                
                # 生成评论
                comment = generate_comment(stock_code, sentiment, pub_time)
                
                # 插入评论
                try:
                    cursor.execute("""
                        INSERT INTO comments (comment_id, platform, stock_code, content, content_clean, 
                            author, publish_time, likes, replies, is_processed)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE content = VALUES(content)
                    """, (
                        comment['comment_id'], comment['platform'], comment['stock_code'],
                        comment['content'], comment['content_clean'], comment['author'],
                        comment['publish_time'], comment['likes'], comment['replies'],
                        comment['is_processed']
                    ))
                    total_comments += 1
                    
                    # 生成情感分析结果
                    sentiment_data = generate_sentiment(comment['comment_id'], sentiment)
                    cursor.execute("""
                        INSERT INTO sentiments (comment_id, label, confidence, positive_score, 
                            neutral_score, negative_score, model_version)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE label = VALUES(label)
                    """, (
                        sentiment_data['comment_id'], sentiment_data['label'],
                        sentiment_data['confidence'], sentiment_data['positive_score'],
                        sentiment_data['neutral_score'], sentiment_data['negative_score'],
                        sentiment_data['model_version']
                    ))
                    total_sentiments += 1
                    
                    if sentiment == 'positive':
                        pos_count += 1
                    elif sentiment == 'negative':
                        neg_count += 1
                    else:
                        neu_count += 1
                        
                except Exception as e:
                    pass  # 忽略重复数据
            
            # 生成每日情绪指标
            emotion = generate_emotion(stock_code, current_date.date(), pos_count, neu_count, neg_count)
            try:
                cursor.execute("""
                    INSERT INTO emotions (stock_code, stat_date, stat_hour, total_count, 
                        positive_count, neutral_count, negative_count, bull_index, bear_index,
                        intensity, temperature, volatility)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE total_count = VALUES(total_count)
                """, (
                    emotion['stock_code'], emotion['stat_date'], emotion['stat_hour'],
                    emotion['total_count'], emotion['positive_count'], emotion['neutral_count'],
                    emotion['negative_count'], emotion['bull_index'], emotion['bear_index'],
                    emotion['intensity'], emotion['temperature'], emotion['volatility']
                ))
                total_emotions += 1
            except Exception as e:
                pass
            
            # 生成行情数据
            quote = generate_quote(stock_code, current_date.date(), current_price)
            current_price = quote['close_price']  # 更新基础价格
            try:
                cursor.execute("""
                    INSERT INTO quotes (stock_code, trade_date, open_price, close_price,
                        high_price, low_price, pre_close, change_amount, change_pct,
                        volume, amount, turnover_rate)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE close_price = VALUES(close_price)
                """, (
                    quote['stock_code'], quote['trade_date'], quote['open_price'],
                    quote['close_price'], quote['high_price'], quote['low_price'],
                    quote['pre_close'], quote['change_amount'], quote['change_pct'],
                    quote['volume'], quote['amount'], quote['turnover_rate']
                ))
                total_quotes += 1
            except Exception as e:
                pass
            
            current_date += timedelta(days=1)
        
        conn.commit()
    
    cursor.close()
    conn.close()
    
    print("\n=== 数据生成完成 ===")
    print(f"评论数据: {total_comments} 条")
    print(f"情感分析: {total_sentiments} 条")
    print(f"情绪指标: {total_emotions} 条")
    print(f"行情数据: {total_quotes} 条")
    print("\n请刷新前端页面查看效果!")

if __name__ == '__main__':
    main()
