"""Render the built pages and MEASURE them, then screenshot for the eye.

A page that loads is not a page that reads. This checks the things that have
actually shipped broken before:

  - every asset the page asks for returns 200 (a relative path that works at /
    and 404s at /keith-godding is invisible until you open the deployed page)
  - no console errors
  - the answer sits near the top on a phone
  - line length stays inside the readable band
  - hit targets clear 44px
  - the personalised link really does turn the offsets into dates
  - the print stylesheet opens the folds rather than hiding the content
"""
import http.server
import json
import pathlib
import re
import socketserver
import sys
import threading

from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
DIST = HERE / "dist"
SHOTS = HERE / "shots"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
CFG = json.loads((DIST / "vercel.json").read_text())
PORT = 8731
# The print stylesheet is tuned to keep the handout short; eleven pages is where
# a checklist stops being read. Twelve is the line, so a normal edit never trips
# it and a layout regression does.
PAGE_CAP = 12

# A personalised link, built the way /setup builds one: a condo seller who is
# also buying, closing 2026-11-27.
import base64

def frag(obj, key):
    raw = json.dumps(obj, separators=(",", ":")).encode()
    return key + "=" + base64.urlsafe_b64encode(raw).decode().rstrip("=")

SELLER = frag({"client": "The Patel family",
               "address": "118 Waverley Road, Toronto",
               "closing": "2026-11-27", "condo": 1, "buying": 1, "rented": 1}, "s")
ADHOC = frag({"name": "Dana Whitfield", "title": "Sales Representative",
              "phone": "416-555-0148", "email": "dana@theagencyre.com",
              "site": "theagencyre.com", "tagline": "Leaside and Davisville"}, "a")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(DIST), **kw)

    def do_GET(self):
        # Mirror what Vercel will actually serve, read from the SAME config it
        # reads: the rewrites that put every registry realtor on one page, then
        # cleanUrls. A test server that resolves paths its own way is testing a
        # site nobody will visit.
        p = self.path.split("#")[0].split("?")[0]
        for r in CFG.get("rewrites", []):
            if p == r["source"]:
                self.path = r["destination"]
                return super().do_GET()
        if not p.endswith("/") and "." not in p.rsplit("/", 1)[-1]:
            cand = DIST / p.lstrip("/") / "index.html"
            if cand.exists():
                self.path = p + "/index.html"
        return super().do_GET()

    def log_message(self, *a):
        pass


def serve():
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def ink_in_margins(browser, printed, pages):
    """Render each printed page and look for ink where the margin should be.

    Every other print check reads the DOM, which is the layout BEFORE Chromium
    paginates it. Only the paper shows what pagination did. So: one PDF per
    page, opened back in the browser's own PDF viewer, screenshotted, and
    checked for any mark inside the 12mm side and 14mm top and bottom margins.
    A page that fits has white edges. A page that does not shows ink there,
    and that ink is content the printer will clip.
    """
    try:
        from PIL import Image
    except ImportError:
        return ["Pillow is not installed, so the printed pages were not "
                "checked for content running off the sheet"]

    out = SHOTS / "print"
    out.mkdir(exist_ok=True)
    for old in out.glob("*.png"):
        old.unlink()
    viewer = browser.new_page(viewport={"width": 850, "height": 1120})
    bad = []
    for n in range(1, pages + 1):
        one = out / f"page{n:02d}.pdf"
        printed.pdf(path=str(one), format="Letter", print_background=True,
                    page_ranges=str(n))
        viewer.goto(f"file://{one}", wait_until="load")
        viewer.wait_for_timeout(1400)
        shot = out / f"page{n:02d}.png"
        viewer.screenshot(path=str(shot))
        one.unlink()
        hit = _margin_ink(Image.open(shot))
        if hit:
            bad.append(f"page {n} has ink in the margin at {hit}, so the "
                       f"printer will clip it")
    viewer.close()
    return bad


