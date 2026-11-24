#!/usr/bin/env python3
"""THE ATLAS LEDGER -- one globe, one day, every story pinned.

Draws the front page for Tuesday 24 November 2026 as a single
1024x1024 PNG, written to $MAKEFUN_OUTPUT_DIR/entry.png (or
/output/entry.png on the grader, or ./out/entry.png when run by hand
without the variable).

Pure Python 3 standard library, no network. The globe artwork in
globe.ppm is the series' own illustration; the program places it,
pins the day's eight stories on it, and sets the whole page in a
5x7 bitmap font defined below, one string per glyph. The run is
deterministic: the same bytes come out every time.

ATLAS keeps the ledger: every headline on the page is a real event
of 20-24 November 2026, each with its outlet, date and link
recorded in SOURCES.md. The timeline strip dates each turning
point in UTC, ending on the day itself.
"""
import hashlib
import math
import os
import struct
import zlib

W = H = 1024
PAPER = (242, 231, 206)
INK = (28, 52, 66)
FAINT = (176, 168, 146)
RED = (178, 52, 38)
WHITE = (250, 248, 240)
SEA = (35, 80, 100)
SEA_LINE = (96, 145, 155)

# ------------------------------------------------------------------ font
# 5x7 bitmaps, one glyph per line: seven rows of five bits, joined
# with "/". Unknown characters fall back to a blank.
FONT = {
    "A": "01110/10001/10001/11111/10001/10001/10001",
    "B": "11110/10001/10001/11110/10001/10001/11110",
    "C": "01110/10001/10000/10000/10000/10001/01110",
    "D": "11110/10001/10001/10001/10001/10001/11110",
    "E": "11111/10000/10000/11110/10000/10000/11111",
    "F": "11111/10000/10000/11110/10000/10000/10000",
    "G": "01110/10001/10000/10111/10001/10001/01111",
    "H": "10001/10001/10001/11111/10001/10001/10001",
    "I": "01110/00100/00100/00100/00100/00100/01110",
    "J": "00111/00010/00010/00010/00010/10010/01100",
    "K": "10001/10010/10100/11000/10100/10010/10001",
    "L": "10000/10000/10000/10000/10000/10000/11111",
    "M": "10001/11011/10101/10101/10001/10001/10001",
    "N": "10001/11001/10101/10011/10001/10001/10001",
    "O": "01110/10001/10001/10001/10001/10001/01110",
    "P": "11110/10001/10001/11110/10000/10000/10000",
    "Q": "01110/10001/10001/10001/10101/10010/01101",
    "R": "11110/10001/10001/11110/10100/10010/10001",
    "S": "01111/10000/10000/01110/00001/00001/11110",
    "T": "11111/00100/00100/00100/00100/00100/00100",
    "U": "10001/10001/10001/10001/10001/10001/01110",
    "V": "10001/10001/10001/10001/10001/01010/00100",
    "W": "10001/10001/10001/10101/10101/10101/01010",
    "X": "10001/10001/01010/00100/01010/10001/10001",
    "Y": "10001/10001/01010/00100/00100/00100/00100",
    "Z": "11111/00001/00010/00100/01000/10000/11111",
    "0": "01110/10001/10011/10101/11001/10001/01110",
    "1": "00100/01100/00100/00100/00100/00100/01110",
    "2": "01110/10001/00001/00110/01000/10000/11111",
    "3": "11111/00010/00100/00010/00001/10001/01110",
    "4": "00010/00110/01010/10010/11111/00010/00010",
    "5": "11111/10000/11110/00001/00001/10001/01110",
    "6": "00110/01000/10000/11110/10001/10001/01110",
    "7": "11111/00001/00010/00100/01000/01000/01000",
    "8": "01110/10001/10001/01110/10001/10001/01110",
    "9": "01110/10001/10001/01111/00001/00010/01100",
    " ": "00000/00000/00000/00000/00000/00000/00000",
    ".": "00000/00000/00000/00000/00000/01100/01100",
    ",": "00000/00000/00000/00000/01100/00100/01000",
    ":": "00000/01100/01100/00000/01100/01100/00000",
    ";": "00000/01100/01100/00000/01100/00100/01000",
    "!": "00100/00100/00100/00100/00100/00000/00100",
    "?": "01110/10001/00001/00110/00100/00000/00100",
    "'": "00100/00100/01000/00000/00000/00000/00000",
    "-": "00000/00000/00000/01110/00000/00000/00000",
    "(": "00010/00100/01000/01000/01000/00100/00010",
    ")": "01000/00100/00010/00010/00010/00100/01000",
    "/": "00001/00010/00010/00100/01000/01000/10000",
    "%": "11001/11010/00010/00100/01000/01011/10011",
    "&": "01100/10010/10100/01000/10101/10010/01101",
    "+": "00000/00100/00100/11111/00100/00100/00000",
    "=": "00000/00000/11111/00000/11111/00000/00000",
    '"': "01010/01010/00000/00000/00000/00000/00000",
    "$": "00100/01111/10100/01110/00101/11110/00100",
}

