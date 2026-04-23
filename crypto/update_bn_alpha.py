#!/usr/bin/env python3
"""
BN Alpha Auto-Update Script
- Fetches latest Binance futures/spot data
- Classifies Alpha (futures-only) vs Normal (has spot)
- Calculates 30-day daily Top10 gainers
- Generates AI analysis/interpretation
- Updates singclaw-site/crypto/bn-alpha.html
- Git push to deploy via Vercel
"""

import json
import time
import urllib.request
import os
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ─── Config ───
SITE_DIR = Path(os.path.expanduser("~/.openclaw/workspace/singclaw-site"))
OUTPUT_HTML = SITE_DIR / "crypto" / "bn-alpha.html"
DATA_CACHE = Path(os.path.expanduser("~/.openclaw/workspace/crypto/bn_alpha_data.json"))

def fetch_json(url, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            if i < retries - 1:
                time.sleep(1)
            else:
                print(f"FAILED: {url}: {e}")
                return None

def get_futures_symbols():
    info = fetch_json("https://fapi.binance.com/fapi/v1/exchangeInfo")
    symbols = {}
    for s in info["symbols"]:
        if s["contractType"] == "PERPETUAL" and s["quoteAsset"] == "USDT" and s["status"] == "TRADING":
            symbols[s["symbol"]] = s["baseAsset"]
    return symbols

def get_spot_bases():
    info = fetch_json("https://api.binance.com/api/v3/exchangeInfo")
    bases = set()
    for s in info["symbols"]:
        if s["quoteAsset"] == "USDT" and s["status"] == "TRADING":
            bases.add(s["baseAsset"])
    return bases

def get_24h_tickers():
    tickers = fetch_json("https://fapi.binance.com/fapi/v1/ticker/24hr")
    return {t["symbol"]: {
        "price": float(t["lastPrice"]),
        "change_pct": float(t["priceChangePercent"]),
        "volume_usd": float(t["quoteVolume"]),
    } for t in tickers}

def get_daily_klines(symbol, limit=31):
    data = fetch_json(f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=1d&limit={limit}")
    if not data:
        return []
    result = []
    for k in data:
        o, c = float(k[1]), float(k[4])
        chg = ((c - o) / o) * 100 if o > 0 else 0
        dt = datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        result.append({"date": dt, "change": round(chg, 2)})
    return result

def generate_ai_analysis(stats):
    """Generate AI interpretation text based on data"""
    lines = []
    
    total_futures = stats["total_futures"]
    alpha_count = stats["alpha_count"]
    normal_count = stats["normal_count"]
    alpha_pct = alpha_count / total_futures * 100
    top10_alpha_pct = stats["top10_alpha_pct"]
    overweight = stats["overweight_ratio"]
    
    # Market regime
    alpha_avg = stats["alpha_avg_today"]
    normal_avg = stats["normal_avg_today"]
    
    lines.append("## 🤖 AI 解读")
    lines.append("")
    
    # Overweight analysis
    if overweight > 2.5:
        lines.append(f"**Alpha超额极强（{overweight:.2f}x）**：Alpha币占池子{alpha_pct:.1f}%但吃掉了{top10_alpha_pct:.1f}%的Top10席位。")
        lines.append("当前是Alpha币的强势周期，小市值合约币的投机热度远超主流币。建议关注高频上榜币的轮动机会。")
    elif overweight > 1.5:
        lines.append(f"**Alpha适度超额（{overweight:.2f}x）**：Alpha币在Top10中的占比高于其池子比例，说明小市值合约币仍有结构性机会。")
    else:
        lines.append(f"**Alpha超额减弱（{overweight:.2f}x）**：Alpha币的超额表现在收敛，市场热度可能在回归主流币。谨慎追Alpha。")
    
    lines.append("")
    
    # Today's comparison
    if alpha_avg > normal_avg + 2:
        lines.append(f"📈 今日Alpha组均涨{alpha_avg:+.2f}%，跑赢Normal组({normal_avg:+.2f}%)，Alpha动量持续。")
    elif normal_avg > alpha_avg + 2:
        lines.append(f"📉 今日Normal组均涨{normal_avg:+.2f}%，反超Alpha组({alpha_avg:+.2f}%)，资金回流主流币。")
    else:
        lines.append(f"⚖️ 今日两组涨幅接近（Alpha {alpha_avg:+.2f}% vs Normal {normal_avg:+.2f}%），市场分化不明显。")
    
    lines.append("")
    
    # Top frequency coins
    if stats.get("top_freq_coins"):
        top3 = stats["top_freq_coins"][:3]
        names = "、".join([f"{c[0]}({c[1]}次)" for c in top3])
        lines.append(f"🏆 近30天最稳定的Alpha龙头：{names}。这些币反复出现在Top10说明有持续的资金关注。")
    
    lines.append("")
    
    # Risk warning
    recent_alpha_counts = stats.get("recent_daily_alpha_counts", [])
    if recent_alpha_counts:
        last3 = recent_alpha_counts[-3:]
        avg_recent = sum(last3) / len(last3)
        if avg_recent > 7:
            lines.append("⚠️ 近3天Alpha在Top10占比极高（>70%），市场投机情绪过热，注意回调风险。")
        elif avg_recent < 4:
            lines.append("💡 近3天Alpha在Top10占比偏低（<40%），投机降温中，等待下一轮启动信号。")
    
    return "\n".join(lines)

def build_html(stats, ai_text, daily_top10, alpha_symbols, today_alpha_top10, today_normal_top10, freq_coins):
    """Build the complete HTML page"""
    now = datetime.now(timezone(timedelta(hours=8)))
    date_str = now.strftime("%Y-%m-%d %H:%M")
    
    # Freq bars HTML
    freq_html = ""
    max_freq = freq_coins[0][1] if freq_coins else 1
    for i, (name, count) in enumerate(freq_coins[:16]):
        pct = count / max_freq * 100
        freq_html += f'''      <div class="freq-item">
        <div class="freq-rank">{i+1}</div>
        <div class="freq-name">{name}</div>
        <div class="freq-bar-wrap"><div class="freq-bar-fill" style="width:{pct:.0f}%"></div></div>
        <div class="freq-count">{count} 次</div>
      </div>\n'''
    
    # Today top10 HTML
    def top10_list_html(items):
        html = ""
        for i, (sym, pct, vol) in enumerate(items[:10]):
            name = sym.replace("USDT", "")
            cls = "pos" if pct > 0 else "neg"
            html += f'          <li><span class="rank">{i+1}</span><span class="coin">{name}</span><span class="chg {cls}">{pct:+.2f}%</span></li>\n'
        return html
    
    # Daily cards HTML (top 8 days by alpha count)
    sorted_days = sorted(daily_top10, key=lambda d: d["alpha_count"], reverse=True)[:8]
    daily_html = ""
    for day in sorted_days:
        dt_short = day["date"][5:]  # MM-DD
        daily_html += f'''      <div class="daily-card">
        <div class="daily-date">{dt_short}</div>
        <div class="daily-meta">Alpha占比 <span class="alpha-ratio">{day["alpha_count"]}/10</span></div>
        <ol class="daily-list">\n'''
        for i, (sym, chg, is_alpha) in enumerate(day["top10"]):
            tag = "🔶" if is_alpha else "🔵"
            name = sym.replace("USDT", "")
            daily_html += f'          <li><span class="rank">{i+1}</span>{tag} <span class="coin">{name}</span><span class="chg pos">{chg:+.1f}%</span></li>\n'
        daily_html += '''        </ol>
      </div>\n'''
    
    # Alpha coin tags
    alpha_tags = "".join([f'<span class="alpha-coin">{s.replace("USDT","")}</span>' for s in sorted(alpha_symbols)])
    
    # AI analysis HTML
    ai_html = ai_text.replace("## ", "<h3>").replace("\n\n", "</p><p>").replace("**", "<strong>").replace("**", "</strong>")
    # Simple markdown to HTML
    ai_paragraphs = []
    for line in ai_text.split("\n"):
        if line.startswith("## "):
            ai_paragraphs.append(f'<h3>{line[3:]}</h3>')
        elif line.startswith("**") and line.endswith("**"):
            ai_paragraphs.append(f'<p><strong>{line[2:-2]}</strong></p>')
        elif line.strip():
            # Bold markers
            import re
            line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
            ai_paragraphs.append(f'<p>{line}</p>')
    ai_section_html = "\n".join(ai_paragraphs)
    
    html = f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>BN Alpha 回测报告 · 超额命中{stats["overweight_ratio"]:.2f}x | SingClaw</title>
  <meta name="description" content="Binance {stats["total_futures"]}个合约币分组统计：{stats["alpha_count"]}个Alpha币占池子{stats["alpha_count"]/stats["total_futures"]*100:.0f}%却霸占{stats["top10_alpha_pct"]:.0f}%的每日Top10涨幅榜。30天回测+AI解读。"/>
  <meta property="og:title" content="BN Alpha 30天回测 · 超额命中{stats["overweight_ratio"]:.2f}x"/>
  <meta property="og:description" content="{stats["alpha_count"]}个Alpha币占{stats["alpha_count"]/stats["total_futures"]*100:.0f}%池子，拿走{stats["top10_alpha_pct"]:.0f}%的Top10席位。"/>
  <meta property="og:url" content="https://singclaw.xyz/crypto/bn-alpha.html"/>
  <link rel="icon" type="image/svg+xml" href="/favicon.svg"/>
  <link rel="stylesheet" href="/css/design-tokens.css"/>
  <script type="application/ld+json">
  {{
    "@context":"https://schema.org",
    "@type":"Article",
    "headline":"BN Alpha 30天回测报告",
    "description":"Binance合约Alpha币回测，超额命中率{stats["overweight_ratio"]:.2f}倍",
    "url":"https://singclaw.xyz/crypto/bn-alpha.html",
    "datePublished":"{now.strftime("%Y-%m-%d")}",
    "author":{{"@type":"Organization","name":"SingClaw"}},
    "publisher":{{"@type":"Organization","name":"SingClaw","url":"https://singclaw.xyz"}}
  }}
  </script>
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
    .mobile-menu a.active{{color:var(--sc-accent)}}
    @media(max-width:768px){{.nav-links{{display:none}}.hamburger{{display:block}}}}
    .hero{{padding:80px 0 48px;text-align:center;position:relative}}
    .hero-bg{{position:absolute;inset:0;overflow:hidden;pointer-events:none}}
    .hero-bg .orb{{position:absolute;border-radius:50%}}
    .hero-bg .orb1{{width:600px;height:600px;top:-20%;right:-10%;background:radial-gradient(circle,rgba(0,212,170,.08),transparent 55%)}}
    .hero-bg .orb2{{width:400px;height:400px;bottom:0;left:-5%;background:radial-gradient(circle,var(--sc-gold-bg),transparent 55%)}}
    .hero h1{{font-size:clamp(32px,5vw,52px);font-weight:900;letter-spacing:-.04em;line-height:1.1;margin-bottom:16px;position:relative;z-index:2}}
    .hero h1 em{{font-style:normal;background:linear-gradient(135deg,var(--sc-gold),var(--sc-accent));-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
    .hero p{{color:var(--sc-dim);font-size:17px;max-width:680px;margin:0 auto 28px;line-height:1.7;position:relative;z-index:2}}
    .hero-date{{color:var(--sc-muted);font-size:13px;position:relative;z-index:2}}
    .stats-bar{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px;padding:40px 0}}
    .stat-card{{padding:24px;border-radius:16px;background:var(--sc-card);border:1px solid var(--sc-border);text-align:center}}
    .stat-num{{font-size:36px;font-weight:900;line-height:1;margin-bottom:6px}}
    .stat-label{{font-size:12px;color:var(--sc-dim);font-weight:500;text-transform:uppercase;letter-spacing:.05em}}
    .stat-green .stat-num{{color:var(--sc-accent)}}
    .stat-orange .stat-num{{color:var(--sc-gold)}}
    .stat-blue .stat-num{{color:var(--sc-blue,#4d8ffa)}}
    .stat-purple .stat-num{{color:var(--sc-purple,#a855f7)}}
    .section{{padding:48px 0;border-top:1px solid var(--sc-border)}}
    .section-header{{margin-bottom:32px}}
    .section-header h2{{font-size:28px;font-weight:800;margin-bottom:8px}}
    .section-header p{{color:var(--sc-dim);font-size:15px;line-height:1.6}}
    .ai-box{{padding:28px;border-radius:16px;background:linear-gradient(135deg,rgba(0,212,170,.04),rgba(77,143,250,.04));border:1px solid rgba(0,212,170,.15);margin-bottom:32px}}
    .ai-box h3{{font-size:20px;font-weight:800;margin-bottom:16px;color:var(--sc-accent)}}
    .ai-box p{{color:var(--sc-dim);font-size:14px;line-height:1.8;margin-bottom:10px}}
    .ai-box strong{{color:var(--sc-text)}}
    .freq-list{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px}}
    .freq-item{{display:flex;align-items:center;gap:12px;padding:14px 16px;border-radius:12px;background:var(--sc-card);border:1px solid var(--sc-border)}}
    .freq-rank{{width:28px;height:28px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;background:var(--sc-gold-bg);color:var(--sc-gold);flex-shrink:0}}
    .freq-name{{font-weight:700;font-size:15px;flex:1}}
    .freq-bar-wrap{{flex:2;height:8px;border-radius:4px;background:rgba(255,255,255,.06);overflow:hidden}}
    .freq-bar-fill{{height:100%;border-radius:4px;background:linear-gradient(90deg,var(--sc-gold),var(--sc-accent))}}
    .freq-count{{font-size:13px;font-weight:600;color:var(--sc-dim);min-width:50px;text-align:right}}
    .daily-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:16px}}
    .daily-card{{padding:20px;border-radius:14px;background:var(--sc-card);border:1px solid var(--sc-border)}}
    .daily-date{{font-weight:800;font-size:15px;margin-bottom:4px}}
    .daily-meta{{font-size:12px;color:var(--sc-dim);margin-bottom:12px}}
    .daily-meta .alpha-ratio{{color:var(--sc-gold);font-weight:700}}
    .daily-list{{list-style:none;padding:0;margin:0}}
    .daily-list li{{display:flex;align-items:center;gap:8px;padding:4px 0;font-size:13px}}
    .daily-list .rank{{width:20px;color:var(--sc-muted);font-weight:600;text-align:right;flex-shrink:0}}
    .daily-list .coin{{font-weight:700;min-width:80px}}
    .daily-list .chg{{font-weight:600;font-variant-numeric:tabular-nums}}
    .pos{{color:#22c55e}}.neg{{color:#ef4444}}
    .strat-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px}}
    .strat-card{{padding:24px;border-radius:14px;background:var(--sc-card);border:1px solid var(--sc-border)}}
    .strat-card h3{{font-size:18px;font-weight:800;margin-bottom:8px}}
    .strat-card p{{font-size:14px;color:var(--sc-dim);line-height:1.6}}
    .strat-icon{{font-size:28px;margin-bottom:12px}}
    .risk-banner{{padding:20px 24px;border-radius:14px;background:rgba(239,68,68,.06);border:1px solid rgba(239,68,68,.15);margin-top:40px}}
    .risk-banner h3{{color:#ef4444;font-size:15px;font-weight:800;margin-bottom:8px}}
    .risk-banner p{{color:var(--sc-dim);font-size:13px;line-height:1.6}}
    .alpha-coin-grid{{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px}}
    .alpha-coin{{padding:4px 12px;border-radius:8px;font-size:12px;font-weight:600;background:var(--sc-gold-bg);border:1px solid var(--sc-gold-border);color:var(--sc-gold)}}
    @media(max-width:768px){{.daily-grid{{grid-template-columns:1fr}}.stats-bar{{grid-template-columns:repeat(2,1fr)}}.freq-list{{grid-template-columns:1fr}}.strat-grid{{grid-template-columns:1fr}}}}
    @media(max-width:480px){{.stats-bar{{grid-template-columns:1fr}}}}
    footer{{padding:40px 0;border-top:1px solid var(--sc-border);text-align:center;color:var(--sc-muted);font-size:13px}}
  </style>
</head>
<body>
<nav>
  <div class="container">
    <div class="nav-inner">
      <a href="/" class="logo"><img src="/favicon.svg" alt="SingClaw"/> SingClaw</a>
      <div class="nav-links">
        <a href="/36/">36计</a>
        <a href="/24/">24节气</a>
        <a href="/game/">ShrimpFi</a>
        <a href="/crypto/">5层分析</a>
        <a href="/crypto/bn-alpha.html" class="active">BN Alpha</a>
        <a href="/stars/">明星站</a>
      </div>
      <button class="hamburger" onclick="document.querySelector('.mobile-menu').classList.toggle('open')">
        <span></span><span></span><span></span>
      </button>
    </div>
  </div>
</nav>
<div class="mobile-menu">
  <a href="/36/">36计</a>
  <a href="/24/">24节气</a>
  <a href="/game/">ShrimpFi</a>
  <a href="/crypto/">5层分析</a>
  <a href="/crypto/bn-alpha.html" class="active">BN Alpha</a>
  <a href="/stars/">明星站</a>
</div>

<section class="hero">
  <div class="hero-bg"><div class="orb orb1"></div><div class="orb orb2"></div></div>
  <div class="container">
    <h1>BN Alpha <em>30天回测</em></h1>
    <p>Binance {stats["total_futures"]}个USDT永续合约中，{stats["alpha_count"]}个只有合约没有现货的"Alpha币"，占池子{stats["alpha_count"]/stats["total_futures"]*100:.0f}%却拿走了每日Top10涨幅榜{stats["top10_alpha_pct"]:.0f}%的席位。超额命中率 <strong>{stats["overweight_ratio"]:.2f}倍</strong>。</p>
    <div class="hero-date">📅 更新时间: {date_str} (UTC+8) · 数据来源: Binance Futures API · 自动更新</div>
  </div>
</section>

<div class="container">
  <div class="stats-bar">
    <div class="stat-card stat-orange"><div class="stat-num">{stats["total_futures"]}</div><div class="stat-label">合约总数</div></div>
    <div class="stat-card stat-green"><div class="stat-num">{stats["alpha_count"]}</div><div class="stat-label">Alpha币 (无现货)</div></div>
    <div class="stat-card stat-blue"><div class="stat-num">{stats["normal_count"]}</div><div class="stat-label">Normal (有现货)</div></div>
    <div class="stat-card stat-purple"><div class="stat-num">{stats["overweight_ratio"]:.2f}x</div><div class="stat-label">超额命中倍数</div></div>
  </div>
</div>

<div class="container">
  <section class="section">
    <div class="ai-box">
      {ai_section_html}
    </div>
  </section>
</div>

<div class="container">
  <section class="section">
    <div class="section-header">
      <h2>🏆 30天高频上榜 Alpha 币</h2>
      <p>过去30天中出现在每日Top10涨幅榜次数最多的Alpha币</p>
    </div>
    <div class="freq-list">
{freq_html}    </div>
  </section>
</div>

<div class="container">
  <section class="section">
    <div class="section-header">
      <h2>📈 今日 24h 分组涨幅</h2>
      <p>{now.strftime("%Y-%m-%d")} · Alpha组 vs Normal组 Top 10 对比</p>
    </div>
    <div class="daily-grid">
      <div class="daily-card">
        <div class="daily-date">🔶 Alpha Top 10</div>
        <div class="daily-meta">均涨 <span class="alpha-ratio">{stats["alpha_avg_today"]:+.2f}%</span> · {stats["alpha_up"]}涨 / {stats["alpha_down"]}跌</div>
        <ol class="daily-list">
{top10_list_html(today_alpha_top10)}        </ol>
      </div>
      <div class="daily-card">
        <div class="daily-date">🔵 Normal Top 10</div>
        <div class="daily-meta">均涨 {stats["normal_avg_today"]:+.2f}% · {stats["normal_up"]}涨 / {stats["normal_down"]}跌</div>
        <ol class="daily-list">
{top10_list_html(today_normal_top10)}        </ol>
      </div>
    </div>
  </section>
</div>

<div class="container">
  <section class="section">
    <div class="section-header">
      <h2>📅 30天每日 Top 10 涨幅榜</h2>
      <p>🔶 = Alpha币 (无现货) · 🔵 = Normal (有现货) · 按Alpha占比排序展示Top8天</p>
    </div>
    <div class="daily-grid">
{daily_html}    </div>
  </section>
</div>

<div class="container">
  <section class="section">
    <div class="section-header">
      <h2>💡 基于回测的操作策略</h2>
    </div>
    <div class="strat-grid">
      <div class="strat-card"><div class="strat-icon">1️⃣</div><h3>首日暴涨次日追</h3><p>Alpha币首次进入Top10且涨幅>50%，次日回调5-10%时追入，持有1-2天。</p></div>
      <div class="strat-card"><div class="strat-icon">2️⃣</div><h3>龙头见顶换轮动</h3><p>龙头连续上榜3天后回落，关注同组其他高频币是否接力启动。</p></div>
      <div class="strat-card"><div class="strat-icon">3️⃣</div><h3>成交量>$2000万</h3><p>暴涨必须配合足够成交量，低成交量的暴涨高反噬风险。</p></div>
      <div class="strat-card"><div class="strat-icon">4️⃣</div><h3>硬止损 -8% / 止盈 +25%</h3><p>无现货=深度差+插针多。小仓高赔率，止损必须硬。</p></div>
    </div>
    <div class="risk-banner">
      <h3>⚠️ 风险提示</h3>
      <p>Alpha币的高波动性是双刃剑。回测不代表未来。合约有爆仓风险。本页面仅为数据研究，不构成投资建议。</p>
    </div>
  </section>
</div>

<div class="container">
  <section class="section">
    <div class="section-header">
      <h2>📋 完整 Alpha 币列表 ({stats["alpha_count"]}个)</h2>
    </div>
    <div class="alpha-coin-grid">{alpha_tags}</div>
  </section>
</div>

<footer>
  <div class="container">
    <p>SingClaw · Crypto Alpha Research · 自动更新 · 数据来源: Binance Futures API</p>
    <p style="margin-top:8px">© 2026 SingClaw. 仅供研究参考，不构成投资建议。</p>
  </div>
</footer>
</body>
</html>'''
    return html

def git_push():
    """Git add, commit, push"""
    os.chdir(str(SITE_DIR))
    subprocess.run(["git", "add", "crypto/bn-alpha.html"], check=True)
    result = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
    if result.returncode == 0:
        print("No changes to commit")
        return False
    now = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M")
    subprocess.run(["git", "commit", "-m", f"auto: update BN Alpha data {now}"], check=True)
    subprocess.run(["git", "push"], check=True)
    print(f"✅ Pushed at {now}")
    return True

def main():
    print("🔄 Starting BN Alpha update...")
    
    # 1. Get symbols
    print("  Fetching futures symbols...")
    futures_map = get_futures_symbols()
    futures_symbols = set(futures_map.keys())
    futures_bases = set(futures_map.values())
    
    print("  Fetching spot symbols...")
    spot_bases = get_spot_bases()
    
    alpha_bases = futures_bases - spot_bases
    normal_bases = futures_bases & spot_bases
    alpha_symbols = sorted([b + "USDT" for b in alpha_bases if b + "USDT" in futures_symbols])
    normal_symbols = sorted([b + "USDT" for b in normal_bases if b + "USDT" in futures_symbols])
    alpha_set = set(alpha_symbols)
    
    print(f"  Total: {len(futures_symbols)} | Alpha: {len(alpha_symbols)} | Normal: {len(normal_symbols)}")
    
    # 2. Today's tickers
    print("  Fetching 24h tickers...")
    ticker_map = get_24h_tickers()
    
    alpha_changes = [(s, ticker_map[s]["change_pct"], ticker_map[s]["volume_usd"]) 
                     for s in alpha_symbols if s in ticker_map]
    normal_changes = [(s, ticker_map[s]["change_pct"], ticker_map[s]["volume_usd"]) 
                      for s in normal_symbols if s in ticker_map]
    alpha_changes.sort(key=lambda x: x[1], reverse=True)
    normal_changes.sort(key=lambda x: x[1], reverse=True)
    
    alpha_pcts = [c[1] for c in alpha_changes]
    normal_pcts = [c[1] for c in normal_changes]
    
    # 3. 30-day klines
    print(f"  Fetching 30-day klines for {len(futures_symbols)} symbols...")
    all_klines = {}
    syms_list = sorted(futures_symbols)
    for idx, sym in enumerate(syms_list):
        klines = get_daily_klines(sym)
        if klines:
            all_klines[sym] = klines
        if (idx + 1) % 100 == 0:
            print(f"    ... {idx+1}/{len(syms_list)}")
            time.sleep(0.3)
    
    # Build daily top10
    dates = set()
    for sym, daily in all_klines.items():
        for d in daily:
            dates.add(d["date"])
    dates = sorted(dates)[-30:]
    
    from collections import Counter
    top10_freq = Counter()
    daily_top10_results = []
    
    for dt in dates:
        day_changes = []
        for sym, daily in all_klines.items():
            for d in daily:
                if d["date"] == dt:
                    day_changes.append((sym, d["change"], sym in alpha_set))
                    break
        day_changes.sort(key=lambda x: x[1], reverse=True)
        top10 = day_changes[:10]
        alpha_in_top10 = sum(1 for _, _, a in top10 if a)
        
        for s, _, _ in top10:
            top10_freq[s] += 1
        
        daily_top10_results.append({
            "date": dt,
            "top10": [(s, c, a) for s, c, a in top10],
            "alpha_count": alpha_in_top10,
        })
    
    total_alpha_hits = sum(r["alpha_count"] for r in daily_top10_results)
    total_slots = len(daily_top10_results) * 10
    
    # Alpha frequency
    alpha_freq = sorted([(s.replace("USDT",""), c) for s, c in top10_freq.items() if s in alpha_set], 
                        key=lambda x: x[1], reverse=True)
    
    # 4. Build stats
    stats = {
        "total_futures": len(futures_symbols),
        "alpha_count": len(alpha_symbols),
        "normal_count": len(normal_symbols),
        "top10_alpha_pct": total_alpha_hits / total_slots * 100 if total_slots > 0 else 0,
        "overweight_ratio": (total_alpha_hits / total_slots) / (len(alpha_symbols) / len(futures_symbols)) if len(futures_symbols) > 0 else 0,
        "alpha_avg_today": sum(alpha_pcts) / len(alpha_pcts) if alpha_pcts else 0,
        "normal_avg_today": sum(normal_pcts) / len(normal_pcts) if normal_pcts else 0,
        "alpha_up": sum(1 for p in alpha_pcts if p > 0),
        "alpha_down": sum(1 for p in alpha_pcts if p < 0),
        "normal_up": sum(1 for p in normal_pcts if p > 0),
        "normal_down": sum(1 for p in normal_pcts if p < 0),
        "top_freq_coins": alpha_freq[:10],
        "recent_daily_alpha_counts": [r["alpha_count"] for r in daily_top10_results[-7:]],
    }
    
    # 5. Generate AI analysis
    print("  Generating AI analysis...")
    ai_text = generate_ai_analysis(stats)
    
    # 6. Build HTML
    print("  Building HTML...")
    html = build_html(stats, ai_text, daily_top10_results, alpha_symbols,
                      alpha_changes[:10], normal_changes[:10], alpha_freq)
    
    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"  Written to {OUTPUT_HTML}")
    
    # 7. Save cache
    cache = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "stats": {k: v for k, v in stats.items() if not isinstance(v, list) or k == "top_freq_coins"},
    }
    DATA_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    
    # 8. Git push
    print("  Pushing to GitHub...")
    git_push()
    
    print("✅ BN Alpha update complete!")

if __name__ == "__main__":
    main()