def _margin_ink(im, side_mm=12, ends_mm=14, tol_mm=1.5):
    """Find the sheet inside the viewer screenshot, then read its margins."""
    im = im.convert("RGB")
    w, h = im.size
    px = im.load()
    cols = [x for x in range(w)
            if sum(1 for y in range(0, h, 6) if all(c > 235 for c in px[x, y]))
            > (h / 6) * 0.5]
    rows = [y for y in range(h)
            if sum(1 for x in range(0, w, 6) if all(c > 235 for c in px[x, y]))
            > (w / 6) * 0.5]
    if not cols or not rows:
        return None
    sheet = im.crop((min(cols), min(rows), max(cols) + 1, max(rows) + 1))
    W, H = sheet.size
    bx = int((side_mm - tol_mm) * W / 215.9)
    by = int((ends_mm - tol_mm) * H / 279.4)
    p = sheet.load()
    for y in range(0, H, 2):
        for x in list(range(0, bx, 2)) + list(range(W - bx, W, 2)):
            if not all(c > 240 for c in p[x, y]):
                return f"x={x} y={y} of a {W}x{H} sheet"
    for x in range(0, W, 2):
        for y in list(range(0, by, 2)) + list(range(H - by, H, 2)):
            if not all(c > 240 for c in p[x, y]):
                return f"x={x} y={y} of a {W}x{H} sheet"
    return None


def _syllables(w):
    w = w.lower().strip(".,;:!?'\"()")
    if not w:
        return 0
    w = re.sub(r"e$", "", w)
    return max(1, len(re.findall(r"[aeiouy]+", w)))


def reading_grade(blocks):
    """Flesch-Kincaid over the PROSE a seller reads, block by block.

    Keith's bar is that a twelve year old can understand it, which is about
    grade seven, and that is a measurement rather than a feeling. Measured per
    block on purpose: running the whole page through as one string welds
    headings and bullet lists into sentences nobody wrote and reports a grade
    nobody experiences. The source fold is excluded because it cites external
    documents by their real titles, which are not ours to simplify.
    """
    words = sents = syl = 0
    for t in blocks:
        ws = re.findall(r"[A-Za-z']+", t)
        ss = [x for x in re.split(r"(?<=[.!?])\s+", t.strip()) if len(x.split()) >= 3]
        if not ws or not ss:
            continue
        words += len(ws)
        sents += len(ss)
        syl += sum(_syllables(w) for w in ws)
    if not words or not sents:
        return None
    return 0.39 * (words / sents) + 11.8 * (syl / words) - 15.59


