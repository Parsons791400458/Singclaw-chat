#!/usr/bin/env python3
"""
准确查询Hyperliquid测试网账户余额和历史记录
"""

import logging
from hyperliquid.info import Info
from hyperliquid.utils.constants import TESTNET_API_URL
from eth_account import Account

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(message)s')

def check_account():
    # 使用示例私钥
    TEST_PRIVATE_KEY = '0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80'
    account = Account.from_key(TEST_PRIVATE_KEY)
    wallet_address = account.address

    logging.info(f"钱包地址: {wallet_address}")
    logging.info("=" * 60)

    # 创建Info客户端
    info = Info(base_url=TESTNET_API_URL)

    # 查询账户状态
    try:
        user_state = info.user_state(wallet_address)
        logging.info("\n📊 账户状态详情:")
        logging.info(f"完整数据: {user_state}")

        # 解析余额
        if 'marginSummary' in user_state:
            margin = user_state['marginSummary']
            logging.info(f"\n💰 余额信息:")
            logging.info(f"  accountValue: {margin.get('accountValue', 'N/A')} USD")
            logging.info(f"  totalMarginUsed: {margin.get('totalMarginUsed', 'N/A')} USD")
            logging.info(f"  totalNtlPos: {margin.get('totalNtlPos', 'N/A')} USD")
            logging.info(f"  totalRawUsd: {margin.get('totalRawUsd', 'N/A')} USD")

        # 解析持仓
        if 'assetPositions' in user_state:
            positions = user_state['assetPositions']
            logging.info(f"\n📈 当前持仓 ({len(positions)} 个):")
            for pos in positions:
                position = pos.get('position', {})
                coin = position.get('coin', 'N/A')
                szi = position.get('szi', 'N/A')
                entry = position.get('entryPx', 'N/A')
                value = position.get('positionValue', 'N/A')
                logging.info(f"  {coin}: 数量={szi}, 入场价={entry}, 价值={value} USD")

        # 可提款金额
        withdrawable = user_state.get('withdrawable', 'N/A')
        logging.info(f"\n💵 可提款: {withdrawable} USD")

    except Exception as e:
        logging.error(f"❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 查询历史成交记录
    try:
        logging.info("\n📜 历史成交记录:")
        fills = info.user_fills(wallet_address)
        if fills:
            logging.info(f"最近 {len(fills)} 笔成交:")
            for fill in fills[:10]:  # 只显示最近10笔
                logging.info(f"  {fill}")
        else:
            logging.info("无历史成交记录")
    except Exception as e:
        logging.error(f"❌ 查询历史成交失败: {e}")

if __name__ == "__main__":
    check_account()
