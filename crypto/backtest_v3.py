#!/usr/bin/env python3
"""V3 极端费率策略回测"""
import json, time, traceback
from datetime import datetime, timezone, timedelta
from hyperliquid.info import Info

tz8=timezone(timedelta(hours=8))
INITIAL_CAPITAL=300.0
COINS=["BTC","ETH","SOL","AVAX","APT","ATOM","SUI","JUP"]
STOP_ATR_MULT=2.0; TP_ATR_MULT=3.0; DEFAULT_LEVERAGE=3
MAX_MARGIN_PCT=0.15; MAX_POSITIONS=5; DAILY_LOSS_LIMIT=0.03; SIGNAL_THRESHOLD=0.6

def calc_sma(v,p): return sum(v[-p:])/p if len(v)>=p else None
def calc_rsi(c,p=14):
    if len(c)<p+1: return None
    d=[c[i]-c[i-1] for i in range(1,len(c))]; g=[max(0,x) for x in d[-p:]]; l=[max(0,-x) for x in d[-p:]]
    ag,al=sum(g)/p,sum(l)/p; return 100-(100/(1+ag/al)) if al else 100
def calc_atr(c,p=14):
    if len(c)<p+1: return None
    trs=[]
    for i in range(1,len(c)):
        h,l,pc=float(c[i]['h']),float(c[i]['l']),float(c[i-1]['c'])
        trs.append(max(h-l,abs(h-pc),abs(l-pc)))
    return sum(trs[-p:])/p
def calc_macd(c):
    if len(c)<26: return None,None
    e12=e26=pe12=pe26=c[0]
    for i,x in enumerate(c):
        e12=e12*11/13+x*2/13; e26=e26*25/27+x*2/27
        if i<len(c)-1: pe12=pe12*11/13+x*2/13; pe26=pe26*25/27+x*2/27
    return e12-e26,pe12-pe26

def get_funding(flist,ts):
    rates=[float(f['fundingRate']) for f in flist if f['time']<=ts]
    if not rates: return 0,0,0
    cur=rates[-1]
    recent=rates[-3:] if len(rates)>=3 else rates
    older=rates[-6:-3] if len(rates)>=6 else rates[:max(0,len(rates)-3)]
    avg_r=sum(recent)/len(recent) if recent else 0
    avg_o=sum(older)/len(older) if older else 0
    return cur, avg_r-avg_o, sum(rates)/len(rates)

def signal(candles,flist,idx):
    cl=[float(c['c']) for c in candles[:idx+1]]; vo=[float(c['v']) for c in candles[:idx+1]]
    if len(cl)<50: return 0,{}
    ma20=calc_sma(cl,20); ma50=calc_sma(cl,50); rsi=calc_rsi(cl,14)
    atr=calc_atr(candles[:idx+1],14); dif,pd=calc_macd(cl)
    if any(x is None for x in [ma20,ma50,rsi,atr,dif,pd]): return 0,{}
    cur_fund,fund_chg,fund_avg=get_funding(flist,candles[idx]['t'])
    score=0; extreme=None
    score+=0.35 if ma20>ma50 else -0.35
    if rsi<30: score+=0.20
    elif rsi>70: score-=0.20
    elif rsi<40: score+=0.08
    elif rsi>60: score-=0.08
    if dif>0 and dif>pd: score+=0.15
    elif dif<0 and dif<pd: score-=0.15
    # V3: 极端费率加权
    if cur_fund<-0.0003:
        score+=0.8; extreme="⚡极端负费率_LONG"
        if fund_chg<-0.0002: score+=0.15; extreme="⚡⚡加速负费率_LONG"
    elif cur_fund<-0.0001:
        score+=0.45; extreme="负费率_LONG"
        if fund_chg<-0.0001: score+=0.1; extreme="恶化负费率_LONG"
    elif cur_fund>0.0002:
        score-=0.8; extreme="⚡极端正费率_SHORT"
        if fund_chg>0.0002: score-=0.15; extreme="⚡⚡加速正费率_SHORT"
    else:
        if cur_fund>0.0001: score+=0.15
        elif cur_fund<-0.0001: score-=0.15
    va=calc_sma(vo,20)
    if va and va>0 and vo[-1]<va*0.8: return 0,{}
    thr=0.4 if extreme else SIGNAL_THRESHOLD
    if score>thr: return 1,{'rsi':rsi,'atr':atr,'funding':cur_fund,'chg':fund_chg,'score':score,'extreme':extreme}
    elif score<-thr: return -1,{'rsi':rsi,'atr':atr,'funding':cur_fund,'chg':fund_chg,'score':score,'extreme':extreme}
    return 0,{}

