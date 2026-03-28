#!/usr/bin/env python3
"""
自动交易引擎 v2 - Paper Trading
基于优化回测参数：4h周期, 信号门槛0.6, 成交量过滤, 保证金上限15%
"""
import json, time, math, sys, os
from datetime import datetime, timezone, timedelta
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from eth_account import Account

tz8 = timezone(timedelta(hours=8))

# ============ 配置 ============
CLAWFI_KEY = "502806e92f57d670cebd173166819dc3082f03d04ed1be9d3c17eb3ae8146e24"
CLAWFI_ADDR = "0x7478d07e8ee9a938225224c542f6f4656637bb98"
# 小夏钱包 - 待用户提供后填入
XIAOXIA_KEY = os.environ.get("XIAOXIA_PRIVATE_KEY", "")
XIAOXIA_ADDR = "0xD7C04b230f9f28d286Ba27216c103b1CFfC24126"

INITIAL_CAPITAL = 300.0
# 通用配置
MAX_POSITIONS = 5
MAX_DAILY_LOSS_STREAK = 3
VOLUME_FILTER = True

# ============ 账户策略区分 ============
# 小夏账户：20天5倍激进趋势策略
XIAOXIA_CONFIG = {
    "MAX_RISK_PER_TRADE": 0.05,
    "DEFAULT_LEVERAGE": 5,
    "STOP_ATR_MULT": 1.8,
    "TP_ATR_MULT": 3.5,
    "DAILY_LOSS_LIMIT": 0.08,
    "SIGNAL_THRESHOLD": 0.4,
    "MAX_MARGIN_PCT": 0.2,
    "CANDLE_INTERVAL": "2h"
}
# ClawFi账户：极端短线策略（按要求调整）
CLAWFI_CONFIG = {
    "MAX_RISK_PER_TRADE": 0.08,
    "DEFAULT_LEVERAGE": 7,
    "STOP_ATR_MULT": 1.5,
    "TP_ATR_MULT": 2.0,
    "DAILY_LOSS_LIMIT": 0.1,
    "SIGNAL_THRESHOLD": 0.3,
    "MAX_MARGIN_PCT": 0.25,
    "CANDLE_INTERVAL": "1h"
}

COINS = ["BTC", "ETH", "SOL", "AVAX", "APT", "ATOM", "SUI", "JUP"]

GETNOTE_API_KEY = "gk_live_495c771f96a77997.468bfa28d307b2293120ef3fa6d5acac2fc41afe6b8625f9"
GETNOTE_CLIENT_ID = "cli_3802f9db08b811f197679c63c078bacc"
GETNOTE_TOPIC_ID = "ongRlB9J"
GETNOTE_HEADERS = {
    "Authorization": GETNOTE_API_KEY,
    "X-Client-ID": GETNOTE_CLIENT_ID,
    "Content-Type": "application/json"
}

LOG_FILE = "/root/.openclaw/workspace/crypto/logs/trading_engine.log"
TRADES_FILE = "/root/.openclaw/workspace/crypto/logs/trades.jsonl"

def log(msg):
    ts = datetime.now(tz8).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + "\n")

def save_trade(trade):
    os.makedirs(os.path.dirname(TRADES_FILE), exist_ok=True)
    with open(TRADES_FILE, 'a') as f:
        f.write(json.dumps(trade, ensure_ascii=False) + "\n")

# ============ 指标 ============
def calc_sma(vals, p):
    return sum(vals[-p:]) / p if len(vals) >= p else None

def calc_rsi(closes, p=14):
    if len(closes) < p + 1: return None
    d = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    g = [max(0, x) for x in d[-p:]]
    l = [max(0, -x) for x in d[-p:]]
    ag, al = sum(g)/p, sum(l)/p
    return 100 - (100 / (1 + ag/al)) if al else 100

def calc_atr(candles, p=14):
    if len(candles) < p + 1: return None
    trs = []
    for i in range(1, len(candles)):
        h, l, pc = float(candles[i]['h']), float(candles[i]['l']), float(candles[i-1]['c'])
        trs.append(max(h-l, abs(h-pc), abs(l-pc)))
    return sum(trs[-p:]) / p

