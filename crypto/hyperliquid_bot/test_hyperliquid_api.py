#!/usr/bin/env python3
"""测试Hyperliquid API - 获取SUI价格"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hyperliquid_api import HyperliquidAPI
import requests
import json

def test_hyperliquid_api():
    print("=== Hyperliquid API 测试 ===\n")
    
    # 从配置文件读取
    from config import TESTNET, API_KEY, api_secret
    
    # 初始化API
    api = HyperliquidAPI(API_KEY, api_secret, testnet=TESTNET)
    
    print(f"配置:")
    print(f" 测试网: {TESTNET}")
    print(f"API Key: {API_KEY[:10]}...{API_KEY[-4:]}")
    print(f"API Secret: {'已设置' if api_secret else '未设置'}")
    print()
    
    # 测试健康检查
    print("1. 健康检查:")
    try:
        response = requests.get(f"{api.base_url}/health", timeout=5)
        print(f"  状态码: {response.status_code}")
        if response.status_code == 200:
            print("  ✅ 通过")
        else:
            print("  ❌ 失败")
    except Exception as e:
        print(f"  ❌ 异常: {e}")
    print()
    
    # 测试SUI价格
    print("2. SUI价格获取:")
    try:
        response = requests.get(f"{api.base_url}/api/v1/markets/SUIUSDT/price", timeout=5)
        print(f"  状态码: {response.status_code}")
        if response.status_code == 200:
            # 尝试解析JSON
            try:
                data = response.json()
                price = data.get("price")
                print(f"  ✅ 成功")
                print(f"  SUI价格: ${price}")
            except:
                # 如果JSON解析失败，尝试其他方式
                print("  ❌ JSON解析失败")
                print(f"  响应内容: {response.text[:200]}...")
        else:
            print("  ❌ 失败")
    except Exception as e:
        print(f"  ❌ 异常: {e}")
    print()
    
    # 测试账户信息
    print("3. 账户信息:")
    try:
        response = requests.get(f"{api.base_url}/api/v1/account", timeout=5)
        print(f"  状态码: {response.status_code}")
        if response.status_code == 200:
            # 尝试解析JSON
            try:
                data = response.json()
                balance = data.get("totalBalance")
                print(f"  ✅ 成功")
                print(f"  账户余额: {balance}")
            except:
                print("  ❌ JSON解析失败")
                print(f"  响应内容: {response.text[:200]}...")
        else:
            print("  ❌ 失败")
    except Exception as e:
        print(f"  ❌ 异常: {e}")
    print()
    
    # 测试订单创建
    print("4. 订单创建 (测试):")
    try:
        order_data = {
            "symbol": "SUIUSDT",
            "side": "buy",
            "amount": 1.0,
            "type": "market",
            "reduceOnly": False
        }
        response = requests.post(
            f"{api.base_url}/api/v1/orders",
            json=order_data,
            timeout=5
        )
        print(f"  状态码: {response.status_code}")
        if response.status_code == 200:
            print("  ✅ 成功")
        else:
            print("  ❌ 失败")
    except Exception as e:
        print(f"  ❌ 异常: {e}")
    print()
    
    # 获取SUI价格的备用方法
    print("5. 备用价格来源:")
    try:
        response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=sui&vs_currencies=usd", timeout=10)
        print(f"  状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            price = data.get("sui", {}).get("usd")
            print(f"  ✅ CoinGecko SUI价格: ${price}")
        else:
            print("  ❌ CoinGecko失败")
    except Exception as e:
        print(f"  ❌ CoinGecko异常: {e}")
    print()
    
    # 获取SUI价格的备用方法2
    try:
        response = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=SUIUSDT", timeout=10)
        print(f"  状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            price = float(data.get("price", 0))
            print(f"  ✅ Binance SUI价格: ${price}")
        else:
            print("  ❌ Binance失败")
    except Exception as e:
        print(f"  ❌ Binance异常: {e}")

if __name__ == "__main__":
    test_hyperliquid_api()