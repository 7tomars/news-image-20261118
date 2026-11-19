#!/usr/bin/env python3
"""The World Today - a one-page newspaper poster of Wednesday 18 Nov 2026.

Self-contained renderer: own raster canvas, own stroke typeface, own PNG
encoder.  Python standard library only, no network, fully deterministic.
Writes entry.png (1024x1024) into $MAKEFUN_OUTPUT_DIR or /output.
"""

import math
import os
import struct
import zlib

# ---------------------------------------------------------------- canvas ---

SIZE = 1024          # final image is SIZE x SIZE
SS = 2               # supersampling factor for smooth strokes
W = SIZE * SS        # device width
H = SIZE * SS        # device height

PAPER = (247, 243, 232)
INK = (22, 22, 26)
RED = (168, 30, 30)
GRAY = (100, 97, 90)


def new_canvas():
    return bytearray(PAPER) * (W * H)


def put_px(fb, x, y, rgb):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        fb[i] = rgb[0]
        fb[i + 1] = rgb[1]
        fb[i + 2] = rgb[2]


def fill_rect(fb, x, y, w, h, rgb):
    """Filled rectangle in design coordinates."""
    x0, y0 = int(x * SS), int(y * SS)
    x1, y1 = int((x + w) * SS), int((y + h) * SS)
    for yy in range(max(0, y0), min(H, y1)):
        base = yy * W * 3
        for xx in range(max(0, x0), min(W, x1)):
            i = base + xx * 3
            fb[i] = rgb[0]
            fb[i + 1] = rgb[1]
            fb[i + 2] = rgb[2]


def stamp(fb, cx, cy, r, rgb):
    """Filled disc in device coordinates (the pen tip)."""
    x0, x1 = int(cx - r), int(cx + r + 0.5)
    y0, y1 = int(cy - r), int(cy + r + 0.5)
    r2 = r * r
    for yy in range(y0, y1 + 1):
        dy = yy - cy
        for xx in range(x0, x1 + 1):
            dx = xx - cx
            if dx * dx + dy * dy <= r2:
                put_px(fb, xx, yy, rgb)


def draw_segment(fb, x0, y0, x1, y1, r, rgb):
    """Thick line between two device-space points."""
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    steps = max(1, int(length / max(1.0, r * 0.55)))
    for i in range(steps + 1):
        t = i / steps
        stamp(fb, x0 + dx * t, y0 + dy * t, r, rgb)


# -------------------------------------------------------------- typeface ---
# Stroke glyphs on a grid: x in 0..6, y in 0..8 (0 = cap top, 8 = baseline).
# Each glyph is a list of strokes; each stroke is a list of (x, y) points.

def _arc(cx, cy, rx, ry, a0, a1):
    n = max(10, int(abs(a1 - a0) / 10))
    pts = []
    for i in range(n + 1):
        t = math.radians(a0 + (a1 - a0) * i / n)
        pts.append((cx + rx * math.cos(t), cy + ry * math.sin(t)))
    return pts


_S_UPPER = [(5.3, 1.5), (4.2, 0.4), (2.6, 0.1), (1.2, 0.7), (0.55, 2.0),
            (1.0, 3.3), (2.2, 4.1), (4.0, 4.7), (5.3, 5.7), (5.1, 7.1),
            (3.9, 8.0), (2.0, 7.9), (0.6, 6.9)]
_S_LOWER = [(5.1, 1.6), (4.0, 0.5), (2.5, 0.2), (1.2, 0.8), (0.7, 2.1),
            (1.2, 3.3), (2.4, 4.0), (4.0, 4.6), (5.1, 5.6), (4.9, 7.0),
            (3.8, 7.9), (2.0, 7.8), (0.8, 6.9)]
_BOWL_P = [_arc(3.0, 2.1, 2.2, 2.1, -90, 90)]

