#!/usr/bin/env python3
"""
每日复盘脚本 - 分析当日交易、持仓变化、策略效果
"""
import json, time, os, requests
from datetime import datetime, timezone, timedelta
from hyperliquid.info import Info

tz8 = timezone(timedelta(hours=8))
LOG = "/root/.openclaw/workspace/crypto/logs/daily_review.log"

API_KEY = "gk_live_495c771f96a77997.468bfa28d307b2293120ef3fa6d5acac2fc41afe6b8625f9"
CLIENT_ID = "cli_3802f9db08b811f197679c63c078bacc"
HEADERS = {"Authorization": API_KEY, "X-Client-ID": CLIENT_ID, "Content-Type": "application/json"}
TOPIC_ID = "ongRlB9J"

ACCOUNTS = [
    {"name": "小夏", "addr": "0xD7C04b230f9f28d286Ba27216c103b1CFfC24126"},
    {"name": "ClawFi", "addr": "0x7478d07e8ee9a938225224c542f6f4656637bb98"}
]

def log(msg):
    ts = datetime.now(tz8).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")

def write_note(content, title):
    try:
        resp = requests.post("https://openapi.biji.com/open/api/v1/resource/note/save",
            headers=HEADERS, json={
                "title": title, "content": content,
                "note_type": "plain_text",
                "tags": ["每日复盘", "samh7914_bot", datetime.now(tz8).strftime("%Y%m%d")],
                "topic_ids": [TOPIC_ID]
            }, timeout=15)
        r = resp.json()
        if r.get('success'):
            log(f"✅ 笔记已写入知识库 (ID: {r['data']['id']})")
            return True
        else:
            log(f"❌ 笔记写入失败: {r.get('error')}")
            return False
    except Exception as e:
        log(f"❌ 笔记异常: {e}")
        return False

def run_review():
    log("=" * 50)
    log("每日复盘开始")
    
    info = Info(base_url="https://api.hyperliquid.xyz", skip_ws=True)
    mids = info.all_mids()
    now = datetime.now(tz8).strftime("%Y-%m-%d %H:%M:%S")
    today = datetime.now(tz8).strftime("%Y-%m-%d")
    
    # 读取今日交易记录
    trades_file = "/root/.openclaw/workspace/crypto/logs/trades.jsonl"
    today_trades = []
    if os.path.exists(trades_file):
        with open(trades_file, 'r') as f:
            for line in f:
                try:
                    t = json.loads(line.strip())
                    if t.get('time', '').startswith(today):
                        today_trades.append(t)
                except: pass
    
    # 读取信号扫描日志
    signal_file = "/root/.openclaw/workspace/crypto/logs/trading_engine.log"
    today_signals = []
    if os.path.exists(signal_file):
        with open(signal_file, 'r') as f:
            for line in f:
                if line.strip().startswith(f"[{today}"):
                    if "🟢" in line or "🔴" in line:
                        today_signals.append(line.strip())
    
    # 构建复盘内容
    content = f"# 每日复盘 | {today}\n\n"
    content += f"**时间**: {now} GMT+8  \n"
    content += f"**Agent**: samh7914_bot  \n\n"
    
    # 账户概览
    content += "---\n## 📊 账户概览\n\n"
    total_eq = 0
    for acc in ACCOUNTS:
        state = info.user_state(acc['addr'])
        eq = float(state['marginSummary']['accountValue'])
        total_eq += eq
        positions = [p['position'] for p in state['assetPositions'] if float(p['position']['szi']) != 0]
        total_pnl = sum(float(p['unrealizedPnl']) for p in positions)
        
        content += f"### {acc['name']}\n"
        content += f"- 净值: **${eq:.2f}**\n"
        content += f"- 持仓: {len(positions)} 个\n"
        content += f"- 浮盈/亏: ${total_pnl:.2f}\n\n"
        
        if positions:
            content += "| 币种 | 方向 | 数量 | 入场价 | 现价 | 浮盈 |\n"
            content += "|------|------|------|--------|------|------|\n"
            for p in positions:
                coin = p['coin']
                sz = float(p['szi'])
                side = 'LONG' if sz > 0 else 'SHORT'
                entry = float(p['entryPx'])
                mid = float(mids.get(coin, 0))
                pnl = float(p['unrealizedPnl'])
                content += f"| {coin} | {side} | {abs(sz):.4f} | ${entry:.2f} | ${mid:.2f} | ${pnl:.2f} |\n"
            content += "\n"
    
    content += f"**双账户总净值: ${total_eq:.2f}**\n\n"
    
    # 今日信号
    content += "---\n## 🎯 今日信号\n\n"
    if today_signals:
        for s in today_signals[-10:]:  # 最多显示10条
            # 提取关键信息
            if "🟢" in s:
                content += f"- 🟢 {s.split('🟢')[-1].strip()}\n" if '🟢' in s else f"- {s}\n"
            elif "🔴" in s:
                content += f"- 🔴 {s.split('🔴')[-1].strip()}\n" if '🔴' in s else f"- {s}\n"
    else:
        content += "今日无新信号\n"
    content += "\n"
    
    # 今日交易记录
    content += "---\n## 📋 今日交易记录\n\n"
    if today_trades:
        for t in today_trades:
            action = t.get('action', '?')
            coin = t.get('coin', '?')
            side = t.get('side', '')
            price = t.get('price', t.get('fill_price', 0))
            status = t.get('status', '')
            score = t.get('score', '')
            rsi = t.get('rsi', '')
            
            if action == 'paper_signal':
                extra = f" score={score} RSI={rsi}" if score else ""
                content += f"- 📝 [PAPER] {side} {coin} @${price:.4f}{extra}\n"
            elif action == 'open':
                content += f"- ✅ [OPEN] {side} {coin} @${price:.4f}\n"
            elif action == 'close':
                content += f"- 🔒 [CLOSE] {side} {coin}\n"
    else:
        content += "今日无交易记录（Paper模式，仅扫描信号）\n"
    content += "\n"
    
    # 市场概况
    content += "---\n## 🌐 市场概况\n\n"
    major = {'BTC': 'Bitcoin', 'ETH': 'Ethereum', 'SOL': 'Solana'}
    for coin, name in major.items():
        mid = float(mids.get(coin, 0))
        if mid > 0:
            content += f"- {name} ({coin}): ${mid:,.2f}\n"
    content += "\n"
    
    # 策略评估
    content += "---\n## 📈 策略评估\n\n"
    content += f"- 今日信号数: {len(today_signals)}\n"
    content += f"- 今日交易数: {len(today_trades)}\n"
    
    # 持仓盈亏分析
    for acc in ACCOUNTS:
        state = info.user_state(acc['addr'])
        positions = [p['position'] for p in state['assetPositions'] if float(p['position']['szi']) != 0]
        if positions:
            win = sum(1 for p in positions if float(p['unrealizedPnl']) > 0)
            lose = sum(1 for p in positions if float(p['unrealizedPnl']) <= 0)
            content += f"- {acc['name']} 持仓盈亏比: {win}盈/{lose}亏\n"
    
    content += "\n### 📋 明日关注\n"
    content += "- 检查4h K线是否有新信号\n"
    content += "- 关注BTC/ETH关键位突破\n"
    content += "- 复盘策略参数是否需要调整\n"
    
    # 写入笔记
    title = f"[每日复盘] {today} | 双账户${total_eq:.2f}"
    write_note(content, title)
    
    log("每日复盘完成")

if __name__ == "__main__":
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    run_review()
