#!/usr/bin/env python3
import json
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from hyperliquid.utils import constants
import eth_account

# 配置区域
PRIVATE_KEY = "0xf76123c45691d1c94e9d7ab1ca49fae0cd0caa3e9c1afde91cea0ebb7a928f38"
SYMBOL = "BTC"
IS_BUY = True
SIZE = 0.001
PRICE = 60000.0

def run_testnet_trade():
    # A. 初始化账户
    account = eth_account.Account.from_key(PRIVATE_KEY)
    address = account.address
    print(f"✅ 账户已就绪: {address}")

    # B. 初始化 Exchange (指向测试网)
    exchange = Exchange(account, constants.TESTNET_API_URL)

    # C. 初始化 Info (用于查余额)
    info = Info(constants.TESTNET_API_URL, skip_ws=True)

    try:
        # 1. 检查状态 (先打印完整结构)
        user_state = info.user_state(address)
        print("📦 user_state 完整结构:")
        print(json.dumps(user_state, indent=2))
        margin_summary = user_state.get("marginSummary", {})
        # 尝试多种可能的余额字段名
        withdrawable = (
            margin_summary.get("withdrawable")
            or margin_summary.get("availableBalance")
            or margin_summary.get("availableForWithdraw")
            or margin_summary.get("accountValue")
        )
        if withdrawable is not None:
            print(f"💰 当前可用保证金: {withdrawable} USDC")
        else:
            print("💰 未能识别余额字段，已在上方完整输出")

        # 2. 发送订单 (限价单, GTC)
        print(f"正在下单: {SYMBOL} | {'买入' if IS_BUY else '卖出'} | 价格: {PRICE} | 数量: {SIZE}")
        order_result = exchange.order(
            SYMBOL,
            IS_BUY,
            SIZE,
            PRICE,
            {"limit": {"tif": "Gtc"}}
        )

        # 3. 解析结果
        if order_result["status"] == "ok":
            status = order_result["response"]["data"]["statuses"][0]
            if "resting" in status:
                print(f"🎉 下单成功! 订单 ID: {status['resting']['oid']}")
            elif "error" in status:
                print(f"❌ 订单被拒绝: {status['error']}")
            else:
                print(f"⚠️ 未知响应: {status}")
        else:
            print(f"❌ 请求发送失败: {order_result}")

    except Exception as e:
        print(f"🔥 运行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_testnet_trade()