#!/usr/bin/env python3
"""
Crypto Historical Data Fetcher
从 Binance API 获取 BTC/ETH 历史数据（日线，2 年）
Binance 公共 API 无需认证，更稳定可靠
"""

import requests
import pandas as pd
import json
from datetime import datetime, timedelta
import time
import os

BINANCE_API = "https://api.binance.com/api/v3"

def get_klines_data(symbol, interval="1d", limit=1000):
    """从 Binance 获取 K 线数据"""
    url = f"{BINANCE_API}/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Binance API error: {response.status_code} - {response.text}")
    data = response.json()
    return data

def process_klines_data(klines, symbol):
    """处理 Binance K 线数据为 DataFrame"""
    # Binance K 线格式：[开仓时间，开盘价，最高价，最低价，收盘价，成交量，...]
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades', 'taker_buy_base',
        'taker_buy_quote', 'ignore'
    ])
    
    # 转换时间戳
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df.set_index('date')
    
    # 转换数值类型
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = df[col].astype(float)
    
    # 添加币种标识
    df['symbol'] = symbol
    
    # 计算技术指标
    df['returns'] = df['close'].pct_change()
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['sma_50'] = df['close'].rolling(window=50).mean()
    df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = df['ema_12'] - df['ema_26']
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['rsi'] = calculate_rsi(df['close'], period=14)
    df['bollinger_upper'], df['bollinger_middle'], df['bollinger_lower'] = calculate_bollinger_bands(df['close'], period=20)
    df['atr'] = calculate_atr(df)
    
    return df

def calculate_rsi(prices, period=14):
    """计算 RSI 指标"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_bollinger_bands(prices, period=20, std_multiplier=2):
    """计算布林带"""
    middle = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper = middle + (std * std_multiplier)
    lower = middle - (std * std_multiplier)
    return upper, middle, lower

def calculate_atr(df, period=14):
    """计算 ATR（平均真实波幅）"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    high_low = high - low
    high_close = abs(high - close.shift(1))
    low_close = abs(low - close.shift(1))
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()
    return atr

def main():
    print("🚀 开始获取历史数据 (Binance API)...")
    
    # 确保输出目录存在
    output_dir = "/root/.openclaw/workspace/crypto/data"
    os.makedirs(output_dir, exist_ok=True)
    
    # 定义要获取的交易对
    symbols = {
        'BTCUSDT': 'BTC',
        'ETHUSDT': 'ETH',
        'SOLUSDT': 'SOL'
    }
    
    all_data = []
    
    for symbol, name in symbols.items():
        print(f"📥 获取 {name} 历史数据...")
        try:
            # 获取 K 线数据 (最多 1000 条/次)
            klines = get_klines_data(symbol, interval="1d", limit=1000)
            df = process_klines_data(klines, name)
            all_data.append(df)
            
            # 保存单个币种数据
            single_file = f"{output_dir}/{name}_historical_data.csv"
            df.to_csv(single_file)
            print(f"✅ {name} 数据获取完成 ({len(df)} 条) -> {single_file}")
            
            time.sleep(0.5)  # 避免 API 限流
        except Exception as e:
            print(f"❌ {name} 数据获取失败：{e}")
    
    if all_data:
        combined_df = pd.concat(all_data)
        output_file = f"{output_dir}/historical_data.csv"
        combined_df.to_csv(output_file)
        print(f"\n✅ 数据保存至：{output_file}")
        print(f"📊 总数据量：{len(combined_df)} 条")
        print(f"📈 数据时间范围：{combined_df.index[0]} 至 {combined_df.index[-1]}")
        
        # 数据质量报告
        print("\n📋 数据质量报告:")
        print(f"   - BTC 记录数：{len(all_data[0])}")
        print(f"   - ETH 记录数：{len(all_data[1]) if len(all_data) > 1 else 'N/A'}")
        print(f"   - SOL 记录数：{len(all_data[2]) if len(all_data) > 2 else 'N/A'}")
        print(f"   - 缺失值检查：{combined_df.isnull().sum().sum()} 个空值")
    else:
        print("❌ 无有效数据获取")

if __name__ == "__main__":
    main()
