"""Read-only XAUUSD signal visualization. No external packages beyond project deps."""
from __future__ import annotations

import argparse
import html
import importlib
import json
import math
import webbrowser
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

PLANNER: Any = importlib.import_module('02_AI.MarketIntelligence.r03_signal_planner')
MTF: Any = importlib.import_module('02_AI.MarketIntelligence.r03_mtf_reasoning')
ORCH = '04_Testing.production_portability.run_xauusd_r03_v2_orchestrator'
ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / '04_Testing' / 'production_portability' / 'reports' / 'xau_signal_chart.html'


def candle_payload(frame: pd.DataFrame, decision: Any) -> list[dict[str, Any]]:
    bars = MTF.closed_bars(frame, 'M5', MTF.utc_timestamp(decision))
    rows: list[dict[str, Any]] = []
    for row in bars.itertuples(index=False):
        record = {'time': str(row.time), 'open': float(row.open),
                  'high': float(row.high), 'low': float(row.low), 'close': float(row.close)}
        if not all(math.isfinite(record[k]) for k in ('open', 'high', 'low', 'close')):
            raise ValueError('NONFINITE_CHART_PRICE')
        rows.append(record)
    return rows


def make_html(report: Mapping[str, Any], bars: list[dict[str, Any]]) -> str:
    if not bars:
        raise ValueError('NO_COMPLETED_CANDLES')
    data = json.dumps({'report': dict(report), 'candles': bars}, allow_nan=False)
    data = data.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    title = html.escape(str(report.get('broker_symbol', 'XAUUSD')))
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PulseViper | Read-only chart</title>
<style>
body{background:#0b1220;color:#e2e8f0;font:14px system-ui;margin:0;padding:24px}
main{max-width:1150px;margin:auto}h1{margin:0 0 5px}.muted{color:#9caec4}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(235px,1fr));gap:12px;margin:18px 0}
.card{border:1px solid #334155;border-radius:12px;padding:15px;background:#131e2d}
.big{font-size:24px;font-weight:700;margin:8px 0}.blue{color:#60a5fa}.green{color:#34d399}.red{color:#fb7185}
canvas{width:100%;height:520px;display:block;background:#0c1625;border:1px solid #334155;border-radius:12px}
footer{line-height:1.6;margin-top:16px}.tag{display:inline-block;padding:4px 10px;border:1px solid #f59e0b;border-radius:18px;color:#fbbf24}
</style></head><body><main>
<h1>PulseViper — '''+title+''' Signal Chart</h1><div class="muted">Only completed genuine MT5 M5 bars · Decision: <span id="decision"></span> UTC</div>
<div class="cards"><div class="card">Decision<div class="big" id="state"></div><div id="reason" class="muted"></div></div>
<div class="card">BUY scenario<div class="big green" id="buy"></div><div id="buyinfo" class="muted"></div></div>
<div class="card">SELL scenario<div class="big red" id="sell"></div><div id="sellinfo" class="muted"></div></div></div>
<canvas id="chart"></canvas><footer><span class="tag">RESEARCH ONLY · NO LIVE TRADING</span>
<p>Roman Urdu: Neeli line BUY trigger, laal/pink SELL trigger. Green/pink dotted lines targets aur stop-loss zones dikhati hain. BUY/SELL blocked ho to bhi scenario sirf education ke liye dikhaya gaya hai. Entry trigger cross hona automated trade instruction nahi.</p>
<p id="meta" class="muted"></p></footer></main>
<script id="payload" type="application/json">'''+data+'''</script>
<script>
'use strict';
const data=JSON.parse(document.getElementById('payload').textContent);
const r=data.report, bars=data.candles, canvas=document.getElementById('chart'), ctx=canvas.getContext('2d');
const el=(id)=>document.getElementById(id);
el('decision').textContent=r.decision_time_utc;
el('state').textContent=r.decision;
el('reason').textContent=r.reason;
el('buy').textContent=r.buy_setup.eligible?'Possible above '+r.buy_setup.trigger_above:'Blocked';
el('sell').textContent=r.sell_setup.eligible?'Possible below '+r.sell_setup.trigger_below:'Blocked';
el('buyinfo').textContent='SL '+r.buy_setup.stop_loss+' | TP1 '+r.buy_setup.target_1+' | TP2 '+r.buy_setup.target_2;
el('sellinfo').textContent='SL '+r.sell_setup.stop_loss+' | TP1 '+r.sell_setup.target_1+' | TP2 '+r.sell_setup.target_2;
el('meta').textContent='H1 '+r.h1_structure+' | H4 '+r.h4_structure+' | Last M5 close '+r.last_closed_m5_price+' | Spread/slippage not priced. No proven edge.';
function draw(){
const scale=window.devicePixelRatio||1; const rect=canvas.getBoundingClientRect();
canvas.width=Math.max(400,Math.round(rect.width*scale));canvas.height=Math.round(520*scale);
ctx.setTransform(scale,0,0,scale,0,0);const w=rect.width,h=520,L=18,R=100,T=25,B=48;
const levels=[
{v:r.buy_setup.trigger_above,label:'BUY',color:'#60a5fa',solid:true},
{v:r.sell_setup.trigger_below,label:'SELL',color:'#fb7185',solid:true}
];
for(const [side,clr] of [['buy_setup','#34d399'],['sell_setup','#fda4af']]){
 const s=r[side]; if(!s.eligible)continue;
 for(const [field,label] of [['stop_loss','SL'],['target_1','TP1'],['target_2','TP2']]){
  if(Number.isFinite(s[field]))levels.push({v:s[field],label:side.startsWith('buy')?'B '+label:'S '+label,color:clr,solid:false});
 }
}
const nums=bars.flatMap(b=>[b.low,b.high]).concat(levels.map(x=>x.v));
let min=Math.min(...nums),max=Math.max(...nums),pad=Math.max(0.5,(max-min)*0.08);min-=pad;max+=pad;
const y=(v)=>T+(max-v)/(max-min)*(h-T-B);
ctx.fillStyle='#0c1625';ctx.fillRect(0,0,w,h);
ctx.font='12px system-ui';ctx.textBaseline='middle';
for(let i=0;i<6;i++){const v=min+(max-min)*i/5,yy=y(v);
 ctx.strokeStyle='#26354a';ctx.setLineDash([2,4]);ctx.beginPath();ctx.moveTo(L,yy);ctx.lineTo(w-R,yy);ctx.stroke();ctx.setLineDash([]);
 ctx.fillStyle='#98a9bf';ctx.fillText(v.toFixed(2),w-R+8,yy);}
const slot=(w-L-R)/bars.length;
bars.forEach((b,i)=>{const x=L+(i+0.5)*slot, up=b.close>=b.open,c=up?'#34d399':'#fb7185';
 ctx.strokeStyle=c;ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(x,y(b.high));ctx.lineTo(x,y(b.low));ctx.stroke();
 ctx.fillStyle=c;const yt=y(Math.max(b.open,b.close)),yb=y(Math.min(b.open,b.close));
 ctx.fillRect(x-Math.max(1,slot*0.32),yt,Math.max(2,slot*0.64),Math.max(1,yb-yt));});
for(const line of levels){const yy=y(line.v);ctx.strokeStyle=line.color;ctx.lineWidth=line.solid?2:1;ctx.setLineDash(line.solid?[]:[5,4]);
ctx.beginPath();ctx.moveTo(L,yy);ctx.lineTo(w-R,yy);ctx.stroke();ctx.setLineDash([]);
ctx.fillStyle=line.color;ctx.font='bold 11px system-ui';ctx.fillText(line.label+' '+line.v.toFixed(2),w-R+7,yy-11);}
ctx.fillStyle='#94a3b8';ctx.font='12px system-ui';ctx.fillText('Oldest closed M5',L,h-17);
ctx.fillText('Latest closed M5',Math.max(L,w-R-130),h-17);
}
addEventListener('resize',draw);draw();
</script></body></html>'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-open', action='store_true')
    args = parser.parse_args()
    try:
        orch: Any = importlib.import_module(ORCH)
        snap = orch.acquire_genuine_snapshot()
        orch.verify_snapshot_authority(snap)
        if snap.is_synthetic is not False or snap.canonical_instrument != 'XAUUSD':
            raise ValueError('GENUINE_XAUUSD_REQUIRED')
        report = PLANNER.plan(snap.market_data, snap.decision_time_utc)
        report['broker_symbol'] = snap.broker_symbol
        bars = candle_payload(snap.market_data['M5'], snap.decision_time_utc)
        path = OUTPUT
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(make_html(report, bars), encoding='utf-8')
        print('CHART_BRIDGE_STATUS=PASS_READ_ONLY')
        print('CHART_PATH='+str(path))
        print(PLANNER.speak(report))
        if not args.no_open:
            webbrowser.open(path.as_uri())
        return 0
    except Exception as exc:
        print('CHART_BRIDGE_STATUS=BLOCKED')
        print(type(exc).__name__+': '+str(exc))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
