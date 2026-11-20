HTML = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hybrid Stat Arb Bot</title>
<style>
:root{color-scheme:dark;--bg:#0b1220;--panel:#121d30;--muted:#9fb0c8;--line:#263650;--green:#35c58a;--red:#f07178;--blue:#72a7ff}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:#edf3fb;font:15px system-ui,Arial}
main{max-width:1050px;margin:32px auto;padding:0 16px}.top{display:flex;justify-content:space-between;gap:12px;align-items:center;flex-wrap:wrap}
h1{font-size:25px;margin:0}.muted{color:var(--muted)}.pill{border:1px solid var(--line);padding:7px 11px;border-radius:20px;font-size:12px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-top:20px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:17px}
.label{color:var(--muted);font-size:12px}.value{font-size:23px;font-weight:700;margin-top:7px;overflow-wrap:anywhere}
.signal{font-size:22px;font-weight:750}.good{color:var(--green)}.bad{color:var(--red)}
button{background:var(--blue);color:#07111f;border:0;border-radius:9px;padding:11px 16px;font-weight:700;cursor:pointer}
pre{white-space:pre-wrap;overflow-wrap:anywhere;color:#cbd8eb;font-size:12px}
footer{margin:20px 0;color:var(--muted);font-size:12px;line-height:1.6}
</style></head>
<body><main>
<div class="top"><div><h1>Hybrid Statistical Arbitrage</h1><div class="muted">AUDUSD / NZDUSD · 5-minute research dashboard</div></div><span class="pill">PAPER / SIGNAL ONLY · NO LIVE ORDERS</span></div>
<div class="grid">
<div class="card"><div class="label">Latest signal</div><div id="signal" class="signal">Loading…</div></div>
<div class="card"><div class="label">Spread Z-score</div><div id="z" class="value">—</div></div>
<div class="card"><div class="label">Hedge ratio</div><div id="beta" class="value">—</div></div>
<div class="card"><div class="label">Half-life (bars)</div><div id="hl" class="value">—</div></div>
<div class="card"><div class="label">Cointegration p-value</div><div id="coint" class="value">—</div></div>
<div class="card"><div class="label">Residual ADF p-value</div><div id="adf" class="value">—</div></div>
<div class="card"><div class="label">Volatility percentile</div><div id="vol" class="value">—</div></div>
<div class="card"><div class="label">Spread strength proxy</div><div id="strength" class="value">—</div></div>
</div>
<div class="card" style="margin-top:12px"><div class="top"><div><b>Bot status</b><div id="status" class="muted">Checking service…</div></div><button onclick="refresh(true)">Analyze now</button></div><pre id="reasons">Waiting for analysis…</pre></div>
<footer>Research prototype only. Yahoo Finance data can be delayed, incomplete or unavailable. No broker orders are sent. Render Free can sleep or restart. Do not use for unattended live trading.</footer>
</main>
<script>
const fmt=(v,n=3)=>v===null||v===undefined||!Number.isFinite(Number(v))?"—":Number(v).toFixed(n);
async function refresh(force=false){
 try{
  if(force){const r=await fetch('/api/analyze',{method:'POST'});if(!r.ok){const x=await r.json();throw new Error(x.detail||'Analysis failed');}}
  const r=await fetch('/api/status');const s=await r.json();const d=s.latest;
  document.getElementById('status').textContent=s.last_error?'Data error: '+s.last_error:'Service active · Last analysis: '+(s.last_analysis||'pending');
  if(!d){document.getElementById('reasons').textContent=s.last_error||'Waiting for first analysis…';return;}
  const sig=document.getElementById('signal');sig.textContent=d.signal;sig.className='signal '+(d.signal.includes('LONG')?'good':d.signal.includes('SHORT')||d.signal.includes('STOP')?'bad':'');
  document.getElementById('z').textContent=fmt(d.zscore);
  document.getElementById('beta').textContent=fmt(d.hedge_ratio);
  document.getElementById('hl').textContent=fmt(d.half_life_bars,1);
  document.getElementById('coint').textContent=fmt(d.cointegration_p,4);
  document.getElementById('adf').textContent=fmt(d.residual_adf_p,4);
  document.getElementById('vol').textContent=fmt(d.volatility_percentile,1)+'%';
  document.getElementById('strength').textContent=fmt(d.spread_strength_proxy,1);
  document.getElementById('reasons').textContent='Filters passed: '+d.filters_passed+'\\nReasons: '+(d.reasons||[]).join('; ')+'\\nBars: '+d.bars+'\\nData timestamp: '+d.timestamp+'\\nMode: '+d.mode;
 }catch(e){document.getElementById('status').textContent='Error: '+e.message;}
}
refresh();setInterval(()=>refresh(false),30000);
</script></body></html>
"""
