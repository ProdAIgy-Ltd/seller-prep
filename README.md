# Seller's prep list

A static, Agency-branded checklist for a homeowner between the day their sale
goes firm and the week after closing. Ontario specific. Deployed to Vercel.

**It is realtor agnostic on purpose.** Nothing in the checklist assumes who
handed it over, so any Agency agent can send it under their own name without a
word of it being edited or a line of it being wrong for them.

```
python make_assets.py     # once: subsets the licensed faces, sizes the marks
python build.py           # -> dist/
python audit.py           # renders it, measures it, screenshots it -> shots/
```

`audit.py` is the gate. It has to pass before anything is pushed.

## Deploying

This repo IS the Vercel project. Root Directory stays at the default (`.`),
build is `python3 build.py`, output is `dist`, and nothing needs installing:
the build is standard library only. All of that is already in `vercel.json`,
so an import needs no settings typed in.

Every push to `main` deploys. Adding a realtor is one line in `agents.json`
plus a push.

**This repo is PUBLIC**, which is deliberate and is what lets it deploy on a
Vercel Hobby plan (Hobby refuses a private repo owned by an organization).
Two consequences:

- The licensed OTF originals are NOT here. Only the subset `.woff2` the live
  site already serves to every visitor. The originals stay private in
  `ProdAIgy-Ltd/prodaigy-fieldwork` under `seller-prep/assets/_source/`, and
  `make_assets.py` only runs there.
- Nothing secret belongs in this repo. No client data, no keys, no prod
  anything. The page holds no client data by design: seller details ride in
  the URL fragment and never reach a server.
---

## How one page serves many realtors and many clients

There are two variables: **who is sending it** and **who it is for**. They are
handled differently on purpose, because they have different lifetimes.

### Who is sending it

| Route | Who it is for | What it takes |
|---|---|---|
| `/` | Anyone. Brokerage close only, no named agent. | Nothing. Share the link. |
| `/keith-godding` | An agent with a tidy address of their own. | One entry in `agents.json`, then push. |
| `/#a=<encoded>` | Any agent, immediately. | Fill in `/setup`. No commit, no deploy, nobody's permission. |

The registry and the self-serve link are both here deliberately. A registry
alone makes every new agent wait on somebody with repository access, which is
how a shared tool quietly becomes one person's tool. A self-serve link alone
gives an agent a long ugly URL to put on a listing presentation. So: the
registry is for the tidy address, not for permission.

Adding an agent to the registry is one object in `agents.json` plus an optional
headshot at `assets/headshots/<slug>.webp`. The build **stops** if the headshot
named there is missing, because a broken image on a client-facing close is a
broken page and it should never reach a deploy.

#### The photograph, both ways

An agent filling in `/setup` has two ways to get their face on the close, and
neither of them involves anybody with repository access.

**Upload it.** The file is cropped square, biased upward so a portrait does not
lose the top of the head, shrunk to 192px and encoded to WebP **in the
browser**, then carried inside the link as a `data:` URI. There is no server to
upload to. Measured end to end: a 176KB phone photograph becomes about 6KB and
the finished link about 11,000 characters, which sends fine by email or text
and looks unwieldy written out. Zero network requests are made while it
happens, which is checked rather than claimed.

**Paste its address.** Shorter link, same picture, and it depends on that
address staying up. This used to fail in silence: the content policy allows an
image from `self`, `https:` or `data:` and nothing else, so an `http://`
address or a Drive share page (a page, not a picture) simply never appeared and
the agent found out from a client. The field now checks the address in front of
them and says which of those three things went wrong, previews what will
actually render, and warns when the photograph it found is too small for a
phone.

A browser that cannot decode the photograph hides it. That is the runtime twin
of the build-time guard above, and it covers the server-rendered registry photo
too, which `stampAgent` never touches. Verified against a mutant that replaced
the headshot with bytes no browser can read.

### Who it is for

Client details travel in the **URL fragment**, base64 of a small JSON object:

```
https://<host>/keith-godding#s=eyJjbGllbnQiOiJUaGUgUGF0ZWwgZmFtaWx5Iiwi...
```

A fragment is never sent to the server. It is not in a Vercel access log, not
in a proxy log, not in a referrer. A client's address and closing date stay
between the agent, the client and the browser, which is the whole reason this
is not `?address=...`. There is no database, no account and no form post, so
there is also nothing to breach and nothing to keep.

