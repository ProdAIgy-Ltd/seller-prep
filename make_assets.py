"""Turn the source art in assets/_source/ into what the site actually serves.

Run it once after changing a source file or adding a realtor headshot; the
output is committed, so a build (and a deploy) needs neither this script nor
fontTools nor Pillow.

    python make_assets.py

EVERYTHING IT READS LIVES IN THIS DIRECTORY. It used to reach across into
_576-oakwood-floorplans/assets for the faces and the marks, which meant this
project could not be copied, moved or deployed on its own, and a tidy-up in an
unrelated folder would have broken it silently. Source art is vendored under
assets/_source/ instead. It is bigger in git and worth it.

Faces per the brand lock (first-access-signals CLAUDE.md section 5, 2026-04-15):
  Flama Ultracondensed  -> H1 headlines
  Blacker Pro Display   -> H2/H3 secondary and display accents
  DIN 2014 Bold         -> labels and subheadings
  DIN 2014 Regular      -> body

Fonts are SUBSET, not shipped whole: the deployed page is public, and a subset
carrying only the glyphs this page draws is both a fraction of the bytes and a
far smaller slice of a licensed face sitting on a public URL.
"""
import io
import json
import pathlib

from fontTools import subset
from fontTools.ttLib import TTFont
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "assets" / "_source"
OUT = HERE / "assets"
(OUT / "fonts").mkdir(parents=True, exist_ok=True)
(OUT / "headshots").mkdir(parents=True, exist_ok=True)

FACES = {
    "flama-bold":  ("FlamaUltracondensed-Bold.otf",           700),
    "blacker-reg": ("BlackerProDisplayCondensed-Regular.otf", 400),
    "blacker-med": ("BlackerProDisplayCondensed-Medium.otf",  500),
    "din-reg":     ("DIN2014-Regular.otf",                    400),
    "din-bold":    ("DIN2014-Bold.otf",                       700),
}

# Latin, the punctuation and the symbols the page actually draws. Icons are
# inline SVG rather than glyphs, so nothing beyond this is needed.
KEEP = ("U+0020-007E,U+00A0,U+00A9,U+00AE,U+00B0,U+00B7,U+00D7,"
        "U+2018,U+2019,U+201C,U+201D,U+2022,U+2026,U+2013")

report = []
for name, (fname, weight) in FACES.items():
    path = SRC / "fonts" / fname
    if not path.exists():
        raise SystemExit(f"MISSING source face: {path}")
    font = TTFont(str(path))
    opts = subset.Options()
    opts.layout_features = ["kern", "liga", "tnum", "calt"]
    opts.desubroutinize = True
    opts.notdef_outline = True
    opts.recalc_bounds = True
    opts.drop_tables += ["DSIG"]
    sub = subset.Subsetter(options=opts)
    sub.populate(unicodes=subset.parse_unicodes(KEEP))
    sub.subset(font)
    font.flavor = "woff2"
    buf = io.BytesIO()
    font.save(buf)
    raw = buf.getvalue()
    (OUT / "fonts" / f"{name}.woff2").write_bytes(raw)
    report.append((name, path.stat().st_size, len(raw)))

# ---- marks -----------------------------------------------------------------
# The square red mark is the favicon and the header lockup; the wordmark carries
# the brokerage name on the close. Sized for retina at their drawn sizes.
# Only the WHITE wordmark is generated: the close sits on Iron, and print
# inverts that same file rather than loading a black twin. The black source
# stays in _source/ for any future light-ground layout.
MARKS = {
    "ta-mark-red.png":     ("TA_Logo_Red.png",     (256, 256)),
    "ta-wordmark-wht.png": ("TA_Logotype_Wht.png", (720, 316)),
}
for out_name, (src_name, box) in MARKS.items():
    im = Image.open(SRC / src_name).convert("RGBA")
    im.thumbnail(box, Image.LANCZOS)
    # Quantize: these marks are flat colour on transparency, so a palette is
    # both smaller and lossless here. A straight RGBA re-encode of the wordmark
    # came out LARGER than the source, which is the tell that the source was
    # already palettized.
    im.quantize(colors=64, method=Image.FASTOCTREE).save(OUT / out_name, optimize=True)
    report.append((out_name, (SRC / src_name).stat().st_size,
                   (OUT / out_name).stat().st_size))

# A favicon straight off the mark.
fav = Image.open(SRC / "TA_Logo_Red.png").convert("RGBA")
fav.thumbnail((64, 64), Image.LANCZOS)
fav.save(OUT / "favicon.png", optimize=True)

