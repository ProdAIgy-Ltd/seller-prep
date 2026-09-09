"""Build the static site.

  python build.py            -> dist/

What comes out:
  dist/index.html            the brokerage page, no named realtor. Shareable.
  dist/<slug>/index.html     one page per realtor in agents.json
  dist/setup/index.html      the link builder, for realtors and for their clients
  dist/a/                    fonts and marks, root-absolute so every path works
  dist/404.html

The headers and the build settings live in seller-prep/vercel.json, which Vercel
reads from the ROOT DIRECTORY. A copy inside dist/ is never read.

Asset paths are ROOT-ABSOLUTE (/a/...). A relative path works at / and breaks at
/keith-godding/, and the failure is invisible until the deployed page is opened
in a browser, which is exactly the class of miss this kit has shipped before.
"""
import hashlib
import html
import json
import pathlib
import re
import shutil
import sys

import content
from template import CSS, JS

HERE = pathlib.Path(__file__).resolve().parent
DIST = HERE / "dist"
ASSETS = HERE / "assets"

E = html.escape


def esc(s):
    return E(str(s), quote=True)


# ---------------------------------------------------------------------------
# Copy gate. The bans are not advisory; they have each cost a rebuild.
# ---------------------------------------------------------------------------
BANNED = [
    (r"[—–]", "em-dash or en-dash"),
    (r"\bAI\b", 'the word "AI"'),
    (r"\bbps\b|\bbasis points\b", "finance jargon (bps)"),
    (r"\bprints?\b(?! )", "finance jargon (prints)"),
    # The realtor-agnostic rule, made mechanical. A first person plural in the
    # checklist would put words in the mouth of whichever realtor shares it.
    (r"\b(we|our|ours|us|we're|we've|let's)\b", "first person plural"),
]


# A sentence in a JS string is read by a seller exactly like a sentence in the
# HTML, and copy_gate strips <script> before it looks. So the runtime copy went
# unchecked: the progress line, the calendar text, every message /setup shows a
# realtor. A "we" in any of them breaks the realtor-agnostic rule just as
# thoroughly, and nothing would have caught it.
#
# Only literals containing a SPACE are checked. That is what separates prose
# from machinery: 'input,select', 'ag-photo' and 'tel:' carry no space, while
# every sentence does.
JS_STR = re.compile(
    r"'((?:[^'\\\n]|\\.)*)'"
    r'|"((?:[^"\\\n]|\\.)*)"'
)


def copy_gate_js(src, where):
    prose = [m.group(1) or m.group(2) or "" for m in JS_STR.finditer(src)]
    copy_gate(" \n".join(t for t in prose if " " in t), where)


def copy_gate(text, where):
    """Run over the RENDERED reader-facing text, not the source. Source comments
    are exempt; what a seller reads is not."""
    body = re.sub(r"<(script|style)\b.*?</\1>", " ", text, flags=re.S | re.I)
    body = re.sub(r"<[^>]+>", " ", body)
    body = html.unescape(body)
    bad = []
    for pat, why in BANNED:
        for m in re.finditer(pat, body, re.I):
            a, b = max(0, m.start() - 45), min(len(body), m.end() + 45)
            frag = " ".join(body[a:b].split())
            bad.append(f"  {why}: ...{frag}...")
    if bad:
        raise SystemExit(f"COPY GATE FAILED in {where}:\n" + "\n".join(bad))


# ---------------------------------------------------------------------------
# Pieces
# ---------------------------------------------------------------------------
CHEV = ('<svg viewBox="0 0 10 6" fill="none" aria-hidden="true">'
        '<path d="M1 1l4 4 4-4" stroke="currentColor" stroke-width="1.6" '
        'stroke-linecap="round"/></svg>')

PRINT_ICON = ('<svg viewBox="0 0 16 16" fill="none" aria-hidden="true">'
              '<path d="M4.5 6V2h7v4M4.5 12H3V7.5h10V12h-1.5M4.5 10h7v4h-7z" '
              'stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/></svg>')


