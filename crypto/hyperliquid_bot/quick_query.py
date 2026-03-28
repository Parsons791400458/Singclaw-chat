#!/usr/bin/env python3
import sys
from hyperliquid.info import Info
from hyperliquid.utils.constants import TESTNET_API_URL
from eth_account import Account

PRIVATE_KEY = "0xf76123c45691d1c94e9d7ab1ca49fae0cd0caa3e9c1afde91cea0ebb7a928f38"
account = Account.from_key(PRIVATE_KEY)
wallet_address = account.address

print(f"查询地址: {wallet_address}")

info = Info(base_url=TESTNET_API_URL)

# 查询用户状态
user_state = info.user_state(wallet_address)

# 检查各种字段
print("\n=== 账户信息 ===")
print("所有顶层键:", list(user_state.keys()))

if 'marginSummary' in user_state:
    print("\nmarginSummary:", user_state['marginSummary'])
if 'crossMarginSummary' in user_state:
    print("crossMarginSummary:", user_state['crossMarginSummary'])
if 'withdrawable' in user_state:
    print("withdrawable:", user_state['withdrawable'])
if 'assetPositions' in user_state:
    positions = user_state['assetPositions']
    print(f"\nassetPositions 数量: {len(positions)}")
    for i, pos in enumerate(positions):
        position = pos.get('position', {})
        coin = position.get('coin', 'N/A')
        szi = position.get('szi', '0')
        entry = position.get('entryPx', 'N/A')
        pos_value = position.get('positionValue', '0')
        print(f"  [{i}] {coin}: 数量={szi}, 入场价={entry}, 价值={pos_value}")

# 计算总价值
total_value = 0.0
if 'marginSummary' in user_state:
    total_value += float(user_state['marginSummary'].get('accountValue', 0))
if 'assetPositions' in user_state:
    for pos in user_state['assetPositions']:
        pos_value = pos.get('position', {}).get('positionValue', 0)
        total_value += float(pos_value)

print(f"\n总权益 (估算): {total_value} USDC")