def calc_macd(closes):
    if len(closes) < 26: return None, None
    e12, e26, pe12, pe26 = closes[0], closes[0], closes[0], closes[0]
    for i, c in enumerate(closes):
        e12 = e12 * 11/13 + c * 2/13
        e26 = e26 * 25/27 + c * 2/27
        if i < len(closes) - 1:
            pe12 = pe12 * 11/13 + c * 2/13
            pe26 = pe26 * 25/27 + c * 2/27
    return e12 - e26, (pe12 - pe26)

def get_funding(flist, ts):
    """获取费率 + 变化率 + 历史均值"""
    rates = []
    for f in flist:
        if f['time'] <= ts: rates.append(float(f['fundingRate']))
        else: break
    if not rates: return 0, 0, 0
    cur = rates[-1]
    recent = rates[-3:] if len(rates) >= 3 else rates
    older = rates[-6:-3] if len(rates) >= 6 else rates[:max(0, len(rates)-3)]
    avg_r = sum(recent) / len(recent) if recent else 0
    avg_o = sum(older) / len(older) if older else 0
    return cur, avg_r - avg_o, sum(rates) / len(rates)

def generate_signal(candles, funding_list, idx):
    """v2+v3 混合信号: 趋势35% + RSI20% + MACD15% + 费率30%"""
    closes = [float(c['c']) for c in candles[:idx+1]]
    volumes = [float(c['v']) for c in candles[:idx+1]]
    if len(closes) < 50: return 0, {}
    
    ma20 = calc_sma(closes, 20)
    ma50 = calc_sma(closes, 50)
    rsi = calc_rsi(closes, 14)
    atr = calc_atr(candles[:idx+1], 14)
    dif, prev_dif = calc_macd(closes)
    
    if any(x is None for x in [ma20, ma50, rsi, atr, dif, prev_dif]):
        return 0, {}
    
    ts = candles[idx]['t']
    funding, funding_chg, funding_avg = get_funding(funding_list, ts)
    
    score = 0
    extreme = None
    
    # v3: 费率信号 (30%) - 核心改进
    # Hyperliquid 费率是每8小时结算一次
    # 极端负费率 = 空头过度拥挤，此时趋势可能仍是下跌
    # 所以极端费率时降低趋势权重，让费率主导
    
    if funding<-0.0005:  # 🔥超极端: <-0.05%/8h = -0.15%/天
        score += 0.95
        extreme = "🔥超极端负费率_LONG"
        if funding_chg<-0.0003:
            score += 0.15
            extreme = "🔥🔥加速恶化_LONG"
    elif funding<-0.0003:  # ⚡极端: <-0.03%/8h = -0.09%/天 (ATOM常见)
        score += 0.80
        extreme = "⚡极端负费率_LONG"
        if funding_chg<-0.0002:
            score += 0.15
            extreme = "⚡⚡加速负费率_LONG"
    elif funding<-0.0001:  # 负费率: <-0.01%/8h = -0.03%/天
        score += 0.45
        extreme = "负费率_LONG"
        if funding_chg<-0.0001:
            score += 0.10
            extreme = "恶化负费率_LONG"
    elif funding>0.0003:  # 极端正费率: >+0.03%/8h
        score -= 0.80
        extreme = "⚡极端正费率_SHORT"
        if funding_chg>0.0002:
            score -= 0.15
            extreme = "⚡⚡加速正费率_SHORT"
    else:  # 普通费率
        if funding>0.0001: score += 0.15
        elif funding<-0.0001: score -= 0.15
    
    # 趋势 (35%) — 极端费率时降低趋势权重（费率>趋势）
    if extreme:
        score += 0.15 if ma20 > ma50 else -0.15  # 极端时趋势权重降至15%
    else:
        score += 0.35 if ma20 > ma50 else -0.35  # 正常趋势权重35%
    
    # RSI (20%)
    if rsi < 30: score += 0.20
    elif rsi > 70: score -= 0.20
    elif rsi < 40: score += 0.08
    elif rsi > 60: score -= 0.08
    
    # MACD (15%)
    if dif > 0 and dif > prev_dif: score += 0.15
    elif dif < 0 and dif < prev_dif: score -= 0.15
    
    # v3: 费率信号 (30%) - 核心改进
    # Hyperliquid 费率是每8小时结算一次
    # -0.01%/8h = -0.03%/天 (普通负费率)
    # -0.03%/8h = -0.09%/天 (极端负费率，ATOM常见)
    # -0.05%/8h = -0.15%/天 (超极端，30天仅7次)
    # 用户参考: -0.1%/小时 = -0.8%/8h = -2.4%/天 (理论上极端，HL上尚未出现)
    
    if funding < -0.0005:  # 超极端: <-0.05%/8h = -0.15%/天
        score += 0.95
        extreme = "🔥超极端负费率_LONG"
        if funding_chg < -0.0003:
            score += 0.15
            extreme = "🔥🔥加速恶化_LONG"
    elif funding < -0.0003:  # 极端: <-0.03%/8h = -0.09%/天 (ATOM常见)
        score += 0.80
        extreme = "⚡极端负费率_LONG"
        if funding_chg < -0.0002:
            score += 0.15
            extreme = "⚡⚡加速负费率_LONG"
    elif funding < -0.0001:  # 负费率: <-0.01%/8h = -0.03%/天
        score += 0.45
        extreme = "负费率_LONG"
        if funding_chg < -0.0001:
            score += 0.10
            extreme = "恶化负费率_LONG"
    elif funding > 0.0003:  # 极端正费率: >+0.03%/8h
        score -= 0.80
        extreme = "⚡极端正费率_SHORT"
        if funding_chg > 0.0002:
            score -= 0.15
            extreme = "⚡⚡加速正费率_SHORT"
    else:  # 普通费率
        if funding > 0.0001: score += 0.15
        elif funding < -0.0001: score -= 0.15
    
    # 成交量过滤
    if VOLUME_FILTER:
        va = calc_sma(volumes, 20)
        if va and va > 0 and volumes[-1] < va * 0.8:
            return 0, {}
    
    details = {
        'ma20': ma20, 'ma50': ma50, 'rsi': rsi, 'atr': atr,
        'dif': dif, 'prev_dif': prev_dif,
        'funding': funding, 'funding_chg': funding_chg,
        'score': score, 'extreme': extreme
    }
    
    # 极端费率信号降低门槛 (0.4 vs 普通0.6)
    threshold = 0.4 if extreme else 0.3
    
    if score > threshold: return 1, details
    elif score < -threshold: return -1, details
    return 0, details