def render_item(phase_key, it):
    iid = f"{phase_key}.{it['id']}"
    flags = ",".join(it.get("flags", []))
    cls = "item crit" if it.get("critical") else "item"
    did = "d-" + iid.replace(".", "-")

    tags = []
    if it.get("critical"):
        tags.append('<span class="tag m">Do not skip</span>')
    if it.get("money"):
        tags.append('<span class="tag m">Costs money</span>')
    for f in it.get("flags", []):
        label = {"condo": "Condo", "freehold": "House",
                 "buying": "If buying too", "rented_kit": "Rented equipment"}[f]
        tags.append(f'<span class="tag">{label}</span>')
    tagrow = f'<div class="tags">{"".join(tags)}</div>' if tags else ""

    det = [f"<p>{esc(it['detail'])}</p>"]
    if it.get("list"):
        det.append("<ul>" + "".join(f"<li>{esc(x)}</li>" for x in it["list"]) + "</ul>")
    if it.get("link"):
        label, href = it["link"]
        det.append(f'<a class="lnk" href="{esc(href)}" target="_blank" '
                   f'rel="noopener noreferrer">{esc(label)}</a>')

    return f"""<li class="{cls}" data-id="{esc(iid)}" data-flags="{esc(flags)}">
<div class="itop">
<input type="checkbox" id="c-{esc(iid)}" aria-labelledby="t-{esc(iid)}">
<div class="ibody">
<span class="ttl" id="t-{esc(iid)}">{esc(it['title'])}</span>
{tagrow}
<button class="more" type="button" aria-expanded="false" aria-controls="{did}"><span>Why</span>{CHEV}</button>
</div></div>
<div class="det" id="{did}" hidden>{''.join(det)}</div>
</li>"""


def render_phase(p):
    off = "" if p["offset"] is None else str(p["offset"])
    if p["offset"] is None:
        chip = '<span class="date soft">Start now</span>'
    elif p["offset"] == 0:
        chip = '<span class="date soft">Closing day</span>'
    elif p["offset"] < 0:
        d = -p["offset"]
        chip = (f'<span class="date soft">{d} day{"" if d == 1 else "s"} '
                f'after closing</span>')
    else:
        d = p["offset"]
        chip = (f'<span class="date soft">{d} day{"" if d == 1 else "s"} '
                f'before closing</span>')
    items = "".join(render_item(p["key"], it) for it in p["items"])
    return f"""<div class="phase" data-offset="{off}">
<div class="phead"><h3 class="when">{esc(p['label'])}</h3>{chip}
<span class="pdone"></span></div>
<p class="plede">{esc(p['lede'])}</p>
<ul class="items">{items}</ul>
</div>"""


def render_headlines():
    cards = "".join(
        f'<div class="card"><div class="n">{esc(h["n"])}</div>'
        f'<h3>{esc(h["title"])}</h3><p>{esc(h["body"])}</p></div>'
        for h in content.HEADLINES)
    return f'<div class="cards">{cards}</div>'


def render_sources():
    rows = "".join(
        f'<li><a href="{esc(u)}" target="_blank" rel="noopener noreferrer">{esc(t)}</a></li>'
        for t, u in content.SOURCES.values())
    return (f'<details class="srcs"><summary>Where this came from</summary>'
            f'<ul>{rows}</ul></details>')


def agent_block(agent, brokerage):
    """The close. With no agent this is the brokerage alone, which is what makes
    the page shareable: nothing on it assumes who handed it over."""
    if not agent:
        # The block is present but empty, so a fragment-supplied realtor can
        # fill it at runtime without the page reflowing around a missing node.
        return f"""<div class="agent">
<div class="who" id="agentblock" hidden>
<img class="ph" id="ag-photo" alt="" hidden>
<div><div class="nm2" id="ag-name"></div>
<div class="rl" id="ag-title"></div>
<div class="ct"><span id="ag-tag"></span><br>
<a id="ag-phone" hidden></a><br><a id="ag-email" hidden></a><br>
<a id="ag-site" hidden></a></div></div>
</div>
<div class="fmark"><img src="/a/ta-wordmark-wht.png" alt="{esc(brokerage['name'])}" width="132"></div>
</div>"""

    photo = (f'<img class="ph" id="ag-photo" src="/a/headshots/{esc(agent["headshot"])}" '
             f'alt="{esc(agent["name"])}">' if agent.get("headshot")
             else '<img class="ph" id="ag-photo" alt="" hidden>')
    tel = re.sub(r"[^\d+]", "", agent.get("phone", ""))
    ct = []
    if agent.get("phone"):
        ct.append(f'<a id="ag-phone" href="tel:{esc(tel)}">{esc(agent["phone"])}</a>')
    if agent.get("email"):
        ct.append(f'<a id="ag-email" href="mailto:{esc(agent["email"])}">{esc(agent["email"])}</a>')
    if agent.get("site"):
        site = agent["site"]
        href = site if site.startswith("http") else "https://" + site
        ct.append(f'<a id="ag-site" href="{esc(href)}" target="_blank" '
                  f'rel="noopener noreferrer">{esc(site)}</a>')
    tag = f'<span id="ag-tag">{esc(agent["tagline"])}</span><br>' if agent.get("tagline") else '<span id="ag-tag"></span>'
    return f"""<div class="agent" id="agentblock">
{photo}
<div><div class="nm2" id="ag-name">{esc(agent['name'])}</div>
<div class="rl" id="ag-title">{esc(agent.get('title','Realtor'))} &middot; {esc(brokerage['name'])}</div>
<div class="ct">{tag}{'<br>'.join(ct)}</div></div>
<div class="fmark"><img src="/a/ta-wordmark-wht.png" alt="{esc(brokerage['name'])}" width="132"></div>
</div>"""


