#!/usr/bin/env python3
"""
使用真实Agent密钥验证Hyperliquid测试网
"""

import logging
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils.constants import TESTNET_API_URL
from eth_account import Account

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def verify_account():
    # 真实提供的密钥
    PRIVATE_KEY = "0xf76123c45691d1c94e9d7ab1ca49fae0cd0caa3e9c1afde91cea0ebb7a928f38"
    API_WALLET = "0x0B517B39505B6eB90ef2E95C5d5fd03650C3F208"
    MAIN_ADDRESS = "0xD7C04b230f9f28d286Ba27216c103b1CFfC24126"

    logging.info("=" * 60)
    logging.info("Hyperliquid真实账户验证")
    logging.info("=" * 60)

    # 初始化账户
    account = Account.from_key(PRIVATE_KEY)
    derived_address = account.address
    logging.info(f"私钥推导地址: {derived_address}")
    logging.info(f"API钱包地址: {API_WALLET}")
    logging.info(f"主账户地址: {MAIN_ADDRESS}")
    logging.info(f"地址匹配: {derived_address.lower() == API_WALLET.lower()}")

    # 创建Info客户端
    info = Info(base_url=TESTNET_API_URL)

    # 1. 查询API钱包状态
    try:
        logging.info("\n📊 查询API钱包状态...")
        user_state = info.user_state(API_WALLET)
        logging.info(f"✅ API钱包查询成功")

        margin_summary = user_state.get('marginSummary', {})
        account_value = margin_summary.get('accountValue', 'N/A')
        total_used = margin_summary.get('totalMarginUsed', 'N/A')
        logging.info(f"账户价值: {account_value} USDC")
        logging.info(f"已用保证金: {total_used} USDC")

        withdrawable = user_state.get('withdrawable', 'N/A')
        logging.info(f"可提款: {withdrawable}")

        # 持仓详情
        positions = user_state.get('assetPositions', [])
        logging.info(f"当前持仓数: {len(positions)}")
        for pos in positions:
            position = pos.get('position', {})
            coin = position.get('coin', 'N/A')
            szi = position.get('szi', '0')
            entry = position.get('entryPx', 'N/A')
            logging.info(f"  {coin}: 数量={szi}, 入场价={entry}")

    except Exception as e:
        logging.error(f"❌ API钱包查询失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 2. 查询主账户状态
    try:
        logging.info(f"\n📊 查询主账户状态...")
        main_state = info.user_state(MAIN_ADDRESS)
        logging.info(f"✅ 主账户查询成功")

        margin_summary = main_state.get('marginSummary', {})
        account_value = margin_summary.get('accountValue', 'N/A')
        logging.info(f"主账户价值: {account_value} USDC")

        positions = main_state.get('assetPositions', [])
        logging.info(f"主账户持仓数: {len(positions)}")

    except Exception as e:
        logging.error(f"❌ 主账户查询失败: {e}")

    # 3. 查询历史交易
    try:
        logging.info(f"\n📜 查询历史成交记录...")
        fills = info.user_fills(API_WALLET)
        logging.info(f"✅ 历史记录查询成功")
        logging.info(f"成交记录数: {len(fills) if isinstance(fills, list) else 'N/A'}")

        if isinstance(fills, list) and fills:
            latest = fills[-1]
            logging.info(f"最新成交: {latest}")

    except Exception as e:
        logging.error(f"❌ 历史记录查询失败: {e}")

    # 4. 尝试下单（使用Exchange客户端）
    try:
        logging.info(f"\n💰 测试下单功能...")
        exchange = Exchange(wallet=account, base_url=TESTNET_API_URL)

        # 查询资产元数据获取tick size
        meta = info.meta()
        btc_asset = info.name_to_asset('BTC')
        btc_info = next((a for a in meta['universe'] if info.name_to_asset(a['name']) == btc_asset), None)
        tick_size = 0.5 if btc_info is None else 10 ** (-btc_info['szDecimals'])
        logging.info(f"BTC tick size: {tick_size}")

        # 获取当前中价并调整为合法价格
        all_mids = info.all_mids()
        btc_mid = float(all_mids.get('BTC', 63170.0))
        # 调整价格到tick size的整数倍（向下取整避免rounding问题）
        adjusted_price = round(btc_mid / tick_size - 0.5) * tick_size
        logging.info(f"BTC当前中价: {btc_mid} → 调整后: {adjusted_price}")

        # 尝试下小额买单（确保数量也是合法的）
        sz = 0.0001  # 最小数量
        logging.info(f"下单参数: BTC 买入 {sz} @ {adjusted_price}")

        order_result = exchange.order(
            name="BTC",
            is_buy=True,
            sz=sz,
            limit_px=adjusted_price,
            order_type={"limit": {"tif": "Gtc"}}
        )
        logging.info(f"✅ 下单API调用成功")
        logging.info(f"订单响应: {order_result}")

    except Exception as e:
        logging.error(f"❌ 下单失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    logging.info("\n" + "=" * 60)
    logging.info("✅ 验证完成")
    return True

if __name__ == "__main__":
    import sys
    success = verify_account()
    sys.exit(0 if success else 1)
