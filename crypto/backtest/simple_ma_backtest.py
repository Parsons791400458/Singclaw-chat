#!/usr/bin/env python3
"""
简化版 MA 回测脚本 - 用于调试 0 交易问题
功能：单 MA 策略，打印所有信号，验证回测流程
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json

# 配置
DATA_PATH = "/root/.openclaw/workspace/crypto/data/historical_data.csv"
INITIAL_CAPITAL = 100000
POSITION_SIZE = 0.1  # 每次使用 10% 资金

def load_data():
    """加载历史数据"""
    print(f"📂 加载数据：{DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    print(f"✅ 数据加载完成：{len(df)} 条记录")
    print(f"   时间范围：{df['date'].min()} ~ {df['date'].max()}")
    return df

def calculate_signals(df):
    """计算 MA 交叉信号"""
    print("\n📊 计算技术指标...")
    
    # 计算 MA
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['sma_50'] = df['close'].rolling(window=50).mean()
    
    # 计算信号
    df['signal'] = 0
    df['position'] = 0
    
    # 金叉 (买入信号): SMA20 上穿 SMA50
    df['golden_cross'] = (df['sma_20'] > df['sma_50']) & (df['sma_20'].shift(1) <= df['sma_50'].shift(1))
    
    # 死叉 (卖出信号): SMA20 下穿 SMA50
    df['death_cross'] = (df['sma_20'] < df['sma_50']) & (df['sma_20'].shift(1) >= df['sma_50'].shift(1))
    
    # 统计信号数量
    golden_count = df['golden_cross'].sum()
    death_count = df['death_cross'].sum()
    
    print(f"✅ 指标计算完成")
    print(f"   金叉信号数量：{golden_count}")
    print(f"   死叉信号数量：{death_count}")
    
    return df

def print_signal_details(df):
    """打印前 10 个信号的详细信息"""
    print("\n📋 前 10 个金叉信号详情:")
    golden_signals = df[df['golden_cross']].head(10)
    
    for idx, row in golden_signals.iterrows():
        print(f"   {row['date']}: 价格={row['close']:.2f}, SMA20={row['sma_20']:.2f}, SMA50={row['sma_50']:.2f}")
    
    print("\n📋 前 10 个死叉信号详情:")
    death_signals = df[df['death_cross']].head(10)
    
    for idx, row in death_signals.iterrows():
        print(f"   {row['date']}: 价格={row['close']:.2f}, SMA20={row['sma_20']:.2f}, SMA50={row['sma_50']:.2f}")

def simple_backtest(df):
    """简化回测"""
    print("\n💰 执行简化回测...")
    
    capital = INITIAL_CAPITAL
    position = 0
    trades = []
    
    for idx, row in df.iterrows():
        if pd.isna(row['sma_20']) or pd.isna(row['sma_50']):
            continue
        
        # 金叉：买入
        if row['golden_cross'] and position == 0:
            # 使用 10% 资金买入
            buy_amount = capital * POSITION_SIZE
            position = buy_amount / row['close']
            capital -= buy_amount
            
            trades.append({
                'date': row['date'],
                'type': 'BUY',
                'price': row['close'],
                'amount': position,
                'cost': buy_amount,
                'capital_remaining': capital
            })
            
            print(f"   🟢 买入：{row['date']} @ {row['close']:.2f}, 数量={position:.6f}, 花费={buy_amount:.2f}")
        
        # 死叉：卖出
        elif row['death_cross'] and position > 0:
            sell_value = position * row['close']
            capital += sell_value
            
            trades.append({
                'date': row['date'],
                'type': 'SELL',
                'price': row['close'],
                'amount': position,
                'value': sell_value,
                'capital_remaining': capital
            })
            
            print(f"   🔴 卖出：{row['date']} @ {row['close']:.2f}, 数量={position:.6f}, 收入={sell_value:.2f}")
            position = 0
    
    # 最终估值
    if position > 0:
        final_value = capital + position * df.iloc[-1]['close']
    else:
        final_value = capital
    
    profit = final_value - INITIAL_CAPITAL
    profit_pct = (profit / INITIAL_CAPITAL) * 100
    
    print(f"\n📊 回测结果:")
    print(f"   初始资金：${INITIAL_CAPITAL:,.2f}")
    print(f"   最终价值：${final_value:,.2f}")
    print(f"   总收益：${profit:,.2f} ({profit_pct:.2f}%)")
    print(f"   交易次数：{len(trades)}")
    
    return {
        'initial_capital': INITIAL_CAPITAL,
        'final_value': final_value,
        'profit': profit,
        'profit_pct': profit_pct,
        'trade_count': len(trades),
        'trades': trades
    }

def main():
    print("=" * 60)
    print("简化版 MA 回测脚本 - 调试 0 交易问题")
    print("=" * 60)
    
    # 1. 加载数据
    df = load_data()
    
    # 2. 计算信号
    df = calculate_signals(df)
    
    # 3. 打印信号详情
    print_signal_details(df)
    
    # 4. 执行回测
    results = simple_backtest(df)
    
    # 5. 保存结果
    output_path = "/root/.openclaw/workspace/crypto/backtest/simple_ma_results.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ 结果已保存：{output_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()
