
#!/usr/bin/env python3
# 加密市场自动巡检脚本，每30分钟执行一次
import os
import time
import requests
from dotenv import load_dotenv
from hyperliquid.info import Info
from hyperliquid.utils import constants

# 加载配置
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_GROUP_ID', '-1002263718459')  # 正确群ID，已验证
XIAOXIA_ADDRESS = '0xD7C04b230f9f28d286Ba27216c103b1CFfC24126'
CLAWFI_ADDRESS = '0x7478d07e8ee9a938225224c542f6f4656637bb98'

info = Info(constants.MAINNET_API_URL, skip_ws=True)

def send_telegram_message(text):
    """发送消息到Telegram"""
    if not TELEGRAM_BOT_TOKEN:
        print("未配置Telegram Bot Token，跳过推送")
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}
        res = requests.post(url, data=data)
        res.raise_for_status()
        print("消息推送成功")
        return True
    except Exception as e:
        print(f"消息推送失败: {e}")
        return False

def get_market_data():
    """获取市场数据"""
    try:
        # 主流币价格
        mids = info.all_mids()
        btc = float(mids.get('BTC', 0))
        eth = float(mids.get('ETH', 0))
        sol = float(mids.get('SOL', 0))
        
        # 恐惧贪婪指数
        fng_res = requests.get("https://api.alternative.me/fng/?limit=1", timeout=10).json()
        fng_value = fng_res['data'][0]['value']
        fng_class = fng_res['data'][0]['value_classification']
        
        return {
            "btc": int(round(btc, 0)),
            "eth": int(round(eth, 0)),
            "sol": round(sol, 1),
            "fng_value": fng_value,
            "fng_class": fng_class
        }
    except Exception as e:
        print(f"获取市场数据失败: {e}")
        return None

def get_account_state(address):
    """获取账户状态"""
    try:
        state = info.user_state(address)
        account_value = round(float(state['marginSummary']['accountValue']), 2)
        position_count = len(state['assetPositions'])
        return {
            "value": account_value,
            "positions": position_count
        }
    except Exception as e:
        print(f"获取账户状态失败: {e}")
        return None

def main():
    current_time = time.strftime("%Y-%m-%d %H:%M", time.localtime())
    print(f"[{current_time}] 开始执行巡检任务...")
    
    # 获取数据
    market_data = get_market_data()
    xiaoxia_state = get_account_state(XIAOXIA_ADDRESS)
    clawfi_state = get_account_state(CLAWFI_ADDRESS)
    
    if not market_data or not xiaoxia_state or not clawfi_state:
        print("数据获取失败，终止推送")
        return
    
    # 组装消息
    message = f"""📊 加密大盘速递 [{current_time}]
━━━━━━━━━━━━━━━━
🔥 BTC ${market_data['btc']:,} | ETH ${market_data['eth']:,} | SOL ${market_data['sol']}
😨 市场情绪: {market_data['fng_class']} ({market_data['fng_value']})
💰 账户状态:
- 小夏主网: ${xiaoxia_state['value']} | 持仓数: {xiaoxia_state['positions']}
- ClawFi主网: ${clawfi_state['value']} | 持仓数: {clawfi_state['positions']}
"""
    
    # 发送消息
    print("推送消息:\n", message)
    send_telegram_message(message)
    print("巡检任务执行完成")

if __name__ == "__main__":
    main()