# ============ 交易执行 ============
def place_order(exchange, coin, side, size, price, sl, tp):
    """下单并设置止损止盈"""
    try:
        # 根据精度舍入
        price = round_price(price, coin)
        sl = round_price(sl, coin)
        tp = round_price(tp, coin)
        
        # 市价单（带滑点）
        is_buy = side == 1
        if is_buy:
            exec_price = price * 1.002  # buy稍高
        else:
            exec_price = price * 0.998  # sell稍低
        exec_price = round_price(exec_price, coin)
        
        result = exchange.order(coin, is_buy, size, exec_price, 
            {"limit": {"tif": "Ioc"}, "sl": sl, "tp": tp})
        log(f"下单: {coin} {'LONG' if is_buy else 'SHORT'} size={size} @${exec_price} SL={sl} TP={tp} | {json.dumps(result)[:300]}")
        
        status = result.get('status', '')
        if status == 'ok':
            resp_data = result.get('response', {}).get('data', {})
            statuses = resp_data.get('statuses', [])
            if statuses and statuses[0].get('filled'):
                fill = statuses[0]
                save_trade({
                    'time': datetime.now(tz8).strftime("%Y-%m-%d %H:%M:%S"),
                    'action': 'open',
                    'coin': coin, 'side': 'LONG' if is_buy else 'SHORT',
                    'size': size, 'price': exec_price, 'sl': sl, 'tp': tp,
                    'fill_price': fill.get('avgPx', str(exec_price)),
                    'status': 'filled'
                })
                log(f"✅ 开仓成功: {coin} @${fill.get('avgPx', exec_price)}")
                return True, fill.get('avgPx', exec_price)
            elif statuses and statuses[0].get('error'):
                log(f"❌ 下单被拒: {statuses[0]['error']}")
                return False, None
        return False, None
    except Exception as e:
        log(f"下单异常: {e}")
        return False, None

