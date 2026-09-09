var REGISTRY={"keith-godding": {"slug": "keith-godding", "name": "Keith Godding", "title": "Realtor", "phone": "416-520-6687", "email": "keith@firstaccesshomes.com", "site": "firstaccesshomes.com", "headshot": "keith-godding.webp", "tagline": "Toronto and the GTA"}};
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
function hash(seed){
  var h=5381;
  for(var i=0;i<seed.length;i++) h=((h*33)^seed.charCodeAt(i))>>>0;
  return h.toString(36);
}
// WHICH LIST this is, which is the home and the household, NOT the closing
// date. The date is a fact ABOUT the list, not its identity, and it moves:
// this list's own advice is that closings slip by a day fairly often. The key
// used to include it, so a seller who corrected their date by one day came
// back to every tick gone and no way to get them back, and the calendar wrote
// eight brand new events instead of updating the eight already in their phone.
// With neither an address nor a name there is one list on the device, so the
// seed is empty rather than falling back to the date.
function listKey(){
  var seed=(S.address||'')+'|'+(S.client||'');
  return seed==='|' ? '0' : hash(seed);
}
function storeKey(){ return 'sellerprep:'+listKey(); }
function legacyKey(){
  return 'sellerprep:'+hash((S.address||'')+'|'+(S.closing||'')+'|'+(S.client||''));
}
function load(){
  try{
    var k=storeKey(), raw=localStorage.getItem(k);
    if(raw) return JSON.parse(raw)||{};
    // Carry ticks across rather than dropping them on the floor: from the old
    // date-keyed entry, and from the anonymous list somebody ticked before they
    // filled their details in. The anonymous one is MOVED, not copied, so a
    // realtor's phone cannot hand one client's ticks to the next.
    var from=localStorage.getItem(legacyKey()) ||
             (listKey()!=='0' ? localStorage.getItem('sellerprep:0') : null);
    if(from){
      localStorage.setItem(k, from);
      localStorage.removeItem(legacyKey());
      if(listKey()!=='0') localStorage.removeItem('sellerprep:0');
      return JSON.parse(from)||{};
    }
    return {};
  }
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
         'CALSCALE:GREGORIAN','METHOD:PUBLISH',
         fold('X-WR-CALNAME:Selling'+(S.address?(' '+S.address):''))];
  var where=S.address? (' at '+S.address) : '';
  // Every reminder carries the way back. A calendar alert that names three
  // things to do and gives no way to reach the list is a dead end: the person
  // is standing in their kitchen holding a notification. This link opens THEIR
  // list, dates and ticks and all, because the whole of it rides in the URL.
  var back = location.href;
  // The UID must NOT contain the date. It used to, so moving a closing date by
  // one day made eight brand new events instead of updating the eight already
  // there, and the client ended up with two overlapping sets and no idea which
  // was live. Key it on the phase and on which client's list this is, then
  // raise SEQUENCE so a calendar accepts the new dates as a revision.
  var key = listKey();
  var seq = 0;
  try{ seq = (parseInt(localStorage.getItem('sp-seq-'+key),10)||0) + 1;
       localStorage.setItem('sp-seq-'+key, String(seq)); }catch(e){}
  document.querySelectorAll('.phase').forEach(function(ph,i){
    var raw=ph.dataset.offset;
    if(raw===''||raw==null) return;
    var d=phaseDate(Number(raw));
    if(!d) return;
    var label=ph.querySelector('.when').textContent.trim();
    var items=[].slice.call(ph.querySelectorAll('li.item')).filter(function(l){return !l.hidden;});
    var body=items.map(function(l){ return '- '+l.querySelector('.ttl').textContent.trim(); }).join('\\n');
    L.push('BEGIN:VEVENT');
    L.push('UID:sellerprep-'+i+'-'+key+'@theagency');
    L.push('SEQUENCE:'+seq);
    L.push('DTSTAMP:'+stamp+'Z');
    L.push('DTSTART;VALUE=DATE:'+icsDate(d));
    L.push('DTEND;VALUE=DATE:'+icsDate(shift(d,1)));
    L.push(fold('SUMMARY:Selling'+where+': '+label));
    L.push(fold('DESCRIPTION:'+body+'\\n\\nOpen your list: '+back));
    L.push(fold('URL:'+back));
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
// ---------------------------------------------------------------------------
// What is due now
// ---------------------------------------------------------------------------
// The answer on a return visit. Somebody who lands here on day 40 because a
// calendar reminder fired needs the few things they owe this week, not the
// forty they already read on day one. Nothing to show without a closing date,
// because without one nothing is due.
var WEEK = 7;
var CHEVRON = '<svg viewBox="0 0 10 6" fill="none" aria-hidden="true" '
  + 'style="width:9px;height:9px"><path d="M1 1l4 4 4-4" stroke="currentColor" '
  + 'stroke-width="1.8" stroke-linecap="round"/></svg>';

function openItems(){
  var today=midnight(new Date()), late=[], soon=[], next=null;
  document.querySelectorAll('.phase').forEach(function(ph){
    if(ph.hidden) return;
    var raw=ph.dataset.offset;
    var d = (raw===''||raw==null) ? today : phaseDate(Number(raw));
    if(!d) return;
    d=midnight(d);
    var days=Math.round((d-today)/86400000);
    var items=[].slice.call(ph.querySelectorAll('li.item')).filter(function(li){
      return !li.hidden && !DONE[li.dataset.id];
    });
    if(days<0){ late=late.concat(items); }
    else if(days<=WEEK){ soon=soon.concat(items); }
    else if(items.length && !next){ next={label:ph.querySelector('.when').textContent.trim(),
                                          date:d, n:items.length}; }
  });
  return {late:late, soon:soon, next:next};
}

function paintNow(){
  var band=document.getElementById('nowband');
  if(!band) return;
  if(!CLOSING){ band.hidden=true; return; }
  band.hidden=false;
  var o=openItems(), card=document.getElementById('nowcard');
  var k=document.getElementById('now-k'), h=document.getElementById('now-h'),
      sub=document.getElementById('now-sub'), list=document.getElementById('now-list'),
      more=document.getElementById('now-more');
  var show=o.late.concat(o.soon), lateN=o.late.length;
  card.classList.toggle('clear', show.length===0);

  if(show.length===0){
    k.textContent='Up to date';
    h.textContent = o.next ? 'Nothing to do until '+fmtShort(o.next.date)
                           : 'That is the whole list done.';
    sub.textContent = o.next
      ? o.next.n+(o.next.n===1?' thing':' things')+' next, under '+o.next.label.toLowerCase()+'.'
      : 'Every item is ticked.';
    list.innerHTML=''; more.hidden=true;
    return;
  }
  if(lateN){
    k.textContent='Catch up';
    h.textContent = lateN===1 ? 'One thing is past its date'
                              : lateN+' things are past their date';
    sub.textContent = o.soon.length
      ? 'Another '+o.soon.length+(o.soon.length===1?' is':' are')+' due within the week.'
      : 'Nothing else is due for a week.';
  }else{
    k.textContent='This week';
    h.textContent = show.length+(show.length===1?' thing to do':' things to do');
    sub.textContent = 'Everything else on the list is further out.';
  }
  var top=show.slice(0,5);
  list.innerHTML = top.map(function(li,i){
    return '<li><button class="nowgo'+(i<lateN?' late':'')+'" type="button" data-go="'
      + esc(li.dataset.id) + '"><span class="dot"></span><span class="lbl">'
      + esc(li.querySelector('.ttl').textContent.trim())
      + '</span><span class="arw">' + CHEVRON + '</span></button></li>';
  }).join('');
  if(show.length>top.length){
    more.hidden=false;
    more.textContent = (show.length-top.length)+' more are further down the list.';
  } else { more.hidden=true; }
}

function goToItem(id){
  var li=[].slice.call(document.querySelectorAll('li.item')).filter(function(x){
    return x.dataset.id===id;
  })[0];
  if(!li) return;
  var det=li.querySelector('.det'), btn=li.querySelector('.more');
  if(det && det.hidden && btn){ btn.click(); }
  var reduce=matchMedia('(prefers-reduced-motion:reduce)').matches;
  li.scrollIntoView({behavior: reduce?'auto':'smooth', block:'center'});
  li.classList.remove('flash');
  void li.offsetWidth;
  li.classList.add('flash');
  setTimeout(function(){ li.classList.remove('flash'); }, 1700);
}

// ---------------------------------------------------------------------------
// The sheet, and the echo inside it
// ---------------------------------------------------------------------------
// A modal <dialog> already traps focus and blocks the page behind it, but on
// iOS the page under it still rubber-bands, which reads as the sheet coming
// loose. Lock the body while one is open and put focus where the answer starts.
function openSheet(dlg, opener){
  if(!dlg) return;
  dlg.__opener = opener || null;
  document.body.style.overflow='hidden';
  dlg.showModal();
  var first=dlg.querySelector('input,button.pick');
  if(first && !matchMedia('(hover:none)').matches) try{ first.focus(); }catch(e){}
}
document.addEventListener('close', function(e){
  if(e.target && e.target.tagName==='DIALOG'){
    document.body.style.overflow='';
    var o=e.target.__opener;
    if(o) try{ o.focus(); }catch(err){}
  }
}, true);

// How many items a given set of answers actually leaves on the list, without
// touching the page: the same flag rules applyFlags uses, counted on the side.
function countFor(f){
  var n=0;
  document.querySelectorAll('li.item').forEach(function(li){
    var flags=(li.dataset.flags||'').split(',').filter(Boolean);
    var show=true;
    flags.forEach(function(fl){ if(!f[fl]) show=false; });
    if(show) n++;
  });
  return n;
}

function formEcho(){
  var v=document.getElementById('f-closing'), out=document.getElementById('f-payoff'),
      cnt=document.getElementById('f-count');
  var d=v?parseYMD(v.value):null;
  if(out){
    if(!d){ out.textContent=''; }
    else{
      var n=Math.round((midnight(d)-midnight(new Date()))/86400000);
      var when = n>1 ? n+' days away'
               : n===1 ? 'tomorrow'
               : n===0 ? 'today'
               : (-n)+(n===-1?' day ago':' days ago');
      out.innerHTML='<b>'+esc(fmt(d)+', '+d.getFullYear())+'</b>'+esc(when)
        + (n>0 ? '. Every date below is counted back from it.' : '.');
    }
  }
  if(cnt){
    var f={condo:!!(document.getElementById('f-condo')||{}).checked,
           buying:!!(document.getElementById('f-buying')||{}).checked,
           rented:!!(document.getElementById('f-rented')||{}).checked};
    cnt.innerHTML='Your list: <b>'+countFor(f)+' things</b>.';
  }
}

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
      save(DONE); paint(); paintNow();
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
      formEcho();
      openSheet(dlg, b);
    });
  });
  document.querySelectorAll('[data-close-dlg]').forEach(function(b){
    b.addEventListener('click',function(){ b.closest('dialog').close(); });
  });
  // Show what the answers bought, while they are still being given. The date is
  // the whole point of the sheet, so the line under it says the day in full,
  // how far off it is, and what falls in the first week. The count under the
  // three questions moves as they are ticked, so the effect of each one is
  // visible rather than promised.
  ['f-closing','f-condo','f-buying','f-rented'].forEach(function(id){
    var el=document.getElementById(id);
    if(el){ el.addEventListener('input',formEcho); el.addEventListener('change',formEcho); }
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
    var bandWasHidden = (document.getElementById('nowband')||{}).hidden;
    render();
    // Show what just happened. Giving a closing date turns on the band at the
    // top of the page, and a person who filled the sheet in from halfway down
    // would otherwise close it, see nothing move, and have no idea it worked.
    // Only on the transition: an edit later should leave them where they were.
    var band=document.getElementById('nowband');
    if(band && bandWasHidden && !band.hidden){
      var reduce=matchMedia('(prefers-reduced-motion:reduce)').matches;
      band.scrollIntoView({behavior: reduce?'auto':'smooth', block:'center'});
    }
  });

  var nowlist=document.getElementById('now-list');
  if(nowlist) nowlist.addEventListener('click',function(e){
    var b=e.target.closest('[data-go]');
    if(b) goToItem(b.getAttribute('data-go'));
  });

  var reset=document.getElementById('reset');
  if(reset) reset.addEventListener('click',function(){
    if(!confirm('Clear the ticks on this list? The dates and address stay.')) return;
    DONE={}; save(DONE); paint(); paintNow();
  });

  document.querySelectorAll('[data-print]').forEach(function(b){
    b.addEventListener('click',function(){ window.print(); });
  });

  // ---- keeping it without paper -------------------------------------------
  // Four in five sellers will not print this, and a ninety day list that gets
  // opened once is worth nothing. So this sheet takes a position instead of
  // offering a menu: the calendar first, because it is the only one of these
  // that comes back and finds them, then sending it to themselves, because a
  // person's own messages thread is where they actually look.
  var kdlg=document.getElementById('kdlg');
  var keep=document.getElementById('keep');
  if(keep && kdlg) keep.addEventListener('click',function(){
    var lede=document.getElementById('k-lede'),
        calSub=document.getElementById('k-cal-sub');
    if(CLOSING){
      var n=Math.round((midnight(CLOSING)-midnight(new Date()))/86400000);
      lede.textContent = n>0
        ? 'You close in '+n+(n===1?' day':' days')+', and this list runs the whole '
          + 'way. Put it somewhere that brings you back.'
        : 'This list runs past closing. Put it somewhere that brings you back.';
      calSub.textContent = 'Adds a reminder before each stage, each one carrying a '
        + 'link back to this list. Nothing else to remember.';
    }else{
      lede.textContent = 'Closing is a long way off and this list runs the whole '
        + 'way. Put it somewhere that brings you back.';
      calSub.textContent = 'Add your closing date first and this writes a reminder '
        + 'before each stage, each one carrying a link back to your list.';
    }
    // The steps differ per phone and getting them wrong is worse than not
    // offering them, so name the one they are holding. Deliberately NO web app
    // manifest: on Android, Chrome installs a manifest's start_url, and this
    // page's whole personalisation rides in the URL fragment, so an install
    // would hand the client a blank list. Without one, "Add to Home screen" is
    // a plain shortcut to the exact URL they are looking at, fragment and all.
    var ua=navigator.userAgent||'';
    var ios=/iPad|iPhone|iPod/.test(ua) ||
            (/Macintosh/.test(ua) && navigator.maxTouchPoints>1);
    var steps = ios
      ? ['Tap the share button at the bottom of Safari. It is the square with '
         + 'an arrow coming out of it.',
         'Scroll down and tap <b>Add to Home Screen</b>, then tap <b>Add</b>.']
      : ['Tap the three dots at the top right of Chrome.',
         'Tap <b>Add to Home screen</b>, then tap <b>Add</b>.'];
    steps.push('The list becomes an icon on your phone, and your ticks are '
               + 'still on it when you open it.');
    document.getElementById('k-steps').innerHTML =
      steps.map(function(t){ return '<li>'+t+'</li>'; }).join('');
    openSheet(kdlg, keep);
  });

  // Sending it to themselves. One tap into the share sheet they already know,
  // which works in an in-app browser where Add to Home Screen does not, and
  // lands the link in the thread or the inbox they will actually search.
  var share=document.getElementById('k-share');
  if(share) share.addEventListener('click',function(){
    var sub=document.getElementById('k-share-sub');
    var title=document.title;
    var text=(S.address? ('Selling '+S.address+'. ') : '')
             + 'Everything between sold and keys, in order.';
    if(navigator.share){
      navigator.share({title:title, text:text, url:location.href})
        .then(function(){ sub.textContent='Sent. It is in whichever app you picked.'; })
        .catch(function(){});
      return;
    }
    copyLink(function(ok){
      sub.textContent = ok
        ? 'Link copied. Paste it into a message to yourself and it is saved.'
        : 'Copy the address from your browser bar and send it to yourself.';
    });
  });

  function copyLink(done){
    var url=location.href;
    if(navigator.clipboard && window.isSecureContext){
      navigator.clipboard.writeText(url).then(function(){done(true);},fallback);
    } else fallback();
    function fallback(){
      var t=document.createElement('textarea');
      t.value=url; t.style.position='fixed'; t.style.opacity='0';
      document.body.appendChild(t); t.select();
      var ok=false;
      try{ ok=document.execCommand('copy'); }catch(e){}
      t.remove(); done(ok);
    }
  }

  var cal=document.getElementById('k-cal');
  if(cal) cal.addEventListener('click',function(){
    var t=buildICS();
    if(!t){
      // No dead ends. A person who taps the calendar without a closing date
      // gets taken to the one question that unlocks it, not an alert telling
      // them off.
      kdlg.close();
      var opener=document.querySelector('[data-open-setup]');
      if(opener) opener.click();
      return;
    }
    var blob=new Blob([t],{type:'text/calendar;charset=utf-8'});
    var a=document.createElement('a');
    a.href=URL.createObjectURL(blob);
    a.download='selling-'+(S.address? S.address.replace(/[^a-z0-9]+/gi,'-').toLowerCase().slice(0,40) : 'prep-list')+'.ics';
    document.body.appendChild(a); a.click();
    setTimeout(function(){ URL.revokeObjectURL(a.href); a.remove(); },0);
    document.getElementById('k-cal-sub').textContent =
      'Downloaded. Open the file and your calendar offers to add them all.';
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
  paintNow();
  var setup=document.getElementById('setupcard');
  if(setup){
    var personal = !!(S.address||S.closing||S.client);
    setup.classList.toggle('done',personal);
    var h=document.getElementById('setup-h'), p=document.getElementById('setup-p'),
        b=document.getElementById('setup-b');
    if(personal){
      // The right prompt at the right moment. Somebody who has just given their
      // closing date is exactly the person who should be told to put the list
      // where it will find them again, and this is the one second they are
      // paying attention to this card.
      h.textContent='These dates are yours.';
      p.textContent='Counted back from your closing date, and safe if it moves. '
        + 'Now put the list somewhere that brings you back to it.';
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