def main():
    SHOTS.mkdir(exist_ok=True)
    srv = serve()
    base = f"http://127.0.0.1:{PORT}"
    fails, notes = [], []

    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME)

        def visit(page, url):
            errs, bad = [], []
            page.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errs.append(str(e)))
            page.on("response", lambda r: bad.append(f"{r.status} {r.url}")
                    if r.status >= 400 else None)
            page.goto(url, wait_until="networkidle")
            return errs, bad

        # ---- phone, plain -------------------------------------------------
        ctx = br.new_context(viewport={"width": 390, "height": 844},
                             device_scale_factor=2)
        pg = ctx.new_page()
        errs, bad = visit(pg, f"{base}/")
        if errs: fails.append(f"/ console errors: {errs}")
        if bad:  fails.append(f"/ failed requests: {bad}")

        # The answer on screen one. Measured, not assumed.
        h1_bottom = pg.evaluate("document.querySelector('h1').getBoundingClientRect().bottom")
        first_card = pg.evaluate("document.querySelector('.card').getBoundingClientRect().top")
        notes.append(f"phone: headline ends {h1_bottom:.0f}px, first card at {first_card:.0f}px")
        if h1_bottom > 844:
            fails.append(f"headline does not fit screen one on a phone ({h1_bottom:.0f}px)")

        # Hit targets.
        small = pg.evaluate("""() => {
          const out=[];
          document.querySelectorAll('button,input[type=checkbox],a.btn,.chk').forEach(el=>{
            const r=el.getBoundingClientRect();
            if(r.width===0&&r.height===0) return;
            const t=el.closest('label,.itop')||el;
            const tr=t.getBoundingClientRect();
            if(Math.max(r.height,tr.height)<44)
              out.push((el.id||el.className||el.tagName)+' '+Math.round(r.height));
          });
          return out;
        }""")
        if small:
            fails.append(f"hit targets under 44px: {small}")

        # Line length. Over about 78 characters a phone reader loses the line.
        cpl = pg.evaluate("""() => {
          const probe=document.createElement('span');
          probe.style.cssText='position:absolute;visibility:hidden;white-space:pre';
          document.body.appendChild(probe);
          let worst=0,which='';
          document.querySelectorAll('.det p,.plede,.card p,.sub,.lede').forEach(el=>{
            const cs=getComputedStyle(el);
            probe.style.font=cs.font;
            probe.textContent='0';
            const ch=probe.getBoundingClientRect().width||8;
            const n=el.getBoundingClientRect().width/ch;
            if(n>worst){worst=n;which=el.className||el.tagName;}
          });
          probe.remove();
          return [Math.round(worst),which];
        }""")
        notes.append(f"phone: longest line about {cpl[0]} characters ({cpl[1]})")
        if cpl[0] > 80:
            fails.append(f"line length {cpl[0]} characters, too long to track")

        # An element the page hides by attribute must actually be gone. An
        # author `display:` rule silently beats the UA sheet's
        # [hidden]{display:none}, which left an empty 21px rule under the hero
        # and a 78px void in the close, both invisible to every other check.
        leaked = pg.evaluate("""() => [...document.querySelectorAll('[hidden]')]
          .map(el => ({what: el.id ? '#'+el.id : '.'+el.className.split(' ')[0],
                       display: getComputedStyle(el).display,
                       h: Math.round(el.getBoundingClientRect().height)}))
          .filter(x => x.display !== 'none')""")
        if leaked:
            fails.append(f"[hidden] elements still rendering: {leaked}")
        notes.append("every [hidden] element really is display:none")

        # The seam between the hero and the first section. `.wrap` sets
        # `padding:0 var(--pad)`, and a class beats an element selector, so
        # every `<section class="wrap">` silently lost the vertical padding
        # that `section` gives it and the first eyebrow landed ON the colour
        # change, red text touching black. Nothing else here would notice:
        # every element is present, visible, correctly sized and the right
        # colour. Only the distance between two of them is wrong.
        seam = pg.evaluate("""() => {
          const hero = document.querySelector('.hero');
          // The first VISIBLE one: the due-now band sits above it in the DOM
          // and is hidden until there is a closing date, so a plain
          // querySelector picks a zero-height element and measures nonsense.
          const first = [...document.querySelectorAll('main .eyebrow')]
            .find(e => e.getBoundingClientRect().height > 0);
          if(!hero || !first) return null;
          return Math.round(first.getBoundingClientRect().top
                            - hero.getBoundingClientRect().bottom);
        }""")
        if seam is None:
            fails.append("could not find the hero or the first section heading")
        elif seam < 24:
            fails.append(f"the first line after the hero sits {seam}px below the "
                         f"colour change, so it reads as touching it")
        else:
            notes.append(f"hero seam: first line sits {seam}px clear of it")

        # Every sheet's action has to be ON SCREEN when the sheet opens. The
        # sheet body scrolls and the footer is pinned, which is the whole point
        # of the layout, and one `overflow:visible` quietly undid it: the sheet
        # painted past its own box and the only button slid off the bottom of
        # the phone. Nothing else would have noticed. The button existed, was
        # the right size, the right colour and perfectly reachable by keyboard.
        for dlg_id, opener in (("pdlg", "[data-open-setup]"), ("kdlg", "#keep")):
            pg.click(opener)
            pg.wait_for_timeout(600)
            r = pg.evaluate("""(id) => {
              const d = document.getElementById(id);
              if(!d || !d.open) return {err: 'did not open'};
              const btn = d.querySelector('.sheet-foot button');
              if(!btn) return {err: 'no action in the footer'};
              const b = btn.getBoundingClientRect(), h = window.innerHeight;
              return {bottom: Math.round(b.bottom), top: Math.round(b.top),
                      vh: h, label: btn.textContent.trim()};
            }""", dlg_id)
            if r.get("err"):
                fails.append(f"#{dlg_id}: {r['err']}")
            elif r["bottom"] > r["vh"] + 1 or r["top"] < 0:
                fails.append(f"#{dlg_id}: its action '{r['label']}' sits at "
                             f"{r['top']}..{r['bottom']}px on a {r['vh']}px screen, "
                             f"so it is off screen when the sheet opens")
            else:
                notes.append(f"#{dlg_id}: '{r['label']}' on screen at "
                             f"{r['bottom']}px of {r['vh']}px")
            # Nothing inside a sheet may be wider than the sheet. On iOS
            # an input[type=date] keeps an intrinsic width from its own
            # date format and will not shrink, so the field ran off the
            # right edge and the whole drawer could be dragged sideways.
            over = pg.evaluate("""(id) => {
              const d = document.getElementById(id);
              const w = d.getBoundingClientRect().width, out = [];
              d.querySelectorAll('*').forEach(el => {
                const cs = getComputedStyle(el);
                if(cs.display === 'none') return;
                const r = el.getBoundingClientRect();
                if(r.width > w + 1) out.push((el.id ? '#'+el.id : el.tagName)
                  + ' ' + Math.round(r.width) + 'px');
              });
              return {w: Math.round(w), out: out.slice(0, 4),
                      scroll: d.scrollWidth > Math.ceil(w) + 1};
            }""", dlg_id)
            # The width check above cannot REPRODUCE the iOS case: the engine
            # with the bug is WebKit and this is Chromium, whose date input
            # shrinks perfectly well. A mutant that removed the fix passed it.
            # So pin the fix itself. Weaker than measuring an outcome, and
            # honest about which of the two this is.
            if dlg_id == "pdlg":
                dt = pg.evaluate("""() => {
                  const i = document.getElementById('f-closing');
                  const cs = getComputedStyle(i);
                  return {app: cs.webkitAppearance || cs.appearance,
                          minW: cs.minWidth};
                }""")
                if dt["app"] != "none" or dt["minW"] not in ("0px", "0"):
                    fails.append(f"the closing-date field is back to appearance "
                                 f"{dt['app']!r} / min-width {dt['minW']!r}, which "
                                 f"is what let it run off the right of the sheet "
                                 f"on iOS and drag the drawer sideways")
            if over["out"] or over["scroll"]:
                fails.append(f"#{dlg_id} is {over['w']}px wide but holds "
                             f"{over['out'] or 'content'} and can be "
                             f"dragged sideways")
            pg.evaluate("(id) => document.getElementById(id).close()", dlg_id)
            pg.wait_for_timeout(250)

        # The count in the sheet and the count in the header answer the same
        # question and must not disagree. They did, in half the combinations:
        # the sheet had grown its own copy of the flag rules under its own
        # names, and separately the page threw away an explicit "nothing here
        # is rented" because it stripped zeros out of the link.
        mismatches = []
        for condo in (0, 1):
            for buying in (0, 1):
                for rented in (0, 1):
                    pg.click("[data-open-setup]")
                    pg.wait_for_timeout(220)
                    for sel, want in (("#f-condo", condo), ("#f-buying", buying),
                                      ("#f-rented", rented)):
                        if pg.is_checked(sel) != bool(want):
                            pg.click(sel)
                    pg.fill("#f-closing", "2026-11-27")
                    pg.wait_for_timeout(120)
                    in_sheet = int(re.sub(r"\D", "", pg.inner_text("#f-count")))
                    pg.click("#f-save")
                    pg.wait_for_timeout(320)
                    on_page = int(re.search(r"of (\d+)", pg.inner_text("#count")).group(1))
                    if in_sheet != on_page:
                        mismatches.append(f"condo={condo} buying={buying} "
                                          f"rented={rented}: sheet {in_sheet}, "
                                          f"page {on_page}")
        if mismatches:
            fails.append("the sheet and the header disagree on how many things "
                         "are on the list: " + "; ".join(mismatches))
        else:
            notes.append("sheet count matches the page in all 8 combinations")
        pg.goto(f"{base}/", wait_until="networkidle")
        pg.wait_for_timeout(300)

        blocks = pg.eval_on_selector_all(
            ".det p, .card p, .lede, .plede, .sub, .handoff .screenonly, .ttl",
            "els => els.map(e => e.innerText.trim())"
        )
        grade = reading_grade([b for b in blocks if len(b.split()) > 5])
        if grade is None:
            fails.append("could not read any prose to grade")
        elif grade > 8.0:
            fails.append(f"the writing reads at grade {grade:.1f}; the bar is a "
                         f"twelve year old, about grade 7, and 8 is the line")
        else:
            notes.append(f"reading level: grade {grade:.1f}")

        # The average is too blunt on its own: one impenetrable paragraph in
        # eighty moves it by a tenth of a grade, so an aggregate gate cannot
        # catch the thing it exists for. Check each block's own density too.
        # The line is derived from what the writing actually measures, not from
        # feel: across the 70 blocks of eight words or more the worst sits at
        # 1.80 syllables per word and the median at 1.39, while a paragraph
        # rewritten in officialese reads 2.63. So 2.0 is silent today and
        # catches that with room to spare.
        dense = []
        for t in blocks:
            ws = re.findall(r"[A-Za-z']+", t)
            if len(ws) < 8:
                continue
            per = sum(_syllables(w) for w in ws) / len(ws)
            if per > 2.0:
                dense.append(f"{per:.2f}/word: {t[:60]}")
        if dense:
            fails.append("writing a seller could not follow: " + "; ".join(dense[:3]))

        pg.screenshot(path=str(SHOTS / "phone-top.png"))
        pg.evaluate("window.scrollTo(0, document.querySelector('.phase').offsetTop - 60)")
        pg.wait_for_timeout(400)
        pg.screenshot(path=str(SHOTS / "phone-list.png"))

        # ---- phone, personalised -----------------------------------------
        pg2 = ctx.new_page()
        errs, bad = visit(pg2, f"{base}/keith-godding#{SELLER}")
        if errs: fails.append(f"personalised console errors: {errs}")
        if bad:  fails.append(f"personalised failed requests: {bad}")
        pg2.wait_for_timeout(300)

        # Did the offsets become real dates?
        chips = pg2.evaluate(
            "[...document.querySelectorAll('.phase:not([hidden]) .date')].map(e=>e.textContent.trim())")
        soft = [c for c in chips if "before closing" in c or "after closing" in c]
        if soft:
            fails.append(f"closing date given but these stayed generic: {soft}")
        notes.append(f"personalised dates: {chips[0]!r} ... {chips[-1]!r}")

        # Did the flags do anything?
        shown = pg2.evaluate("document.querySelectorAll('li.item:not([hidden])').length")
        total = pg2.evaluate("document.querySelectorAll('li.item').length")
        total_all = lambda: total
        notes.append(f"condo + buying seller sees {shown} of {total} items")
        if shown == total:
            fails.append("flags filtered nothing; a house-only item is showing to a condo seller")

        # The reverse direction. Filtering that only works one way would pass
        # the check above while showing a house seller the elevator booking.
        plain = frag({"closing": "2026-11-27"}, "s")
        pgF = ctx.new_page()
        visit(pgF, f"{base}/#{plain}")
        pgF.wait_for_timeout(300)
        f_shown = pgF.evaluate("document.querySelectorAll('li.item:not([hidden])').length")
        # Scope this to the CHECKLIST, not the whole body. The three headline
        # cards name condos on purpose and are shown to everyone, so a body-wide
        # text scan reports a bug that is not there.
        f_flags = pgF.evaluate(
            "[...document.querySelectorAll('li.item:not([hidden])')]"
            ".map(l=>l.dataset.flags).filter(Boolean)")
        leaked = [f for f in f_flags if f in ("condo", "buying")]
        if leaked:
            fails.append(f"house seller, not buying, still sees items flagged: {leaked}")
        if "freehold" not in f_flags:
            fails.append("the house-only item is hidden from a house seller")
        notes.append(f"house seller, not buying, sees {f_shown} of {total_all()} items")
        pgF.close()

        stamp = pg2.evaluate("document.getElementById('stamp').textContent")
        if "Waverley" not in stamp:
            fails.append("address did not reach the header")
        if "days to go" not in stamp and "Closed" not in stamp and "closing day" not in stamp:
            fails.append("countdown missing")

        # Ticking survives a reload.
        pg2.evaluate("document.querySelector('li.item:not([hidden]) input').click()")
        pg2.wait_for_timeout(200)
        before = pg2.evaluate("document.getElementById('count').textContent")
        pg2.reload(wait_until="networkidle")
        pg2.wait_for_timeout(300)
        after = pg2.evaluate("document.getElementById('count').textContent")
        if before != after:
            fails.append(f"progress lost on reload: {before!r} then {after!r}")
        notes.append(f"progress survives reload: {after.strip()!r}")

        # And survives the closing date MOVING, which is the case that actually
        # happens: this list's own advice is that closings slip by a day fairly
        # often. Ticks were keyed on a hash that included the closing date, so
        # correcting it by one day silently threw away every tick the seller had
        # made, with no way back. The reload check above could never see it,
        # because on a reload the date has not changed.
        moved = frag({"client": "The Patel family",
                      "address": "118 Waverley Road, Toronto",
                      "closing": "2026-11-28", "condo": 1, "buying": 1, "rented": 1}, "s")
        pg2.goto(f"{base}/keith-godding#{moved}", wait_until="networkidle")
        pg2.wait_for_timeout(400)
        shifted = pg2.evaluate("document.getElementById('count').textContent")
        done_before = int(re.search(r"\d+", after).group())
        done_after = int(re.search(r"\d+", shifted).group())
        if done_after < done_before:
            fails.append(f"moving the closing date by one day threw away the "
                         f"seller's ticks: {after.strip()!r} became {shifted.strip()!r}")
        else:
            notes.append(f"ticks survive the closing date moving: {shifted.strip()!r}")

        pg2.screenshot(path=str(SHOTS / "phone-personal.png"))
        ctx.close()

        # ---- desktop ------------------------------------------------------
        ctx2 = br.new_context(viewport={"width": 1280, "height": 900},
                              device_scale_factor=2)
        pg3 = ctx2.new_page()
        errs, bad = visit(pg3, f"{base}/keith-godding#{SELLER}")
        if errs: fails.append(f"desktop console errors: {errs}")
        if bad:  fails.append(f"desktop failed requests: {bad}")
        pg3.wait_for_timeout(300)
        reg_close = pg3.evaluate("document.getElementById('agentblock').textContent")
        if "Keith Godding" not in reg_close:
            fails.append("the registry realtor did not reach the close on /keith-godding")
        if "THE AGENCY" not in reg_close:
            fails.append("the brokerage line is missing from the registry close")
        head = pg3.evaluate("""() => {
          const i=document.getElementById('ag-photo');
          if(!i || i.hidden) return null;
          return {src:i.getAttribute('src'), w:i.naturalWidth, alt:i.alt,
                  drawn: Math.round(i.getBoundingClientRect().width)};
        }""")
        if not head:
            fails.append("the registry realtor's headshot is not showing")
        elif not head["w"]:
            fails.append(f"the headshot did not decode: {head['src']}")
        elif not head["alt"]:
            fails.append("the headshot has no alt text")
        elif head["w"] < head["drawn"] * 3:
            # A photograph the device has to upscale is the soft one, and soft
            # on a face is the first thing a client notices. Three times the
            # drawn size is what a modern phone asks for, so it is the floor,
            # checked rather than remembered: this fails if the asset shrinks
            # OR if the close ever draws it bigger.
            fails.append(f"headshot is {head['w']}px for a {head['drawn']}px "
                         f"circle: a 3x screen needs {head['drawn'] * 3}px")
        else:
            notes.append(f"headshot loads ({head['w']}px for a {head['drawn']}px "
                         f"circle, clears 3x, alt {head['alt']!r})")
        # The home-screen icon. A browser does not request it, so nothing else
        # here would notice it missing, and the cost of it missing is a seller
        # who saves the list and gets a blurry screenshot as its icon.
        icons = pg3.evaluate("""() => [...document.querySelectorAll(
          'link[rel=\"apple-touch-icon\"]')].map(l => l.getAttribute('href'))""")
        # Two of these is not belt and braces, it is a coin toss: with no sizes
        # attribute to choose by, the browser takes the last one declared, and
        # the head already carried a link to the full red lockup whose wordmark
        # is illegible at 60pt. One link, or the wrong icon ships.
        if len(icons) > 1:
            fails.append(f"{len(icons)} apple-touch-icon links, so the icon "
                         f"is whichever comes last: {icons}")
        icon = icons[0] if icons else None
        if not icon:
            fails.append("no apple-touch-icon, so a home-screen save gets a "
                         "screenshot for an icon")
        else:
            r = pg3.request.get(base + icon)
            if r.status != 200:
                fails.append(f"the home-screen icon 404s at {icon}")
            else:
                dim = pg3.evaluate("""(src) => new Promise(res => {
                  const i = new Image();
                  i.onload = () => res(i.naturalWidth);
                  i.onerror = () => res(0);
                  i.src = src;
                })""", icon)
                if dim < 180:
                    fails.append(f"the home-screen icon is {dim}px; iOS asks "
                                 f"for 180")
                else:
                    notes.append(f"home-screen icon {dim}px, served at {icon}")
        notes.append("registry realtor resolves from the path")
        pg3.screenshot(path=str(SHOTS / "desk-top.png"))
        pg3.evaluate("window.scrollTo(0, document.querySelector('.phase').offsetTop - 80)")
        pg3.wait_for_timeout(400)
        pg3.screenshot(path=str(SHOTS / "desk-list.png"))
        pg3.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        pg3.wait_for_timeout(500)
        pg3.screenshot(path=str(SHOTS / "desk-footer.png"))

        # Fonts really loaded. A fallback serif here would be an unbranded page
        # that still looks fine, which is the worst kind of failure.
        faces = pg3.evaluate("""async () => {
          await document.fonts.ready;
          return [...document.fonts].map(f=>f.family+':'+f.status);
        }""")
        missing = [f for f in faces if not f.endswith("loaded")]
        if missing:
            fails.append(f"brand faces did not load: {missing}")
        notes.append(f"faces: {len(faces)} declared, all loaded")

        # ---- an unregistered realtor, straight from a link ----------------
        pg4 = ctx2.new_page()
        errs, bad = visit(pg4, f"{base}/#{ADHOC}&{SELLER}")
        if errs: fails.append(f"ad-hoc realtor console errors: {errs}")
        pg4.wait_for_timeout(300)
        close = pg4.evaluate("document.getElementById('agentblock').textContent")
        if "Dana Whitfield" not in close:
            fails.append("realtor supplied in the link did not reach the close")
        if "Leaside" not in close:
            fails.append("realtor tagline did not reach the close")
        notes.append("realtor from a link renders on the close")
        pg4.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        pg4.wait_for_timeout(400)
        pg4.screenshot(path=str(SHOTS / "desk-adhoc-footer.png"))

        # ---- print, measured on the paper itself ---------------------------
        # A seller prints this and ticks it with a pen, so "it prints" is not
        # the bar: nothing may be cut off, no tick box may be missing, and no
        # block may be too tall to fit a sheet. The first two are measured in
        # the DOM at the exact printable size; the last is measured on the
        # RENDERED PAGES, by looking for ink where the margin should be.
        MM = 96 / 25.4
        PRINT_W = round((215.9 - 24) * MM)     # Letter less the 12mm side margins
        PRINT_H = round((279.4 - 28) * MM)     # less the 14mm top and bottom
        ctx5 = br.new_context(viewport={"width": PRINT_W, "height": PRINT_H},
                              device_scale_factor=1)
        pg5 = ctx5.new_page()
        visit(pg5, f"{base}/keith-godding#{SELLER}")
        pg5.wait_for_timeout(300)
        pg5.emulate_media(media="print")
        pg5.wait_for_timeout(200)

        hidden_details = pg5.evaluate("""() => {
          let n=0;
          document.querySelectorAll('.det').forEach(d=>{
            if(getComputedStyle(d).display==='none') n++;
          });
          return n;
        }""")
        if hidden_details:
            fails.append(f"print hides {hidden_details} detail blocks; paper cannot be clicked")

        wide = pg5.evaluate("""(W) => {
          const out=[];
          document.querySelectorAll('body *').forEach(el=>{
            const cs=getComputedStyle(el);
            if(cs.display==='none'||cs.visibility==='hidden') return;
            const r=el.getBoundingClientRect();
            if(r.width===0&&r.height===0) return;
            if(r.right>W+1||r.left<-1)
              out.push((el.tagName+'.'+(el.className||'')).slice(0,40)
                       +' ['+Math.round(r.left)+'..'+Math.round(r.right)+']');
          });
          return out.slice(0,6);
        }""", PRINT_W)
        if wide:
            fails.append(f"content runs past the {PRINT_W}px printable width: {wide}")

        # break-inside:avoid cannot save a block that is taller than the sheet.
        # That one WILL be split, and a split is where a reader loses the thread.
        tootall = pg5.evaluate("""(H) => {
          const out=[];
          document.querySelectorAll('li.item,.card,.phead,.agent').forEach(el=>{
            const r=el.getBoundingClientRect();
            if(r.height>H) out.push(Math.round(r.height)+'px: '
              +(el.textContent||'').trim().slice(0,40));
          });
          return out;
        }""", PRINT_H)
        if tootall:
            fails.append(f"blocks taller than one {PRINT_H}px page, so they get cut: {tootall}")

        boxes = pg5.evaluate("""() => {
          const out={shown:0, missing:[]};
          document.querySelectorAll('li.item').forEach(li=>{
            if(getComputedStyle(li).display==='none') return;
            out.shown++;
            const b=li.querySelector('input[type=checkbox]');
            const r=b?b.getBoundingClientRect():{width:0,height:0};
            if(!b||r.width<10||r.height<10)
              out.missing.push((li.dataset.id||'?'));
          });
          return out;
        }""")
        if boxes["missing"]:
            fails.append("items with no tick box on paper: " + ", ".join(boxes["missing"]))

        faint = pg5.evaluate("""() => {
          function bg(el){ let e=el;
            while(e){ const c=getComputedStyle(e).backgroundColor;
              if(c&&c!=='rgba(0, 0, 0, 0)'&&c!=='transparent') return c;
              e=e.parentElement; }
            return 'rgb(255, 255, 255)'; }
          const bad=[];
          document.querySelectorAll('h1,h2,h3,p,li,span,a,div,b').forEach(el=>{
            const t=[...el.childNodes].some(n=>n.nodeType===3&&n.textContent.trim());
            if(!t) return;
            const cs=getComputedStyle(el);
            if(cs.display==='none'||cs.visibility==='hidden') return;
            const f=cs.color.match(/\d+/g).map(Number), k=bg(el).match(/\d+/g).map(Number);
            if(Math.abs(f[0]-k[0])+Math.abs(f[1]-k[1])+Math.abs(f[2]-k[2]) < 90)
              bad.push(el.textContent.trim().slice(0,30));
          });
          return bad.slice(0,5);
        }""")
        if faint:
            fails.append(f"text that will not read on paper: {faint}")

        pdf = SHOTS / "print.pdf"
        pg5.pdf(path=str(pdf), format="Letter", print_background=True)
        raw = pdf.read_bytes()
        pages = raw.count(b"/Type /Page\n") or raw.count(b"/Type/Page")
        if not pages:
            fails.append("the print PDF reports no pages")
        # A cap, for two reasons. A handout that runs to eleven pages gets
        # skimmed and the whole print stylesheet is tuned to keep it under
        # that, so a jump past it is a regression worth failing on its own.
        # And the per-page render below costs about a second and a half a
        # page, so a layout bug that explodes the page count would otherwise
        # turn the gate into a coffee break instead of a red line.
        elif pages > PAGE_CAP:
            fails.append(f"the list prints to {pages} pages, past the "
                         f"{PAGE_CAP} it is laid out to fit; not rendering "
                         f"them all")
        else:
            fails.extend(ink_in_margins(br, pg5, pages))
        notes.append(f"print: {pages} pages, {boxes['shown']} tick boxes, "
                     f"nothing past {PRINT_W}px, no ink in the margins")
        pg5.emulate_media(media="screen")
        ctx5.close()
        notes.append("print opens every fold")

        # ---- setup page ---------------------------------------------------
        pg6 = ctx2.new_page()
        errs, bad = visit(pg6, f"{base}/setup")
        if errs: fails.append(f"/setup console errors: {errs}")
        if bad:  fails.append(f"/setup failed requests: {bad}")
        pg6.fill("#g-name", "Dana Whitfield")
        pg6.fill("#g-phone", "416-555-0148")
        pg6.fill("#g-address", "118 Waverley Road, Toronto")
        pg6.fill("#g-closing", "2026-11-27")
        pg6.wait_for_timeout(250)
        made = pg6.inner_text("#out")
        if "#a=" not in made or "s=" not in made:
            fails.append(f"/setup did not build a link with both parts: {made}")
        if "?" in made:
            fails.append("/setup put details in the query string; they must stay in the fragment")
        notes.append("setup builds a link carrying realtor and client, fragment only")
        pg6.screenshot(path=str(SHOTS / "desk-setup.png"), full_page=False)

        br.close()
    srv.shutdown()

    print("\n".join("  " + n for n in notes))
    if fails:
        print("\nFAILED:")
        print("\n".join("  " + f for f in fails))
        return 1
    print("\n  all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