def get_tick_size(info, coin):
    """获取币种的tick size"""
    try:
        meta = info.meta()
        for asset in meta['universe']:
            if asset['name'] == coin:
                return float(asset['szDecimals'])  # e.g. 1 for BTC, 2 for ETH
        return 2  # default
    except:
        return 2

def round_price(price, coin):
    """根据币种价格tick size舍入"""
    # 实测 tick sizes (2026-03-17)
    tick_map = {
        'BTC': 1, 'ETH': 0.1, 'SOL': 0.001, 'AVAX': 0.001,
        'APT': 0.00001, 'ATOM': 0.00001, 'SUI': 0.0001, 'JUP': 0.00001
    }
    tick = tick_map.get(coin, 0.001)
    if tick >= 1:
        return round(price / tick) * tick
    decimals = len(str(tick).rstrip('0').split('.')[-1])
    return round(price, decimals)

def close_position(exchange, coin, side, size):
    """平仓 - 使用市价单"""
    try:
        is_buy = side == -1  # SHORT平仓要buy, LONG平仓要sell
        info = Info(base_url="https://api.hyperliquid.xyz", skip_ws=True)
        mid = float(info.all_mids().get(coin, 0))
        if mid == 0: return False
        # 用高精度市价单
        if is_buy:
            price = mid * 1.005  # buy稍高确保成交
        else:
            price = mid * 0.995  # sell稍低确保成交
        price = round_price(price, coin)
        result = exchange.order(coin, is_buy, size, price, {"limit": {"tif": "Ioc"}})
        log(f"平仓: {coin} {'LONG' if side==1 else 'SHORT'} size={size} @${price} | {json.dumps(result)[:200]}")
        resp_data = result.get('response', {}).get('data', {})
        statuses = resp_data.get('statuses', [])
        if statuses:
            if statuses[0].get('filled'):
                save_trade({
                    'time': datetime.now(tz8).strftime("%Y-%m-%d %H:%M:%S"),
                    'action': 'close', 'coin': coin, 'side': 'LONG' if side==1 else 'SHORT',
                    'size': size, 'fill_price': statuses[0].get('avgPx', str(price)),
                    'pnl': statuses[0].get('pnl', '0'), 'status': 'filled'
                })
                log(f"✅ 平仓成功: {coin} @${statuses[0].get('avgPx', price)}")
                return True
            elif statuses[0].get('error'):
                log(f"❌ 平仓失败: {statuses[0].get('error')}")
                return False
        return False
    except Exception as e:
        log(f"平仓异常: {e}")
        return False

