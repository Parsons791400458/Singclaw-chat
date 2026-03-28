
# Hyperliquid自动交易机器人 v2.0
# 小夏主网账户20天5倍收益挑战专用
import os
import time
import json
from dotenv import load_dotenv
from eth_account import Account
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants

# 导入配置与策略
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import ACCOUNTS, TRADING_RULES, ALERT_CONFIG
from strategy_v1 import TrendFollowingStrategy

# 加载环境变量
load_dotenv()
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
TELEGRAM_CHAT_ID = '-1002263718459'  # 正确群ID，交易信号推送到群
AUTO_TRADE = False  # 自动交易开关，False为人工确认模式

# 初始化客户端
account = Account.from_key(PRIVATE_KEY)
info = Info(constants.MAINNET_API_URL, skip_ws=True)
exchange = Exchange(account, constants.MAINNET_API_URL)
strategy = TrendFollowingStrategy(info, {'TRADING_RULES': TRADING_RULES})

def send_alert(message):
    """发送告警到Telegram"""
    try:
        import requests
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if bot_token:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
            requests.post(url, data=data)
        print(f"[ALERT] {message}")
    except Exception as e:
        print(f"发送告警失败: {e}")

def get_account_state():
    """获取账户状态"""
    state = info.clearinghouse_state(account.address)
    account_value = float(state['marginSummary']['accountValue'])
    positions = state['positions']
    position_map = {p['coin']: float(p['szi']) for p in positions}
    return account_value, position_map

def close_position(asset, current_size):
    """平仓"""
    try:
        is_buy = current_size < 0
        size = abs(current_size)
        order_res = exchange.market_open(asset, is_buy, size, None, reduce_only=True)
        if order_res['status'] == 'ok':
            send_alert(f"✅ 平仓成功: {asset} {size} 张")
            return True
        else:
            send_alert(f"❌ 平仓失败: {asset} {order_res}")
            return False
    except Exception as e:
        send_alert(f"❌ 平仓异常: {asset} {e}")
        return False

def open_position(asset, signal):
    """开仓"""
    try:
        account_value, _ = get_account_state()
        price = float(info.all_mids()[asset])
        size = strategy.calculate_position_size(account_value, price)
        if size <= 0:
            return False
            
        is_buy = signal == 1
        order_res = exchange.market_open(asset, is_buy, size, TRADING_RULES['leverage'])
        if order_res['status'] == 'ok':
            direction = "做多" if is_buy else "做空"
            send_alert(f"✅ 开仓成功: {asset} {direction} {size} 张，价格 ${round(price,2)}")
            return True
        else:
            send_alert(f"❌ 开仓失败: {asset} {order_res}")
            return False
    except Exception as e:
        send_alert(f"❌ 开仓异常: {asset} {e}")
        return False

def main():
    send_alert("🚀 自动交易机器人启动成功，开始执行小夏主网20天5倍收益挑战策略")
    print("机器人启动成功，开始扫描交易信号...")
    
    while True:
        try:
            account_value, position_map = get_account_state()
            print(f"[巡检] 当前账户净值: ${round(account_value,2)}，持仓数: {len(position_map)}")
            
            for asset in TRADING_RULES['allowed_assets']:
                signal = strategy.generate_signal(asset)
                current_size = position_map.get(asset, 0)
                
                # 有持仓且信号反转：平仓
                if current_size != 0:
                    if (current_size > 0 and signal == -1) or (current_size < 0 and signal == 1):
                        if AUTO_TRADE:
                            close_position(asset, current_size)
                        else:
                            direction = "平多" if current_size > 0 else "平空"
                            price = float(info.all_mids()[asset])
                            send_alert(f"⚠️ 平仓信号触发：{asset} {direction}\n当前价格：${round(price,2)}\n请确认是否执行平仓操作！")
                # 无持仓且有信号：开仓
                elif current_size == 0 and signal != 0:
                    if AUTO_TRADE:
                        open_position(asset, signal)
                    else:
                        direction = "做多" if signal == 1 else "做空"
                        price = float(info.all_mids()[asset])
                        account_value, _ = get_account_state()
                        size = strategy.calculate_position_size(account_value, price)
                        send_alert(f"⚠️ 开仓信号触发：{asset} {direction}\n当前价格：${round(price,2)}\n预计开仓数量：{size}张\n请确认是否执行开仓操作！")
                    
            # 每5分钟扫描一次
            time.sleep(300)
            
        except Exception as e:
            send_alert(f"⚠️ 机器人异常: {str(e)}，5分钟后重试")
            time.sleep(300)

if __name__ == "__main__":
    main()