DIALOG = """<dialog id="pdlg" aria-labelledby="dlgh">
<form method="dialog"></form>
<div class="dlg">
<h3 id="dlgh">Make this list yours</h3>
<p>This stays in your browser. Nothing is sent anywhere and no account is needed.</p>
<form class="pf two" id="pform">
<div class="fld full"><label for="f-client">Your name, or the household</label>
<input type="text" id="f-client" placeholder="The Patel family" autocomplete="off"></div>
<div class="fld full"><label for="f-address">The home you are selling</label>
<input type="text" id="f-address" placeholder="118 Waverley Road, Toronto" autocomplete="off"></div>
<div class="fld full"><label for="f-closing">Closing date</label>
<input type="date" id="f-closing">
<div class="hint">Every date on the list is counted back from this.</div></div>
<div class="fld full"><div class="checks">
<label class="chk"><input type="checkbox" id="f-condo">
<span>It is a condominium<i>Adds the elevator booking and the building's moving rules.</i></span></label>
<label class="chk"><input type="checkbox" id="f-buying">
<span>I am buying another home at the same time<i>Adds lining the two closing dates up.</i></span></label>
<label class="chk"><input type="checkbox" id="f-rented" checked>
<span>Something here is rented, like the water heater<i>Adds paying it out or handing it over.</i></span></label>
</div></div>
<div class="btnrow full">
<button class="btn red" type="submit">Save</button>
<button class="btn ghost" type="button" data-close-dlg>Cancel</button>
</div>
</form>
</div></dialog>

<!-- Keeping it without paper. A seller who does not want a printout still wants
     the list somewhere they will find it again, and "bookmark it" is not an
     answer anybody follows. The home screen is: it becomes an icon beside their
     other apps, it opens straight back to their own list, and the ticks are
     already on the device. So this dialog takes a position and leads with that,
     with the two steps for the phone they are actually holding. The PDF and the
     calendar follow as the other two things a person might want. -->
<dialog id="kdlg" aria-labelledby="kdlgh">
<form method="dialog"></form>
<div class="dlg">
<h3 id="kdlgh">Keep this on your phone</h3>
<p>No paper needed. Put it on your home screen and it opens like an app, with
your own dates and your ticks already on it.</p>
<ol class="steps" id="k-steps"></ol>
<p class="hint" id="k-other">Prefer a file? Choose <b>Print</b> and then
<b>Save as PDF</b> instead. A PDF is a snapshot, so ticks made after you save it
will not show up in it.</p>
<div class="btnrow full">
<button class="btn red" type="button" id="k-cal">Put the dates in my calendar</button>
<button class="btn ghost" type="button" data-close-dlg>Close</button>
</div>
</div></dialog>"""


def page(agent, brokerage, n_items, css_url, js_url):
    name = agent["name"] if agent else brokerage["name"]
    title = f"Seller's prep list &middot; {esc(name)}"
    desc = ("Everything a home seller in Ontario needs to do between the day the "
            "sale is firm and the week after closing, counted back from the "
            "closing date.")
    canon_name = esc(name)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{esc(desc)}">
<meta name="theme-color" content="#0c0c0c">
<meta name="color-scheme" content="light">
<meta property="og:title" content="Seller's prep list">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="article">
<link rel="icon" href="/a/favicon.png" type="image/png">
<!-- A seller who does not want paper puts this on their home screen. iOS
     takes THIS file for the icon, not the favicon. There is deliberately no
     web app manifest: Chrome would install its start_url, and the client's
     dates ride in the URL fragment, so an install would open a blank list. -->
<link rel="apple-touch-icon" href="/a/apple-touch-icon.png">
<meta name="apple-mobile-web-app-title" content="Prep list">
<meta name="theme-color" content="#ED2127">
<link rel="apple-touch-icon" href="/a/ta-mark-red.png">
<link rel="preload" as="font" type="font/woff2" href="/a/fonts/flama-bold.woff2" crossorigin>
<link rel="preload" as="font" type="font/woff2" href="/a/fonts/din-reg.woff2" crossorigin>
<link rel="stylesheet" href="{css_url}">
</head>
<body>

<header class="bar">
<div class="wrap">
<img src="/a/ta-mark-red.png" alt="" width="26" height="26">
<span class="nm">Seller&rsquo;s prep list</span>
<span class="sp"></span>
<span class="count" id="count"></span>
<button class="iconbtn" data-print type="button" aria-label="Print this list" title="Print">{PRINT_ICON}</button>
</div>
<div class="prog"><i id="bar"></i></div>
</header>