What the fragment carries, and what each thing does:

| Field | Effect on the page |
|---|---|
| `client` | Names the household in the header |
| `address` | Names the home in the header |
| `closing` | Turns every phase from "30 days before closing" into a real date, drives the countdown, and fills the calendar export |
| `condo` | Adds the elevator booking, the building's moving rules, the status certificate |
| `buying` | Adds lining the two closing dates up |
| `rented` | Adds paying out or handing over the water heater and the rest |

A client who gets the plain link is not stuck: the page asks for the same
details itself, in a dialog, and writes them into its own fragment. An agent
who cannot be bothered to personalise anything still sends something useful.

Progress ticks live in `localStorage`, keyed by a hash of the client's details,
so one agent's device does not carry one client's ticks onto the next client's
list. Every read and write is wrapped, because private mode and blocked storage
both throw rather than return empty.

### Scaling past The Agency

The brokerage is one object at the top of `agents.json` plus two mark files in
`assets/`. Nothing else in the build hard-codes it. A second brokerage is a
second `agents.json` and a second Vercel project off the same source, which is
the point at which the brokerage should become a build argument rather than a
constant. It is not one yet because nobody has asked for it, and building the
abstraction before the second case is how it gets built wrong.

---

## What is in here

| File | What it does |
|---|---|
| `content.py` | The checklist. Every word a seller reads, plus the source behind every factual claim. This is the file to edit. |
| `agents.json` | The realtor registry and the brokerage block. |
| `template.py` | CSS and the runtime. No network calls of any kind. |
| `build.py` | Assembles the pages, runs the copy gate, writes `dist/`. |
| `make_assets.py` | Subsets the licensed faces to woff2, sizes the marks, and crops headshots. Reads only `assets/_source/`. Run after changing source art; output is committed. |
| `audit.py` | Renders the built pages in Chromium and measures them. |
| `assets/_source/` | The source art: five licensed OTF faces, three marks, headshots. **Never deployed.** |
| `dist/` | The built site, committed. Drop it on any static host with no build step. |

### Assets

Everything the site needs is in this directory. `make_assets.py` reads only
`assets/_source/` and writes what is actually served:

| Source | Served |
|---|---|
| `_source/fonts/*.otf` (5 licensed faces) | `fonts/*.woff2`, subset to the glyphs the page draws, 45KB total |
| `_source/TA_*.png` | `ta-mark-red.png`, the two wordmarks, `favicon.png` |
| `_source/headshot-<slug>.png` | `headshots/<slug>.webp`, square, cropped upward, 192px, about 6KB |

**`_source/` never ships.** The subset faces exist so a licensed font does not
sit on a public URL in its original form, and a plain `copytree` once undid
that by sweeping the whole folder into the deploy. The build now excludes it
and asserts no `.otf`, `.ttf` or `.woff` reached the tree, verified against a
mutant of the pre-fix line.

To add a realtor's photograph: drop `assets/_source/headshot-<slug>.png`, run
`python make_assets.py`, and set `"headshot": "<slug>.webp"` in `agents.json`.
The build stops if that file is missing.

#### Why 192px WebP at quality 88

The close draws the face at 62px in a circle, so a 3x phone asks for 186 real
pixels. Under that the device is upscaling, and upscaling is what soft looks
like. Root-mean-square error per channel against the untouched source crop:

| | bytes | error |
|---|---|---|
| 128 WebP q72 | 2,184 | 5.19 |
| 176 JPEG q86 (what this shipped before) | 7,205 | 2.94 |
| **192 WebP q88** | **6,078** | **2.28** |
| 192 WebP q94 | 8,890 | 1.76 |

So the WebP is sharper AND smaller than the JPEG it replaced, and q94 buys half
a point for half again the bytes. `/setup`'s browser-side uploader encodes to
the same 192 at 0.88, so a self-serve photograph and a registry photograph are
the same picture, and the length readout no longer claims otherwise.

`audit.py` checks the ratio rather than the number: it fails if the photograph
supplies fewer than three times the pixels the close draws, which catches both
a shrunken asset and a close that grows the circle. Verified against a mutant
that re-encoded the headshot at 128px.

### The copy gate

