"""
市场数据服务 - 获取A股行情数据
"""
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
from loguru import logger

from app.core.database import SessionLocal
from app.models.models import Stock, Quote


class MarketDataService:
    """
    市场数据服务
    
    使用AKShare获取A股行情数据
    """
    
    def __init__(self):
        self._akshare = None
    
    @property
    def ak(self):
        """延迟加载akshare"""
        if self._akshare is None:
            try:
                import akshare as ak
                self._akshare = ak
            except ImportError:
                logger.error("akshare not installed. Run: pip install akshare")
                raise
        return self._akshare
    
    def _convert_code(self, stock_code: str) -> str:
        """转换股票代码格式"""
        code = stock_code.replace("SH", "").replace("SZ", "").replace(".", "")
        return code
    
    def fetch_stock_list(self) -> List[Dict]:
        """
        获取A股股票列表
        """
        try:
            # 获取沪深A股列表
            df = self.ak.stock_zh_a_spot_em()
            
            stocks = []
            for _, row in df.iterrows():
                code = row['代码']
                name = row['名称']
                
                # 确定市场
                if code.startswith('6'):
                    market = 'SH'
                elif code.startswith(('0', '3')):
                    market = 'SZ'
                else:
                    market = ''
                
                stocks.append({
                    'stock_code': code,
                    'stock_name': name,
                    'market': market
                })
            
            logger.info(f"Fetched {len(stocks)} stocks from market")
            return stocks
            
        except Exception as e:
            logger.error(f"Fetch stock list error: {e}")
            return []
    
    def fetch_stock_history(self, stock_code: str, 
                           start_date: str, 
                           end_date: str) -> List[Dict]:
        """
        获取股票历史行情
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
        
        Returns:
            行情数据列表
        """
        code = self._convert_code(stock_code)
        
        try:
            df = self.ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"  # 前复权
            )
            
            if df.empty:
                return []
            
            quotes = []
            for _, row in df.iterrows():
                quotes.append({
                    'trade_date': row['日期'],
                    'open_price': float(row['开盘']),
                    'close_price': float(row['收盘']),
                    'high_price': float(row['最高']),
                    'low_price': float(row['最低']),
                    'volume': int(row['成交量']),
                    'amount': float(row['成交额']),
                    'change_pct': float(row['涨跌幅']),
                    'change_amount': float(row['涨跌额']),
                    'turnover_rate': float(row['换手率']) if '换手率' in row else None
                })
            
            logger.info(f"Fetched {len(quotes)} quotes for {stock_code}")
            return quotes
            
        except Exception as e:
            logger.error(f"Fetch stock history error for {stock_code}: {e}")
            return []
    
    def fetch_realtime_quote(self, stock_codes: List[str]) -> List[Dict]:
        """
        获取实时行情
        """
        try:
            df = self.ak.stock_zh_a_spot_em()
            
            codes = [self._convert_code(c) for c in stock_codes]
            df = df[df['代码'].isin(codes)]
            
            quotes = []
            for _, row in df.iterrows():
                quotes.append({
                    'stock_code': row['代码'],
                    'stock_name': row['名称'],
                    'price': float(row['最新价']) if row['最新价'] != '-' else None,
                    'change_pct': float(row['涨跌幅']) if row['涨跌幅'] != '-' else None,
                    'change_amount': float(row['涨跌额']) if row['涨跌额'] != '-' else None,
                    'volume': int(row['成交量']) if row['成交量'] != '-' else 0,
                    'amount': float(row['成交额']) if row['成交额'] != '-' else 0
                })
            
            return quotes
            
        except Exception as e:
            logger.error(f"Fetch realtime quote error: {e}")
            return []
    
    def save_quotes_to_db(self, stock_code: str, quotes: List[Dict]):
        """
        保存行情数据到数据库
        """
        db = SessionLocal()
        try:
            for q in quotes:
                trade_date = q['trade_date']
                if isinstance(trade_date, str):
                    trade_date = datetime.strptime(trade_date, '%Y-%m-%d').date()
                
                # 查找或创建
                existing = db.query(Quote).filter(
                    Quote.stock_code == stock_code,
                    Quote.trade_date == trade_date
                ).first()
                
                if existing:
                    existing.open_price = q['open_price']
                    existing.close_price = q['close_price']
                    existing.high_price = q['high_price']
                    existing.low_price = q['low_price']
                    existing.volume = q['volume']
                    existing.amount = q['amount']
                    existing.change_pct = q['change_pct']
                    existing.change_amount = q['change_amount']
                    existing.turnover_rate = q.get('turnover_rate')
                else:
                    quote = Quote(
                        stock_code=stock_code,
                        trade_date=trade_date,
                        open_price=q['open_price'],
                        close_price=q['close_price'],
                        high_price=q['high_price'],
                        low_price=q['low_price'],
                        volume=q['volume'],
                        amount=q['amount'],
                        change_pct=q['change_pct'],
                        change_amount=q['change_amount'],
                        turnover_rate=q.get('turnover_rate')
                    )
                    db.add(quote)
            
            db.commit()
            logger.info(f"Saved {len(quotes)} quotes for {stock_code}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Save quotes error: {e}")
        finally:
            db.close()
    
    def sync_stock_list(self):
        """
        同步股票列表到数据库
        """
        stocks = self.fetch_stock_list()
        
        db = SessionLocal()
        try:
            for s in stocks:
                existing = db.query(Stock).filter(
                    Stock.stock_code == s['stock_code']
                ).first()
                
                if not existing:
                    stock = Stock(
                        stock_code=s['stock_code'],
                        stock_name=s['stock_name'],
                        market=s['market'],
                        status=1
                    )
                    db.add(stock)
            
            db.commit()
            logger.info(f"Synced {len(stocks)} stocks")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Sync stock list error: {e}")
        finally:
            db.close()
    
    def sync_quotes(self, stock_code: str, days: int = 30):
        """
        同步股票近期行情
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        quotes = self.fetch_stock_history(
            stock_code,
            start_date.strftime('%Y%m%d'),
            end_date.strftime('%Y%m%d')
        )
        
        if quotes:
            self.save_quotes_to_db(stock_code, quotes)


# 服务单例
_market_service: Optional[MarketDataService] = None


def get_market_service() -> MarketDataService:
    """获取市场数据服务单例"""
    global _market_service
    if _market_service is None:
        _market_service = MarketDataService()
    return _market_service