GLYPHS = {
    "A": [[(0, 8), (3, 0), (6, 8)], [(1.4, 5.4), (4.6, 5.4)]],
    "B": [[(0, 0), (0, 8)], [(0, 0), (3.1, 0)], _arc(3.1, 2.0, 2.1, 2.0, -90, 90),
          [(0, 4), (3.1, 4)], _arc(3.3, 6.0, 2.3, 2.0, -90, 90), [(0, 8), (3.3, 8)]],
    "C": [_arc(3.05, 4.0, 2.95, 3.95, 55, 305)],
    "D": [[(0, 0), (0, 8)], [(0, 0), (2.6, 0)], _arc(2.6, 4.0, 2.9, 4.0, -90, 90),
          [(0, 8), (2.6, 8)]],
    "E": [[(5.1, 0), (0, 0), (0, 8), (5.3, 8)], [(0, 4), (4.2, 4)]],
    "F": [[(5.1, 0), (0, 0), (0, 8)], [(0, 4), (4.2, 4)]],
    "G": [_arc(3.05, 4.0, 2.95, 3.95, 55, 300), [(3.6, 4.8), (5.9, 4.8)],
          [(5.9, 4.8), (5.9, 7.4)]],
    "H": [[(0, 0), (0, 8)], [(6, 0), (6, 8)], [(0, 4), (6, 4)]],
    "I": [[(1.2, 0), (4.8, 0)], [(3, 0), (3, 8)], [(1.2, 8), (4.8, 8)]],
    "J": [[(5.2, 0), (5.2, 6.1)], _arc(3.05, 6.1, 2.15, 1.9, 0, 160)],
    "K": [[(0, 0), (0, 8)], [(5.3, 0), (0.5, 4.3)], [(1.5, 3.3), (5.5, 8)]],
    "L": [[(0, 0), (0, 8), (5.3, 8)]],
    "M": [[(0, 8), (0, 0), (3, 3.6), (6, 0), (6, 8)]],
    "N": [[(0, 8), (0, 0), (6, 8), (6, 0)]],
    "O": [_arc(3.0, 4.0, 3.0, 4.0, 0, 360)],
    "P": [[(0, 8), (0, 0)], [(0, 0), (3.0, 0)], _BOWL_P[0], [(0, 4.2), (3.0, 4.2)]],
    "Q": [_arc(3.0, 4.0, 3.0, 4.0, 0, 360), [(3.4, 5.6), (6.1, 8.4)]],
    "R": [[(0, 8), (0, 0)], [(0, 0), (3.0, 0)], _BOWL_P[0], [(0, 4.2), (3.0, 4.2)],
          [(2.7, 4.2), (5.5, 8)]],
    "S": [_S_UPPER],
    "T": [[(0, 0), (6, 0)], [(3, 0), (3, 8)]],
    "U": [[(0, 0), (0, 5.9)], _arc(3.0, 5.9, 3.0, 2.1, 180, 0), [(6, 0), (6, 5.9)]],
    "V": [[(0, 0), (3, 8), (6, 0)]],
    "W": [[(0, 0), (1.5, 8), (3, 3.8), (4.5, 8), (6, 0)]],
    "X": [[(0, 0), (6, 8)], [(6, 0), (0, 8)]],
    "Y": [[(0, 0), (3, 3.4), (6, 0)], [(3, 3.4), (3, 8)]],
    "Z": [[(0.2, 0), (5.8, 0), (0.2, 8), (5.8, 8)]],
    "0": [_arc(3.0, 4.0, 2.5, 4.0, 0, 360)],
    "1": [[(1.6, 1.4), (3.5, 0), (3.5, 8)], [(1.3, 8), (5.0, 8)]],
    "2": [[(0.7, 1.7), (1.2, 0.6), (2.6, 0.1), (4.3, 0.5), (5.2, 1.8),
           (4.9, 3.2), (3.6, 4.6), (0.5, 8), (5.5, 8)]],
    "3": [[(0.7, 1.3), (1.9, 0.2), (3.9, 0.2), (5.0, 1.5), (4.5, 3.1), (3.1, 3.9)],
          [(3.1, 3.9), (4.6, 4.3), (5.3, 5.7), (4.7, 7.4), (3.0, 8.0),
           (1.1, 7.7), (0.4, 6.7)]],
    "4": [[(4.3, 8), (4.3, 0), (0.2, 5.8), (5.8, 5.8)]],
    "5": [[(5.3, 0), (0.7, 0), (0.5, 3.7)], _arc(3.1, 5.7, 2.5, 2.3, -95, 95)],
    "6": [_arc(3.05, 5.6, 2.5, 2.4, 0, 360),
          [(5.2, 1.3), (4.0, 0.4), (2.4, 0.6), (1.2, 2.0), (0.65, 4.6)]],
    "7": [[(0.4, 0), (5.7, 0), (2.7, 8)]],
    "8": [_arc(3.0, 2.05, 2.05, 1.95, 0, 360), _arc(3.0, 6.05, 2.55, 1.95, 0, 360)],
    "9": [_arc(2.95, 2.4, 2.5, 2.4, 0, 360),
          [(5.45, 2.6), (5.2, 5.0), (4.0, 7.2), (2.4, 8.0), (1.0, 7.5)]],
    ".": [[(3.0, 7.5), (3.0, 7.9)]],
    ",": [[(3.2, 7.3), (2.6, 8.8)]],
    "'": [[(3.0, 0.0), (2.7, 1.8)]],
    "-": [[(0.8, 4.0), (4.6, 4.0)]],
    ":": [[(3.0, 2.0), (3.0, 2.4)], [(3.0, 6.6), (3.0, 7.0)]],
    ";": [[(3.0, 2.0), (3.0, 2.4)], [(3.2, 6.6), (2.6, 8.6)]],
    "!": [[(3.0, 0.0), (3.0, 5.6)], [(3.0, 7.4), (3.0, 7.8)]],
    "?": [[(0.8, 1.5), (1.6, 0.3), (3.6, 0.1), (5.1, 1.2), (4.9, 2.9),
           (3.9, 4.0), (3.1, 4.7), (3.1, 5.6)], [(3.1, 7.4), (3.1, 7.8)]],
    "/": [[(5.0, 0.0), (1.0, 8.0)]],
    "(": [_arc(3.6, 4.0, 1.8, 4.2, 120, 240)],
    ")": [_arc(2.4, 4.0, 1.8, 4.2, -60, 60)],
    "$": [_S_LOWER, [(3.0, -0.5), (3.0, 8.5)]],
    "%": [_arc(1.7, 1.7, 1.5, 1.5, 0, 360), _arc(4.6, 6.3, 1.5, 1.5, 0, 360),
          [(5.4, 0.2), (0.9, 7.8)]],
    "·": [[(3.0, 4.0), (3.0, 4.35)]],
}

