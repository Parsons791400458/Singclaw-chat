"""
技术指标计算模块 - 实现RSI、MACD、均线等指标
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional, List, Dict

class TechnicalIndicators:
    """技术指标计算工具类"""
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """
        计算RSI (相对强弱指数)
        
        Args:
            prices: 收盘价序列
            period: 周期，默认14
            
        Returns:
            RSI值序列 (0-100)
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        计算MACD (异同移动平均线)
        
        Returns:
            (macd_line, signal_line, histogram)
        """
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
        """计算简单移动平均线"""
        return prices.rolling(window=period).mean()
    
    @staticmethod
    def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
        """计算指数移动平均线"""
        return prices.ewm(span=period).mean()
    
    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        计算布林带
        
        Returns:
            (upper_band, middle_band, lower_band)
        """
        middle_band = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        return upper_band, middle_band, lower_band
    
    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        计算ATR (平均真实波幅)
        
        Args:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            
        Returns:
            ATR值序列
        """
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        atr = true_range.rolling(window=period).mean()
        return atr
    
    @staticmethod
    def calculate_kdj(high: pd.Series, low: pd.Series, close: pd.Series,
                     k_period: int = 14, d_period: int = 3, j_period: int = 3) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        计算KDJ随机指标
        
        Returns:
            (k_line, d_line, j_line)
        """
        # 计算最高/low的滚动窗口
        highest_high = high.rolling(window=k_period).max()
        lowest_low = low.rolling(window=k_period).min()
        
        # 计算RSV
        rsv = (close - lowest_low) / (highest_high - lowest_low) * 100
        
        # 计算K线
        k_line = rsv.rolling(window=d_period).mean()
        
        # 计算D线
        d_line = k_line.rolling(window=d_period).mean()
        
        # 计算J线
        j_line = 3 * k_line - 2 * d_line
        
        return k_line, d_line, j_line
    
    @staticmethod
    def check_golden_cross(short: pd.Series, long: pd.Series, lookback: int = 3) -> bool:
        """
        检查是否金叉（短线上穿长线）
        
        Args:
            short: 短期线
            long: 长期线
            lookback: 检查最近几根K线
            
        Returns:
            是否发生金叉
        """
        if len(short) < lookback + 1 or len(long) < lookback + 1:
            return False
        
        # 检查是否当前short > long 且 前一个周期 short <= long
        for i in range(1, lookback + 1):
            if short.iloc[-i] > long.iloc[-i] and short.iloc[-i-1] <= long.iloc[-i-1]:
                return True
        return False
    
    @staticmethod
    def check_dead_cross(short: pd.Series, long: pd.Series, lookback: int = 3) -> bool:
        """
        检查是否死叉（短线下穿长线）
        """
        if len(short) < lookback + 1 or len(long) < lookback + 1:
            return False
        
        for i in range(1, lookback + 1):
            if short.iloc[-i] < long.iloc[-i] and short.iloc[-i-1] >= long.iloc[-i-1]:
                return True
        return False
    
    @staticmethod
    def calculate_indicators_from_klines(klines: List[Dict]) -> Dict:
        """
        从K线数据计算所有技术指标
        
        Args:
            klines: K线数据列表，每个元素包含:
                - open: 开盘价
                - high: 最高价
                - low: 最低价
                - close: 收盘价
                - volume: 成交量
                - timestamp: 时间戳
                
        Returns:
            包含所有指标的字典
        """
        if not klines:
            return {}
        
        # 转换为DataFrame
        df = pd.DataFrame(klines)
        df['close'] = pd.to_numeric(df['close'])
        df['high'] = pd.to_numeric(df['high'])
        df['low'] = pd.to_numeric(df['low'])
        df['volume'] = pd.to_numeric(df['volume'])
        
        # 计算各项指标
        indicators = {}
        
        # RSI
        indicators['rsi'] = TechnicalIndicators.calculate_rsi(df['close'])
        
        # MACD
        macd_line, signal_line, histogram = TechnicalIndicators.calculate_macd(df['close'])
        indicators['macd_line'] = macd_line
        indicators['signal_line'] = signal_line
        indicators['macd_histogram'] = histogram
        
        # 均线
        indicators['sma_20'] = TechnicalIndicators.calculate_sma(df['close'], 20)
        indicators['sma_50'] = TechnicalIndicators.calculate_sma(df['close'], 50)
        indicators['ema_12'] = TechnicalIndicators.calculate_ema(df['close'], 12)
        indicators['ema_26'] = TechnicalIndicators.calculate_ema(df['close'], 26)
        
        # ATR
        indicators['atr'] = TechnicalIndicators.calculate_atr(df['high'], df['low'], df['close'])
        
        # 布林带
        upper, middle, lower = TechnicalIndicators.calculate_bollinger_bands(df['close'])
        indicators['bb_upper'] = upper
        indicators['bb_middle'] = middle
        indicators['bb_lower'] = lower
        
        # KDJ
        k, d, j = TechnicalIndicators.calculate_kdj(df['high'], df['low'], df['close'])
        indicators['k_line'] = k
        indicators['d_line'] = d
        indicators['j_line'] = j
        
        # 最新值
        latest = {}
        for key, series in indicators.items():
            if not series.empty and not pd.isna(series.iloc[-1]):
                latest[key] = series.iloc[-1]
        
        return latest


# 测试代码
if __name__ == "__main__":
    print("技术指标计算模块测试")
    print("=" * 50)
    
    # 生成测试数据
    np.random.seed(42)
    n = 100
    prices = pd.Series(np.random.randn(n).cumsum() + 100)
    
    # 测试RSI
    rsi = TechnicalIndicators.calculate_rsi(prices)
    print(f"RSI最新值: {rsi.iloc[-1]:.2f}")
    
    # 测试MACD
    macd, signal, hist = TechnicalIndicators.calculate_macd(prices)
    print(f"MACD: {macd.iloc[-1]:.4f}, Signal: {signal.iloc[-1]:.4f}")
    
    # 测试均线
    sma20 = TechnicalIndicators.calculate_sma(prices, 20)
    print(f"SMA20: {sma20.iloc[-1]:.2f}")
    
    # 测试ATR
    high = prices + np.random.randn(n)
    low = prices - np.random.randn(n)
    atr = TechnicalIndicators.calculate_atr(high, low, prices)
    print(f"ATR: {atr.iloc[-1]:.4f}")
    
    print("\n✅ 所有指标计算正常")