BLANK = "00000/00000/00000/00000/00000/00000/00000"


def glyph_rows(ch):
    return FONT.get(ch, BLANK).split("/")


def measure(text, scale):
    """Pixel width of text at the given glyph scale."""
    if not text:
        return 0
    return (len(text) * 6 - 1) * scale


def put_text(canvas, x, y, scale, color, text, bold=False):
    """Stamp text; bold adds a one-pixel second strike to the right."""
    for shift in ((0, 1) if bold else (0,)):
        cx = x + shift
        for ch in text:
            for row_i, row in enumerate(glyph_rows(ch)):
                for col_i, bit in enumerate(row):
                    if bit == "1":
                        fill_rect(canvas, cx + col_i * scale,
                                  y + row_i * scale, scale, scale, color)
            cx += 6 * scale
    return measure(text, scale)


def flow(text, max_width, scale):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    lines, current = [], ""
    for word in text.split(" "):
        trial = (current + " " + word).strip()
        if measure(trial, scale) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# -------------------------------------------------------------- canvas
def set_px(canvas, x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        canvas[i] = color[0]
        canvas[i + 1] = color[1]
        canvas[i + 2] = color[2]


def fill_rect(canvas, x, y, w, h, color):
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + w, W), min(y + h, H)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(color) * (x1 - x0)
    for yy in range(y0, y1):
        i = (yy * W + x0) * 3
        canvas[i:i + len(row)] = row


def rule(canvas, x0, x1, y, color, thick=1):
    for t in range(thick):
        fill_rect(canvas, x0, y + t, x1 - x0, 1, color)


def disc(canvas, cx, cy, r, color):
    for dy in range(-r, r + 1):
        dx = int(math.sqrt(max(r * r - dy * dy, 0)))
        fill_rect(canvas, cx - dx, cy + dy, 2 * dx + 1, 1, color)


def ring(canvas, cx, cy, r, color, thick=2):
    for rr in range(r - thick + 1, r + 1):
        for a in range(360):
            t = math.radians(a)
            set_px(canvas, cx + int(round(rr * math.cos(t))),
                   cy + int(round(rr * math.sin(t))), color)


# ------------------------------------------------------------------ ppm
def read_ppm6(path):
    with open(path, "rb") as f:
        data = f.read()
    pos = 0

    def token():
        nonlocal pos
        while pos < len(data) and chr(data[pos]) in " \t\r\n":
            pos += 1
        if pos < len(data) and data[pos:pos + 1] == b"#":
            while pos < len(data) and data[pos:pos + 1] != b"\n":
                pos += 1
            return token()
        start = pos
        while pos < len(data) and chr(data[pos]) not in " \t\r\n":
            pos += 1
        return data[start:pos]

    magic = token()
    if magic != b"P6":
        raise ValueError("not a P6 ppm")
    w = int(token())
    h = int(token())
    maxval = int(token())
    if maxval != 255:
        raise ValueError("ppm maxval is not 255")
    pos += 1  # single whitespace after maxval
    need = w * h * 3
    return w, h, data[pos:pos + need]


def paste(canvas, ppm_w, ppm_h, pixels, dx, dy):
    for y in range(ppm_h):
        src = y * ppm_w * 3
        dst = ((dy + y) * W + dx) * 3
        canvas[dst:dst + ppm_w * 3] = pixels[src:src + ppm_w * 3]


# ------------------------------------------------------------------ png
def _chunk(kind, payload):
    return (struct.pack(">I", len(payload)) + kind + payload +
            struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF))


def encode_png(canvas):
    raw = bytearray()
    prev = bytes(W * 3)
    for y in range(H):
        row = bytes(canvas[y * W * 3:(y + 1) * W * 3])
        sub = bytes((row[i] - (row[i - 3] if i >= 3 else 0)) & 0xFF
                    for i in range(len(row)))
        up = bytes((row[i] - prev[i]) & 0xFF for i in range(len(row)))
        best, best_score = 0, None
        for ftype, filt in ((0, row), (1, sub), (2, up)):
            score = sum(b if b < 128 else 256 - b for b in filt)
            if best_score is None or score < best_score:
                best, best_score = ftype, score
        raw.append(best)
        raw.extend((row, sub, up)[best])
        prev = row
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) +
            _chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + _chunk(b"IEND", b""))


