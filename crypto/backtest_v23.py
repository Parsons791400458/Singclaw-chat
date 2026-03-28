#!/usr/bin/env python3
"""v2+v3 混合策略回测 (更新阈值, 修复除零)"""
import json, time
from datetime import datetime, timezone, timedelta
from hyperliquid.info import Info

tz8=timezone(timedelta(hours=8)); CAP=300.0
COINS=["BTC","ETH","SOL","AVAX","APT","ATOM","SUI","JUP"]
STOP=2.0; TP=3.0; LEV=3; MAXPOS=5; DAILY_LIMIT=0.03; SIG_THR=0.6

def sma(v,p): return sum(v[-p:])/p if len(v)>=p else None
def rsi(c,p=14):
    if len(c)<p+1: return None
    d=[c[i]-c[i-1] for i in range(1,len(c))]; g=[max(0,x) for x in d[-p:]]; l=[max(0,-x) for x in d[-p:]]
    a,b=sum(g)/p,sum(l)/p; return 100-(100/(1+a/b)) if b else 100
def atr(c,p=14):
    if len(c)<p+1: return None
    t=[]
    for i in range(1,len(c)):
        h,l,pc=float(c[i]['h']),float(c[i]['l']),float(c[i-1]['c'])
        t.append(max(h-l,abs(h-pc),abs(l-pc)))
    return sum(t[-p:])/p
def macd(c):
    if len(c)<26: return None,None
    e12=e26=pe12=pe26=c[0]
    for i,x in enumerate(c):
        e12=e12*11/13+x*2/13; e26=e26*25/27+x*2/27
        if i<len(c)-1: pe12=pe12*11/13+x*2/13; pe26=pe26*25/27+x*2/27
    return e12-e26,pe12-pe26

def get_fund(fl,ts):
    rr=[float(f['fundingRate']) for f in fl if f['time']<=ts]
    if not rr: return 0,0,0
    cur=rr[-1]; rec=rr[-3:] if len(rr)>=3 else rr
    old=rr[-6:-3] if len(rr)>=6 else rr[:max(0,len(rr)-3)]
    ar=sum(rec)/len(rec) if rec else 0; ao=sum(old)/len(old) if old else 0
    return cur, ar-ao, sum(rr)/len(rr)

def sig(candles,fl,idx):
    cl=[float(c['c']) for c in candles[:idx+1]]; vo=[float(c['v']) for c in candles[:idx+1]]
    if len(cl)<50: return 0,{}
    m20=sma(cl,20); m50=sma(cl,50); r=rsi(cl,14); a=atr(candles[:idx+1],14); d,pd=macd(cl)
    if any(x is None for x in [m20,m50,r,a,d,pd]): return 0,{}
    fd,fc,fa=get_fund(fl,candles[idx]['t'])
    sc=0; ext=None
    # 费率先算
    if fd<-0.0005:
        sc+=0.95; ext="🔥超极端负费率_LONG"
        if fc<-0.0003: sc+=0.15; ext="🔥🔥加速恶化_LONG"
    elif fd<-0.0003:
        sc+=0.80; ext="⚡极端负费率_LONG"
        if fc<-0.0002: sc+=0.15; ext="⚡⚡加速负费率_LONG"
    elif fd<-0.0001:
        sc+=0.45; ext="负费率_LONG"
        if fc<-0.0001: sc+=0.10; ext="恶化负费率_LONG"
    elif fd>0.0003:
        sc-=0.80; ext="⚡极端正费率_SHORT"
        if fc>0.0002: sc-=0.15; ext="⚡⚡加速正费率_SHORT"
    else:
        if fd>0.0001: sc+=0.15
        elif fd<-0.0001: sc-=0.15
    # 趋势: 极端费率时降低权重
    if ext:
        sc+=0.15 if m20>m50 else -0.15
    else:
        sc+=0.35 if m20>m50 else -0.35
    if r<30: sc+=0.20
    elif r>70: sc-=0.20
    elif r<40: sc+=0.08
    elif r>60: sc-=0.08
    if d>0 and d>pd: sc+=0.15
    elif d<0 and d<pd: sc-=0.15
    if fd<-0.0005:
        sc+=0.95; ext="🔥超极端负费率_LONG"
        if fc<-0.0003: sc+=0.15; ext="🔥🔥加速恶化_LONG"
    elif fd<-0.0003:
        sc+=0.80; ext="⚡极端负费率_LONG"
        if fc<-0.0002: sc+=0.15; ext="⚡⚡加速负费率_LONG"
    elif fd<-0.0001:
        sc+=0.45; ext="负费率_LONG"
        if fc<-0.0001: sc+=0.10; ext="恶化负费率_LONG"
    elif fd>0.0003:
        sc-=0.80; ext="⚡极端正费率_SHORT"
        if fc>0.0002: sc-=0.15; ext="⚡⚡加速正费率_SHORT"
    else:
        if fd>0.0001: sc+=0.15
        elif fd<-0.0001: sc-=0.15
    va=sma(vo,20)
    if va and va>0 and vo[-1]<va*0.8: return 0,{}
    thr=0.4 if ext else SIG_THR
    if sc>thr: return 1,{'rsi':r,'atr':a,'fd':fd,'fc':fc,'sc':sc,'ext':ext}
    elif sc<-thr: return -1,{'rsi':r,'atr':a,'fd':fd,'fc':fc,'sc':sc,'ext':ext}
    return 0,{}