`build.py` runs over the **rendered** text of every page, not the source, and
fails the build on an em-dash, an en-dash, the word "AI", finance jargon, or a
first person plural. It also runs over the **runtime copy**: the gate strips
`<script>` before it reads a page, so the progress line, the calendar text and
every message `/setup` shows a realtor were going unchecked. Those are read by
a seller exactly like the HTML, so the JS string literals carrying a space (the
sentences, as opposed to `input,select` and `tel:`) go through the same
patterns. Verified against a mutant with a "we" planted in the runtime. The last one is the realtor-agnostic rule made mechanical:
a "we" in the checklist puts words in the mouth of whichever agent shares it.

The voice is therefore second person to the seller throughout. This is a
deliberate departure from the first-person-singular Keith standard that binds
the Signals app and the CMAs, and it has to be, because a page written as "I"
is a page only one person can send. The agent appears once, on the close, from
config.

### Sources

Every factual claim carries a source in `content.py`'s `SOURCES`, and the ones
a seller would want to open are linked from the item itself. The page also
carries them in a fold on the close. Claims verified during the build:

- Ontario gives you six days after moving to update a driver's licence and
  vehicle permit, and one online session covers the licence, plates, health
  card and photo card together.
- Canada Post mail forwarding takes five to ten business days to start.
- A seller stays responsible for the property until completion, and should not
  cancel insurance until the lawyer confirms the deal closed.
- Rented equipment is either assumed by the buyer through the agreement or paid
  out before closing; the rental company usually registers a notice against
  title either way.
- Fixtures stay unless excluded in writing, chattels go unless included in
  writing.
- Every home sale is reported to the Canada Revenue Agency, including one fully
  covered by the principal residence exemption; not reporting runs to one
  hundred dollars a month up to eight thousand.

### Paper, and the seller who does not want paper

A seller prints this and ticks it with a pen, so "it prints" is not the bar.
`audit.py` measures the paper: nothing past the 725px printable width of a
Letter sheet, no block taller than one 950px page (`break-inside: avoid`
cannot save a block that does not fit, and that one gets cut), a tick box on
every visible item, no text that will not read in ink, and then the part only
paper can answer. It renders each printed page through the browser's own PDF
viewer and looks for ink inside the margins, because every other check reads
the layout BEFORE the browser paginates it. A page that fits has white edges.
It currently runs to **8 pages**, and the gate fails past 12 both because a
longer handout gets skimmed and because rendering pages costs about a second
and a half each. The pages land in `shots/print/` for the eye.

Verified against four mutants: the page made wider than the sheet, the tick
boxes hidden in print, an item made taller than a page, and the print margin
cut to 3mm, which is inside what most printers can physically reach. Each was
caught, and the last one only by the ink check.

**Without paper**, the answer is the home screen, and the page takes that
position rather than offering a menu. "Keep it on my phone" gives the two
steps for the phone the reader is actually holding, iOS or Android, and then
the list is an icon that opens straight back to their own dates with their
ticks intact, since the ticks live on that device. A PDF and the calendar
export sit underneath as the other two things somebody might want.

There is deliberately **no web app manifest**. On Android, Chrome installs a
manifest's `start_url`, and every personal detail on this page rides in the
URL fragment, so an install would hand the client a blank list. Without one,
"Add to Home screen" is a plain shortcut to the exact URL in front of them,
fragment and all. What the page does carry is an `apple-touch-icon`, because
iOS takes that file and nothing else for the icon: the Agency monogram in
white on Agency Red, edge to edge, since iOS applies its own rounding and
Apple's guidance is to keep words out of an icon. The gate checks it is there,
returns 200 and is 180px, because a browser never requests it, so nothing else
would notice it missing until a seller saw a blurry screenshot on their home
screen.

### What audit.py measures

Not "does it load". It checks that every asset returns 200 at both `/` and
`/<slug>` (a relative path that works at the root and 404s one level down is
invisible until the deployed page is opened), that no request fails, that the
brand faces actually loaded rather than falling back to a system serif, that
the headline fits screen one on a 390px phone, that line length stays under 80
characters, that every hit target clears 44px, that a closing date really does
turn every offset into a date, that the flags filter **in both directions** (a
house seller must not be shown the elevator booking, and the reverse), that
ticks survive a reload, that no element the page hides by attribute is still
taking up space, that the realtor's photograph carries at least three times the
pixels it is drawn at, that print opens every fold, and that `/setup` builds a
link with the details in the fragment rather than the query string.