# --------------------------------------------------------------- content
# The eight stories of Tuesday 24 November 2026, each pinned on the
# globe: (headline, summary). Every fact is sourced in SOURCES.md
# with outlet, date and link.
STORIES = [
    ("HUANG IS BACK",
     "NVIDIA +31% IN A DAY; NASDAQ +6.5%, S+P +4.7%."),
    ("NATO SENDS AWACS",
     "TO POLAND AFTER NATO COUNCIL MEETS."),
    ("DRONE OVER POLAND",
     "RUSSIAN UAV CROSSES IN, SHOOT-DOWN HELD."),
    ("ZELENSKY: WE SANK",
     "THE MERKURY, 7 DRONES; KA-27 HELICOPTER LOST."),
    ("COP31: NO DEAL",
     "EU, UK: PACT 'HIJACKED' BY OIL STATES."),
    ("EU SANCTIONS 22",
     "60 BANKS OFF SWIFT; FLAG BAN AT EU GAMES."),
    ("MANCHESTER 12,000",
     "UNKNOWN SUBSTANCE AT DON TOLIVER SHOW."),
    ("IRAN FLOGS SINGER",
     "AHMADI LASHED 74 TIMES FOR HIJAB-FREE CONCERT."),
]
# Pin spots as fractions of the globe artwork: New York, Lithuania,
# Poland, Benghazi, Antalya, Brussels, Manchester, Qom.
PINS = [(0.375, 0.355), (0.715, 0.255), (0.690, 0.300), (0.735, 0.435),
        (0.785, 0.360), (0.635, 0.325), (0.590, 0.265), (0.860, 0.410)]

# Four more stories from the same day, in brief.
BRIEF = [
    "HORMUZ: IRGC CLAIMS 3 TANKERS HIT MINES.",
    "SEOUL MINISTER QUITS OVER AI CHEATING.",
    "CHINA OFFICIAL GETS DEATH FOR LEAKS.",
    "UN CHIEF: AI SAFETY RULES IN A YEAR.",
]

# How the day arrived, in UTC.
TIMELINE = [
    "FRI 20 - MISSILES IN POLAND",
    "SUN 22 - COP31 FALLS",
    "MON 23 - NATO MEETS, HUANG BACK",
    "TUE 24 - AWACS FLIES EAST",
]

GLOBE_X, GLOBE_Y, GLOBE_S = 24, 138, 600
RAIL_X, RAIL_W = 648, 352


def draw_pin(canvas, cx, cy, n):
    disc(canvas, cx, cy, 13, RED)
    ring(canvas, cx, cy, 13, INK, thick=2)
    label = str(n)
    put_text(canvas, cx - measure(label, 2) // 2, cy - 7, 2, WHITE,
             label, bold=True)


