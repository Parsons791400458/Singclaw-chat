#!/usr/bin/env python3
"""检查Hyperliquid API状态"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hyperliquid_api import HyperliquidAPI
import json

def check_api():
    print("=== Hyperliquid API 状态检查 ===\n")
    
    # 初始化
    api = HyperliquidAPI(testnet=True)
    
    # 检查基础设置
    print("基础配置:")
    print(f"  base_url: {api.base_url}")
    print(f"  api_key 配置: {'已设置' if api.api_key else '未设置'}")
    print()
    
    # 健康检查
    print("健康检查...")
    try:
        health = api.health_check()
        print(f"  结果: {'✅ 通过' if health else '❌ 失败'}")
    except Exception as e:
        print(f"  ❌ 异常: {e}")
    print()
    
    # 获取账户信息
    print("获取账户信息...")
    try:
        account = api.get_account_info()
        if account:
            print(f"  账户余额: {account.get('balance', 'N/A')}")
            print(f"  完整信息: {json.dumps(account, indent=2, ensure_ascii=False)}")
        else:
            print("  ❌ 返回空数据")
    except Exception as e:
        print(f"  ❌ 异常: {e}")
    print()

if __name__ == "__main__":
    check_api()