# Advance widths in grid units (glyph body is 6 units wide).
ADV = {" ": 3.8, "I": 6.0, "1": 6.4, ".": 3.4, ",": 3.4, "'": 3.0, ":": 3.4,
       ";": 3.4, "!": 3.4, "-": 5.6, "/": 4.8, "(": 4.2, ")": 4.2, "·": 3.4}
DEFAULT_ADV = 7.6


def normalize(text):
    return (text.upper()
            .replace("–", "-").replace("—", "-")
            .replace("‘", "'").replace("’", "'")
            .replace("“", "'").replace("”", "'"))


def text_width(text, cap_h):
    unit = cap_h / 8.0
    return sum(ADV.get(ch, DEFAULT_ADV) for ch in normalize(text)) * unit


def draw_text(fb, text, x, y, cap_h, rgb, bold=False, align="left"):
    """Draw one line of text; (x, y) is the cap-top-left in design coords."""
    text = normalize(text)
    unit = cap_h / 8.0
    width = text_width(text, cap_h)
    if align == "center":
        x = x - width / 2.0
    elif align == "right":
        x = x - width
    r = unit * SS * (0.80 if bold else 0.55)
    cx = x
    for ch in text:
        if ch != " ":
            glyph = GLYPHS.get(ch)
            if glyph:
                for stroke in glyph:
                    pts = [((cx + gx * unit) * SS, (y + gy * unit) * SS)
                           for gx, gy in stroke]
                    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                        draw_segment(fb, x0, y0, x1, y1, r, rgb)
                    if len(pts) == 1:
                        stamp(fb, pts[0][0], pts[0][1], r, rgb)
        cx += ADV.get(ch, DEFAULT_ADV) * unit
    return width


def wrap(text, cap_h, max_width):
    """Greedy word wrap; returns a list of lines."""
    words = normalize(text).split()
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, cap_h) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(fb, text, x, y, cap_h, rgb, max_width, line_h, bold=False):
    lines = wrap(text, cap_h, max_width)
    for i, line in enumerate(lines):
        draw_text(fb, line, x, y + i * line_h, cap_h, rgb, bold=bold)
    return len(lines) * line_h


# --------------------------------------------------------------- content ---

MARGIN = 46
RIGHT = SIZE - MARGIN
COL_W = 451
COL2_X = 527

LEAD_KICKER = "LEAD STORY · FIRST-EVER SUMMIT · APEC, SHENZHEN"
LEAD_HEAD = "XI-TRUMP-PUTIN SUMMIT SET FOR THURSDAY"
LEAD_BODY = ("XI GREETED TRUMP AT THE AIRPORT AND THE THREE LEADERS SHOOK "
             "HANDS AT THE APEC RECEPTION. THE SUMMIT WILL DISCUSS UKRAINE, "
             "THE US-IRAN WAR, NUCLEAR AND TRADE ISSUES.")

STORIES_LEFT = [
    ("IRAN STRIKES US BASES IN KUWAIT AND BAHRAIN",
     "IN REPLY TO US STRIKES ON MISSILE SITES ON QESHM ISLAND IN THE "
     "STRAIT OF HORMUZ."),
    ("KERCH BRIDGE ATTACKED A SECOND DAY: SPAN DOWN",
     "ROAD AND RAIL TRAFFIC HALTED. ZELENSKY DETAILED A SEVEN-PHASE "
     "OPERATION."),
    ("BOARD OF PEACE ACCUSES BOTH SIDES IN GAZA",
     "TRUMP'S BOARD SAYS ISRAEL AND HAMAS VIOLATED CEASEFIRE "
     "COMMITMENTS, IN A 12-PAGE REPORT SEEN BY REUTERS."),
]