# The home-screen icon. A seller who does not want paper puts this list on
# their home screen, and iOS takes THIS file, not the favicon and not the
# manifest. Two things it gets wrong if you hand it the mark as it comes:
# transparency renders as black, and iOS applies its own rounding, so a
# pre-rounded or edge-to-edge icon comes out wrong. So: flatten onto Canvas
# white, and inset the mark to 62% of the box, which is the proportion Apple's
# own icons keep and what stops it looking cramped beside them.
ICON_PX = 180
src_mark = Image.open(SRC / "TA_Logo_Red.png").convert("RGB")
# Take the A monogram ALONE, measured out of the source rather than guessed at:
# the white pixels above the wordmark. The full lockup does not work at 60pt.
# Its wordmark would render about seven pixels tall, which is illegible, and
# Apple's own guidance is to keep words out of an icon. The label under the
# icon already says what this is.
_w, _h = src_mark.size
_px = src_mark.load()
_xs, _ys = [], []
for _y in range(0, int(_h * 0.55), 2):
    for _x in range(0, _w, 2):
        if all(c > 200 for c in _px[_x, _y]):
            _xs.append(_x)
            _ys.append(_y)
box = (min(_xs), min(_ys), max(_xs) + 1, max(_ys) + 1)
# Paint the monogram through a MASK rather than pasting a crop of the source.
# A crop brings the source's own red with it, and that red is a hair off the
# locked #ED2127, so the rectangle showed as a faint block behind the mark.
# Alpha is a RAMP off the luminance, not the luminance itself: Agency Red sits
# at luminance 95, so using L directly painted the whole crop 37% white and put
# a pink block behind the mark. The ramp maps the red to nothing and the white
# to solid, keeping the curve's antialiased edge in between.
glyph = src_mark.crop(box).convert("L").point(
    lambda v: 0 if v <= 130 else min(255, round((v - 130) * 255 / 105)))
side = int(ICON_PX * 0.58)
glyph = glyph.resize((side, round(side * glyph.height / glyph.width)), Image.LANCZOS)
icon = Image.new("RGB", (ICON_PX, ICON_PX), "#ED2127")   # Agency Red, locked
icon.paste(Image.new("RGB", glyph.size, "#FFFFFF"),
           ((ICON_PX - glyph.width) // 2, (ICON_PX - glyph.height) // 2), glyph)
icon.save(OUT / "apple-touch-icon.png", optimize=True)
report.append(("apple-touch-icon.png", (SRC / "TA_Logo_Red.png").stat().st_size,
               (OUT / "apple-touch-icon.png").stat().st_size))

# ---- headshots -------------------------------------------------------------
# Drawn at 62px in a circle on the close, so a 3x phone asks for 186 real
# pixels and anything smaller is upscaled on the device. Any
# assets/_source/headshot-<slug>.* becomes assets/headshots/<slug>.webp, which
# is the filename agents.json points at.
#
# 192px WebP at quality 88, measured, not guessed. Root-mean-square error per
# channel against the untouched source crop, with the encoded bytes:
#
#     128 WebP q72   2,184 B   5.19
#     176 JPEG q86   7,205 B   2.94   <- what this used to ship
#     192 WebP q88   6,078 B   2.28
#     192 WebP q94   8,890 B   1.76
#
# So the WebP is sharper AND smaller than the JPEG it replaces, and q94 buys
# half a point of error for half again the bytes. WebP has been in every
# browser since Safari 14 (2020), and the same 192/0.88 pair is what the /setup
# uploader encodes in the browser, so a self-serve photograph and a registry
# photograph are the same picture.
HEAD_PX = 192
HEAD_Q = 88
for src in sorted(SRC.glob("headshot-*")):
    slug = src.stem[len("headshot-"):]
    im = Image.open(src).convert("RGB")
    w, h = im.size
    side = min(w, h)
    # Centre horizontally; bias the crop UPWARD, because a centred square on a
    # portrait cuts the top of the head off and leaves a chest.
    left = (w - side) // 2
    top = min(max(0, (h - side) // 4), h - side)
    im = im.crop((left, top, left + side, top + side))
    im = im.resize((HEAD_PX, HEAD_PX), Image.LANCZOS)
    dest = OUT / "headshots" / f"{slug}.webp"
    im.save(dest, "WEBP", quality=HEAD_Q, method=6)
    stale = OUT / "headshots" / f"{slug}.jpg"
    if stale.exists():
        stale.unlink()
    report.append((f"headshots/{slug}.webp", src.stat().st_size, dest.stat().st_size))

font_total = sum(r[2] for r in report[:len(FACES)])
served = sum(p.stat().st_size for p in OUT.rglob("*")
             if p.is_file() and "_source" not in p.parts)
for name, before, after in report:
    print(f"  {name:<26} {before:>9,} -> {after:>7,}")
print(f"\n  {len(FACES)} faces subset, {font_total:,} bytes of woff2")
print(f"  {served:,} bytes served in total (source art is not deployed)")
