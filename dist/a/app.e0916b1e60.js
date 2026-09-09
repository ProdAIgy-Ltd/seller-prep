var REGISTRY={"keith-godding": {"slug": "keith-godding", "name": "Keith Godding", "title": "Realtor", "phone": "416-520-6687", "email": "keith@firstaccesshomes.com", "site": "firstaccesshomes.com", "headshot": "keith-godding.jpg", "tagline": "Toronto and the GTA"}};
var BROKERAGE="THE AGENCY";

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