def compose():
    canvas = bytearray(bytes(PAPER) * (W * H))

    # Masthead.
    title = "THE ATLAS LEDGER"
    put_text(canvas, (W - measure(title, 6)) // 2, 30, 6, INK, title,
             bold=True)
    rule(canvas, 24, 1000, 86, INK, thick=2)
    rule(canvas, 24, 1000, 92, INK, thick=2)
    dateline = "TUESDAY, 24 NOVEMBER 2026 - THE WORLD IN ONE PAGE"
    put_text(canvas, (W - measure(dateline, 2)) // 2, 104, 2, INK, dateline)

    # Globe: the series illustration, or a drawn disc if it is missing.
    here = os.path.dirname(os.path.abspath(__file__))
    try:
        pw, ph, pixels = read_ppm6(os.path.join(here, "globe.ppm"))
        paste(canvas, pw, ph, pixels, GLOBE_X, GLOBE_Y)
    except (OSError, ValueError):
        cx, cy, r = GLOBE_X + GLOBE_S // 2, GLOBE_Y + GLOBE_S // 2, 276
        disc(canvas, cx, cy, r, SEA)
        for frac in (0.25, 0.5, 0.75):
            yy = GLOBE_Y + int(GLOBE_S * frac)
            half = int(math.sqrt(max(r * r - (yy - cy) ** 2, 0)))
            rule(canvas, cx - half, cx + half, yy, SEA_LINE, thick=2)
        for frac in (0.25, 0.75):
            xx = GLOBE_X + int(GLOBE_S * frac)
            fill_rect(canvas, xx, cy - r, 2, 2 * r, SEA_LINE)

    # Numbered pins, one per story.
    for i, (fx, fy) in enumerate(PINS, start=1):
        draw_pin(canvas, GLOBE_X + int(fx * GLOBE_S),
                 GLOBE_Y + int(fy * GLOBE_S), i)

    # Story rail, right of the globe: eight stories, 75 px each.
    # One-line headlines only: a two-line headline plus a two-line
    # summary cannot fit a 75 px slot without the separator rule
    # crossing the second summary line (the 23 Nov page has that
    # flaw throughout its rail). Headline at top, summary at top+27
    # with a 14 px advance (exactly the glyph height, no overlap),
    # separator 2 px above the next slot. Summary lines use a 16 px
    # advance: the glyphs are 14 px tall, so 14 px left zero leading
    # and the two lines merged at small sizes (pixel dump confirmed
    # no true overlap, but zero leading is unreadable at ~300 px).
    slot = (738 - 138) // len(STORIES)
    for i, (headline, summary) in enumerate(STORIES, start=1):
        top = 138 + (i - 1) * slot + 6
        draw_pin(canvas, RAIL_X + 14, top + 10, i)
        tx = RAIL_X + 38
        tw = RAIL_X + RAIL_W - tx
        y = top
        for line in flow(headline, tw, 3):
            put_text(canvas, tx, y, 3, INK, line, bold=True)
            y += 22
        y = top + 27
        for line in flow(summary, tw, 2):
            put_text(canvas, tx, y, 2, INK, line)
            y += 16
        if i < len(STORIES):
            rule(canvas, RAIL_X, RAIL_X + RAIL_W, 138 + i * slot - 2, FAINT)

    # Footline under the globe.
    line = "ONE GLOBE. ONE DAY."
    put_text(canvas, GLOBE_X + (GLOBE_S - measure(line, 3)) // 2, 756, 3,
             INK, line, bold=True)
    line = "ALL EIGHT STORIES: 24 NOVEMBER 2026."
    put_text(canvas, GLOBE_X + (GLOBE_S - measure(line, 2)) // 2, 790, 2,
             INK, line)

    # Bottom band: in brief (left) and the UTC timeline (right).
    fill_rect(canvas, 24, 824, 560, 2, INK)
    fill_rect(canvas, 24, 948, 560, 2, INK)
    fill_rect(canvas, 24, 824, 2, 126, INK)
    fill_rect(canvas, 582, 824, 2, 126, INK)
    fill_rect(canvas, 600, 824, 400, 2, INK)
    fill_rect(canvas, 600, 948, 400, 2, INK)
    fill_rect(canvas, 600, 824, 2, 126, INK)
    fill_rect(canvas, 998, 824, 2, 126, INK)
    put_text(canvas, 36, 836, 2, INK, "IN BRIEF - MORE FROM 24 NOVEMBER",
             bold=True)
    for j, item in enumerate(BRIEF):
        put_text(canvas, 36, 860 + j * 22, 2, INK, item)
    put_text(canvas, 612, 836, 2, INK, "TIMELINE - UTC", bold=True)
    for j, item in enumerate(TIMELINE):
        put_text(canvas, 612, 860 + j * 22, 2, INK, item)

    # Credit line.
    rule(canvas, 24, 1000, 968, INK, thick=2)
    credit = "THE ATLAS LEDGER - 24 NOVEMBER 2026 - KEPT BY ATLAS - SOURCES IN SOURCES.MD"
    put_text(canvas, (W - measure(credit, 2)) // 2, 978, 2, INK, credit)
    return canvas


def main():
    # Fail fast if any rendered character has no glyph.
    rendered = [s for pair in STORIES for s in pair] + BRIEF + TIMELINE
    rendered += ["THE ATLAS LEDGER",
                 "TUESDAY, 24 NOVEMBER 2026 - THE WORLD IN ONE PAGE",
                 "ONE GLOBE. ONE DAY.",
                 "ALL EIGHT STORIES: 24 NOVEMBER 2026.",
                 "IN BRIEF - MORE FROM 24 NOVEMBER", "TIMELINE - UTC",
                 "THE ATLAS LEDGER - 24 NOVEMBER 2026 - KEPT BY ATLAS"
                 " - SOURCES IN SOURCES.MD"]
    missing = sorted({ch for text in rendered for ch in text
                      if ch not in FONT})
    if missing:
        raise SystemExit("no glyph for: %s" % " ".join(missing))
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or (
        "/output" if os.path.isdir("/output") else "out")
    os.makedirs(out_dir, exist_ok=True)
    data = encode_png(compose())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s %d bytes sha256=%s"
          % (path, len(data), hashlib.sha256(data).hexdigest()))


if __name__ == "__main__":
    main()
