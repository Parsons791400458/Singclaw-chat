#!/usr/bin/env python3
"""
观察池自动更新脚本 — 每4h抓取数据 + OI场景判定 + 生成网页快照
"""

import json, time, os, sys
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError

BJT = timezone(timedelta(hours=8))
NOW = datetime.now(BJT)
SNAPSHOT_FILE = "/root/.openclaw/workspace/crypto/watchlist_snapshots.json"
HTML_FILE = "/root/.openclaw/workspace/singclaw-site/crypto/watchlist.html"

# 观察池完整列表
WATCHLIST = [
    "TIA", "HEMI", "SKL", "STX", "MET",
    "H", "GWEI", "UB", "SOON",
    "TAG", "LIGHT", "B", "BLUAI", "EDGE", "PIEVERSE"
]

COIN_META = {
    "TIA":      {"tag": "持仓", "note": "HL 5x多"},
    "HEMI":     {"tag": "预警", "note": "OKX 6x多 4/29解锁"},
    "SKL":      {"tag": "观察", "note": "机构背书 赔率高"},
    "STX":      {"tag": "观察", "note": "BTC L2 Stacks"},
    "MET":      {"tag": "观察", "note": "Solana DEX"},
    "H":        {"tag": "Alpha", "note": "OI大 3.3x"},
    "GWEI":     {"tag": "重点", "note": "S1强看多 +27% OI健康"},
    "UB":       {"tag": "Alpha", "note": "补涨 2.9x"},
    "SOON":     {"tag": "Alpha", "note": "3.8x"},
    "TAG":      {"tag": "Alpha", "note": "4.0x"},
    "LIGHT":    {"tag": "重点", "note": "稳涨+OI健康增长"},
    "B":        {"tag": "Alpha", "note": "2.6x"},
    "BLUAI":    {"tag": "Alpha", "note": "AI概念 3.6x"},
    "EDGE":     {"tag": "Alpha", "note": "OI最大 4.1x"},
    "PIEVERSE": {"tag": "Alpha", "note": "1.8x"},
}

# CoinGlass 8大OI场景定义
# S1: OI↑ + 价格↑ = 强看多
# S2: OI↑ + 价格横盘 = 蓄力偏多
# S1b: OI↑ + 价格↓ = 分歧偏多
# S3: OI↓ + 价格↓ = 多头投降
# S4: OI↓ + 价格↑ = 空头回补
# S5: OI↓ + 价格横盘 = 观望
# S6: OI平 + 价格↑ = 现货驱动
# S7: OI爆增 + 价格↑ = 多头过热

def fetch_json(url, headers=None):
    """Fetch JSON from URL"""
    req = Request(url)
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"  [WARN] fetch failed: {url[:60]}... -> {e}")
        return None

def get_binance_data(symbol):
    """Get price, 24h change, volume from Binance Futures"""
    data = fetch_json(f"https://fapi.binance.com/fapi/v1/ticker/24hr?symbol={symbol}USDT")
    if not data or 'lastPrice' not in data:
        return None
    return {
        "price": float(data["lastPrice"]),
        "chg24h": float(data["priceChangePercent"]),
        "vol24h": float(data["quoteVolume"]),
        "high24h": float(data["highPrice"]),
        "low24h": float(data["lowPrice"]),
    }

def get_binance_oi(symbol):
    """Get current OI from Binance Futures"""
    data = fetch_json(f"https://fapi.binance.com/fapi/v1/openInterest?symbol={symbol}USDT")
    if not data or 'openInterest' not in data:
        return 0
    return float(data["openInterest"])