<div class="hero">
<div class="wrap">
<div class="kick">Sold &middot; What happens next</div>
<h1>Everything between sold and keys</h1>
<div class="rule"></div>
<p class="lede"><span id="nitems">{n_items}</span> things, in the order they need
doing, counted back from your closing date. The ones that cost real money if they
are missed are marked.</p>
<div class="stamp" id="stamp" hidden></div>
</div>
</div>

<main>
<section class="wrap">
<div class="eyebrow">Start here</div>
<h2>Three things go wrong more than everything else combined</h2>
{render_headlines()}
<p class="handoff"><span class="screenonly">Everything below is the list itself,
in the order it needs doing. Tick as you go; this device remembers where you got
to.</span><span class="printonly">Everything below is the list itself, in the
order it needs doing.</span></p>

<div class="setup" id="setupcard">
<h3 id="setup-h">Add your closing date.</h3>
<p id="setup-p"></p>
<div class="btnrow">
<button class="btn" type="button" data-open-setup><span id="setup-b">Add my details</span></button>
<button class="btn ghost" type="button" id="keep">Keep it on my phone</button>
<button class="btn ghost" type="button" data-print>Print</button>
</div>
</div>
</section>

<section class="wrap" style="padding-top:0">
{''.join(render_phase(p) for p in content.PHASES)}
<div class="btnrow" style="margin-top:30px">
<button class="btn ghost" type="button" id="reset">Clear my ticks</button>
</div>
</section>
</main>

<footer>
<div class="wrap">
{agent_block(agent, brokerage)}
<div class="fine">
<p><b>This is a general list, not advice about your deal.</b> Your agreement of
purchase and sale, your lawyer and your lender decide what actually applies to
you, and where any of them says something different from this page, they are
right and this page is wrong. It is written for Ontario. Ask <span id="ask-who">{canon_name}</span>
about anything here that does not look like your situation.</p>
<p>Nothing you type on this page leaves your browser. There is no account, no
tracking and no cookie; your details live in the link and your ticks live on
this device only.</p>
<p>&copy; {esc(brokerage['credit'])}. Each office is independently owned and operated.</p>
{render_sources()}
</div>
</div>
</footer>