STORIES_RIGHT = [
    ("MARY PELTOLA WINS ALASKA SENATE RACE",
     "THE DEMOCRAT TAKES THE LAST MIDTERM SEAT CALLED. DEMOCRATS HOLD "
     "THE SENATE 56-44."),
    ("NVIDIA POSTS RECORD $115.8 BILLION QUARTER",
     "REVENUE UP 103%. THE BOARD DECLINES TO BRING JENSEN HUANG BACK "
     "AS CEO."),
    ("TRUMP: 'VERY BIG' TRADE DEAL WITH PHILIPPINES",
     "ANNOUNCED AT A STATE BANQUET IN MANILA, AFTER MEETING PRESIDENT "
     "MARCOS JR."),
    ("KNESSET ELECTS MATAN KAHANA AS SPEAKER",
     "A WIN FOR PRIME MINISTER-ELECT GADI EISENKOT'S BLOC OVER "
     "NETANYAHU'S."),
]


def rule(fb, y, h, rgb=INK):
    fill_rect(fb, MARGIN, y, RIGHT - MARGIN, h, rgb)


def draw_story(fb, x, y, head, body):
    used = draw_wrapped(fb, head, x, y, 19, INK, COL_W, 24, bold=True)
    used += 4
    used += draw_wrapped(fb, body, x, y + used, 15, INK, COL_W, 18.5)
    return used


def draw_column(fb, x, top, stories):
    y = top
    for i, (head, body) in enumerate(stories):
        y += draw_story(fb, x, y, head, body)
        if i < len(stories) - 1:
            y += 5
            fill_rect(fb, x, y, COL_W, 1.6, GRAY)
            y += 7
    return y


def render():
    fb = new_canvas()

    # Masthead
    rule(fb, 28, 6)
    rule(fb, 40, 2)
    draw_text(fb, "THE WORLD TODAY", SIZE / 2, 48, 28, INK, bold=True,
              align="center")
    draw_text(fb, "ALL THE DAY'S NEWS - ON ONE PAGE", SIZE / 2, 84, 13,
              GRAY, align="center")
    rule(fb, 105, 2)

    # Date - the dominant element
    draw_text(fb, "WEDNESDAY", SIZE / 2, 112, 80, INK, bold=True,
              align="center")
    draw_text(fb, "18 NOVEMBER 2026", SIZE / 2, 198, 50, RED, bold=True,
              align="center")
    rule(fb, 262, 5)
    rule(fb, 273, 2)

    # Lead story
    draw_text(fb, LEAD_KICKER, MARGIN, 286, 17, RED, bold=True)
    y = 309
    y += draw_wrapped(fb, LEAD_HEAD, MARGIN, y, 35, INK, RIGHT - MARGIN,
                      42.5, bold=True)
    y += 6
    y += draw_wrapped(fb, LEAD_BODY, MARGIN, y, 19, INK, RIGHT - MARGIN,
                      22)
    y += 8
    rule(fb, y, 3)
    y += 13

    # Two-column story grid
    col_top = y
    ly = draw_column(fb, MARGIN, col_top, STORIES_LEFT)
    ry = draw_column(fb, COL2_X, col_top, STORIES_RIGHT)
    # Vertical divider between the columns
    fill_rect(fb, 505, col_top, 1.6, max(ly, ry) - col_top, GRAY)

    # Footer
    rule(fb, 966, 2)
    draw_text(fb, "EIGHT STORIES · ONE PAGE · COMPILED FROM THE DAY'S "
                  "WIRE REPORTS", SIZE / 2, 975, 12.5, GRAY, align="center")
    return fb


# ------------------------------------------------------------ PNG output ---

def downsample(fb):
    out = bytearray(SIZE * SIZE * 3)
    for y in range(SIZE):
        for x in range(SIZE):
            i = (y * SIZE + x) * 3
            for c in range(3):
                total = 0
                for dy in range(SS):
                    row = (y * SS + dy) * W * 3
                    for dx in range(SS):
                        total += fb[row + (x * SS + dx) * 3 + c]
                out[i + c] = total // (SS * SS)
    return bytes(out)


def png_bytes(rgb):
    raw = bytearray()
    stride = SIZE * 3
    for y in range(SIZE):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", SIZE, SIZE, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", zlib.compress(bytes(raw), 9)) +
            chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    data = png_bytes(downsample(render()))
    with open(os.path.join(out_dir, "entry.png"), "wb") as fh:
        fh.write(data)


if __name__ == "__main__":
    main()
