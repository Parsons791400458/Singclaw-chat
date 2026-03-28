#!/usr/bin/env python3
"""
测试Hyperliquid测试网下单功能
使用示例私钥在测试网执行下单操作
"""

import logging
import json
from datetime import datetime
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from hyperliquid.utils import constants
from eth_account import Account

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_order():
    """测试下单功能"""
    # 使用测试网私钥（示例，仅用于测试）
    TEST_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

    # 初始化账户
    account = Account.from_key(TEST_PRIVATE_KEY)
    wallet_address = account.address
    logging.info(f"钱包地址: {wallet_address}")

    # 创建Exchange客户端（测试网）
    exchange = Exchange(
        wallet=account,
        base_url=constants.TESTNET_API_URL
    )

    # 创建Info客户端
    info = Info(base_url=constants.TESTNET_API_URL)

    # 测试1: 查询账户状态
    try:
        logging.info("📊 查询账户状态...")
        user_state = info.user_state(wallet_address)
        logging.info(f"✅ 账户状态查询成功")
        if user_state and 'marginSummary' in user_state:
            account_value = user_state['marginSummary'].get('accountValue', 'N/A')
            logging.info(f"账户余额: {account_value} USDC")
    except Exception as e:
        logging.error(f"❌ 账户状态查询失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 测试2: 获取可用持仓
    try:
        logging.info("📈 获取当前持仓...")
        user_state = info.user_state(wallet_address)
        positions = []
        if user_state and 'assetPositions' in user_state:
            positions = user_state['assetPositions']
        logging.info(f"✅ 持仓查询成功")
        if positions:
            logging.info(f"当前持仓: {positions}")
        else:
            logging.info("当前无持仓")
    except Exception as e:
        logging.error(f"❌ 持仓查询失败: {e}")

    # 测试3: 尝试下单（小额BTC）
    try:
        logging.info("💰 准备测试下单...")

        # 下单参数 - 使用正确的币种名称和格式
        symbol = "BTC"  # Hyperliquid使用币种符号（如BTC），不是交易对
        is_buy = True  # 买入
        sz = 0.001     # 数量
        limit_px = 80000.0  # 限价（设置具体价格）
        order_type = {"limit": {"tif": "Gtc"}}  # 限价单，GTC

        logging.info(f"下单详情: {symbol} {'买入' if is_buy else '卖出'} {sz} @ ${limit_px}")

        # 执行下单
        order_result = exchange.order(
            name=symbol,
            is_buy=is_buy,
            sz=sz,
            limit_px=limit_px,
            order_type={"limit": {"tif": "Gtc"}}
        )

        logging.info(f"✅ 下单成功！")
        logging.info(f"订单响应: {order_result}")

        # 保存订单信息到日志
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "side": "buy",
            "size": sz,
            "price": limit_px,
            "order_id": order_result.get("orderId", "unknown") if isinstance(order_result, dict) else "unknown",
            "status": "submitted",
            "response": str(order_result)
        }

        with open('/root/.openclaw/workspace/crypto/logs/test_orders.jsonl', 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

        return True

    except Exception as e:
        logging.error(f"❌ 下单失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logging.info("=" * 60)
    logging.info("Hyperliquid测试网下单验证")
    logging.info("=" * 60)

    success = test_order()

    if success:
        logging.info("✅ 测试完成：所有功能正常！")
    else:
        logging.error("❌ 测试失败，请检查错误信息")
