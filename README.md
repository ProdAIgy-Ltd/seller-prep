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
headshot at `assets/headshots/<slug>.jpg`. The build **stops** if the headshot
named there is missing, because a broken image on a client-facing close is a
broken page and it should never reach a deploy.

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
| `assets/_source/` | Not in this repo. The licensed OTF originals live in the private fieldwork repo. |
| `dist/` | The built site, committed. Drop it on any static host with no build step. |

### Assets

Everything the site needs is in this directory. `make_assets.py` reads only
`assets/_source/` and writes what is actually served:

| Source | Served |
|---|---|
| `_source/fonts/*.otf` (5 licensed faces) | `fonts/*.woff2`, subset to the glyphs the page draws, 45KB total |
| `_source/TA_*.png` | `ta-mark-red.png`, the two wordmarks, `favicon.png` |
| `_source/headshot-<slug>.png` | `headshots/<slug>.jpg`, square, cropped upward, 176px, about 7KB |

**`_source/` never ships.** The subset faces exist so a licensed font does not
sit on a public URL in its original form, and a plain `copytree` once undid
that by sweeping the whole folder into the deploy. The build now excludes it
and asserts no `.otf`, `.ttf` or `.woff` reached the tree, verified against a
mutant of the pre-fix line.

To add a realtor's photograph: do it in the private fieldwork repo, where the
source art lives. Drop `assets/_source/headshot-<slug>.png`, run
`python make_assets.py`, then copy the resulting `assets/headshots/<slug>.jpg`
here and set `"headshot": "<slug>.jpg"` in `agents.json`. The build stops if
that file is missing, so a broken close can never reach a deploy.

### The copy gate

`build.py` runs over the **rendered** text of every page, not the source, and
fails the build on an em-dash, an en-dash, the word "AI", finance jargon, or a
first person plural. The last one is the realtor-agnostic rule made mechanical:
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

### What audit.py measures

Not "does it load". It checks that every asset returns 200 at both `/` and
`/<slug>` (a relative path that works at the root and 404s one level down is
invisible until the deployed page is opened), that no request fails, that the
brand faces actually loaded rather than falling back to a system serif, that
the headline fits screen one on a 390px phone, that line length stays under 80
characters, that every hit target clears 44px, that a closing date really does
turn every offset into a date, that the flags filter **in both directions** (a
house seller must not be shown the elevator booking, and the reverse), that
ticks survive a reload, that print opens every fold, and that `/setup` builds a
link with the details in the fragment rather than the query string.