def get_binance_funding(symbol):
    """Get latest funding rate"""
    data = fetch_json(f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={symbol}USDT&limit=1")
    if not data or not isinstance(data, list) or len(data) == 0:
        return 0
    return float(data[0].get("fundingRate", 0))

def get_oi_change(symbol):
    """Get OI change over past 24h using klines proxy (compare current vs 24h ago)"""
    # Use 4h klines to estimate OI trend
    data = fetch_json(f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}USDT&interval=4h&limit=7")
    if not data or len(data) < 7:
        return 0, 0
    # Price change over ~24h
    old_close = float(data[0][4])
    new_close = float(data[-1][4])
    price_chg = (new_close - old_close) / old_close * 100 if old_close > 0 else 0
    return price_chg, 0

def determine_scene(oi_usd, prev_oi_usd, price_chg_24h, oi_pct_chg):
    """
    Determine CoinGlass OI scene based on OI and price changes.
    Uses price_chg_24h and oi_pct_chg (OI % change over period).
    """
    # Thresholds
    PRICE_UP = 3.0      # >3% = up
    PRICE_DOWN = -3.0    # <-3% = down
    OI_UP = 5.0          # >5% = OI increasing
    OI_DOWN = -5.0       # <-5% = OI decreasing
    OI_SURGE = 30.0      # >30% = OI surge

    if oi_pct_chg > OI_SURGE and price_chg_24h > PRICE_UP:
        return "S7", "多头过热", "🔴", "OI爆增+价格涨=过热警告"
    elif oi_pct_chg > OI_UP and price_chg_24h > PRICE_UP:
        return "S1", "强看多", "🟢", "OI↑+价格↑=多头进场"
    elif oi_pct_chg > OI_UP and PRICE_DOWN <= price_chg_24h <= PRICE_UP:
        return "S2", "蓄力", "🟡", "OI↑+价格横盘=蓄力中"
    elif oi_pct_chg > OI_UP and price_chg_24h < PRICE_DOWN:
        return "S1b", "分歧偏多", "🟠", "OI↑+价格↓=多空分歧"
    elif oi_pct_chg < OI_DOWN and price_chg_24h < PRICE_DOWN:
        return "S3", "多头投降", "⚫", "OI↓+价格↓=多头平仓"
    elif oi_pct_chg < OI_DOWN and price_chg_24h > PRICE_UP:
        return "S4", "空头回补", "🔵", "OI↓+价格↑=空头平仓"
    elif oi_pct_chg < OI_DOWN and PRICE_DOWN <= price_chg_24h <= PRICE_UP:
        return "S5", "观望", "⚪", "OI↓+价格横盘=资金离场"
    elif abs(oi_pct_chg) <= OI_UP and price_chg_24h > PRICE_UP:
        return "S6", "现货驱动", "🟣", "OI平+价格↑=现货买盘"
    else:
        return "—", "横盘", "⬜", "无明确信号"

def collect_all_data():
    """Collect data for all watchlist coins"""
    results = []
    for symbol in WATCHLIST:
        print(f"  Fetching {symbol}...")
        ticker = get_binance_data(symbol)
        if not ticker:
            print(f"    [SKIP] {symbol} no data")
            continue

        oi_qty = get_binance_oi(symbol)
        oi_usd = oi_qty * ticker["price"]
        funding = get_binance_funding(symbol)
        price_chg_24h = ticker["chg24h"]

        # For OI change, we use the snapshot comparison if available
        prev_oi = get_prev_oi(symbol)
        if prev_oi and prev_oi > 0:
            oi_pct_chg = (oi_usd - prev_oi) / prev_oi * 100
        else:
            oi_pct_chg = 0  # First snapshot, no comparison

        scene_id, scene_name, scene_emoji, scene_desc = determine_scene(
            oi_usd, prev_oi, price_chg_24h, oi_pct_chg
        )

        meta = COIN_META.get(symbol, {"tag": "观察", "note": ""})

        results.append({
            "symbol": symbol,
            "price": ticker["price"],
            "chg24h": price_chg_24h,
            "high24h": ticker["high24h"],
            "low24h": ticker["low24h"],
            "vol24h": ticker["vol24h"],
            "oi_usd": round(oi_usd, 0),
            "oi_pct_chg": round(oi_pct_chg, 2),
            "funding": round(funding * 100, 4),
            "scene": scene_id,
            "scene_name": scene_name,
            "scene_emoji": scene_emoji,
            "scene_desc": scene_desc,
            "tag": meta["tag"],
            "note": meta["note"],
        })
        time.sleep(0.1)  # Rate limit

    return results

def get_prev_oi(symbol):
    """Get previous OI from last snapshot"""
    if not os.path.exists(SNAPSHOT_FILE):
        return None
    with open(SNAPSHOT_FILE) as f:
        data = json.load(f)
    snapshots = data.get("snapshots", [])
    if not snapshots:
        return None
    last = snapshots[-1]
    for coin in last.get("coins", []):
        if coin["symbol"] == symbol:
            return coin.get("oi_usd", None)
    return None

def get_btc_fng():
    """Get BTC price and FNG"""
    btc = fetch_json("https://fapi.binance.com/fapi/v1/ticker/24hr?symbol=BTCUSDT")
    fng = fetch_json("https://api.alternative.me/fng/?limit=1")
    btc_price = float(btc["lastPrice"]) if btc else 0
    btc_chg = float(btc["priceChangePercent"]) if btc else 0
    fng_val = int(fng["data"][0]["value"]) if fng and "data" in fng else 0
    fng_class = fng["data"][0]["value_classification"] if fng and "data" in fng else ""
    return btc_price, btc_chg, fng_val, fng_class

def save_snapshot(coins, btc_price, btc_chg, fng_val, fng_class):
    """Append new snapshot to JSON"""
    if os.path.exists(SNAPSHOT_FILE):
        with open(SNAPSHOT_FILE) as f:
            data = json.load(f)
    else:
        data = {"meta": {"version": 1, "created": NOW.isoformat()}, "snapshots": []}

    snap_id = len(data["snapshots"]) + 1

    snapshot = {
        "id": snap_id,
        "timestamp": NOW.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "timestamp_bjt": NOW.strftime("%Y-%m-%d %H:%M BJT"),
        "btc_price": btc_price,
        "btc_chg": btc_chg,
        "fng": fng_val,
        "fng_class": fng_class,
        "market_note": f"BTC ${btc_price:,.0f} ({btc_chg:+.2f}%) | FNG={fng_val} {fng_class}",
        "coins": coins,
    }

    data["snapshots"].append(snapshot)
    data["meta"]["last_updated"] = NOW.isoformat()
    data["meta"]["version"] = snap_id

    with open(SNAPSHOT_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  ✅ Snapshot #{snap_id} saved ({len(coins)} coins)")
    return data

def fmt_price(p):
    if p >= 1: return f"${p:.4f}"
    elif p >= 0.01: return f"${p:.5f}"
    else: return f"${p:.6f}"

def fmt_oi(v):
    if v >= 1e6: return f"${v/1e6:.1f}M"
    elif v >= 1e3: return f"${v/1e3:.0f}K"
    else: return f"${v:.0f}"

def fmt_vol(v):
    if v >= 1e6: return f"${v/1e6:.1f}M"
    elif v >= 1e3: return f"${v/1e3:.0f}K"
    else: return f"${v:.0f}"

def chg_class(v):
    if v > 1: return "chg-up"
    elif v < -1: return "chg-down"
    else: return "chg-flat"

def tag_class(tag):
    m = {"持仓": "tag-持仓", "预警": "tag-预警", "观察": "tag-观察", "Alpha": "tag-新增", "新增": "tag-新增"}
    return m.get(tag, "tag-观察")

def scene_color(scene):
    """Return CSS variable reference for scene colors (used in inline styles)"""
    m = {"S1": "var(--sc-success)", "S2": "var(--sc-gold)", "S1b": "#f97316", "S3": "#6b7280",
         "S4": "var(--sc-blue)", "S5": "#9ca3af", "S6": "var(--sc-purple)", "S7": "var(--sc-danger)", "—": "#4b5563"}
    return m.get(scene, "#4b5563")

def scene_class(scene):
    """Return CSS class name for scene badge styling"""
    m = {"S1": "scene-s1", "S2": "scene-s2", "S1b": "scene-s1b", "S3": "scene-s3",
         "S4": "scene-s4", "S5": "scene-s5", "S6": "scene-s6", "S7": "scene-s7", "—": "scene-default"}
    return m.get(scene, "scene-default")

def generate_html(all_data, btc_price, btc_chg, fng_val, fng_class):
    """Generate the full watchlist HTML"""

    # Count scenes
    scene_counts = {}
    for c in all_data:
        s = c["scene"]
        scene_counts[s] = scene_counts.get(s, 0) + 1

    # Build table rows
    table_rows = ""
    for c in all_data:
        table_rows += f'''            <tr data-tag="{c['tag']}" data-scene="{c['scene']}">
              <td class="coin-name">{c['symbol']}</td>
              <td>{fmt_price(c['price'])}</td>
              <td class="{chg_class(c['chg24h'])}">{c['chg24h']:+.2f}%</td>
              <td>{fmt_oi(c['oi_usd'])}</td>
              <td>{c['oi_pct_chg']:+.1f}%</td>
              <td>{fmt_vol(c['vol24h'])}</td>
              <td>{c['funding']:+.4f}%</td>
              <td><span class="scene-badge {scene_class(c['scene'])}">{c['scene_emoji']} {c['scene']} {c['scene_name']}</span></td>
              <td><span class="tag {tag_class(c['tag'])}">{c['tag']}</span></td>
              <td style="font-size:11px;color:var(--sc-dim)">{c['note']}</td>
            </tr>\n'''

    # Build chain nodes from snapshot history
    chain_nodes = ""
    if os.path.exists(SNAPSHOT_FILE):
        with open(SNAPSHOT_FILE) as f:
            snap_data = json.load(f)
        snapshots = snap_data.get("snapshots", [])
        for i, snap in enumerate(reversed(snapshots)):
            is_latest = (i == 0)
            node_class = "chain-node latest" if is_latest else "chain-node"
            badge = '<span class="chain-badge">LATEST</span>' if is_latest else ""

            mini_rows = ""
            for coin in snap.get("coins", []):
                sc = coin.get("scene", "—")
                sn = coin.get("scene_name", "—")
                se = coin.get("scene_emoji", "⬜")
                oi_chg = coin.get("oi_pct_chg", 0)
                p = coin.get("price", 0)
                chg = coin.get("chg24h", 0)
                oi = coin.get("oi_usd", 0)
                cc = chg_class(chg)
                mini_rows += f'<tr><td><b>{coin["symbol"]}</b></td><td>{fmt_price(p)}</td><td class="{cc}">{chg:+.2f}%</td><td>{fmt_oi(oi)}</td><td>{oi_chg:+.1f}%</td><td style="color:{scene_color(sc)}">{se}{sc} {sn}</td></tr>\n'

            chain_nodes += f'''
        <div class="{node_class}">
          <div class="chain-header">
            <span class="chain-time">📸 Snapshot #{snap["id"]} — {snap.get("timestamp_bjt", snap["timestamp"])}</span>
            {badge}
          </div>
          <div class="chain-body">
            <table class="mini-table">
              <thead><tr><th>代号</th><th>价格</th><th>24h%</th><th>OI</th><th>OI变化</th><th>场景</th></tr></thead>
              <tbody>{mini_rows}</tbody>
            </table>
            <div class="chain-note"><strong>市场环境：</strong>{snap.get("market_note","")}</div>
          </div>
        </div>\n'''

    # Count stats
    n_total = len(all_data)
    n_holding = sum(1 for c in all_data if c["tag"] in ("持仓", "预警"))
    n_snapshots = len(snap_data.get("snapshots", [])) if os.path.exists(SNAPSHOT_FILE) else 1
    n_bullish = sum(1 for c in all_data if c["scene"] in ("S1", "S2", "S6"))

    # JSON-LD (separate to avoid f-string brace conflict)
    json_ld_watchlist = '{"@context":"https://schema.org","@type":"WebPage","name":"Crypto Watchlist · SingClaw","description":"加密资产观察池：拉链表结构+OI场景判定，每4h自动更新。","url":"https://singclaw.xyz/crypto/watchlist.html","publisher":{"@type":"Organization","name":"SingClaw","url":"https://singclaw.xyz"}}'

    html = f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>观察池 · Crypto Watchlist | SingClaw</title>
  <meta name="description" content="加密资产观察池：拉链表结构+OI场景判定，每4h自动更新。"/>
  <meta property="og:title" content="观察池 · Crypto Watchlist"/>
  <meta property="og:description" content="加密资产观察池：拉链表结构+OI场景判定，每4h自动更新。"/>
  <meta property="og:type" content="website"/>
  <meta property="og:image" content="https://singclaw.xyz/favicon.svg"/>
  <meta property="og:site_name" content="SingClaw"/>
  <meta property="og:url" content="https://singclaw.xyz/crypto/watchlist.html"/>
  <link rel="canonical" href="https://singclaw.xyz/crypto/watchlist.html"/>
  <link rel="icon" type="image/svg+xml" href="/favicon.svg"/>
  <script type="application/ld+json">
  {{json_ld_watchlist}}
  </script>
  <link rel="stylesheet" href="/css/design-tokens.css"/>
  <style>
    nav{{position:sticky;top:0;z-index:100;background:rgba(2,4,8,.82);backdrop-filter:blur(24px) saturate(1.4);border-bottom:1px solid var(--sc-border)}}
    .nav-inner{{height:64px;display:flex;align-items:center;justify-content:space-between}}
    .logo{{display:flex;align-items:center;gap:10px;font-weight:800;font-size:18px}}
    .logo img{{width:32px;height:32px;border-radius:8px}}
    .nav-links{{display:flex;gap:4px}}
    .nav-links a{{padding:8px 14px;border-radius:8px;font-size:13px;font-weight:500;color:var(--sc-dim);transition:all .2s}}
    .nav-links a:hover{{color:#fff;background:rgba(255,255,255,.05)}}
    .nav-links a.active{{color:var(--sc-accent);background:rgba(0,212,170,.08)}}
    .hamburger{{display:none;background:none;border:none;cursor:pointer;padding:8px}}
    .hamburger span{{display:block;width:20px;height:2px;background:var(--sc-text);margin:4px 0;border-radius:2px}}
    .mobile-menu{{display:none;position:fixed;top:64px;left:0;right:0;bottom:0;background:rgba(2,4,8,.96);backdrop-filter:blur(20px);z-index:99;padding:24px;flex-direction:column;gap:8px}}
    .mobile-menu.open{{display:flex}}
    .mobile-menu a{{padding:14px 16px;border-radius:10px;font-size:16px;font-weight:500;color:var(--sc-dim)}}
    @media(max-width:768px){{.nav-links{{display:none}}.hamburger{{display:block}}}}
    .hero{{padding:80px 0 48px;text-align:center;position:relative}}
    .hero-bg{{position:absolute;inset:0;overflow:hidden;pointer-events:none}}
    .hero-bg .orb{{position:absolute;border-radius:50%}}
    .hero-bg .orb1{{width:600px;height:600px;top:-20%;right:-10%;background:radial-gradient(circle,rgba(0,212,170,.08),transparent 55%)}}
    .hero-bg .orb2{{width:400px;height:400px;bottom:0;left:-5%;background:radial-gradient(circle,var(--sc-purple-bg),transparent 55%)}}
    .hero h1{{font-size:clamp(32px,5vw,52px);font-weight:900;letter-spacing:-.04em;line-height:1.1;margin-bottom:16px;position:relative;z-index:2}}
    .hero h1 em{{font-style:normal;background:linear-gradient(135deg,var(--sc-accent),var(--sc-purple));-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
    .hero p{{color:var(--sc-dim);font-size:17px;max-width:680px;margin:0 auto 20px;line-height:1.7;position:relative;z-index:2}}
    .hero-date{{color:var(--sc-muted);font-size:13px;position:relative;z-index:2}}
    .stats-bar{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;padding:32px 0}}
    .stat-card{{padding:18px;border-radius:14px;background:var(--sc-card);border:1px solid var(--sc-border);text-align:center}}
    .stat-num{{font-size:28px;font-weight:900;line-height:1;margin-bottom:4px}}
    .stat-label{{font-size:10px;color:var(--sc-dim);font-weight:600;text-transform:uppercase;letter-spacing:.06em}}
    .stat-green .stat-num{{color:var(--sc-accent)}}
    .stat-purple .stat-num{{color:var(--sc-purple)}}
    .stat-blue .stat-num{{color:var(--sc-blue)}}
    .stat-gold .stat-num{{color:var(--sc-gold)}}
    .filters{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:20px}}
    .filter-btn{{padding:6px 14px;border-radius:18px;font-size:12px;font-weight:600;border:1px solid var(--sc-border);background:var(--sc-card);color:var(--sc-dim);cursor:pointer;transition:all .2s}}
    .filter-btn:hover,.filter-btn.active{{color:var(--sc-accent);border-color:var(--sc-accent);background:rgba(0,212,170,.08)}}
    .scene-legend{{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px;padding:14px 18px;border-radius:12px;background:var(--sc-card);border:1px solid var(--sc-border)}}
    .scene-item{{display:flex;align-items:center;gap:4px;font-size:11px;color:var(--sc-dim)}}
    .scene-dot{{width:8px;height:8px;border-radius:50%}}
    .table-wrap{{overflow-x:auto;border-radius:14px;border:1px solid var(--sc-border);background:var(--sc-card)}}
    table{{width:100%;border-collapse:collapse;font-size:12px}}
    thead{{background:rgba(255,255,255,.03)}}
    th{{padding:12px 12px;text-align:left;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--sc-dim);white-space:nowrap;cursor:pointer;user-select:none}}
    th:hover{{color:var(--sc-text)}}
    td{{padding:10px 12px;border-top:1px solid var(--sc-border);white-space:nowrap}}
    tr:hover{{background:rgba(255,255,255,.02)}}
    .coin-name{{font-weight:800;font-size:13px}}
    .tag{{display:inline-block;padding:2px 8px;border-radius:6px;font-size:10px;font-weight:700}}
    .tag-持仓{{background:var(--sc-accent-bg);color:var(--sc-accent)}}
    .tag-观察{{background:var(--sc-purple-bg);color:var(--sc-purple)}}
    .tag-新增{{background:var(--sc-gold-bg);color:var(--sc-gold)}}
    .tag-预警{{background:var(--sc-danger-bg);color:var(--sc-danger)}}
    .scene-badge{{display:inline-flex;align-items:center;gap:4px;padding:2px 10px;border-radius:8px;font-size:11px;font-weight:700}}
    .scene-s1{{background:rgba(34,197,94,.12);color:var(--sc-success)}}
    .scene-s2{{background:var(--sc-gold-bg);color:var(--sc-gold)}}
    .scene-s1b{{background:rgba(249,115,22,.12);color:#f97316}}
    .scene-s3{{background:rgba(107,114,128,.12);color:#6b7280}}
    .scene-s4{{background:rgba(77,143,250,.12);color:var(--sc-blue)}}
    .scene-s5{{background:rgba(156,163,175,.12);color:#9ca3af}}
    .scene-s6{{background:var(--sc-purple-bg);color:var(--sc-purple)}}
    .scene-s7{{background:var(--sc-danger-bg);color:var(--sc-danger)}}
    .scene-default{{background:rgba(75,85,99,.12);color:#4b5563}}
    .chg-up{{color:var(--sc-success)}}
    .chg-down{{color:var(--sc-danger)}}
    .chg-flat{{color:var(--sc-dim)}}
    .section{{padding:40px 0;border-top:1px solid var(--sc-border)}}
    .section h2{{font-size:24px;font-weight:800;margin-bottom:8px}}
    .section p.desc{{color:var(--sc-dim);font-size:14px;line-height:1.6;margin-bottom:24px}}
    .chain{{position:relative;padding-left:28px}}
    .chain::before{{content:'';position:absolute;left:9px;top:0;bottom:0;width:2px;background:linear-gradient(180deg,var(--sc-accent),rgba(168,85,247,.3),transparent)}}
    .chain-node{{position:relative;margin-bottom:28px}}
    .chain-node::before{{content:'';position:absolute;left:-28px;top:6px;width:10px;height:10px;border-radius:50%;border:2px solid var(--sc-accent);background:var(--sc-bg)}}
    .chain-node.latest::before{{background:var(--sc-accent);box-shadow:0 0 12px var(--sc-accent-glow)}}
    .chain-header{{display:flex;align-items:center;gap:10px;margin-bottom:10px}}
    .chain-time{{font-size:13px;font-weight:800}}
    .chain-badge{{padding:2px 8px;border-radius:8px;font-size:9px;font-weight:700;background:rgba(0,212,170,.12);color:var(--sc-accent)}}
    .chain-body{{padding:14px 16px;border-radius:12px;background:var(--sc-card);border:1px solid var(--sc-border);overflow-x:auto}}
    .mini-table{{width:100%;font-size:11px;border-collapse:collapse}}
    .mini-table th{{padding:6px 8px;font-size:9px}}
    .mini-table td{{padding:5px 8px;border-top:1px solid rgba(255,255,255,.04)}}
    .chain-note{{margin-top:8px;font-size:11px;color:var(--sc-dim);line-height:1.5}}
    .chain-note strong{{color:var(--sc-text)}}
    footer.sc-w{{padding:40px 0 32px;text-align:center;position:relative}}
    footer.sc-w::before{{content:'';position:absolute;top:0;left:50%;transform:translateX(-50%);width:60%;height:1px;background:linear-gradient(90deg,transparent,var(--sc-accent),transparent)}}
    .footer-links{{display:flex;justify-content:center;flex-wrap:wrap;gap:6px 20px;margin-bottom:16px}}
    .footer-links a{{color:var(--sc-muted);font-size:12px;text-decoration:none;transition:color .2s}}
    .footer-links a:hover{{color:var(--sc-accent)}}
    footer.sc-w .copyright{{color:var(--sc-muted);font-size:11px}}
    .wrap{{max-width:var(--sc-max);margin:0 auto;padding:0 24px}}
    @media(max-width:768px){{.stats-bar{{grid-template-columns:repeat(2,1fr)}}table{{font-size:10px}}td,th{{padding:6px 8px}}}}
  </style>
</head>
<body>
  <nav>
    <div class="wrap nav-inner">
      <a href="/" class="logo"><img src="/favicon.svg" alt="SC"/>SingClaw</a>
      <div class="nav-links">
        <a href="/">首页</a>
        <a href="/crypto/">Crypto</a>
        <a href="/36/">36计</a>
        <a href="/24/">24章经</a>
        <a href="/crypto/bn-alpha.html">BN Alpha</a>
        <a href="/skills-wiki.html">Skills Wiki</a>
        <a href="/opc-onboarding.html">OPC入门</a>
        <a href="/blog/">思享录</a>
        <a href="/crypto/watchlist.html" class="active">观察池</a>
      </div>
      <button class="hamburger" onclick="document.querySelector('.mobile-menu').classList.toggle('open')"><span></span><span></span><span></span></button>
    </div>
    <div class="mobile-menu">
      <a href="/">首页</a><a href="/crypto/">Crypto</a><a href="/36/">36计</a><a href="/24/">24章经</a><a href="/crypto/bn-alpha.html">BN Alpha</a><a href="/skills-wiki.html">Skills Wiki</a><a href="/opc-onboarding.html">OPC入门</a><a href="/blog/">思享录</a><a href="/crypto/watchlist.html" class="active">观察池</a>
    </div>
  </nav>
  <main class="wrap">
    <div class="hero">
      <div class="hero-bg"><div class="orb orb1"></div><div class="orb orb2"></div></div>
      <h1>观察池 · <em>Watchlist</em></h1>
      <p>每4h自动更新 · OI场景判定 · 拉链表快照对比</p>
      <div class="hero-date">🔄 最后更新：{NOW.strftime("%Y-%m-%d %H:%M BJT")} · BTC ${btc_price:,.0f} ({btc_chg:+.2f}%) · FNG={fng_val} {fng_class}</div>
    </div>
    <div class="stats-bar">
      <div class="stat-card stat-green"><div class="stat-num">{n_total}</div><div class="stat-label">观察标的</div></div>
      <div class="stat-card stat-purple"><div class="stat-num">{n_holding}</div><div class="stat-label">活跃持仓</div></div>
      <div class="stat-card stat-gold"><div class="stat-num">{n_snapshots}</div><div class="stat-label">快照版本</div></div>
      <div class="stat-card stat-blue"><div class="stat-num">{n_bullish}</div><div class="stat-label">偏多信号</div></div>
    </div>

    <div class="section" style="border:none;padding-top:0">
      <h2>📋 实时状态 + OI场景</h2>
      <div class="scene-legend">
        <div class="scene-item"><div class="scene-dot" style="background:var(--sc-success)"></div>S1 强看多</div>
        <div class="scene-item"><div class="scene-dot" style="background:var(--sc-gold)"></div>S2 蓄力</div>
        <div class="scene-item"><div class="scene-dot" style="background:#f97316"></div>S1b 分歧</div>
        <div class="scene-item"><div class="scene-dot" style="background:#6b7280"></div>S3 投降</div>
        <div class="scene-item"><div class="scene-dot" style="background:var(--sc-blue)"></div>S4 空头回补</div>
        <div class="scene-item"><div class="scene-dot" style="background:#9ca3af"></div>S5 观望</div>
        <div class="scene-item"><div class="scene-dot" style="background:var(--sc-purple)"></div>S6 现货驱动</div>
        <div class="scene-item"><div class="scene-dot" style="background:var(--sc-danger)"></div>S7 过热</div>
      </div>
      <div class="filters">
        <button class="filter-btn active" onclick="filterTable('all')">全部</button>
        <button class="filter-btn" onclick="filterTable('持仓')">持仓</button>
        <button class="filter-btn" onclick="filterTable('Alpha')">Alpha</button>
        <button class="filter-btn" onclick="filterTable('观察')">观察</button>
        <button class="filter-btn" onclick="filterScene('S1')">🟢S1</button>
        <button class="filter-btn" onclick="filterScene('S2')">🟡S2</button>
        <button class="filter-btn" onclick="filterScene('S7')">🔴S7</button>
      </div>
      <div class="table-wrap">
        <table id="watchTable">
          <thead><tr>
            <th onclick="sortTable(0)">代号</th>
            <th onclick="sortTable(1)">价格</th>
            <th onclick="sortTable(2)">24h%</th>
            <th onclick="sortTable(3)">OI</th>
            <th onclick="sortTable(4)">OI变化</th>
            <th onclick="sortTable(5)">成交量</th>
            <th onclick="sortTable(6)">费率</th>
            <th>场景</th>
            <th>标签</th>
            <th>备注</th>
          </tr></thead>
          <tbody>
{table_rows}          </tbody>
        </table>
      </div>
    </div>

    <div class="section">
      <h2>🔗 拉链表 · 快照历史</h2>
      <p class="desc">每4h生成快照，记录价格/OI/场景状态。纵向追踪每个币的场景变迁。</p>
      <div class="chain">
{chain_nodes}
      </div>
    </div>
  </main>
  <footer class="sc-w"><div class="wrap">
    <div class="footer-links">
      <a href="/">首页</a><a href="/36/">36计</a><a href="/24/">24章经</a><a href="/crypto/">Crypto</a><a href="/crypto/bn-alpha.html">BN Alpha</a><a href="/crypto/watchlist.html">观察池</a><a href="/skills-wiki.html">Skills Wiki</a><a href="/blog/">思享录</a>
    </div>
    <div class="footer-line"></div>
    <p class="copyright">SingClaw · Crypto Watchlist · 每4h自动更新 · 数据来源 Binance</p>
  </div></footer>
  <script>
    function filterTable(tag){{
      document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));
      event.target.classList.add('active');
      document.querySelectorAll('#watchTable tbody tr').forEach(tr=>{{
        tr.style.display=(tag==='all'||tr.dataset.tag===tag)?'':'none';
      }});
    }}
    function filterScene(sc){{
      document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));
      event.target.classList.add('active');
      document.querySelectorAll('#watchTable tbody tr').forEach(tr=>{{
        tr.style.display=(tr.dataset.scene===sc)?'':'none';
      }});
    }}
    let sortDir={{}};
    function sortTable(col){{
      const table=document.getElementById('watchTable');
      const tbody=table.querySelector('tbody');
      const rows=Array.from(tbody.querySelectorAll('tr'));
      const dir=sortDir[col]=!sortDir[col];
      rows.sort((a,b)=>{{
        let aV=a.cells[col].textContent.trim(),bV=b.cells[col].textContent.trim();
        const aN=parseFloat(aV.replace(/[$%,MK]/g,'')),bN=parseFloat(bV.replace(/[$%,MK]/g,''));
        if(!isNaN(aN)&&!isNaN(bN))return dir?aN-bN:bN-aN;
        return dir?aV.localeCompare(bV):bV.localeCompare(aV);
      }});
      rows.forEach(r=>tbody.appendChild(r));
    }}
  </script>
</body>
</html>'''

    with open(HTML_FILE, "w") as f:
        f.write(html)
    print(f"  ✅ HTML generated: {HTML_FILE}")

def main():
    print(f"\n{'='*60}")
    print(f"🔄 观察池更新 — {NOW.strftime('%Y-%m-%d %H:%M BJT')}")
    print(f"{'='*60}")

    # 1. Get market context
    print("\n📊 获取市场环境...")
    btc_price, btc_chg, fng_val, fng_class = get_btc_fng()
    print(f"  BTC: ${btc_price:,.0f} ({btc_chg:+.2f}%) | FNG: {fng_val} {fng_class}")

    # 2. Collect all coin data
    print(f"\n📡 抓取 {len(WATCHLIST)} 个标的数据...")
    all_data = collect_all_data()
    print(f"  成功获取: {len(all_data)}/{len(WATCHLIST)}")

    # 3. Scene summary
    print(f"\n🎯 场景分布:")
    scene_counts = {}
    for c in all_data:
        s = f"{c['scene']} {c['scene_name']}"
        scene_counts[s] = scene_counts.get(s, 0) + 1
    for s, cnt in sorted(scene_counts.items()):
        coins = [c['symbol'] for c in all_data if f"{c['scene']} {c['scene_name']}" == s]
        print(f"  {s}: {cnt}个 — {', '.join(coins)}")

    # 4. Save snapshot
    print(f"\n💾 保存快照...")
    save_snapshot(all_data, btc_price, btc_chg, fng_val, fng_class)

    # 5. Generate HTML
    print(f"\n🌐 生成网页...")
    generate_html(all_data, btc_price, btc_chg, fng_val, fng_class)

    # 6. Git deploy
    print(f"\n🚀 部署...")
    os.system("cd /root/.openclaw/workspace/singclaw-site && git add crypto/watchlist.html && git commit -m 'auto: watchlist update' && git push origin main 2>&1 | tail -3")

    print(f"\n{'='*60}")
    print(f"✅ 完成! https://singclaw.xyz/crypto/watchlist.html")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
