
# 趋势跟踪策略 v1.0
# 小夏主网账户20天5倍收益挑战专用策略

import talib
import numpy as np
from hyperliquid.info import Info

class TrendFollowingStrategy:
    def __init__(self, info_client, config):
        self.info = info_client
        self.config = config
        self.allowed_assets = config['TRADING_RULES']['allowed_assets']
        self.leverage = config['TRADING_RULES']['leverage']
        
    def get_klines(self, asset, interval='1h', limit=60):
        """获取K线数据"""
        try:
            candles = self.info.candles_snapshot(asset, interval, limit)
            closes = np.array([float(c['close']) for c in candles], dtype=np.float64)
            return closes
        except Exception as e:
            print(f"获取{asset}K线失败: {e}")
            return None
    
    def generate_signal(self, asset):
        """生成交易信号：1=买入，-1=卖出，0=无信号"""
        closes = self.get_klines(asset)
        if closes is None or len(closes) < 50:
            return 0
            
        # 计算指标
        ma5 = talib.SMA(closes, timeperiod=5)[-1]
        ma20 = talib.SMA(closes, timeperiod=20)[-1]
        rsi = talib.RSI(closes, timeperiod=14)[-1]
        macd, signal, _ = talib.MACD(closes, fastperiod=12, slowperiod=26, signalperiod=9)
        
        # 买入信号：MA5上穿MA20 + RSI < 70 + MACD上穿信号线
        if ma5 > ma20 and rsi < 70 and macd[-1] > signal[-1] and macd[-2] <= signal[-2]:
            return 1
        # 卖出信号：MA5下穿MA20 + RSI > 30 + MACD下穿信号线
        elif ma5 < ma20 and rsi > 30 and macd[-1] < signal[-1] and macd[-2] >= signal[-2]:
            return -1
        else:
            return 0
    
    def calculate_position_size(self, account_value, asset_price):
        """计算仓位大小：单仓位最大30%净值"""
        max_position_value = account_value * self.config['TRADING_RULES']['max_position_size']
        size = (max_position_value * self.leverage) / asset_price
        # 保留小数精度
        return round(size, 4) if size > 0.001 else 0
