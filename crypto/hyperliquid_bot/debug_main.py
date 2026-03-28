#!/usr/bin/env python3
"""
检查主账户余额
"""

from hyperliquid.info import Info
from hyperliquid.utils.constants import TESTNET_API_URL
import json

MAIN_ADDRESS = "0xD7C04b230f9f28d286Ba27216c103b1CFfC24126"

print(f"=" * 60)
print(f"查询主账户: {MAIN_ADDRESS}")
print(f"=" * 60)

info = Info(base_url=TESTNET_API_URL)

try:
    user_state = info.user_state(MAIN_ADDRESS)

    print("\n完整user_state结构:")
    print(json.dumps(user_state, indent=2))

    # 重点检查余额相关字段
    print("\n=== 余额字段检查 ===")

    margin = user_state.get("marginSummary", {})
    print(f"marginSummary.accountValue: {margin.get('accountValue')}")
    print(f"marginSummary.totalNtlPos: {margin.get('totalNtlPos')}")
    print(f"marginSummary.totalMarginUsed: {margin.get('totalMarginUsed')}")

    cross = user_state.get("crossMarginSummary", {})
    print(f"crossMarginSummary.accountValue: {cross.get('accountValue')}")

    print(f"withdrawable: {user_state.get('withdrawable')}")

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

    account_value = margin.get("accountValue")
    if account_value:
        account_value = float(account_value)
        print(f"\n账户总价值(accountValue): ${account_value:.2f}")

except Exception as e:
    print(f"查询失败: {e}")
    import traceback
    traceback.print_exc()
