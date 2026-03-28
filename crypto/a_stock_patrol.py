
#!/usr/bin/env python3
# A股自动巡检脚本
import os
import time
import akshare as ak
import requests
from dotenv import load_dotenv

# 加载配置
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_GROUP_ID', '-1002263718459')  # 正确群ID

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

def get_a_stock_data():
    """获取A股大盘数据"""
    try:
        # 指数数据（新接口）
        sh_data = ak.stock_zh_index_daily(symbol="sh000001").iloc[-1]
        sz_data = ak.stock_zh_index_daily(symbol="sz399001").iloc[-1]
        cyb_data = ak.stock_zh_index_daily(symbol="sz399006").iloc[-1]
        
        # 涨跌幅计算
        sh_change = round((sh_data['close'] - sh_data['open'])/sh_data['open']*100, 2)
        sz_change = round((sz_data['close'] - sz_data['open'])/sz_data['open']*100, 2)
        cyb_change = round((cyb_data['close'] - cyb_data['open'])/cyb_data['open']*100, 2)
        
        # 涨跌家数
        market_info = ak.stock_a_gt()
        up = market_info['上涨家数'].iloc[0]
        down = market_info['下跌家数'].iloc[0]
        
        # 北向资金
        north_data = ak.stock_em_hsgt_north_net_flow_in()
        north_money = round(float(north_data['当日净流入'].iloc[-1]/100000000), 2)
        
        return {
            "sh": {"name": "上证指数", "price": round(float(sh_data['close']), 2), "change": sh_change},
            "sz": {"name": "深证成指", "price": round(float(sz_data['close']), 2), "change": sz_change},
            "cyb": {"name": "创业板指", "price": round(float(cyb_data['close']), 2), "change": cyb_change},
            "up": up,
            "down": down,
            "north_money": north_money
        }
    except Exception as e:
        print(f"获取A股数据失败: {e}")
        return None

def main():
    current_time = time.strftime("%Y-%m-%d %H:%M", time.localtime())
    print(f"[{current_time}] 开始执行A股巡检任务...")
    
    data = get_a_stock_data()
    if not data:
        # 获取失败用简化数据
        data = {
            "sh": {"name": "上证指数", "price": 0, "change": 0},
            "sz": {"name": "深证成指", "price": 0, "change": 0},
            "cyb": {"name": "创业板指", "price": 0, "change": 0},
            "up": 0,
            "down": 0,
            "north_money": 0
        }
    
    # 涨跌颜色标记
    def get_change_tag(change):
        return "📈" if change > 0 else "📉"
    
    message = f"""🇨🇳 A股大盘速递 [{current_time}]
━━━━━━━━━━━━━━━━
{get_change_tag(data['sh']['change'])} 上证指数: {data['sh']['price']} | {data['sh']['change']}%
{get_change_tag(data['sz']['change'])} 深证成指: {data['sz']['price']} | {data['sz']['change']}%
{get_change_tag(data['cyb']['change'])} 创业板指: {data['cyb']['price']} | {data['cyb']['change']}%
💸 北向资金: {data['north_money']}亿
📊 涨跌家数: {data['up']}涨 / {data['down']}跌
"""
    
    print("推送消息:\n", message)
    send_telegram_message(message)
    print("A股巡检任务执行完成")

if __name__ == "__main__":
    main()
