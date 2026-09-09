"""The page's CSS and JavaScript. Kept apart from build.py so the assembly
stays readable and the styling can be edited without picking through string
concatenation.

Design system per the brand lock (first-access-signals CLAUDE.md section 5):
Plaster ground, Canvas cards, Iron text, Agency Red #ED2127, 12px base radius,
and the single Apple easing curve cubic-bezier(.16,1,.3,1) everywhere.
"""

CSS = r"""
@font-face{font-family:Flama;src:url(/a/fonts/flama-bold.woff2)format('woff2');font-weight:700;font-display:swap}
@font-face{font-family:Blacker;src:url(/a/fonts/blacker-reg.woff2)format('woff2');font-weight:400;font-display:swap}
@font-face{font-family:Blacker;src:url(/a/fonts/blacker-med.woff2)format('woff2');font-weight:500;font-display:swap}
@font-face{font-family:DIN;src:url(/a/fonts/din-reg.woff2)format('woff2');font-weight:400;font-display:swap}
@font-face{font-family:DIN;src:url(/a/fonts/din-bold.woff2)format('woff2');font-weight:700;font-display:swap}

:root{
  --red:#ED2127; --iron:#0c0c0c; --plaster:#F8F7F5; --canvas:#fff;
  --ink:#191714; --grey:#6d6760; --mute:#a39c92; --line:#e7e3dc; --line2:#d9d4cb;
  --ease:cubic-bezier(.16,1,.3,1);
  --r:12px;
  --body:DIN,'Helvetica Neue',Helvetica,Arial,sans-serif;
  --disp:Blacker,Georgia,'Times New Roman',serif;
  --head:Flama,'Haettenschweiler','Arial Narrow',sans-serif;
  --pad:clamp(18px,5vw,40px);
}
*{margin:0;padding:0;box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  background:var(--plaster); color:var(--ink); font-family:var(--body);
  font-size:16px; line-height:1.55; -webkit-font-smoothing:antialiased;
  overflow-x:hidden;
}
.wrap{max-width:760px;margin:0 auto;padding:0 var(--pad)}
a{color:inherit}
:focus-visible{outline:2px solid var(--red);outline-offset:3px;border-radius:3px}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
/* An author display: rule beats the UA sheet's [hidden]{display:none}, so any
   element hidden by attribute that also carries a display kept rendering. This
   makes the attribute win everywhere; audit.py fails the build if it stops. */
[hidden]{display:none!important}

/* ---------- top bar ---------- */
.bar{
  position:sticky;top:0;z-index:60;background:rgba(248,247,245,.94);
  backdrop-filter:saturate(1.6)blur(12px);border-bottom:1px solid var(--line);
}
.bar .wrap{display:flex;align-items:center;gap:12px;height:56px}
.bar img{width:26px;height:26px;border-radius:4px;flex:none}
.bar .nm{
  font-weight:700;font-size:10.5px;letter-spacing:.2em;text-transform:uppercase;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}
.bar .sp{flex:1}
.count{
  font-size:11px;letter-spacing:.1em;color:var(--grey);font-variant-numeric:tabular-nums;
  white-space:nowrap;
}
.count b{color:var(--ink);font-weight:700}
.iconbtn{
  width:44px;height:44px;display:grid;place-items:center;border:1px solid var(--line2);
  background:var(--canvas);border-radius:9px;cursor:pointer;color:var(--ink);flex:none;
  transition:border-color .3s var(--ease),background .3s var(--ease);
}
.iconbtn:hover{border-color:var(--ink)}
.iconbtn svg{width:17px;height:17px;display:block}
.prog{height:2px;background:var(--line);position:relative;overflow:hidden}
.prog i{
  position:absolute;inset:0 auto 0 0;background:var(--red);width:0;
  transition:width .55s var(--ease);
}

/* ---------- hero ---------- */
.hero{background:var(--iron);color:#fff;padding:clamp(38px,9vw,74px) 0 clamp(30px,7vw,54px)}
.kick{
  font-size:10.5px;font-weight:700;letter-spacing:.28em;text-transform:uppercase;
  color:var(--red);
}
h1{
  font-family:var(--head);font-weight:700;text-transform:uppercase;
  font-size:clamp(46px,13.5vw,104px);line-height:.87;letter-spacing:.004em;
  margin:14px 0 0;
}
.lede{
  font-family:var(--disp);font-size:clamp(17px,4.4vw,22px);line-height:1.45;
  color:#cfc9c2;margin-top:20px;max-width:33em;
}
.rule{width:46px;height:3px;background:var(--red);margin:22px 0 0}

/* the personalised stamp */
.stamp{
  margin-top:26px;border-top:1px solid #2a2825;padding-top:20px;
  display:flex;flex-wrap:wrap;gap:10px 30px;align-items:flex-end;
}
.stamp .f{min-width:0}
.stamp .k{
  font-size:9.5px;font-weight:700;letter-spacing:.2em;text-transform:uppercase;
  color:#8a837b;
}
.stamp .v{font-family:var(--disp);font-size:19px;line-height:1.25;margin-top:4px;color:#fff}
.days{
  margin-left:auto;background:var(--red);color:#fff;border-radius:10px;
  padding:9px 15px;text-align:center;flex:none;
}
.days b{display:block;font-family:var(--head);font-size:31px;line-height:1;font-weight:700}
.days span{font-size:9.5px;letter-spacing:.16em;text-transform:uppercase;opacity:.9}

/* ---------- generic blocks ---------- */
section{padding:clamp(34px,7vw,58px) 0}
.eyebrow{
  font-size:10px;font-weight:700;letter-spacing:.24em;text-transform:uppercase;
  color:var(--red);
}
h2{
  font-family:var(--disp);font-weight:500;font-size:clamp(25px,6vw,35px);
  line-height:1.14;margin-top:10px;letter-spacing:-.005em;
}
.sub{color:var(--grey);margin-top:11px;max-width:38em;font-size:15.5px}

/* ---------- the three that go wrong ---------- */
.cards{display:grid;gap:12px;margin-top:26px}
.card{
  background:var(--canvas);border:1px solid var(--line);border-radius:var(--r);
  padding:20px 22px 22px;position:relative;
}
.card .n{
  font-family:var(--head);font-size:15px;font-weight:700;color:var(--red);
  letter-spacing:.06em;
}
.card h3{
  font-family:var(--disp);font-weight:500;font-size:19.5px;line-height:1.24;
  margin:7px 0 8px;
}
.card p{font-size:14.5px;color:var(--grey);line-height:1.6}
.handoff{
  margin-top:24px;padding-top:20px;border-top:1px solid var(--line2);
  font-family:var(--disp);font-size:17px;color:var(--grey);
}
.printonly{display:none}

/* ---------- personalise ---------- */
.setup{
  background:var(--canvas);border:1px solid var(--line2);border-radius:var(--r);
  padding:22px;margin-top:8px;
}
.setup.done{background:transparent;border-style:dashed;padding:15px 18px}
.setup h3{font-family:var(--disp);font-weight:500;font-size:20px;line-height:1.25}
.setup p{font-size:14.5px;color:var(--grey);margin-top:7px}
.btn{
  display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:0 20px;
  background:var(--ink);color:#fff;border:1px solid var(--ink);border-radius:9px;
  font-family:var(--body);font-weight:700;font-size:12px;letter-spacing:.14em;
  text-transform:uppercase;cursor:pointer;text-decoration:none;
  transition:opacity .3s var(--ease);
}
.btn:hover{opacity:.82}
.btn.ghost{background:transparent;color:var(--ink);border-color:var(--line2)}
.btn.ghost:hover{border-color:var(--ink);opacity:1}
.btn.red{background:var(--red);border-color:var(--red)}
.btnrow{display:flex;flex-wrap:wrap;gap:9px;margin-top:16px}

form.pf{display:grid;gap:15px;margin-top:18px}
.fld label{
  display:block;font-size:10px;font-weight:700;letter-spacing:.18em;
  text-transform:uppercase;color:var(--grey);margin-bottom:6px;
}
.fld input[type=text],.fld input[type=date],.fld input[type=tel],.fld input[type=email]{
  width:100%;min-height:44px;padding:10px 13px;border:1px solid var(--line2);
  border-radius:9px;font-family:var(--body);font-size:16px;color:var(--ink);
  background:var(--canvas);transition:border-color .3s var(--ease);
}
.fld input:focus{border-color:var(--ink);outline:none}
.fld .hint{font-size:12.5px;color:var(--mute);margin-top:5px}
.checks{display:grid;gap:2px}
.chk{
  display:flex;gap:11px;align-items:flex-start;min-height:44px;padding:9px 0;
  cursor:pointer;
}
.chk input{
  width:20px;height:20px;margin-top:2px;flex:none;accent-color:var(--red);cursor:pointer;
}
.chk span{font-size:14.5px;line-height:1.45}
.chk span i{display:block;font-style:normal;font-size:12.5px;color:var(--mute)}

/* ---------- phases ---------- */
.phase{border-top:1px solid var(--line2);padding-top:clamp(28px,6vw,44px);margin-top:clamp(28px,6vw,44px)}
.phase:first-of-type{border-top:0;margin-top:0}
.phead{display:flex;flex-wrap:wrap;align-items:baseline;gap:8px 14px}
.when{
  font-family:var(--head);font-weight:700;text-transform:uppercase;
  font-size:clamp(24px,6.2vw,34px);line-height:1;letter-spacing:.01em;
}
.date{
  font-size:11px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;
  color:var(--red);background:#fdeced;border-radius:20px;padding:5px 11px;
  white-space:nowrap;
}
.date.soft{color:var(--grey);background:#efece7}
.plede{color:var(--grey);margin-top:10px;font-size:15.5px;max-width:38em}
.pdone{
  font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--mute);
  margin-left:auto;font-variant-numeric:tabular-nums;white-space:nowrap;
}

ul.items{list-style:none;margin-top:20px;display:grid;gap:9px}
li.item{
  background:var(--canvas);border:1px solid var(--line);border-radius:var(--r);
  transition:border-color .35s var(--ease),background .35s var(--ease);
}
li.item.crit{border-left:3px solid var(--red)}
li.item.on{background:#f4f2ef;border-color:var(--line)}
.itop{display:flex;gap:13px;padding:15px 17px;align-items:flex-start}
.itop input{
  width:22px;height:22px;flex:none;margin-top:1px;accent-color:var(--red);
  cursor:pointer;
}
.ibody{flex:1;min-width:0}
.ttl{
  font-weight:700;font-size:15.5px;line-height:1.38;cursor:pointer;
  display:block;transition:color .3s var(--ease);
}
li.item.on .ttl{color:var(--mute);text-decoration:line-through;text-decoration-thickness:1px}
.tags{display:flex;flex-wrap:wrap;gap:6px;margin-top:7px}
.tag{
  font-size:9.5px;font-weight:700;letter-spacing:.13em;text-transform:uppercase;
  padding:3px 7px;border-radius:5px;background:#efece7;color:var(--grey);
}
.tag.m{background:#fdeced;color:var(--red)}
.more{
  background:none;border:0;padding:0;margin-top:8px;cursor:pointer;color:var(--grey);
  font-family:var(--body);font-size:12.5px;font-weight:700;letter-spacing:.1em;
  text-transform:uppercase;display:inline-flex;align-items:center;gap:6px;
}
.more:hover{color:var(--ink)}
.more svg{width:9px;height:9px;transition:transform .35s var(--ease)}
.more[aria-expanded=true] svg{transform:rotate(180deg)}
.det{padding:0 17px 17px 52px}
.det p{font-size:14.5px;color:var(--grey);line-height:1.62}
.det ul{margin:11px 0 0;padding-left:0;list-style:none;display:grid;gap:5px}
.det ul li{
  font-size:13.5px;color:var(--grey);padding-left:15px;position:relative;
}
.det ul li:before{
  content:'';position:absolute;left:0;top:8px;width:4px;height:4px;border-radius:50%;
  background:var(--line2);
}
.det .lnk{
  display:inline-block;margin-top:12px;font-size:13.5px;font-weight:700;
  color:var(--ink);text-decoration:none;border-bottom:1px solid var(--red);
  padding-bottom:1px;
}
.det .lnk:hover{color:var(--red)}

/* ---------- footer ---------- */
footer{background:var(--iron);color:#cfc9c2;margin-top:clamp(40px,8vw,70px)}
footer .wrap{padding-top:clamp(34px,7vw,56px);padding-bottom:clamp(30px,6vw,46px)}
.agent{display:flex;gap:16px;align-items:flex-start;flex-wrap:wrap}
.who{display:flex;gap:16px;align-items:flex-start;min-width:0}
.agent .ph{
  width:62px;height:62px;border-radius:50%;object-fit:cover;flex:none;
  background:#2a2825;margin-top:3px;
}
.agent .nm2{font-family:var(--disp);font-size:22px;color:#fff;line-height:1.2}
.agent .rl{
  font-size:9.5px;font-weight:700;letter-spacing:.2em;text-transform:uppercase;
  color:var(--red);margin-top:5px;
}
.agent .ct{margin-top:7px;font-size:14px;line-height:1.7}
.agent .ct a{color:#cfc9c2;text-decoration:none;border-bottom:1px solid #3a3733}
.agent .ct a:hover{color:#fff;border-color:var(--red)}
.fmark{margin-left:auto;flex:none;align-self:center}
/* With no named realtor the wordmark is the only thing on the close, and a
   lone mark pushed right reads like a stray watermark rather than a signature.
   Keyed on the hidden ATTRIBUTE, not :only-child: the realtor block is still a
   DOM child when hidden, so :only-child never matches and silently does
   nothing. */
.who[hidden] + .fmark{margin-left:0}
.fmark img{width:132px;display:block;opacity:.92}
.fine{
  margin-top:30px;padding-top:20px;border-top:1px solid #262421;font-size:12px;
  line-height:1.7;color:#7d766e;
}
.fine p+p{margin-top:9px}
.fine b{color:#9a938a;font-weight:700}
.srcs{margin-top:16px}
.srcs summary{
  cursor:pointer;font-size:10.5px;font-weight:700;letter-spacing:.16em;
  text-transform:uppercase;color:#7d766e;
}
.srcs summary:hover{color:#cfc9c2}
.srcs ul{list-style:none;margin-top:11px;display:grid;gap:6px}
.srcs a{color:#7d766e;font-size:12px;text-decoration:none;border-bottom:1px solid #262421}
.srcs a:hover{color:#cfc9c2}

/* ---------- dialog ---------- */
dialog{
  border:0;border-radius:16px;padding:0;max-width:520px;width:calc(100% - 28px);
  background:var(--canvas);color:var(--ink);box-shadow:0 24px 70px rgba(0,0,0,.3);
}
dialog::backdrop{background:rgba(12,12,12,.55);backdrop-filter:blur(3px)}
.dlg{padding:24px}
.dlg h3{font-family:var(--disp);font-weight:500;font-size:23px;line-height:1.2}
.dlg>p{font-size:14.5px;color:var(--grey);margin-top:8px}
.out{
  margin-top:16px;background:var(--plaster);border:1px solid var(--line2);
  border-radius:9px;padding:12px 13px;font-size:12.5px;word-break:break-all;
  line-height:1.55;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
  max-height:120px;overflow:auto;
}
.ok{
  font-size:12.5px;color:var(--red);font-weight:700;letter-spacing:.1em;
  text-transform:uppercase;margin-top:10px;min-height:17px;
}

@media(min-width:620px){
  .cards{grid-template-columns:repeat(3,1fr)}
  .pf.two{grid-template-columns:1fr 1fr}
  .pf.two .full{grid-column:1/-1}
}

@media(prefers-reduced-motion:reduce){
  *{transition-duration:.01ms!important;animation-duration:.01ms!important}
}

/* ---------- print ----------
   A seller who prints this gets the whole list with every fold already open,
   and none of the controls, because paper cannot be clicked. */
@media print{
  @page{margin:14mm 12mm}
  body{background:#fff;font-size:10.5pt}
  .bar,.prog,.setup,.btnrow,.more,dialog,.days,.pdone,.iconbtn{display:none!important}
  .hero{background:#fff;color:var(--ink);padding:0 0 14pt;border-bottom:2px solid var(--iron)}
  .lede{color:var(--grey)}
  .stamp{border-top-color:var(--line2)}
  .stamp .k{color:var(--grey)}
  .stamp .v{color:var(--ink)}
  h1{font-size:40pt}
  section{padding:14pt 0}
  .wrap{max-width:none;padding:0}
  .det{display:block!important;padding-left:34px}
  li.item{break-inside:avoid;border-color:var(--line2)}
  li.item.on{background:#fff}
  li.item.on .ttl{color:var(--ink);text-decoration:none}
  .phase{break-before:auto}
  .phead{break-after:avoid}
  footer{background:#fff;color:var(--ink);border-top:2px solid var(--iron)}
  .agent .nm2,.fine b{color:var(--ink)}
  .agent .ct a{color:var(--ink)}
  .fine{color:var(--grey);border-top-color:var(--line2)}
  .srcs{display:none}
  .screenonly{display:none}
  .printonly{display:inline}
  /* Tighter on paper. A handout that runs to eleven pages gets skimmed; the
     same list at eight gets read. */
  .itop{padding:9px 12px;gap:10px}
  .det{padding:0 12px 10px 34px}
  .det p{font-size:9.5pt;line-height:1.45}
  .det ul{margin-top:6px;gap:2px}
  .det ul li{font-size:9pt}
  .ttl{font-size:10.5pt;line-height:1.3}
  ul.items{gap:5px;margin-top:12px}
  .plede{margin-top:6px;font-size:10pt}
  .cards{gap:8px}
  .card{padding:12px 14px}
  .card p{font-size:9pt;line-height:1.45}
  .phase{padding-top:16pt;margin-top:16pt}
  .tags{margin-top:4px}
  .handoff{margin-top:14px;padding-top:12px;font-size:11pt}
  .fmark img{filter:invert(1)}
  a[href^=http]:after{content:' (' attr(href) ')';font-size:8pt;color:var(--mute);word-break:break-all}
}
"""