# ============ 主逻辑 ============
def run_scan(paper=True, wallet_key=None, wallet_addr=None):
    """执行一次扫描"""
    log("=" * 50)
    log("开始信号扫描 (v2 优化参数)")
    
    info = Info(base_url="https://api.hyperliquid.xyz", skip_ws=True)
    now_ms = int(time.time() * 1000)
    start_ms = now_ms - 30 * 86400000
    
    # 获取账户状态
    state = info.user_state(wallet_addr)
    capital = float(state['marginSummary']['accountValue'])
    current_positions = {}
    for p in state['assetPositions']:
        pos = p['position']
        coin = pos['coin']
        current_positions[coin] = {
            'size': float(pos['szi']),
            'entry': float(pos['entryPx']),
            'side': 1 if float(pos['szi']) > 0 else -1,
            'pnl': float(pos['unrealizedPnl'])
        }
    
    log(f"账户净值: ${capital:.2f}, 当前持仓: {len(current_positions)}")
    
    # 检查止损止盈
    mids = info.all_mids()
    config = CLAWFI_CONFIG if wallet_addr.lower() == CLAWFI_ADDR.lower() else XIAOXIA_CONFIG
    closed_coins = []
    for coin, pos in current_positions.items():
        mid = float(mids.get(coin, 0))
        if mid == 0: continue
        
        candles = info.candles_snapshot(coin, config['CANDLE_INTERVAL'], start_ms, now_ms)
        atr = calc_atr(candles, 14)
        if atr is None: continue
        
        sl = pos['entry'] - atr * config['STOP_ATR_MULT'] if pos['side'] == 1 else pos['entry'] + atr * config['STOP_ATR_MULT']
        tp = pos['entry'] + atr * config['TP_ATR_MULT'] if pos['side'] == 1 else pos['entry'] - atr * config['TP_ATR_MULT']
        
        should_close = False
        reason = ""
        if pos['side'] == 1:
            if mid <= sl: should_close, reason = True, f"止损 (mid={mid} <= sl={sl:.4f})"
            elif mid >= tp: should_close, reason = True, f"止盈 (mid={mid} >= tp={tp:.4f})"
        else:
            if mid >= sl: should_close, reason = True, f"止损 (mid={mid} >= sl={sl:.4f})"
            elif mid <= tp: should_close, reason = True, f"止盈 (mid={mid} <= tp={tp:.4f})"
        
        if should_close:
            log(f"🚨 {coin} 触发{reason}")
            if not paper and wallet_key:
                close_position(
                    Exchange(Account.from_key(wallet_key), base_url="https://api.hyperliquid.xyz", 
                             spot_meta={"universe": [], "tokens": []}),
                    coin, pos['side'], abs(pos['size'])
                )
            closed_coins.append(coin)
    
    for c in closed_coins:
        del current_positions[c]
    
    # 信号扫描
    if len(current_positions) >= MAX_POSITIONS:
        log(f"持仓已满 ({len(current_positions)}/{MAX_POSITIONS})，跳过扫描")
        return
    
    new_signals = []
    for coin in COINS:
        if coin in current_positions: continue
        
        try:
            candles = info.candles_snapshot(coin, config['CANDLE_INTERVAL'], start_ms, now_ms)
            funding = info.funding_history(coin, start_ms)
        except:
            continue
        
        if len(candles) < 55: continue
        
        signal, details = generate_signal(candles, funding, len(candles) - 1)
        
        if signal != 0:
            price = float(candles[-1]['c'])
            atr = details['atr']
            # v3: 极端费率信号用更大风险 (3% vs 2%)
            is_extreme = details.get('extreme') is not None
            risk_pct = 0.03 if is_extreme else config['MAX_RISK_PER_TRADE']
            risk = capital * risk_pct
            sd = atr * config['STOP_ATR_MULT']
            if sd == 0: continue
            size = risk / sd
            margin = size * price / config['DEFAULT_LEVERAGE']
            
            if margin > capital * config['MAX_MARGIN_PCT']:
                log(f"  {coin}: 保证金 ${margin:.2f} 超限 (max ${capital*config['MAX_MARGIN_PCT']:.2f})，跳过")
                continue
            
            sl = price - sd if signal == 1 else price + sd
            tp = price + atr * config['TP_ATR_MULT'] if signal == 1 else price - atr * config['TP_ATR_MULT']
            
            new_signals.append({
                'coin': coin, 'signal': signal, 'price': price,
                'size': size, 'sl': sl, 'tp': tp, 'margin': margin,
                'details': details
            })
            log(f"{'🟢' if signal==1 else '🔴'} 信号: {coin} {'LONG' if signal==1 else 'SHORT'} "
                f"@{price:.4f} score={details['score']:.2f} "
                f"RSI={details['rsi']:.1f} ATR={atr:.4f} funding={details['funding']:.6f} "
                f"size={size:.6f} margin=${margin:.2f} SL={sl:.4f} TP={tp:.4f}"
                f"{' ⚡'+details['extreme'] if details.get('extreme') else ''}")
    
    # 执行下单
    if paper:
        for s in new_signals:
            log(f"📝 [PAPER] 会开仓: {s['coin']} {'LONG' if s['signal']==1 else 'SHORT'} "
                f"@{s['price']:.4f} size={s['size']:.6f}")
            save_trade({
                'time': datetime.now(tz8).strftime("%Y-%m-%d %H:%M:%S"),
                'action': 'paper_signal', 'coin': s['coin'], 
                'side': 'LONG' if s['signal']==1 else 'SHORT',
                'price': s['price'], 'size': s['size'], 'sl': s['sl'], 'tp': s['tp'],
                'score': s['details']['score'], 'rsi': s['details']['rsi'],
                'atr': s['details']['atr'], 'funding': s['details']['funding'],
                'extreme': s['details'].get('extreme'),
                'status': 'paper'
            })
    else:
        if wallet_key and new_signals:
            exchange = Exchange(Account.from_key(wallet_key), 
                base_url="https://api.hyperliquid.xyz",
                spot_meta={"universe": [], "tokens": []})
            for s in new_signals:
                ok, fill = place_order(exchange, s['coin'], s['signal'], s['size'], s['price'], s['sl'], s['tp'])
                if ok:
                    log(f"✅ 实单成交: {s['coin']} @ {fill}")
    
    # 写入笔记
    if new_signals or closed_coins:
        write_patrol_note(capital, current_positions, new_signals, closed_coins, mids, paper)
    
    log("扫描完成")

