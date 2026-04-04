"""
AKShare股票行情数据同步脚本

从AKShare获取真实A股行情数据并同步到数据库
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional

import pymysql
import akshare as ak
import pandas as pd

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'root',
    'database': 'stock_sentiment',
    'charset': 'utf8mb4'
}


class QuotesSyncer:
    """股票行情同步器"""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """连接数据库"""
        self.conn = pymysql.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()
        print("数据库连接成功")
    
    def close(self):
        """关闭连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("数据库连接已关闭")
    
    def get_stock_list(self) -> List[tuple]:
        """获取数据库中的股票列表"""
        self.cursor.execute("SELECT stock_code, stock_name, market FROM stocks WHERE status = 1")
        return self.cursor.fetchall()
    
    def format_stock_code(self, stock_code: str, market: str) -> str:
        """
        格式化股票代码为AKShare格式
        AKShare使用纯数字代码
        """
        return stock_code
    
    def fetch_stock_history(
        self, 
        stock_code: str, 
        start_date: str, 
        end_date: str
    ) -> Optional[pd.DataFrame]:
        """
        获取股票历史行情
        
        Args:
            stock_code: 股票代码（如 000001）
            start_date: 开始日期（如 20240101）
            end_date: 结束日期（如 20240131）
        
        Returns:
            DataFrame或None
        """
        try:
            # 使用akshare获取日线数据
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"  # 前复权
            )
            
            if df is None or df.empty:
                print(f"  [{stock_code}] 未获取到数据")
                return None
            
            return df
            
        except Exception as e:
            print(f"  [{stock_code}] 获取数据失败: {e}")
            return None
    
    def save_quotes(self, stock_code: str, df: pd.DataFrame) -> int:
        """
        保存行情数据到数据库
        
        Returns:
            保存的记录数
        """
        count = 0
        
        for _, row in df.iterrows():
            try:
                # 解析数据
                trade_date = pd.to_datetime(row['日期']).date()
                open_price = float(row['开盘'])
                close_price = float(row['收盘'])
                high_price = float(row['最高'])
                low_price = float(row['最低'])
                volume = int(row['成交量'])
                amount = float(row['成交额'])
                
                # 计算涨跌
                change_pct = float(row['涨跌幅']) if '涨跌幅' in row else 0
                change_amount = float(row['涨跌额']) if '涨跌额' in row else 0
                turnover_rate = float(row['换手率']) if '换手率' in row else 0
                
                # 计算昨收
                pre_close = close_price - change_amount if change_amount else None
                
                # 插入或更新
                self.cursor.execute("""
                    INSERT INTO quotes (
                        stock_code, trade_date, open_price, close_price,
                        high_price, low_price, pre_close, change_amount,
                        change_pct, volume, amount, turnover_rate
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        open_price = VALUES(open_price),
                        close_price = VALUES(close_price),
                        high_price = VALUES(high_price),
                        low_price = VALUES(low_price),
                        pre_close = VALUES(pre_close),
                        change_amount = VALUES(change_amount),
                        change_pct = VALUES(change_pct),
                        volume = VALUES(volume),
                        amount = VALUES(amount),
                        turnover_rate = VALUES(turnover_rate)
                """, (
                    stock_code, trade_date, open_price, close_price,
                    high_price, low_price, pre_close, change_amount,
                    change_pct, volume, amount, turnover_rate
                ))
                count += 1
                
            except Exception as e:
                print(f"  保存记录失败: {e}")
                continue
        
        self.conn.commit()
        return count
    
    def sync_all_stocks(self, days: int = 90):
        """
        同步所有股票的行情数据
        
        Args:
            days: 同步最近多少天的数据
        """
        print("=" * 60)
        print("开始同步A股行情数据")
        print("=" * 60)
        
        self.connect()
        
        try:
            stocks = self.get_stock_list()
            print(f"共 {len(stocks)} 只股票需要同步\n")
            
            # 计算日期范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            start_str = start_date.strftime("%Y%m%d")
            end_str = end_date.strftime("%Y%m%d")
            
            print(f"同步日期范围: {start_str} ~ {end_str}\n")
            
            total_records = 0
            success_count = 0
            
            for stock_code, stock_name, market in stocks:
                print(f"正在同步: {stock_name}({stock_code})")
                
                # 获取数据
                df = self.fetch_stock_history(stock_code, start_str, end_str)
                
                if df is not None and not df.empty:
                    # 保存数据
                    count = self.save_quotes(stock_code, df)
                    total_records += count
                    success_count += 1
                    print(f"  成功同步 {count} 条记录")
                else:
                    print(f"  跳过（无数据）")
                
                print()
            
            print("=" * 60)
            print(f"同步完成！")
            print(f"成功股票: {success_count}/{len(stocks)}")
            print(f"总记录数: {total_records}")
            print("=" * 60)
            
        finally:
            self.close()
    
    def sync_single_stock(self, stock_code: str, days: int = 90):
        """同步单只股票"""
        print(f"同步股票 {stock_code} 的行情数据...")
        
        self.connect()
        
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            start_str = start_date.strftime("%Y%m%d")
            end_str = end_date.strftime("%Y%m%d")
            
            df = self.fetch_stock_history(stock_code, start_str, end_str)
            
            if df is not None and not df.empty:
                count = self.save_quotes(stock_code, df)
                print(f"成功同步 {count} 条记录")
            else:
                print("未获取到数据")
                
        finally:
            self.close()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="同步A股行情数据")
    parser.add_argument("--stock", type=str, help="指定股票代码（不指定则同步全部）")
    parser.add_argument("--days", type=int, default=90, help="同步最近多少天的数据（默认90天）")
    
    args = parser.parse_args()
    
    syncer = QuotesSyncer()
    
    if args.stock:
        syncer.sync_single_stock(args.stock, args.days)
    else:
        syncer.sync_all_stocks(args.days)


if __name__ == "__main__":
    main()
