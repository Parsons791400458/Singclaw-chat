#!/usr/bin/env python3
from hyperliquid.info import Info
from hyperliquid.utils.constants import TESTNET_API_URL
from eth_account import Account
import json

PRIVATE_KEY = '0xf76123c45691d1c94e9d7ab1ca49fae0cd0caa3e9c1afde91cea0ebb7a928f38'
account = Account.from_key(PRIVATE_KEY)
wallet = account.address

print('\n' + '='*60)
print('Agent钱包:', wallet)
print('='*60)

info = Info(base_url=TESTNET_API_URL)

state = info.user_state(wallet)

# 只输出关键信息
print('\n账户状态摘要:')
print('  accountValue:', state.get('marginSummary', {}).get('accountValue'))
print('  crossAccountValue:', state.get('crossMarginSummary', {}).get('accountValue'))
print('  withdrawable:', state.get('withdrawable'))
print('  持仓数量:', len(state.get('assetPositions', [])))

# 输出完整的JSON结构到文件
with open('/root/.openclaw/workspace/crypto/hyperliquid_bot/last_state.json', 'w') as f:
    json.dump(state, f, indent=2)

print('\n完整状态已保存到 last_state.json')