def write_patrol_note(capital, positions, new_signals, closed_coins, mids, paper):
    now = datetime.now(tz8).strftime("%Y-%m-%d %H:%M:%S")
    mode = "PAPER TRADING" if paper else "LIVE"
    
    content = f"""# 交易信号报告 ({mode})

**时间**: {now} GMT+8  
**Agent**: samh7914_bot  
**模式**: {mode}

---

## 账户概览
- 净值: ${capital:.2f}
- 当前持仓: {len(positions)}

## 当前持仓
"""
    for coin, pos in positions.items():
        mid = float(mids.get(coin, 0))
        side = 'LONG' if pos['side'] == 1 else 'SHORT'
        content += f"- {coin}: {side} {abs(pos['size']):.4f} @{pos['entry']:.4f} (mid:{mid:.4f}) PnL: ${pos['pnl']:.2f}\n"
    
    if new_signals:
        content += "\n## 新信号\n"
        for s in new_signals:
            side = "🟢 LONG" if s['signal'] == 1 else "🔴 SHORT"
            content += f"- {side} {s['coin']} @{s['price']:.4f} | score={s['details']['score']:.2f} RSI={s['details']['rsi']:.1f} | SL={s['sl']:.4f} TP={s['tp']:.4f}\n"
    
    if closed_coins:
        content += f"\n## 触发平仓\n"
        for c in closed_coins:
            content += f"- {c}\n"
    
    try:
        import requests
        resp = requests.post("https://openapi.biji.com/open/api/v1/resource/note/save",
            headers=GETNOTE_HEADERS,
            json={
                "title": f"[{'Paper' if paper else 'Live'}] 交易信号 {now[:16]}",
                "content": content,
                "note_type": "plain_text",
                "tags": ["交易信号", "samh7914_bot", now[:10].replace("-", "")],
                "topic_ids": [GETNOTE_TOPIC_ID]
            }, timeout=15)
        if resp.json().get('success'):
            log("✅ 笔记已写入知识库")
    except Exception as e:
        log(f"笔记写入失败: {e}")

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "paper"
    wallet = sys.argv[2] if len(sys.argv) > 2 else CLAWFI_ADDR
    key = sys.argv[3] if len(sys.argv) > 3 else CLAWFI_KEY
    
    if mode == "live" and not key:
        log("❌ LIVE模式需要私钥")
        sys.exit(1)
    
    if mode == "paper":
        # Paper模式：用ClawFi钱包查询持仓，但不下单
        run_scan(paper=True, wallet_key=CLAWFI_KEY, wallet_addr=CLAWFI_ADDR)
    else:
        run_scan(paper=False, wallet_key=key, wallet_addr=wallet)
