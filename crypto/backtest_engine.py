#!/usr/bin/env python3
"""
Hyperliquid 回测引擎 v1.0
策略: 趋势跟踪 + 动量过滤 + 资金费率确认
回测: 30天 1h K线 + funding history
"""
import json, time, math
from datetime import datetime, timezone, timedelta
from hyperliquid.info import Info

tz8 = timezone(timedelta(hours=8))

# ============ 配置 ============
INITIAL_CAPITAL = 300.0  # 小夏账户初始资金
MAX_RISK_PER_TRADE = 0.02  # 单笔最大风险2%
DEFAULT_LEVERAGE = 3
MAX_POSITIONS = 5
STOP_ATR_MULT = 2.0
TP_ATR_MULT = 4.0
DAILY_LOSS_LIMIT = 0.05  # 日亏损上限5%

COINS = ["BTC", "ETH", "SOL", "AVAX", "APT", "ATOM", "SUI", "JUP"]
HISTORY_DAYS = 30

# ============ 数据获取 ============
def fetch_data():
    """获取所有币种的K线和funding数据"""
    info = Info(base_url="https://api.hyperliquid.xyz", skip_ws=True)
    now_ms = int(time.time() * 1000)
    start_ms = now_ms - HISTORY_DAYS * 86400000
    
    data = {}
    for coin in COINS:
        print(f"  获取 {coin} 数据...")
        candles = info.candles_snapshot(coin, "1h", start_ms, now_ms)
        funding = info.funding_history(coin, start_ms)
        data[coin] = {"candles": candles, "funding": funding}
    
    return data

# ============ 指标计算 ============
def calc_sma(closes, period):
    if len(closes) < period:
        return None
    return sum(closes[-period:]) / period

def calc_rsi(closes, period=14):
    if len(closes) < period + 1:
        return None
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [max(0, d) for d in deltas[-period:]]
    losses = [max(0, -d) for d in deltas[-period:]]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calc_atr(candles, period=14):
    if len(candles) < period + 1:
        return None
    trs = []
    for i in range(1, len(candles)):
        h, l = float(candles[i]['h']), float(candles[i]['l'])
        prev_c = float(candles[i-1]['c'])
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        trs.append(tr)
    return sum(trs[-period:]) / period

def calc_macd(closes):
    if len(closes) < 26:
        return None, None, None
    ema12 = closes[0]
    ema26 = closes[0]
    for c in closes[1:]:
        ema12 = ema12 * 11/13 + c * 2/13
        ema26 = ema26 * 25/27 + c * 2/27
    dif = ema12 - ema26
    return dif, ema12, ema26

def get_funding_rate(funding_list, timestamp_ms):
    """获取最接近指定时间的funding rate"""
    rate = 0
    for f in funding_list:
        if f['time'] <= timestamp_ms:
            rate = float(f['fundingRate'])
        else:
            break
    return rate

# ============ 信号生成 ============
def generate_signal(candles, funding_list, idx):
    """在K线索引idx处生成信号
    返回: 1(做多), -1(做空), 0(观望)
    """
    closes = [float(c['c']) for c in candles[:idx+1]]
    if len(closes) < 50:
        return 0
    
    ma20 = calc_sma(closes, 20)
    ma50 = calc_sma(closes, 50)
    rsi = calc_rsi(closes, 14)
    atr = calc_atr(candles[:idx+1], 14)
    dif, _, _ = calc_macd(closes)
    prev_dif, _, _ = calc_macd(closes[:-1])
    
    if atr is None or ma20 is None or ma50 is None or rsi is None:
        return 0
    
    current_price = closes[-1]
    ts = candles[idx]['t']
    funding = get_funding_rate(funding_list, ts)
    
    score = 0
    
    # 趋势方向 (权重40%)
    if ma20 > ma50:
        score += 0.4  # 上升趋势
    else:
        score -= 0.4  # 下降趋势
    
    # RSI (权重25%)
    if rsi < 30:
        score += 0.25  # 超卖做多
    elif rsi > 70:
        score -= 0.25  # 超买卖空
    
    # MACD (权重20%)
    if dif is not None and prev_dif is not None:
        if dif > prev_dif and dif > 0:
            score += 0.2  # 金叉
        elif dif < prev_dif and dif < 0:
            score -= 0.2  # 死叉
    
    # Funding rate (权重15%)
    if funding > 0.0001:
        score += 0.15  # 正funding = 多头强势
    elif funding < -0.0001:
        score -= 0.15
    
    if score > 0.4:
        return 1   # 做多
    elif score < -0.4:
        return -1   # 做空
    return 0

