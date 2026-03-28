#!/usr/bin/env python3
"""手动获取 SUI 价格 - 使用 CoinGecko 备用源"""

import requests
import json

def get_sui_price():
    print("=== SUI 价格查询 ===\n")
    
    # 方法1: CoinGecko
    print("方法1: CoinGecko API")
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=sui&vs_currencies=usd"
        response = requests.get(url, timeout=10)
        print(f"  状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            price = data.get("sui", {}).get("usd")
            print(f"  ✅ SUI价格: ${price}")
            return price
        else:
            print(f"  ❌ 失败: {response.text}")
    except Exception as e:
        print(f"  ❌ 异常: {e}")
    print()
    
    # 方法2: Binance (无需API Key)
    print("方法2: Binance Public API")
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=SUIUSDT"
        response = requests.get(url, timeout=10)
        print(f"  状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            price = float(data.get("price", 0))
            print(f"  ✅ SUI价格: ${price}")
            return price
        else:
            print(f"  ❌ 失败: {response.text}")
    except Exception as e:
        print(f"  ❌ 异常: {e}")
    print()
    
    return None

if __name__ == "__main__":
    price = get_sui_price()
    if price:
        print(f"\n最终价格: ${price}")
    else:
        print("\n❌ 无法获取SUI价格")