{DIALOG}
<script src="{js_url}" defer></script>
</body>
</html>"""


SETUP_JS = r"""(function(){
'use strict';
var REG=__REG__;
function b64e(o){var s=JSON.stringify(o),b=new TextEncoder().encode(s),t='';
for(var i=0;i<b.length;i++)t+=String.fromCharCode(b[i]);
return btoa(t).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');}
function v(id){var e=document.getElementById(id);return e.type==='checkbox'?e.checked:e.value.trim();}

// ---------------------------------------------------------------------------
// The photograph. A realtor who has one online pastes its address and the link
// stays short. A realtor who only has it on their phone uploads it, and it is
// downscaled and encoded HERE, in their browser, then carried inside the link
// itself. Nothing is uploaded to any server, because there is no server to
// upload to: this whole tool is static files.
//
// 192px WebP at 0.88, which is exactly what the registry ships, so an uploaded
// photograph is not a lesser one. The close draws the photo at 62px in a
// circle, and a 3x phone therefore asks for 186 real pixels: under that the
// device is upscaling, and upscaling is what soft looks like. Measured against
// the untouched source crop, root-mean-square error per channel: 128 WebP q72
// read 5.19, 176 JPEG q86 (what the registry shipped before) 2.94, 192 WebP
// q88 2.28, and 192 WebP q94 only 1.76 for half again the bytes. So 192 at
// 0.88 is the knee, and it is both sharper and smaller than the JPEG.
// ---------------------------------------------------------------------------
var PHOTO = null;
var PHOTO_PX = 192;
var PHOTO_Q = 0.88;

function note(msg){ document.getElementById('g-note').textContent = msg; }

function showPhoto(dataUri){
  PHOTO = dataUri;
  var prev = document.getElementById('g-prev');
  var clear = document.getElementById('g-clear');
  if(dataUri){ prev.src = dataUri; prev.hidden = false; clear.hidden = false; }
  else { prev.removeAttribute('src'); prev.hidden = true; clear.hidden = true; }
  build();
}

// A pasted address is the other half of this, and it used to fail in silence.
// The content policy allows an image from 'self', from https, or from a data:
// URI, and nothing else, so an http:// address or a share page that is not
// actually an image simply never appears, with no error a realtor could see.
// Check it here, in front of them, and show what will actually render.
var URLCHECK = null;
function checkPhotoUrl(u){
  u = (u || '').trim();
  if(URLCHECK){ URLCHECK.onload = URLCHECK.onerror = null; URLCHECK = null; }
  if(!u){
    if(!PHOTO) showPhoto(null);
    note('Or paste the address of one already online, below. Leave both empty '
         + 'and the close simply has no photograph.');
    return;
  }
  if(!/^https:\/\//i.test(u)){
    showPhoto(null);
    note('That address has to start with https:// or the browser will refuse '
         + 'to show it.');
    return;
  }
  note('Checking that address ...');
  var probe = new Image();
  URLCHECK = probe;
  probe.onload = function(){
    if(URLCHECK !== probe) return;
    var p = document.getElementById('g-prev');
    p.src = u; p.hidden = false;
    document.getElementById('g-clear').hidden = false;
    note(probe.naturalWidth < 186
      ? 'That photograph loads, but it is only ' + probe.naturalWidth + 'px '
        + 'wide and it will look soft on a phone. Uploading one is sharper.'
      : 'That photograph loads, ' + probe.naturalWidth + 'px wide. The link '
        + 'stays short because only the address travels in it.');
  };
  probe.onerror = function(){
    if(URLCHECK !== probe) return;
    showPhoto(null);
    note('Nothing loaded from that address. Open it in a browser tab: if it '
         + 'does not show a photograph on its own there, it will not show here. '
         + 'A share page from Drive or Dropbox is a page, not a picture.');
  };
  probe.src = u;
}

function loadPhotoFile(file){
  if(!file) return;
  if(!/^image\//.test(file.type)){ note('That file is not an image.'); return; }
  // FileReader, not URL.createObjectURL: the content policy allows data: images
  // but not blob:, so an object URL would be blocked before it ever decoded.
  var fr = new FileReader();
  fr.onerror = function(){ note('That file could not be read.'); };
  fr.onload = function(){
    var img = new Image();
    img.onload = function(){
      var s = Math.min(img.width, img.height);
      var sx = (img.width - s) / 2;
      // Bias the crop UPWARD, because a centred square on a portrait cuts the
      // top of the head off and leaves a chest. Same rule the registry uses.
      var sy = Math.min(Math.max(0, (img.height - s) / 4), img.height - s);
      var c = document.createElement('canvas');
      c.width = c.height = PHOTO_PX;
      var g = c.getContext('2d');
      g.imageSmoothingEnabled = true;
      g.imageSmoothingQuality = 'high';
      g.drawImage(img, sx, sy, s, s, 0, 0, PHOTO_PX, PHOTO_PX);
      var d = c.toDataURL('image/webp', PHOTO_Q);
      // Safari before 14 cannot encode WebP from a canvas and silently hands
      // back a PNG, which is far larger. Check what actually came out, and drop
      // to JPEG rather than carry a 40KB PNG inside the link.
      if(d.slice(0, 15) !== 'data:image/webp') d = c.toDataURL('image/jpeg', PHOTO_Q);
      document.getElementById('g-photo').value = '';
      note('Cropped to a square and shrunk to ' + PHOTO_PX + 'px, in this browser. '
           + 'It travels inside the link.');
      showPhoto(d);
    };
    img.onerror = function(){
      note('That image could not be opened. An iPhone HEIC photo often cannot be; '
           + 'open it and export a JPEG, then try again.');
    };
    img.src = fr.result;
  };
  fr.readAsDataURL(file);
}
function build(){
  var pick=v('g-pick'), base=location.origin+'/', frag=[];
  if(pick && pick!=='__none__'){ base=location.origin+'/'+pick; }
  else if(pick===''){
    var a={};
    ['name','title','phone','email','site','tag'].forEach(function(k){
      var val=v('g-'+k); if(val) a[k==='tag'?'tagline':k]=val;
    });
    var photo = PHOTO || v('g-photo');
    if(photo) a.photo = photo;
    if(Object.keys(a).length) frag.push('a='+b64e(a));
  }
  var s={};
  if(v('g-client'))  s.client=v('g-client');
  if(v('g-address')) s.address=v('g-address');
  if(v('g-closing')) s.closing=v('g-closing');
  if(v('g-condo'))   s.condo=1;
  if(v('g-buying'))  s.buying=1;
  if(v('g-rented'))  s.rented=1;
  if(Object.keys(s).length) frag.push('s='+b64e(s));
  var url=base+(frag.length?'#'+frag.join('&'):'');
  document.getElementById('out').textContent=url;
  document.getElementById('open').href=url;
  reportLength(url);
  return url;
}
function reportLength(url){
  var el = document.getElementById('len'), n = url.length;
  if(n < 400){
    el.className = 'len';
    el.innerHTML = '<b>' + n + '</b> characters. Short enough to put anywhere.';
  } else if(PHOTO){
    el.className = 'len';
    el.innerHTML = '<b>' + n.toLocaleString() + '</b> characters, because the '
      + 'photograph is inside the link. That sends fine by email, text or '
      + 'WhatsApp, but it looks unwieldy written out. The photograph itself is '
      + 'the same either way. For a short link, ask to be added permanently and '
      + 'you get an address like /your-name instead.';
  } else {
    el.className = 'len';
    el.innerHTML = '<b>' + n.toLocaleString() + '</b> characters.';
  }
}

document.querySelectorAll('input,select').forEach(function(e){
  e.addEventListener('input',build); e.addEventListener('change',build);
});
document.getElementById('g-pick').addEventListener('change',function(){
  var r=REG[this.value];
  if(r){
    document.getElementById('g-name').value=r.name||'';
    document.getElementById('g-title').value=r.title||'';
    document.getElementById('g-phone').value=r.phone||'';
    document.getElementById('g-email').value=r.email||'';
    document.getElementById('g-site').value=r.site||'';
    document.getElementById('g-tag').value=r.tagline||'';
  }
  build();
});
document.getElementById('g-file').addEventListener('change',function(){
  loadPhotoFile(this.files && this.files[0]);
  this.value='';   // so re-picking the SAME file fires change again
});
document.getElementById('g-clear').addEventListener('click',function(){
  document.getElementById('g-photo').value = '';
  if(URLCHECK){ URLCHECK.onload = URLCHECK.onerror = null; URLCHECK = null; }
  note('Or paste the address of one already online, below. Leave both empty and '
       + 'the close simply has no photograph.');
  showPhoto(null);
});
document.getElementById('g-photo').addEventListener('input',function(){
  if(this.value.trim() && PHOTO) showPhoto(null);   // a pasted address wins
  checkPhotoUrl(this.value);
});

document.getElementById('copy').addEventListener('click',function(){
  var url=build(), ok=document.getElementById('ok');
  function done(){ ok.textContent='Copied'; setTimeout(function(){ok.textContent='';},2200); }
  if(navigator.clipboard&&window.isSecureContext){
    navigator.clipboard.writeText(url).then(done,fallback);
  } else fallback();
  function fallback(){
    // clipboard API is blocked on plain http and in some embedded browsers;
    // the seller-facing page never needs this but a realtor on a locked-down
    // device does, and a copy button that silently does nothing is worse than
    // no button.
    var t=document.createElement('textarea');
    t.value=url; t.style.position='fixed'; t.style.opacity='0';
    document.body.appendChild(t); t.select();
    try{ document.execCommand('copy'); done(); }
    catch(e){ ok.textContent='Press and hold the link above to copy'; }
    t.remove();
  }
});
build();
})();"""


# ---------------------------------------------------------------------------
# The setup page: how a realtor who is not in the registry still gets a page,
# and how any realtor builds a client's personal link.
# ---------------------------------------------------------------------------
def setup_page(reg, brokerage, css_url, setup_js_url):
    opts = "".join(f'<option value="{esc(a["slug"])}">{esc(a["name"])}</option>'
                   for a in reg)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Make a seller's prep link</title>
<meta name="robots" content="noindex,nofollow">
<link rel="icon" href="/a/favicon.png" type="image/png">
<link rel="stylesheet" href="{css_url}">
<style>
.pf{{max-width:none}}
select{{width:100%;min-height:44px;padding:10px 13px;border:1px solid var(--line2);
border-radius:9px;font-family:var(--body);font-size:16px;background:var(--canvas);color:var(--ink)}}
.step{{border-top:1px solid var(--line2);padding-top:26px;margin-top:30px}}
.step:first-of-type{{border-top:0;margin-top:18px;padding-top:0}}
.stepn{{font-size:10px;font-weight:700;letter-spacing:.24em;text-transform:uppercase;color:var(--red)}}
</style>
</head>
<body>
<header class="bar"><div class="wrap">
<img src="/a/ta-mark-red.png" alt="" width="26" height="26">
<span class="nm">Link builder</span></div></header>

<div class="hero"><div class="wrap">
<div class="kick">For realtors</div>
<h1>Make a link</h1>
<div class="rule"></div>
<p class="lede">Put your name on the list, and your client's details in it. Takes
about a minute and needs nobody's permission.</p>
</div></div>

<main><section class="wrap">

<div class="step">
<div class="stepn">Step one</div>
<h2>Who is sending it</h2>
<p class="sub">Pick a name already set up, or type your own. Typing your own
works straight away; it travels in the link rather than needing anything
published.</p>
<form class="pf two" id="agf" onsubmit="return false">
<div class="fld full"><label for="g-pick">Already set up</label>
<select id="g-pick"><option value="">Type my own details instead</option>
<option value="__none__">No name, brokerage only</option>{opts}</select></div>
<div class="fld"><label for="g-name">Your name</label>
<input type="text" id="g-name" autocomplete="name"></div>
<div class="fld"><label for="g-title">Title</label>
<input type="text" id="g-title" placeholder="Realtor" autocomplete="off"></div>
<div class="fld"><label for="g-phone">Phone</label>
<input type="tel" id="g-phone" autocomplete="tel"></div>
<div class="fld"><label for="g-email">Email</label>
<input type="email" id="g-email" autocomplete="email"></div>
<div class="fld"><label for="g-site">Website</label>
<input type="text" id="g-site" placeholder="firstaccesshomes.com"></div>
<div class="fld"><label for="g-tag">One line under your name</label>
<input type="text" id="g-tag" placeholder="Toronto and the GTA"></div>
<div class="fld full"><label for="g-photo">Your photograph</label>
<div class="photo">
<img id="g-prev" alt="" hidden>
<div class="photo-c">
<div class="btnrow" style="margin-top:0">
<label class="btn ghost" for="g-file">Upload a photo</label>
<input type="file" id="g-file" accept="image/*" hidden>
<button class="btn ghost" type="button" id="g-clear" hidden>Remove</button>
</div>
<div class="hint" id="g-note">Or paste the address of one already online, below.
Leave both empty and the close simply has no photograph.</div>
</div></div>
<input type="text" id="g-photo" placeholder="https://...jpg" style="margin-top:11px">
</div>
</form>
</div>

<div class="step">
<div class="stepn">Step two, optional</div>
<h2>Who it is for</h2>
<p class="sub">Fill this in and the list arrives with their dates already on it.
Leave it empty and they fill it in themselves on the page, which works just as
well.</p>
<form class="pf two" id="clf" onsubmit="return false">
<div class="fld"><label for="g-client">Client or household</label>
<input type="text" id="g-client" placeholder="The Patel family"></div>
<div class="fld"><label for="g-closing">Closing date</label>
<input type="date" id="g-closing"></div>
<div class="fld full"><label for="g-address">The home</label>
<input type="text" id="g-address" placeholder="118 Waverley Road, Toronto"></div>
<div class="fld full"><div class="checks">
<label class="chk"><input type="checkbox" id="g-condo"><span>It is a condominium</span></label>
<label class="chk"><input type="checkbox" id="g-buying"><span>They are buying at the same time</span></label>
<label class="chk"><input type="checkbox" id="g-rented" checked><span>Something is rented, like the water heater</span></label>
</div></div>
</form>
</div>

<div class="step">
<div class="stepn">Step three</div>
<h2>Take the link</h2>
<div class="out" id="out">Fill something in above.</div>
<div class="len" id="len"></div>
<div class="btnrow">
<button class="btn red" type="button" id="copy">Copy link</button>
<a class="btn ghost" id="open" href="/" target="_blank" rel="noopener">Open it</a>
</div>
<div class="ok" id="ok"></div>
<p class="sub" style="margin-top:22px">The client's details sit after the # in
that link, which browsers keep to themselves: it is never sent to the server and
never appears in a log. Send it however you would send anything else.</p>
</div>

</section></main>

<footer><div class="wrap">
<div class="fine">
<p>Adding your name here permanently, so it lives at a tidy address of its own
rather than in a long link, is one line in <b>agents.json</b> and a push.</p>
<p>&copy; {esc(brokerage['credit'])}.</p>
</div>
</div></footer>

<script src="{setup_js_url}" defer></script>
</body></html>"""


# ---------------------------------------------------------------------------
def main():
    n = content.check_ids_unique()
    reg = json.loads((HERE / "agents.json").read_text(encoding="utf-8"))
    brokerage = reg["brokerage"]
    agents = reg["agents"]

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    # assets, root-absolute at /a/. _source is EXCLUDED: it holds the licensed
    # OTF faces and the full-size headshot, and a plain copytree published all
    # of it, which is precisely what subsetting the faces exists to avoid.
    # Deploying a licensed font in its original form is a licence problem, not
    # just wasted bytes, so the exclusion is asserted below rather than trusted.
    shutil.copytree(ASSETS, DIST / "a",
                    ignore=shutil.ignore_patterns("_source"))
    leaked = [p for p in (DIST / "a").rglob("*")
              if p.is_file() and p.suffix.lower() in (".otf", ".ttf", ".woff")]
    if leaked or (DIST / "a" / "_source").exists():
        raise SystemExit(
            "source art reached the deploy tree: "
            + ", ".join(str(p.relative_to(DIST)) for p in leaked)
            + ". Only subset woff2 may ship.")

    # CSS and JS ship as FILES, not inline. Three pages inlining the same 26KB
    # meant every page paid for it again; as files the browser fetches them once
    # and the pages drop to about a quarter of the size. It also lets the policy
    # in vercel.json refuse inline script outright.
    def asset(name, text):
        if name.endswith(".js"):
            copy_gate_js(text, name)
        h = hashlib.sha256(text.encode()).hexdigest()[:10]
        stem, ext = name.rsplit(".", 1)
        out = f"{stem}.{h}.{ext}"
        (DIST / "a" / out).write_text(text, encoding="utf-8")
        return f"/a/{out}"

    css_url = asset("app.css", CSS)
    js_url = asset(
        "app.js",
        "var REGISTRY=" + json.dumps({a["slug"]: a for a in agents})
        + ";\nvar BROKERAGE=" + json.dumps(brokerage["name"]) + ";\n" + JS)
    setup_js_url = asset(
        "setup.js",
        SETUP_JS.replace("__REG__", json.dumps({a["slug"]: a for a in agents})))

    built = []

    def emit(path, text, label):
        copy_gate(text, label)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        built.append((label, len(text.encode())))

    for a in agents:
        if a.get("headshot"):
            src = ASSETS / "headshots" / a["headshot"]
            if not src.exists():
                raise SystemExit(
                    f"agents.json points {a['slug']} at a headshot that is not "
                    f"there: {src}. A missing image on a client-facing close is "
                    f"a broken page, so the build stops rather than shipping it.")
    # ONE page serves every realtor. /keith-godding is a rewrite onto it and the
    # close is filled from the registry at load, exactly as a realtor supplied in
    # the link already was. Generating a page per agent duplicated 47KB of
    # identical checklist for one changed name, which made adding a colleague
    # expensive for no reason.
    emit(DIST / "index.html", page(None, brokerage, n, css_url, js_url), "/")
    emit(DIST / "setup" / "index.html",
         setup_page(agents, brokerage, css_url, setup_js_url), "/setup")

    (DIST / "404.html").write_text(
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Not found</title><link rel="icon" href="/a/favicon.png">'
        '<style>html{background:#0c0c0c;color:#a39c92;font:15px/1.6 system-ui,sans-serif;height:100%}'
        'body{display:grid;place-items:center;height:100%;margin:0;text-align:center;padding:20px}'
        'a{color:#ED2127}</style></head><body><div><p>Nothing at this address.</p>'
        '<p><a href="/">The seller&rsquo;s prep list</a></p></div></body></html>',
        encoding="utf-8")

    (DIST / "robots.txt").write_text(
        "User-agent: *\nAllow: /\nDisallow: /setup\n", encoding="utf-8")

    # ONE vercel.json is the source of truth, at the project root, because that
    # is where Vercel reads it for a git-connected build. A deploy that uploads
    # dist/ directly makes dist/ the root instead, so the same config is copied
    # in with the build-only keys stripped. Both modes therefore get the same
    # headers and neither has its own copy to drift.
    cfg = json.loads((HERE / "vercel.json").read_text(encoding="utf-8"))
    # Destination is "/" and NOT "/index.html": cleanUrls renames index.html to
    # "/", so a rewrite aimed at the .html path lands on something that no
    # longer resolves and every realtor route 404s. Caught on the DEPLOYED site
    # (seller-prep.vercel.app), because a local static server has no cleanUrls
    # to disagree with and resolved /index.html happily.
    cfg["rewrites"] = [{"source": "/" + a["slug"], "destination": "/"}
                       for a in agents]
    for k in ("buildCommand", "outputDirectory", "installCommand", "framework",
              "$schema"):
        cfg.pop(k, None)
    (DIST / "vercel.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")


    root_cfg = json.loads((HERE / "vercel.json").read_text(encoding="utf-8"))
    if root_cfg.get("rewrites") != cfg["rewrites"]:
        root_cfg["rewrites"] = cfg["rewrites"]
        (HERE / "vercel.json").write_text(json.dumps(root_cfg, indent=2) + "\n",
                                          encoding="utf-8")
        print("  vercel.json rewrites refreshed from agents.json")

    total = sum(p.stat().st_size for p in DIST.rglob("*") if p.is_file())
    print(f"  {n} checklist items, ids unique")
    for label, size in built:
        print(f"  {label:<18} {size:>7,} bytes")
    print(f"  {len(agents)} realtor page(s) + the brokerage page + /setup")
    print(f"  dist total {total:,} bytes")
    print("  copy gate passed on every rendered page and on the runtime copy")


if __name__ == "__main__":
    sys.exit(main())