if __name__ == "__main__":
    print("🚀 V3 极端费率策略回测 (30天, 4h)")
    print("  负费率阈值: -0.01% | 极端: -0.03% | 极端正: +0.02%\n")

    info=Info(base_url="https://api.hyperliquid.xyz",skip_ws=True)
    now_ms=int(time.time()*1000); start_ms=now_ms-30*86400000
    data={}
    for coin in COINS:
        data[coin]={"c":info.candles_snapshot(coin,"4h",start_ms,now_ms),"f":info.funding_history(coin,start_ms)}
        print(f"  {coin} ready")

    cap=INITIAL_CAPITAL; pos={}; trades=[]; eq=[]; dp=0; ds=None; stk=0
    btc=data["BTC"]["c"]

    for idx in range(50,len(btc)):
        ts=btc[idx]['t']; dt=datetime.fromtimestamp(ts/1000,tz=tz8)
        if ds is None or dt.date()!=ds: ds=dt.date(); dp=0; stk=0

        # 止损止盈
        cl=[]
        for coin in list(pos.keys()):
            if coin not in data: continue
            cd=None
            for x in data[coin]["c"]:
                if x['t']==ts: cd=x; break
            if not cd: continue
            mr=pos[coin]['sz']*pos[coin]['e']/DEFAULT_LEVERAGE; hit=False
            if pos[coin]['s']==1:
                if float(cd['l'])<=pos[coin]['sl']:
                    pnl=(pos[coin]['sl']-pos[coin]['e'])*pos[coin]['sz']; hit=True; rsn='止损'
                elif float(cd['h'])>=pos[coin]['tp']:
                    pnl=(pos[coin]['tp']-pos[coin]['e'])*pos[coin]['sz']; hit=True; rsn='止盈'
            else:
                if float(cd['h'])>=pos[coin]['sl']:
                    pnl=(pos[coin]['e']-pos[coin]['sl'])*pos[coin]['sz']; hit=True; rsn='止损'
                elif float(cd['l'])<=pos[coin]['tp']:
                    pnl=(pos[coin]['e']-pos[coin]['tp'])*pos[coin]['sz']; hit=True; rsn='止盈'
            if hit:
                ex=pos[coin]['sl'] if rsn=='止损' else pos[coin]['tp']
                trades.append({'coin':coin,'side':'LONG' if pos[coin]['s']==1 else 'SHORT',
                    'entry':pos[coin]['e'],'exit':ex,'size':pos[coin]['sz'],'pnl':pnl,
                    'reason':rsn,'time':dt.strftime("%m-%d %H:%M"),'extreme':pos[coin].get('ext'),
                    'funding':pos[coin].get('fnd')})
                cl.append(coin); dp+=pnl; cap+=mr+pnl
                stk=stk+1 if pnl<=0 else 0
        for c in cl: del pos[c]

        if dp<-cap*DAILY_LOSS_LIMIT or stk>=3:
            ur=sum((float(data[c]["c"][-1]['c'])-pos[c]['e'])*pos[c]['sz'] for c in pos if c in data)
            eq.append({'t':cap+ur}); continue
        if len(pos)>=MAX_POSITIONS:
            ur=sum((float(data[c]["c"][-1]['c'])-pos[c]['e'])*pos[c]['sz'] for c in pos if c in data)
            eq.append({'t':cap+ur}); continue

        for coin in COINS:
            if coin in pos or coin not in data: continue
            ci=None
            for i,c in enumerate(data[coin]["c"]):
                if c['t']==ts: ci=i; break
            if ci is None or ci<50: continue
            sig,det=signal(data[coin]["c"],data[coin]["f"],ci)
            if sig==0: continue
            price=float(data[coin]["c"][ci]['c']); atr=det['atr']
            risk_pct=0.03 if det.get('extreme') else 0.02
            risk=cap*risk_pct; sd=atr*STOP_ATR_MULT
            if sd<=0: continue
            sz=risk/sd; mg=sz*price/DEFAULT_LEVERAGE
            if mg>cap*MAX_MARGIN_PCT: continue
            if sig==1:
                pos[coin]={'e':price,'sz':sz,'s':1,'sl':price-sd,'tp':price+atr*TP_ATR_MULT,'ext':det.get('extreme'),'fnd':det.get('funding')}
            else:
                pos[coin]={'e':price,'sz':sz,'s':-1,'sl':price+sd,'tp':price-atr*TP_ATR_MULT,'ext':det.get('extreme'),'fnd':det.get('funding')}
            cap-=mg
        ur=sum((float(data[c]["c"][-1]['c'])-pos[c]['e'])*pos[c]['sz'] for c in pos if c in data)
        eq.append({'t':cap+ur})

    # 统计 (零除保护)
    wins=[t for t in trades if t['pnl']>0]; losses=[t for t in trades if t['pnl']<=0]
    tpnl=sum(t['pnl'] for t in trades)
    peak=max(e['t'] for e in eq) if eq else INITIAL_CAPITAL; mdd=0
    for e in eq:
        if e['t']>peak: peak=e['t']
        dd=(peak-e['t'])/peak if peak>0 else 0
        if dd>mdd: mdd=dd
    aw=sum(t['pnl'] for t in wins)/len(wins) if wins else 0
    al=sum(abs(t['pnl']) for t in losses)/len(losses) if losses else 1
    pf=(aw/al) if al>0 else 999
    wr=len(wins)/len(trades)*100 if trades else 0
    ext=[t for t in trades if t.get('ext')]; nrm=[t for t in trades if not t.get('ext')]
    ew=[t for t in ext if t['pnl']>0]; nw=[t for t in nrm if t['pnl']>0]
    ewr=len(ew)/len(ext)*100 if ext else 0
    nwr=len(nw)/len(nrm)*100 if nrm else 0

    print(f"""
# V3 极端费率策略 (30天, 4h)

## 三版本对比
| 指标 | v1(1h) | v2(4h) | **v3(费率)** |
|------|--------|--------|-------------|
| 交易 | 110 | 13 | {len(trades)} |
| 胜率 | 31.8% | 53.8% | {wr:.1f}% |
| PnL | -$9.68 | +$37.12 | ${tpnl:+.2f} |
| 收益 | -3.2% | +12.4% | {tpnl/INITIAL_CAPITAL*100:+.1f}% |
| 盈亏比 | 2.06 | 1.92 | {pf:.2f} |
| 回撤 | 120.6% | 38.8% | {mdd*100:.1f}% |
| 净值 | $173 | $288 | ${eq[-1]['t']:.2f} |

## ⚡ 费率信号 vs 普通
| 类型 | 笔数 | 胜率 | PnL |
|------|------|------|-----|
| ⚡费率 | {len(ext)} | {ewr:.1f}% | ${sum(t['pnl'] for t in ext):+.2f} |
| 📊普通 | {len(nrm)} | {nwr:.1f}% | ${sum(t['pnl'] for t in nrm):+.2f} |

## 交易明细
""")
    for t in trades:
        e="🟢" if t['pnl']>0 else "🔴"
        ext=f" ⚡{t['ext']}" if t.get('ext') else ""
        fund=f" [费率:{float(t['funding'])*100:.4f}%]" if t.get('funding') else ""
        print(f"{e} {t['time']} {t['side']:5s} {t['coin']:5s} @{t['entry']:>10.4f} → {t['exit']:>10.4f} | ${t['pnl']:+7.2f} ({t['reason']}){ext}{fund}")

    with open('/root/.openclaw/workspace/crypto/backtest_v3_result.json','w') as f:
        json.dump({'stats':{'total':len(trades),'wr':wr,'pnl':tpnl,'ret':tpnl/INITIAL_CAPITAL*100,
            'mdd':mdd*100,'final':eq[-1]['t'] if eq else INITIAL_CAPITAL,'pf':pf,
            'ext_n':len(ext),'ext_wr':ewr,'ext_pnl':sum(t['pnl'] for t in ext),
            'nrm_n':len(nrm),'nrm_pnl':sum(t['pnl'] for t in nrm)},'trades':trades},f,indent=2,ensure_ascii=False)
    print("\n📁 saved to backtest_v3_result.json")