# ============ 回测引擎 ============
def backtest(data):
    """执行回测"""
    capital = INITIAL_CAPITAL
    positions = {}  # coin -> {entry, size, side, stop, tp, entry_time}
    trades = []
    daily_pnl = 0
    daily_start_ts = None
    equity_curve = []
    signal_log = []
    
    # 确定共同时间范围（BTC为基准）
    btc_candles = data["BTC"]["candles"]
    
    for idx in range(50, len(btc_candles)):
        ts = btc_candles[idx]['t']
        dt = datetime.fromtimestamp(ts/1000, tz=tz8)
        
        # 每日重置
        if daily_start_ts is None or dt.date() != daily_start_ts:
            daily_start_ts = dt.date()
            daily_pnl = 0
        
        # 检查止损止盈
        closed = []
        for coin, pos in positions.items():
            if coin not in data:
                continue
            candle = None
            for c in data[coin]["candles"]:
                if c['t'] == ts:
                    candle = c
                    break
            if candle is None:
                continue
            
            price = float(candle['c'])
            low = float(candle['l'])
            high = float(candle['h'])
            
            margin_return = pos['size'] * pos['entry'] / DEFAULT_LEVERAGE
            if pos['side'] == 1:  # LONG
                if low <= pos['stop']:
                    pnl = (pos['stop'] - pos['entry']) * pos['size']
                    trades.append({
                        'coin': coin, 'side': 'LONG', 'entry': pos['entry'],
                        'exit': pos['stop'], 'size': pos['size'], 'pnl': pnl,
                        'reason': '止损', 'time': dt.strftime("%Y-%m-%d %H:%M")
                    })
                    closed.append(coin)
                    daily_pnl += pnl
                    capital += margin_return + pnl
                elif high >= pos['tp']:
                    pnl = (pos['tp'] - pos['entry']) * pos['size']
                    trades.append({
                        'coin': coin, 'side': 'LONG', 'entry': pos['entry'],
                        'exit': pos['tp'], 'size': pos['size'], 'pnl': pnl,
                        'reason': '止盈', 'time': dt.strftime("%Y-%m-%d %H:%M")
                    })
                    closed.append(coin)
                    daily_pnl += pnl
                    capital += margin_return + pnl
            else:  # SHORT
                if high >= pos['stop']:
                    pnl = (pos['entry'] - pos['stop']) * pos['size']
                    trades.append({
                        'coin': coin, 'side': 'SHORT', 'entry': pos['entry'],
                        'exit': pos['stop'], 'size': pos['size'], 'pnl': pnl,
                        'reason': '止损', 'time': dt.strftime("%Y-%m-%d %H:%M")
                    })
                    closed.append(coin)
                    daily_pnl += pnl
                    capital += margin_return + pnl
                elif low <= pos['tp']:
                    pnl = (pos['entry'] - pos['tp']) * pos['size']
                    trades.append({
                        'coin': coin, 'side': 'SHORT', 'entry': pos['entry'],
                        'exit': pos['tp'], 'size': pos['size'], 'pnl': pnl,
                        'reason': '止盈', 'time': dt.strftime("%Y-%m-%d %H:%M")
                    })
                    closed.append(coin)
                    daily_pnl += pnl
                    capital += margin_return + pnl
        
        for c in closed:
            del positions[c]
        
        # 日亏损检查
        if daily_pnl < -capital * DAILY_LOSS_LIMIT:
            continue
        
        # 信号扫描
        if len(positions) >= MAX_POSITIONS:
            unrealized = sum(
                (float(data[coin]["candles"][-1]['c']) - pos['entry']) * pos['size']
                for coin, pos in positions.items()
                if coin in data
            )
            equity_curve.append({
                'time': dt.strftime("%Y-%m-%d %H:%M"),
                'capital': capital,
                'unrealized': unrealized,
                'total': capital + unrealized,
                'positions': len(positions)
            })
            continue
        
        for coin in COINS:
            if coin in positions or coin not in data:
                continue
            
            candles = data[coin]["candles"]
            # 找到对应时间索引
            candle_idx = None
            for i, c in enumerate(candles):
                if c['t'] == ts:
                    candle_idx = i
                    break
            if candle_idx is None or candle_idx < 50:
                continue
            
            signal = generate_signal(candles, data[coin]["funding"], candle_idx)
            
            if signal == 0:
                continue
            
            price = float(candles[candle_idx]['c'])
            atr = calc_atr(candles[:candle_idx+1], 14)
            if atr is None:
                continue
            
            # 计算仓位（size = 合约张数, 用保证金反算）
            risk_amount = capital * MAX_RISK_PER_TRADE
            stop_dist = atr * STOP_ATR_MULT
            if stop_dist == 0:
                continue
            # 在Hyperliquid perp中, positionValue = size * price
            # PnL per unit size = price_change
            # 要使止损时PnL = -risk_amount: size * stop_dist = risk_amount
            size = risk_amount / stop_dist
            position_value = size * price
            margin = position_value / DEFAULT_LEVERAGE
            
            if margin > capital * 0.3:  # 单笔不超过30%资金
                continue
            
            if signal == 1:  # LONG
                stop = price - stop_dist
                tp = price + atr * TP_ATR_MULT
                positions[coin] = {
                    'entry': price, 'size': size, 'side': 1,
                    'stop': stop, 'tp': tp, 'entry_time': dt.strftime("%Y-%m-%d %H:%M")
                }
                signal_log.append(f"[{dt.strftime('%m-%d %H:%M')}] 🟢 LONG {coin} @{price:.4f} size={size:.6f} SL={stop:.4f} TP={tp:.4f} margin=${margin:.2f}")
            else:  # SHORT
                stop = price + stop_dist
                tp = price - atr * TP_ATR_MULT
                positions[coin] = {
                    'entry': price, 'size': size, 'side': -1,
                    'stop': stop, 'tp': tp, 'entry_time': dt.strftime("%Y-%m-%d %H:%M")
                }
                signal_log.append(f"[{dt.strftime('%m-%d %H:%M')}] 🔴 SHORT {coin} @{price:.4f} size={size:.6f} SL={stop:.4f} TP={tp:.4f} margin=${margin:.2f}")
            
            capital -= margin  # 扣除保证金
        
        # 记录净值
        unrealized = 0
        for coin, pos in positions.items():
            if coin in data and data[coin]['candles']:
                unrealized += (float(data[coin]['candles'][-1]['c']) - pos['entry']) * pos['size'] * pos['side']
        equity_curve.append({
            'time': dt.strftime("%Y-%m-%d %H:%M"),
            'capital': capital,
            'unrealized': unrealized,
            'total': capital + unrealized,
            'positions': len(positions)
        })
    
    return trades, equity_curve, signal_log