# The whole runtime. No network calls, no analytics, no cookies: this page
# carries a client's address and closing date, so it asks for nothing and sends
# nothing anywhere.
JS = r"""
(function(){
'use strict';

// ---------------------------------------------------------------------------
// Config travels in the URL FRAGMENT, never the query string. A fragment is
// not sent to the server and never lands in a Vercel access log, so a client's
// address and closing date stay between the realtor, the client and the
// browser. This is the reason not to use ?address=...
// ---------------------------------------------------------------------------
function b64e(o){
  var s=JSON.stringify(o), b=new TextEncoder().encode(s), t='';
  for(var i=0;i<b.length;i++) t+=String.fromCharCode(b[i]);
  return btoa(t).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
}
function b64d(s){
  try{
    s=s.replace(/-/g,'+').replace(/_/g,'/');
    while(s.length%4) s+='=';
    var bin=atob(s), b=new Uint8Array(bin.length);
    for(var i=0;i<bin.length;i++) b[i]=bin.charCodeAt(i);
    return JSON.parse(new TextDecoder().decode(b));
  }catch(e){ return null; }
}
function readFrag(){
  var out={};
  (location.hash||'').replace(/^#/,'').split('&').forEach(function(kv){
    var i=kv.indexOf('='); if(i<1) return;
    var k=kv.slice(0,i), v=kv.slice(i+1);
    if(k==='s'||k==='a'){ var o=b64d(v); if(o) out[k]=o; }
  });
  return out;
}

var FRAG = readFrag();
var S = FRAG.s || {};              // the seller's details

// Who is sending it, in priority order: a realtor encoded in the link beats the
// registry, so an agent can borrow any path and still sign it themselves.
// REGISTRY is stamped in at build time from agents.json.
function pathAgent(){
  var slug=(location.pathname||'').replace(/^\/|\/$/g,'');
  return (slug && REGISTRY[slug]) ? REGISTRY[slug] : null;
}
var AGENT_OVERRIDE = FRAG.a || pathAgent();

// ---------------------------------------------------------------------------
// Dates. Offsets are days BEFORE closing; negative means after.
// ---------------------------------------------------------------------------
var MON=['January','February','March','April','May','June','July','August',
         'September','October','November','December'];
var DAY=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];

function parseYMD(s){
  if(!s||!/^\d{4}-\d{2}-\d{2}$/.test(s)) return null;
  var p=s.split('-').map(Number);
  var d=new Date(p[0],p[1]-1,p[2]);          // local midnight, never UTC:
  return isNaN(d) ? null : d;                // "2026-11-15" parsed as UTC
}                                            // renders as the 14th west of GMT.
function shift(d,days){ var x=new Date(d.getTime()); x.setDate(x.getDate()+days); return x; }
function fmt(d){ return DAY[d.getDay()]+', '+MON[d.getMonth()]+' '+d.getDate(); }
function fmtShort(d){ return MON[d.getMonth()].slice(0,3)+' '+d.getDate(); }
function midnight(d){ return new Date(d.getFullYear(),d.getMonth(),d.getDate()); }

var CLOSING = parseYMD(S.closing);

function phaseDate(off){
  if(CLOSING===null||off===null||off===undefined) return null;
  return shift(CLOSING, -off);
}

// ---------------------------------------------------------------------------
// Which items apply. An item with flags shows only when every flag is on.
// ---------------------------------------------------------------------------
function flagsOn(){
  return {
    condo:    !!S.condo,
    freehold: !S.condo,
    buying:   !!S.buying,
    rented_kit: S.rented === undefined ? true : !!S.rented
  };
}
function applyFlags(){
  var on=flagsOn(), shown=0;
  document.querySelectorAll('li.item').forEach(function(li){
    var f=li.dataset.flags ? li.dataset.flags.split(',') : [];
    var ok=f.every(function(x){ return on[x]; });
    li.hidden=!ok;
    if(ok) shown++;
  });
  document.querySelectorAll('.phase').forEach(function(ph){
    var any=[].slice.call(ph.querySelectorAll('li.item')).some(function(l){return !l.hidden;});
    ph.hidden=!any;
  });
  return shown;
}

// ---------------------------------------------------------------------------
// Progress. Kept per seller so one realtor's device does not carry one client's
// ticks onto the next client's list.
// ---------------------------------------------------------------------------
function storeKey(){
  var seed=(S.address||'')+'|'+(S.closing||'')+'|'+(S.client||'');
  var h=5381;
  for(var i=0;i<seed.length;i++) h=((h*33)^seed.charCodeAt(i))>>>0;
  return 'sellerprep:'+h.toString(36);
}
function load(){
  try{ return JSON.parse(localStorage.getItem(storeKey())||'{}')||{}; }
  catch(e){ return {}; }   // private mode, cleared data, blocked storage
}
function save(o){
  try{ localStorage.setItem(storeKey(), JSON.stringify(o)); }catch(e){}
}
var DONE = load();

function paint(){
  var total=0, done=0;
  document.querySelectorAll('li.item').forEach(function(li){
    if(li.hidden) return;
    total++;
    var on=!!DONE[li.dataset.id];
    li.classList.toggle('on',on);
    var box=li.querySelector('input[type=checkbox]');
    if(box) box.checked=on;
    if(on) done++;
  });
  document.querySelectorAll('.phase').forEach(function(ph){
    var items=[].slice.call(ph.querySelectorAll('li.item')).filter(function(l){return !l.hidden;});
    var d=items.filter(function(l){ return DONE[l.dataset.id]; }).length;
    var el=ph.querySelector('.pdone');
    if(el) el.textContent = items.length ? (d+' of '+items.length) : '';
  });
  var c=document.getElementById('count');
  if(c) c.innerHTML='<b>'+done+'</b> of '+total+' done';
  var ni=document.getElementById('nitems');
  if(ni) ni.textContent=total;
  var bar=document.getElementById('bar');
  if(bar) bar.style.width = total ? (done/total*100)+'%' : '0';
}

// ---------------------------------------------------------------------------
// Render the personal details into the page.
// ---------------------------------------------------------------------------
function stampSeller(){
  var box=document.getElementById('stamp');
  if(!box) return;
  if(!S.address && !CLOSING){ box.hidden=true; return; }
  var bits='';
  if(S.client)  bits+='<div class="f"><div class="k">Prepared for</div><div class="v">'+esc(S.client)+'</div></div>';
  if(S.address) bits+='<div class="f"><div class="k">The home</div><div class="v">'+esc(S.address)+'</div></div>';
  if(CLOSING){
    bits+='<div class="f"><div class="k">Closing</div><div class="v">'+fmt(CLOSING)+', '+CLOSING.getFullYear()+'</div></div>';
    var n=Math.round((midnight(CLOSING)-midnight(new Date()))/86400000);
    if(n>0)      bits+='<div class="days"><b>'+n+'</b><span>'+(n===1?'day':'days')+' to go</span></div>';
    else if(n===0) bits+='<div class="days"><b>Today</b><span>closing day</span></div>';
    else         bits+='<div class="days"><b>Closed</b><span>'+(-n)+' '+(n===-1?'day':'days')+' ago</span></div>';
  }
  box.innerHTML=bits;
  box.hidden=false;
}
function esc(s){
  return String(s).replace(/[&<>"']/g,function(c){
    return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
  });
}
function stampDates(){
  document.querySelectorAll('.phase').forEach(function(ph){
    var el=ph.querySelector('.date');
    if(!el) return;
    var raw=ph.dataset.offset;
    if(raw===''||raw==null){ return; }             // "as soon as it is firm"
    var d=phaseDate(Number(raw));
    if(!d){ return; }                              // no closing date yet
    el.textContent=fmt(d);
    el.classList.remove('soft');
  });
}
function stampAgent(){
  if(!AGENT_OVERRIDE) return;
  var a=AGENT_OVERRIDE, set=function(id,v,href){
    var el=document.getElementById(id);
    if(!el) return;
    if(!v){ el.hidden=true; return; }
    el.hidden=false;
    if(href){ el.textContent=v; el.href=href; } else { el.textContent=v; }
  };
  set('ag-name',  a.name);
  set('ag-title', (a.title||'Realtor') + ' \u00b7 ' + BROKERAGE);
  if(a.name) document.title = "Seller's prep list \u00b7 " + a.name;
  set('ag-tag',   a.tagline);
  set('ag-phone', a.phone, a.phone?('tel:'+String(a.phone).replace(/[^\d+]/g,'')):null);
  set('ag-email', a.email, a.email?('mailto:'+a.email):null);
  set('ag-site',  a.site,  a.site?(/^https?:/.test(a.site)?a.site:'https://'+a.site):null);
  // Two shapes reach here: the registry stores a FILENAME under
  // /a/headshots/, while /setup stores whatever URL the realtor pasted. Resolve
  // both, and if the image fails to load, drop it rather than leave a broken
  // frame on a client-facing close.
  var ph=document.getElementById('ag-photo');
  if(ph){
    var srcUrl = a.photo || (a.headshot ? '/a/headshots/'+a.headshot : '');
    if(srcUrl){
      ph.onerror=function(){ ph.hidden=true; };
      ph.alt=a.name||'';
      ph.src=srcUrl;
      ph.hidden=false;
    } else { ph.hidden=true; }
  }
  var blk=document.getElementById('agentblock');
  if(blk) blk.hidden=false;
  // The close is not the only place the realtor is named: the honesty line
  // tells the seller who to ask, and "ask THE AGENCY" is nobody.
  var ask=document.getElementById('ask-who');
  if(ask && a.name) ask.textContent=a.name;
}

// ---------------------------------------------------------------------------
// Calendar export. One .ics with a dated reminder per phase, so the list lands
// in the calendar the seller already looks at instead of a page they must
// remember to reopen.
// ---------------------------------------------------------------------------
function icsDate(d){
  return d.getFullYear()+String(d.getMonth()+1).padStart(2,'0')+String(d.getDate()).padStart(2,'0');
}
function fold(line){
  // RFC 5545 wants lines under 75 octets, continued with a leading space.
  var out=[], s=line;
  while(s.length>73){ out.push(s.slice(0,73)); s=' '+s.slice(73); }
  out.push(s);
  return out.join('\r\n');
}
function buildICS(){
  if(!CLOSING) return null;
  var now=new Date(), stamp=icsDate(now)+'T'+
    String(now.getHours()).padStart(2,'0')+String(now.getMinutes()).padStart(2,'0')+'00';
  var L=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//THE AGENCY//Seller prep list//EN',
         'CALSCALE:GREGORIAN','METHOD:PUBLISH'];
  var where=S.address? (' at '+S.address) : '';
  document.querySelectorAll('.phase').forEach(function(ph,i){
    var raw=ph.dataset.offset;
    if(raw===''||raw==null) return;
    var d=phaseDate(Number(raw));
    if(!d) return;
    var label=ph.querySelector('.when').textContent.trim();
    var items=[].slice.call(ph.querySelectorAll('li.item')).filter(function(l){return !l.hidden;});
    var body=items.map(function(l){ return '- '+l.querySelector('.ttl').textContent.trim(); }).join('\\n');
    L.push('BEGIN:VEVENT');
    L.push('UID:sellerprep-'+i+'-'+icsDate(d)+'@theagency');
    L.push('DTSTAMP:'+stamp+'Z');
    L.push('DTSTART;VALUE=DATE:'+icsDate(d));
    L.push('DTEND;VALUE=DATE:'+icsDate(shift(d,1)));
    L.push(fold('SUMMARY:Selling'+where+': '+label));
    L.push(fold('DESCRIPTION:'+body));
    L.push('BEGIN:VALARM','TRIGGER:-PT9H','ACTION:DISPLAY',
           fold('DESCRIPTION:Selling'+where+': '+label),'END:VALARM');
    L.push('END:VEVENT');
  });
  L.push('END:VCALENDAR');
  return L.join('\r\n');
}

// ---------------------------------------------------------------------------
// Wiring
// ---------------------------------------------------------------------------
function boot(){
  // The registry photograph is rendered by the build, so stampAgent's onerror
  // never sees it. Guard it here too: a face that will not decode has to
  // disappear, not sit on a client-facing close as a broken frame. The content
  // policy forbids an inline onerror attribute, so it is attached here, and it
  // is attached before anything else in case the decode has already failed.
  var rp = document.getElementById('ag-photo');
  if(rp && rp.getAttribute('src')){
    rp.addEventListener('error', function(){ rp.hidden = true; });
    if(rp.complete && !rp.naturalWidth) rp.hidden = true;
  }
  // Fold toggles
  document.querySelectorAll('.more').forEach(function(b){
    b.addEventListener('click',function(){
      var det=document.getElementById(b.getAttribute('aria-controls'));
      var open=b.getAttribute('aria-expanded')==='true';
      b.setAttribute('aria-expanded', String(!open));
      det.hidden=open;
      b.querySelector('span').textContent = open ? 'Why' : 'Hide';
    });
  });
  // Ticks
  document.querySelectorAll('li.item input[type=checkbox]').forEach(function(box){
    box.addEventListener('change',function(){
      var li=box.closest('li.item');
      if(box.checked) DONE[li.dataset.id]=1; else delete DONE[li.dataset.id];
      save(DONE); paint();
    });
  });
  // Tapping the title toggles too, which is a much bigger target than the box.
  document.querySelectorAll('li.item .ttl').forEach(function(t){
    t.addEventListener('click',function(){
      var box=t.closest('li.item').querySelector('input[type=checkbox]');
      box.checked=!box.checked;
      box.dispatchEvent(new Event('change'));
    });
  });

  var dlg=document.getElementById('pdlg');
  var openers=document.querySelectorAll('[data-open-setup]');
  openers.forEach(function(b){
    b.addEventListener('click',function(){
      document.getElementById('f-client').value  = S.client||'';
      document.getElementById('f-address').value = S.address||'';
      document.getElementById('f-closing').value = S.closing||'';
      document.getElementById('f-condo').checked = !!S.condo;
      document.getElementById('f-buying').checked= !!S.buying;
      document.getElementById('f-rented').checked= S.rented===undefined?true:!!S.rented;
      dlg.showModal();
    });
  });
  document.querySelectorAll('[data-close-dlg]').forEach(function(b){
    b.addEventListener('click',function(){ b.closest('dialog').close(); });
  });

  var form=document.getElementById('pform');
  if(form) form.addEventListener('submit',function(e){
    e.preventDefault();
    S={
      client:  document.getElementById('f-client').value.trim(),
      address: document.getElementById('f-address').value.trim(),
      closing: document.getElementById('f-closing').value,
      condo:   document.getElementById('f-condo').checked?1:0,
      buying:  document.getElementById('f-buying').checked?1:0,
      rented:  document.getElementById('f-rented').checked?1:0
    };
    Object.keys(S).forEach(function(k){ if(S[k]===''||S[k]===0) delete S[k]; });
    CLOSING=parseYMD(S.closing);
    var keep = AGENT_OVERRIDE ? ('a='+b64e(AGENT_OVERRIDE)+'&') : '';
    history.replaceState(null,'', location.pathname + (Object.keys(S).length? ('#'+keep+'s='+b64e(S)) : (keep?'#'+keep.slice(0,-1):'')));
    DONE=load();
    dlg.close();
    render();
  });

  var reset=document.getElementById('reset');
  if(reset) reset.addEventListener('click',function(){
    if(!confirm('Clear the ticks on this list? The dates and address stay.')) return;
    DONE={}; save(DONE); paint();
  });

  document.querySelectorAll('[data-print]').forEach(function(b){
    b.addEventListener('click',function(){ window.print(); });
  });

  var cal=document.getElementById('cal');
  if(cal) cal.addEventListener('click',function(){
    var t=buildICS();
    if(!t){ alert('Add your closing date first and the dates become real.'); return; }
    var blob=new Blob([t],{type:'text/calendar;charset=utf-8'});
    var a=document.createElement('a');
    a.href=URL.createObjectURL(blob);
    a.download='seller-prep.ics';
    document.body.appendChild(a); a.click();
    setTimeout(function(){ URL.revokeObjectURL(a.href); a.remove(); },0);
  });

  window.addEventListener('hashchange',function(){
    var f=readFrag(); S=f.s||{}; AGENT_OVERRIDE=f.a||AGENT_OVERRIDE;
    CLOSING=parseYMD(S.closing); DONE=load(); render();
  });

  render();
}

function render(){
  applyFlags();
  stampSeller();
  stampDates();
  stampAgent();
  paint();
  var setup=document.getElementById('setupcard');
  if(setup){
    var personal = !!(S.address||S.closing||S.client);
    setup.classList.toggle('done',personal);
    var h=document.getElementById('setup-h'), p=document.getElementById('setup-p'),
        b=document.getElementById('setup-b');
    if(personal){
      h.textContent='These dates are yours.';
      p.textContent='Counted back from your closing date. Change anything if it moves.';
      b.textContent='Edit';
    }else{
      h.textContent='Add your closing date.';
      p.textContent='Every date below becomes a real one, the list drops what does not apply to your home, and your ticks are remembered on this device.';
      b.textContent='Add my details';
    }
  }
}

if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot);
else boot();
})();
"""
