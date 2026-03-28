#!/usr/bin/env python3
"""
调试Hyperliquid账户余额查询
"""

from hyperliquid.info import Info
from hyperliquid.utils.constants import TESTNET_API_URL
from eth_account import Account
import json

PRIVATE_KEY = "0xf76123c45691d1c94e9d7ab1ca49fae0cd0caa3e9c1afde91cea0ebb7a928f38"

# 使用私钥推导地址
account = Account.from_key(PRIVATE_KEY)
wallet_address = account.address

print(f"=" * 60)
print(f"查询地址: {wallet_address}")
print(f"=" * 60)

info = Info(base_url=TESTNET_API_URL)

try:
    user_state = info.user_state(wallet_address)

    # 打印完整JSON结构
    print("\n完整user_state结构:")
    print(json.dumps(user_state, indent=2))

    # 重点检查余额相关字段
    print("\n=== 余额字段检查 ===")

    # 1. marginSummary
    margin = user_state.get("marginSummary", {})
    print(f"marginSummary.accountValue: {margin.get('accountValue')}")
    print(f"marginSummary.totalNtlPos: {margin.get('totalNtlPos')}")
    print(f"marginSummary.totalMarginUsed: {margin.get('totalMarginUsed')}")

    # 2. crossMarginSummary
    cross = user_state.get("crossMarginSummary", {})
    print(f"crossMarginSummary.accountValue: {cross.get('accountValue')}")
    print(f"crossMarginSummary.totalNtlPos: {cross.get('totalNtlPos')}")

    # 3. withdrawable
    print(f"withdrawable: {user_state.get('withdrawable')}")

    # 4. 检查所有持仓
    positions = user_state.get("assetPositions", [])
    print(f"\n持仓数量: {len(positions)}")

    total_position_value = 0
    for i, pos in enumerate(positions):
        position = pos.get("position", {})
        coin = position.get("coin", "N/A")
        szi = position.get("szi", "0")
        entry = position.get("entryPx", "N/A")
        pos_value = position.get("positionValue", "0")
        total_position_value += float(pos_value) if pos_value else 0

        print(f"  持仓{i+1}: {coin}")
        print(f"    数量: {szi}")
        print(f"    入场价: {entry}")
        print(f"    持仓价值: {pos_value}")

    print(f"\n持仓总价值: {total_position_value}")

    # 5. 计算总权益
    account_value = margin.get("accountValue")
    if account_value:
        account_value = float(account_value)
        print(f"\n账户总价值(accountValue): ${account_value:.2f}")
        print(f"= 持仓价值(${total_position_value:.2f}) + 可用余额(${account_value - total_position_value:.2f})")

except Exception as e:
    print(f"查询失败: {e}")
    import traceback
    traceback.print_exc()