if __name__=="__main__":
    print("🚀 v2+v3混合策略回测 (更新阈值, 4h, 30天)\n")

    info=Info(base_url="https://api.hyperliquid.xyz",skip_ws=True)
    nms=int(time.time()*1000); sms=nms-30*86400000
    data={}
    for c in COINS:
        data[c]={"c":info.candles_snapshot(c,"4h",sms,nms),"f":info.funding_history(c,sms)}
        print(f"  {c} ok")

    cap=CAP; pos={}; trades=[]; eq=[]; dp=0; ds=None; stk=0
    btc=data["BTC"]["c"]
    for idx in range(50,len(btc)):
        ts=btc[idx]['t']; dt=datetime.fromtimestamp(ts/1000,tz=tz8)
        if ds is None or dt.date()!=ds: ds=dt.date(); dp=0; stk=0
        closed=[]
        for coin in list(pos.keys()):
            if coin not in data: continue
            cd=None
            for x in data[coin]["c"]:
                if x['t']==ts: cd=x; break
            if not cd: continue
            mr=pos[coin]['sz']*pos[coin]['e']/LEV; hit=False
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
                closed.append(coin); dp+=pnl; cap+=mr+pnl
                stk=stk+1 if pnl<=0 else 0
        for c in closed: del pos[c]
        if dp<-cap*DAILY_LIMIT or stk>=3:
            ur=sum((float(data[c]["c"][-1]['c'])-pos[c]['e'])*pos[c]['sz'] for c in pos if c in data)
            eq.append({'t':cap+ur}); continue
        if len(pos)>=MAXPOS:
            ur=sum((float(data[c]["c"][-1]['c'])-pos[c]['e'])*pos[c]['sz'] for c in pos if c in data)
            eq.append({'t':cap+ur}); continue
        for coin in COINS:
            if coin in pos or coin not in data: continue
            ci=None
            for i,c in enumerate(data[coin]["c"]):
                if c['t']==ts: ci=i; break
            if ci is None or ci<50: continue
            s,det=sig(data[coin]["c"],data[coin]["f"],ci)
            if s==0: continue
            price=float(data[coin]["c"][ci]['c']); a=det['atr']
            rp=0.03 if det.get('ext') else 0.02
            risk=cap*rp; sd=a*STOP
            if sd<=0: continue
            sz=risk/sd; mg=sz*price/LEV
            if mg>cap*0.15: continue
            if s==1:
                pos[coin]={'e':price,'sz':sz,'s':1,'sl':price-sd,'tp':price+a*TP,'ext':det.get('ext'),'fnd':det.get('fd')}
            else:
                pos[coin]={'e':price,'sz':sz,'s':-1,'sl':price+sd,'tp':price-a*TP,'ext':det.get('ext'),'fnd':det.get('fd')}
            cap-=mg
        ur=sum((float(data[c]["c"][-1]['c'])-pos[c]['e'])*pos[c]['sz'] for c in pos if c in data)
        eq.append({'t':cap+ur})

    # Stats with full zero-division protection
    wins=[t for t in trades if t['pnl']>0]; losses=[t for t in trades if t['pnl']<=0]
    tpnl=sum(t['pnl'] for t in trades) if trades else 0
    if not trades:
        print("⚠️ 30天内无交易信号")
        exit()
    peak=max(e['t'] for e in eq); mdd=0
    for e in eq:
        if e['t']>peak: peak=e['t']
        dd=(peak-e['t'])/peak if peak>0 else 0
        if dd>mdd: mdd=dd
    aw=sum(t['pnl'] for t in wins)/len(wins) if wins else 0
    al=sum(abs(t['pnl']) for t in losses)/len(losses) if losses else 1
    pf=aw/al if al>0 else 999
    wr=len(wins)/len(trades)*100

    ext_t=[t for t in trades if t.get('ext')]
    nrm_t=[t for t in trades if not t.get('ext')]
    fire=[t for t in ext_t if '🔥' in t.get('ext','')]
    bolt=[t for t in ext_t if '⚡' in t.get('ext','') and '🔥' not in t.get('ext','')]
    neg=[t for t in ext_t if '负费率' in t.get('ext','') and '⚡' not in t.get('ext','') and '🔥' not in t.get('ext','')]

    def wr_of(lst): return len([t for t in lst if t['pnl']>0])/len(lst)*100 if lst else 0

    def avg_of(lst): return sum(t['pnl'] for t in lst)/len(lst) if lst else 0

    print(f"""
# v2+v3 混合策略 (30天, 4h)

## 版本对比
| 指标 | v2 | v2+v3 |
|------|----|-------|
| 交易 | 13 | {len(trades)} |
| 胜率 | 53.8% | {wr:.1f}% |
| PnL | +$37.12 | ${tpnl:+.2f} |
| 收益 | +12.4% | {tpnl/CAP*100:+.1f}% |
| 盈亏比 | 1.92 | {pf:.2f} |
| 回撤 | 38.8% | {mdd*100:.1f}% |
| 净值 | $288 | ${eq[-1]['t']:.2f} |

## 费率信号效果
| 类型 | 笔数 | 胜率 | PnL | 均PnL |
|------|------|------|-----|------|
| 🔥超极端 | {len(fire)} | {wr_of(fire):.0f}% | ${sum(t['pnl'] for t in fire):+.2f} | ${avg_of(fire):+.2f} |
| ⚡极端 | {len(bolt)} | {wr_of(bolt):.0f}% | ${sum(t['pnl'] for t in bolt):+.2f} | ${avg_of(bolt):+.2f} |
| 负费率 | {len(neg)} | {wr_of(neg):.0f}% | ${sum(t['pnl'] for t in neg):+.2f} | ${avg_of(neg):+.2f} |
| 📊普通 | {len(nrm_t)} | {wr_of(nrm_t):.1f}% | ${sum(t['pnl'] for t in nrm_t):+.2f} | ${avg_of(nrm_t):+.2f} |

## 交易明细
""")
    for t in trades:
        e="🟢" if t['pnl']>0 else "🔴"
        ex=f" {t['ext']}" if t.get('ext') else ""
        fd=f" [日费率:{float(t['funding'])*3*100:.4f}%]" if t.get('funding') else ""
        print(f"{e} {t['time']} {t['side']:5s} {t['coin']:5s} @{t['entry']:>10.4f} → {t['exit']:>10.4f} | ${t['pnl']:+7.2f} ({t['reason']}){ex}{fd}")

    with open('/root/.openclaw/workspace/crypto/backtest_v23_result.json','w') as f:
        json.dump({'stats':{'total':len(trades),'wr':wr,'pnl':tpnl,'ret':tpnl/CAP*100,
            'mdd':mdd*100,'final':eq[-1]['t'],'pf':pf},'trades':trades},f,indent=2,ensure_ascii=False)
    print("\n📁 saved to backtest_v23_result.json")