# ============ 统计报告 ============
def generate_report(trades, equity_curve, signal_log):
    if not trades:
        return "无交易记录"
    
    wins = [t for t in trades if t['pnl'] > 0]
    losses = [t for t in trades if t['pnl'] <= 0]
    total_pnl = sum(t['pnl'] for t in trades)
    
    # 最大回撤
    peak = equity_curve[0]['total']
    max_dd = 0
    for e in equity_curve:
        if e['total'] > peak:
            peak = e['total']
        dd = (peak - e['total']) / peak
        if dd > max_dd:
            max_dd = dd
    
    avg_win = sum(t['pnl'] for t in wins) / len(wins) if wins else 0
    avg_loss = sum(t['pnl'] for t in losses) / len(losses) if losses else 0
    
    report = f"""# 回测报告 ({HISTORY_DAYS}天)

## 核心指标
| 指标 | 数值 |
|------|------|
| 初始资金 | ${INITIAL_CAPITAL:.2f} |
| 总交易数 | {len(trades)} |
| 盈利次数 | {len(wins)} |
| 亏损次数 | {len(losses)} |
| 胜率 | {len(wins)/len(trades)*100:.1f}% |
| 总PnL | ${total_pnl:.2f} |
| 收益率 | {total_pnl/INITIAL_CAPITAL*100:.1f}% |
| 平均盈利 | ${avg_win:.2f} |
| 平均亏损 | ${avg_loss:.2f} |
| 盈亏比 | {abs(avg_win/avg_loss):.2f}:1" if avg_loss != 0 else "" |
| 最大回撤 | {max_dd*100:.1f}% |
| 最终净值 | ${equity_curve[-1]['total']:.2f} |

## 交易明细
"""
    
    for t in trades[-20:]:  # 只显示最近20笔
        emoji = "🟢" if t['pnl'] > 0 else "🔴"
        report += f"{emoji} {t['time']} {t['side']} {t['coin']} @{t['entry']:.4f} → {t['exit']:.4f} | PnL ${t['pnl']:.2f} ({t['reason']})\n"
    
    if len(trades) > 20:
        report += f"\n_... 还有 {len(trades)-20} 笔交易_\n"
    
    return report, {
        'total_trades': len(trades),
        'win_rate': len(wins)/len(trades)*100 if trades else 0,
        'total_pnl': total_pnl,
        'return_pct': total_pnl/INITIAL_CAPITAL*100,
        'max_drawdown': max_dd*100,
        'final_equity': equity_curve[-1]['total'] if equity_curve else INITIAL_CAPITAL,
        'profit_factor': abs(sum(t['pnl'] for t in wins) / sum(t['pnl'] for t in losses)) if losses and sum(t['pnl'] for t in losses) != 0 else float('inf'),
    }

if __name__ == "__main__":
    print("🚀 开始回测...")
    print(f"   币种: {', '.join(COINS)}")
    print(f"   周期: {HISTORY_DAYS}天 1h K线")
    print(f"   初始资金: ${INITIAL_CAPITAL}")
    print()
    
    data = fetch_data()
    
    print(f"\n📊 执行回测...")
    trades, equity_curve, signal_log = backtest(data)
    
    report, stats = generate_report(trades, equity_curve, signal_log)
    
    print(report)
    
    # 保存结果
    with open('/root/.openclaw/workspace/crypto/backtest_result.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now(tz8).strftime("%Y-%m-%d %H:%M:%S"),
            'config': {'coins': COINS, 'days': HISTORY_DAYS, 'capital': INITIAL_CAPITAL},
            'stats': stats,
            'trades': trades,
            'equity_curve': equity_curve[-50:]  # 最后50个点
        }, f, indent=2)
    
    print(f"\n📁 详细结果已保存至 crypto/backtest_result.json")
    print(f"📝 信号日志共 {len(signal_log)} 条")
