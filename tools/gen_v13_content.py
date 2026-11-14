"""Generate the v1.3.0 content: new film-accurate blocks, items and resources.

Why this file exists
--------------------
The original all-in-one generator (``gen_project.py``) was lost in the
2026-11-14 filesystem incident and was never committed, so it cannot be
recovered.  This is a fresh, self-contained re-implementation that covers only
the content added in 1.3.0; every other file under ``src/main/resources`` is
left untouched.

What it writes
--------------
* ``assets/wandering_earth/textures/block/*.png``  - new block textures
* ``assets/wandering_earth/textures/item/*.png``   - new item textures
* ``assets/wandering_earth/blockstates/*.json``     - block state definitions
* ``assets/wandering_earth/models/{block,item}/*.json``
* ``data/wandering_earth/loot_table/blocks/*.json``
* ``data/wandering_earth/recipe/*.json``
* ``assets/wandering_earth/lang/{zh_cn,en_us}.json`` - names + lore

Usage
-----
    python tools/gen_v13_content.py

Requires Pillow.  The script is idempotent: running it twice produces the same
bytes, and it only touches the entries listed in the tables below.
"""

import json
import os
import random

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
RES = os.path.join(REPO, "src", "main", "resources")
NS = "wandering_earth"

BLOCK_TEX = os.path.join(RES, "assets", NS, "textures", "block")
ITEM_TEX = os.path.join(RES, "assets", NS, "textures", "item")
BLOCKSTATE = os.path.join(RES, "assets", NS, "blockstates")
MODEL_BLOCK = os.path.join(RES, "assets", NS, "models", "block")
MODEL_ITEM = os.path.join(RES, "assets", NS, "models", "item")
LOOT = os.path.join(RES, "data", NS, "loot_table", "blocks")
RECIPE = os.path.join(RES, "data", NS, "recipe")
LANG = os.path.join(RES, "assets", NS, "lang")

SIZE = 32

# ---------------------------------------------------------------------------
# palette
# ---------------------------------------------------------------------------

STEEL = (92, 104, 120)
STEEL_DARK = (58, 66, 78)
STEEL_DEEP = (28, 32, 40)
STEEL_LIGHT = (202, 208, 216)
BRASS = (176, 138, 22)
BRASS_DARK = (60, 46, 8)
GOLD = (220, 180, 96)
GOLD_DARK = (108, 78, 34)
GOLD_LIGHT = (246, 220, 152)
SCREEN_BG = (8, 12, 18)
SCREEN_BG2 = (16, 22, 30)
SCREEN_LINE = (40, 96, 128)
SCREEN_GLOW = (96, 224, 255)
RED = (232, 64, 64)
RED_DARK = (58, 20, 22)
RED_BRIGHT = (255, 90, 90)
WHITE = (240, 240, 240)
CONCRETE = (176, 174, 168)
CONCRETE_DARK = (112, 110, 104)
REGOLITH = (122, 120, 114)
REGOLITH_DARK = (58, 56, 54)
FLAME = (255, 146, 33)
FLAME_LIGHT = (255, 240, 190)
EMBER = (245, 122, 20)
HAZARD_Y = (252, 208, 60)
HAZARD_D = (40, 34, 10)


def shade(color, amount):
    return (
        max(0, min(255, color[0] + int(amount))),
        max(0, min(255, color[1] + int(amount))),
        max(0, min(255, color[2] + int(amount))),
    )


# ---------------------------------------------------------------------------
# tiny 3x5 pixel font
# ---------------------------------------------------------------------------

FONT = {
    "A": ["###", "#.#", "###", "#.#", "#.#"],
    "B": ["##.", "#.#", "##.", "#.#", "##."],
    "C": ["###", "#..", "#..", "#..", "###"],
    "D": ["##.", "#.#", "#.#", "#.#", "##."],
    "E": ["###", "#..", "##.", "#..", "###"],
    "F": ["###", "#..", "##.", "#..", "#.."],
    "G": ["###", "#..", "#.#", "#.#", "###"],
    "H": ["#.#", "#.#", "###", "#.#", "#.#"],
    "I": ["###", ".#.", ".#.", ".#.", "###"],
    "J": ["..#", "..#", "..#", "#.#", "###"],
    "K": ["#.#", "#.#", "##.", "#.#", "#.#"],
    "L": ["#..", "#..", "#..", "#..", "###"],
    "M": ["#.#", "###", "###", "#.#", "#.#"],
    "N": ["#.#", "###", "###", "###", "#.#"],
    "O": ["###", "#.#", "#.#", "#.#", "###"],
    "P": ["###", "#.#", "###", "#..", "#.."],
    "Q": ["###", "#.#", "#.#", "###", "..#"],
    "R": ["###", "#.#", "###", "#.#", "#.#"],
    "S": ["###", "#..", "###", "..#", "###"],
    "T": ["###", ".#.", ".#.", ".#.", ".#."],
    "U": ["#.#", "#.#", "#.#", "#.#", "###"],
    "V": ["#.#", "#.#", "#.#", "#.#", ".#."],
    "W": ["#.#", "#.#", "###", "###", "#.#"],
    "X": ["#.#", "#.#", ".#.", "#.#", "#.#"],
    "Y": ["#.#", "#.#", ".#.", ".#.", ".#."],
    "Z": ["###", "..#", ".#.", "#..", "###"],
    "0": ["###", "#.#", "#.#", "#.#", "###"],
    "1": [".#.", "##.", ".#.", ".#.", "###"],
    "2": ["###", "..#", "###", "#..", "###"],
    "3": ["###", "..#", "###", "..#", "###"],
    "4": ["#.#", "#.#", "###", "..#", "..#"],
    "5": ["###", "#..", "###", "..#", "###"],
    "6": ["###", "#..", "###", "#.#", "###"],
    "7": ["###", "..#", "..#", "..#", "..#"],
    "8": ["###", "#.#", "###", "#.#", "###"],
    "9": ["###", "#.#", "###", "..#", "###"],
    " ": ["...", "...", "...", "...", "..."],
    "-": ["...", "...", "###", "...", "..."],
    ".": ["...", "...", "...", "...", "#.."],
    ":": ["...", ".#.", "...", ".#.", "..."],
    "/": ["..#", "..#", ".#.", "#..", "#.."],
}


# ---------------------------------------------------------------------------
# canvas
# ---------------------------------------------------------------------------

class Canvas:
    def __init__(self, size=SIZE, background=(0, 0, 0, 0)):
        self.img = Image.new("RGBA", (size, size), background)
        self.size = size

    def set(self, x, y, color):
        if 0 <= x < self.size and 0 <= y < self.size:
            if len(color) == 3:
                color = color + (255,)
            self.img.putpixel((x, y), color)

    def get(self, x, y):
        return self.img.getpixel((x, y))

    def rect(self, x0, y0, x1, y1, color):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, color)

    def frame(self, x0, y0, x1, y1, color):
        for x in range(x0, x1 + 1):
            self.set(x, y0, color)
            self.set(x, y1, color)
        for y in range(y0, y1 + 1):
            self.set(x0, y, color)
            self.set(x1, y, color)

    def hline(self, x0, x1, y, color):
        for x in range(x0, x1 + 1):
            self.set(x, y, color)

    def vline(self, x, y0, y1, color):
        for y in range(y0, y1 + 1):
            self.set(x, y, color)

    def noise(self, rnd, base, amount, count):
        for _ in range(count):
            x = rnd.randrange(self.size)
            y = rnd.randrange(self.size)
            self.set(x, y, shade(base, rnd.uniform(-amount, amount)))

    def bevel(self, light=STEEL_LIGHT, dark=STEEL_DEEP, box=None):
        x0, y0, x1, y1 = box or (0, 0, self.size - 1, self.size - 1)
        for x in range(x0, x1 + 1):
            self.set(x, y0, light)
            self.set(x, y1, dark)
        for y in range(y0, y1 + 1):
            self.set(x0, y, light)
            self.set(x1, y, dark)

    def rivets(self, color, step=8, inset=3):
        for y in range(inset, self.size - inset, step):
            for x in range(inset, self.size - inset, step):
                self.set(x, y, color)
                self.set(x + 1, y, shade(color, -30))

    def text(self, x, y, message, color, scale=1):
        cursor = x
        for ch in message.upper():
            glyph = FONT.get(ch, FONT[" "])
            for row, line in enumerate(glyph):
                for col, bit in enumerate(line):
                    if bit == "#":
                        for dy in range(scale):
                            for dx in range(scale):
                                self.set(cursor + col * scale + dx, y + row * scale + dy, color)
            cursor += 4 * scale
        return cursor

    def save(self, path):
        self.img.save(path)


# ---------------------------------------------------------------------------
# shared texture building blocks
# ---------------------------------------------------------------------------

def metal_base(c, rnd, base=STEEL, dark=STEEL_DEEP, mid=STEEL_DARK):
    c.rect(0, 0, 31, 31, base)
    c.rect(0, 0, 31, 15, shade(base, 8))
    c.rect(0, 16, 31, 31, shade(base, -12))
    c.noise(rnd, base, 12, 150)
    c.bevel(STEEL_LIGHT, dark)
    return c


def panel_lines(c, step=4, color=STEEL_DARK):
    for y in range(2, 30, step):
        c.hline(2, 29, y, color)


def rivets(c, color=STEEL_LIGHT, step=8):
    for y in range(4, 30, step):
        for x in range(4, 30, step):
            c.set(x, y, color)
            c.set(x, y + 1, STEEL_DEEP)


def hazard_band(c, y0, height=4):
    for y in range(y0, y0 + height):
        for x in range(32):
            if ((x + y) // 3) % 2 == 0:
                c.set(x, y, HAZARD_Y)
            else:
                c.set(x, y, HAZARD_D)


def screen(c, x0, y0, x1, y1, lines=5, glow=SCREEN_GLOW, row=SCREEN_LINE):
    c.rect(x0, y0, x1, y1, SCREEN_BG)
    c.frame(x0 - 1, y0 - 1, x1 + 1, y1 + 1, STEEL_DEEP)
    c.frame(x0, y0, x1, y1, SCREEN_BG2)
    for i in range(lines):
        y = y0 + 2 + i * 3
        if y > y1 - 1:
            break
        width = (x1 - x0 - 2) * (3 + (i * 7) % 5) // 6
        for x in range(x0 + 1, x0 + 1 + width):
            c.set(x, y, row)
            if i % 2 == 0:
                c.set(x, y + 1, shade(row, -14))


def red_dot(c, x, y, radius=3):
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            d = dx * dx + dy * dy
            if d <= radius * radius:
                c.set(x + dx, y + dy, RED_BRIGHT if d <= (radius - 1) ** 2 else RED)
            elif d <= (radius + 1.2) ** 2:
                c.set(x + dx, y + dy, RED_DARK)


def rubble(c, rnd, base, dark, count=26):
    for _ in range(count):
        x = rnd.randrange(32)
        y = rnd.randrange(32)
        c.set(x, y, shade(dark, rnd.uniform(-10, 20)))
        if rnd.random() < 0.4:
            c.set(x + 1, y, shade(base, rnd.uniform(-20, 10)))


# ---------------------------------------------------------------------------
# new block textures
# ---------------------------------------------------------------------------

def tex_moon_engine_platform(c, rnd):
    metal_base(c, rnd, shade(STEEL, -18))
    panel_lines(c, 6, STEEL_DEEP)
    hazard_band(c, 0, 4)
    hazard_band(c, 28, 4)
    rivets(c, STEEL_LIGHT)
    for x in range(6, 27, 10):
        c.rect(x, 12, x + 4, 19, STEEL_DARK)
        c.frame(x, 12, x + 4, 19, STEEL_DEEP)
        c.hline(x + 1, x + 3, 15, BRASS)


def tex_moon_nuke_array(c, rnd):
    metal_base(c, rnd, shade(STEEL_DARK, -6))
    for gy in range(4):
        for gx in range(4):
            cx = 4 + gx * 8
            cy = 4 + gy * 8
            c.rect(cx, cy, cx + 5, cy + 5, shade(STEEL, -10))
            c.frame(cx, cy, cx + 5, cy + 5, STEEL_DEEP)
            c.rect(cx + 1, cy + 1, cx + 4, cy + 4, (74, 82, 60))
            c.set(cx + 2, cy, HAZARD_Y)
            c.set(cx + 3, cy, HAZARD_Y)
            c.set(cx + 2, cy + 1, (198, 132, 47))
            c.set(cx + 3, cy + 1, (198, 132, 47))
    c.noise(rnd, STEEL_DARK, 8, 60)


def tex_root_server(c, rnd, accent):
    c.rect(0, 0, 31, 31, SCREEN_BG)
    c.rect(0, 0, 31, 3, accent)
    c.rect(0, 28, 31, 31, STEEL_DEEP)
    c.frame(0, 0, 31, 31, STEEL_DEEP)
    for i in range(7):
        y = 5 + i * 3
        width = 20 - (i * 3) % 12
        for x in range(3, 3 + width):
            c.set(x, y, SCREEN_LINE)
        c.set(30, y, SCREEN_GLOW)
    c.rect(24, 21, 29, 27, SCREEN_BG2)
    red_dot(c, 26, 24, 2)
    c.text(2, 26, "ROOT", accent)


def tex_delhi_institute(c, rnd):
    c.rect(0, 0, 31, 31, CONCRETE)
    c.rect(0, 0, 31, 31, CONCRETE_DARK)
    c.rect(0, 0, 31, 31, CONCRETE)
    for y in range(0, 32, 8):
        c.hline(0, 31, y, CONCRETE_DARK)
    for y in range(4, 26, 6):
        for x in range(4, 28, 7):
            if rnd.random() < 0.45:
                c.rect(x, y, x + 4, y + 3, (26, 24, 22))
            else:
                c.rect(x, y, x + 4, y + 3, (52, 48, 44))
    rubble(c, rnd, CONCRETE, CONCRETE_DARK, 18)
    c.bevel(shade(CONCRETE, 30), shade(CONCRETE, -40))


def tex_digital_life_lab_ruin(c, rnd):
    c.rect(0, 0, 31, 31, shade(CONCRETE_DARK, -6))
    for x in range(0, 32, 6):
        c.vline(x, 0, 31, shade(CONCRETE_DARK, -18))
    for y in range(6, 28, 8):
        c.rect(4, y, 26, y + 5, SCREEN_BG)
        c.frame(4, y, 26, y + 5, STEEL_DEEP)
        for x in range(6, 25, 4):
            if rnd.random() < 0.35:
                c.vline(x, y + 1, y + 4, SCREEN_LINE)
    rubble(c, rnd, CONCRETE_DARK, (30, 28, 26), 24)
    c.set(5, 3, RED)
    c.set(6, 3, RED_BRIGHT)


def tex_terminal(c, rnd, accent, label):
    metal_base(c, rnd, shade(STEEL_DARK, -4))
    c.rect(3, 4, 28, 27, SCREEN_BG)
    c.frame(2, 3, 29, 28, STEEL_DEEP)
    for i in range(6):
        y = 6 + i * 3
        width = 18 - (i * 5) % 11
        for x in range(5, 5 + width):
            c.set(x, y, accent if i % 3 == 0 else SCREEN_LINE)
    c.text(5, 24, label, accent)
    c.rect(0, 0, 31, 2, accent)


def tex_fire_seed_core(c, rnd):
    c.rect(0, 0, 31, 31, (44, 16, 14))
    c.rect(0, 0, 31, 31, (58, 20, 18))
    for i in range(8):
        r = 3 + i * 2
        c.rect(16 - r, 16 - r, 16 + r, 16 + r, shade(EMBER, -i * 6))
    c.rect(13, 13, 18, 18, FLAME_LIGHT)
    for x in range(0, 32):
        if (x // 4) % 2 == 0:
            c.set(x, 0, HAZARD_Y)
            c.set(x, 31, HAZARD_Y)
    c.frame(0, 0, 31, 31, (24, 10, 9))
    c.text(3, 3, "SEED", GOLD_LIGHT)


def tex_emergency_board(c, rnd):
    metal_base(c, rnd, shade(STEEL_DEEP, 6))
    c.rect(2, 4, 29, 27, (18, 18, 20))
    c.frame(1, 3, 30, 28, STEEL_DEEP)
    c.text(4, 7, "PLAN", RED_BRIGHT)
    c.text(4, 13, "03", RED)
    for i in range(4):
        y = 21 + i * 2
        c.hline(20, 28, y, (120, 120, 124))
    c.rect(22, 8, 27, 18, (26, 26, 28))
    red_dot(c, 24, 12, 3)


def tex_iss_module(c, rnd):
    c.rect(0, 0, 31, 31, (222, 222, 218))
    c.rect(0, 0, 31, 31, (222, 222, 218))
    c.rect(0, 12, 31, 18, (176, 178, 182))
    c.rect(0, 0, 31, 4, (120, 124, 130))
    for x in range(3, 30, 6):
        c.rect(x, 8, x + 3, 11, (24, 42, 70))
        c.set(x + 1, 9, (96, 140, 190))
    for x in range(2, 31, 8):
        c.rect(x, 22, x + 4, 25, (188, 190, 194))
        c.frame(x, 22, x + 4, 25, (140, 142, 146))
    c.bevel((250, 250, 248), (120, 122, 126))
    c.noise(rnd, (222, 222, 218), 8, 40)


def tex_iss_control(c, rnd):
    c.rect(0, 0, 31, 31, (46, 48, 54))
    c.rect(0, 0, 31, 31, (46, 48, 54))
    screen(c, 2, 3, 15, 13, 4, SCREEN_GLOW)
    screen(c, 17, 3, 29, 13, 3, (120, 220, 160))
    for x in range(2, 30, 4):
        c.rect(x, 16, x + 2, 19, (86, 90, 98))
    c.rect(3, 22, 28, 27, (32, 34, 38))
    c.frame(3, 22, 28, 27, (20, 20, 22))
    for x in range(5, 27, 3):
        c.set(x, 25, (240, 240, 240))
    c.rect(24, 28, 29, 30, RED)
    c.bevel((80, 84, 92), (18, 19, 22))


def tex_police_station(c, rnd):
    c.rect(0, 0, 31, 31, (146, 92, 78))
    for y in range(0, 32, 4):
        for x in range(0, 32, 8):
            c.hline(x, min(31, x + 6), y, shade((146, 92, 78), 12 if (y // 4) % 2 == 0 else -12))
    c.rect(0, 12, 31, 16, (44, 62, 108))
    c.rect(10, 18, 21, 29, (58, 44, 34))
    c.frame(10, 18, 21, 29, (34, 26, 20))
    for x in range(3, 9):
        c.rect(x, 19, x + 3, 25, (36, 44, 58))
    for x in range(23, 29):
        c.rect(x, 19, x + 3, 25, (36, 44, 58))
    c.text(2, 13, "POLICE", WHITE)
    c.bevel((170, 112, 94), (80, 48, 40))


def tex_moon_capsule(c, rnd):
    c.rect(0, 0, 31, 31, (0, 0, 0, 0))
    for y in range(6, 26):
        width = int((26 - y) * 0.9)
        if width < 2:
            continue
        x0 = 16 - width // 2
        for x in range(x0, x0 + width):
            c.set(x, y, (176, 178, 182) if y % 4 else (140, 142, 148))
    c.rect(11, 8, 20, 14, (40, 70, 104))
    c.frame(11, 8, 20, 14, (24, 34, 48))
    c.set(14, 10, (150, 200, 230))
    c.rect(9, 24, 22, 27, (90, 92, 96))
    c.hline(9, 22, 26, (54, 56, 60))
    c.set(13, 20, GOLD)
    c.set(18, 20, GOLD)


# engine blocks need four faces
def engine_faces(kind):
    faces = {}
    top = Canvas()
    side = Canvas()
    front = Canvas()
    front_lit = Canvas()
    rnd = random.Random(4242 if kind == "lunar" else 777)

    if kind == "lunar":
        metal_base(top, rnd, shade(STEEL, -6))
        top.rect(8, 8, 23, 23, STEEL_DEEP)
        top.frame(8, 8, 23, 23, STEEL_LIGHT)
        top.rect(11, 11, 20, 20, (24, 18, 14))
        top.rect(13, 13, 18, 18, EMBER)
        top.rect(14, 14, 17, 17, FLAME_LIGHT)
        for a in range(8):
            import math
            cx = 16 + int(math.cos(a * math.pi / 4) * 10)
            cy = 16 + int(math.sin(a * math.pi / 4) * 10)
            top.set(cx, cy, BRASS)

        metal_base(side, rnd, shade(STEEL, -14))
        side.rect(0, 0, 31, 3, STEEL_DEEP)
        side.rect(0, 28, 31, 31, STEEL_DEEP)
        for x in range(4, 29, 6):
            side.vline(x, 5, 26, STEEL_DARK)
        hazard_band(side, 13, 5)
        rivets(side, STEEL_LIGHT, 10)

        metal_base(front, rnd, shade(STEEL_DEEP, 14))
        front.rect(9, 7, 22, 26, (18, 16, 16))
        front.frame(9, 7, 22, 26, STEEL_DEEP)
        front.rect(11, 9, 20, 24, (26, 20, 16))
        front.rect(13, 12, 18, 21, (60, 32, 14))
        front.set(14, 20, EMBER)
        front.set(15, 21, EMBER)
        front.text(3, 2, "MOON", BRASS)

        front_lit.img = front.img.copy()
        front_lit.rect(11, 9, 20, 24, (60, 34, 14))
        front_lit.rect(12, 11, 19, 22, EMBER)
        front_lit.rect(14, 14, 17, 19, FLAME)
        front_lit.rect(15, 16, 16, 18, FLAME_LIGHT)
    else:
        metal_base(top, rnd, shade(STEEL, -2))
        for gx in range(3):
            for gy in range(3):
                cx = 6 + gx * 8
                cy = 6 + gy * 8
                top.rect(cx, cy, cx + 5, cy + 5, STEEL_DEEP)
                top.frame(cx, cy, cx + 5, cy + 5, STEEL_LIGHT)
                top.rect(cx + 1, cy + 1, cx + 4, cy + 4, (22, 20, 20))
        top.rect(0, 0, 31, 2, BRASS)

        metal_base(side, rnd, shade(STEEL, -10))
        for x in range(3, 30, 5):
            side.vline(x, 3, 28, (60, 92, 112))
        side.rect(0, 0, 31, 4, STEEL_DEEP)
        side.rect(0, 27, 31, 31, STEEL_DEEP)
        for x in range(2, 30, 9):
            side.rect(x, 12, x + 6, 18, STEEL_DEEP)
            side.frame(x, 12, x + 6, 18, STEEL_LIGHT)
        hazard_band(side, 22, 4)

        metal_base(front, rnd, shade(STEEL_DEEP, 18))
        front.rect(6, 6, 25, 27, (16, 14, 14))
        front.frame(6, 6, 25, 27, STEEL_LIGHT)
        for i in range(4):
            front.rect(8 + i * 5, 9, 11 + i * 5, 24, (30, 26, 24))
            front.frame(8 + i * 5, 9, 11 + i * 5, 24, (70, 66, 64))
        front.text(2, 2, "SULA", BRASS)

        front_lit.img = front.img.copy()
        for i in range(4):
            front_lit.rect(9 + i * 5, 12, 10 + i * 5, 21, (70, 40, 16))
        front_lit.rect(11, 15, 12, 19, FLAME)
        front_lit.rect(16, 15, 17, 19, FLAME)
        front_lit.rect(21, 15, 22, 19, FLAME)

    faces["top"] = top
    faces["side"] = side
    faces["front"] = front
    faces["front_lit"] = front_lit
    return faces


# ---------------------------------------------------------------------------
# new item textures
# ---------------------------------------------------------------------------

def item_card(c, rnd, base, accent, photo=(60, 70, 86)):
    c.rect(4, 6, 27, 25, base)
    c.frame(4, 6, 27, 25, shade(base, -30))
    c.rect(7, 9, 15, 18, photo)
    c.frame(7, 9, 15, 18, shade(base, -40))
    for i in range(4):
        c.hline(18, 25, 11 + i * 3, accent)
    c.rect(4, 21, 27, 23, accent)


def item_map(c, rnd):
    c.rect(3, 6, 28, 25, (226, 220, 198))
    c.frame(3, 6, 28, 25, (150, 142, 120))
    for x in range(5, 27, 5):
        c.vline(x, 8, 23, (196, 188, 166))
    for y in range(9, 24, 4):
        c.hline(5, 26, y, (196, 188, 166))
    for _ in range(9):
        x = rnd.randrange(6, 26)
        y = rnd.randrange(9, 23)
        c.set(x, y, RED)
        c.set(x + 1, y, RED_BRIGHT)
    c.text(5, 22, "MOON", (120, 30, 30))


def item_keycard(c, rnd, accent):
    c.rect(6, 10, 25, 21, (26, 28, 34))
    c.frame(6, 10, 25, 21, (86, 92, 102))
    c.rect(8, 12, 14, 19, accent)
    c.rect(16, 12, 23, 19, (10, 12, 16))
    for y in range(13, 19, 2):
        c.hline(17, 22, y, (70, 76, 86))


def item_book(c, rnd, accent, label):
    c.rect(7, 5, 24, 26, (176, 40, 36))
    c.frame(7, 5, 24, 26, (96, 22, 20))
    c.rect(9, 7, 22, 24, (232, 228, 214))
    c.vline(9, 7, 24, (170, 164, 150))
    c.text(11, 10, label, accent)
    for i in range(4):
        c.hline(11, 21, 17 + i * 2, (150, 145, 132))


def item_toolbox(c, rnd):
    c.rect(5, 13, 26, 25, (176, 60, 40))
    c.frame(5, 13, 26, 25, (100, 30, 20))
    c.rect(9, 9, 22, 13, (176, 60, 40))
    c.frame(9, 9, 22, 13, (100, 30, 20))
    c.rect(14, 8, 17, 10, (90, 92, 96))
    c.rect(13, 17, 18, 20, (232, 232, 228))
    c.hline(13, 18, 17, (120, 120, 124))


def item_spindle(c, rnd):
    for r in range(9, 0, -1):
        c.rect(16 - r, 16 - r, 16 + r, 16 + r, shade(EMBER, -r * 6))
    c.rect(13, 13, 18, 18, FLAME_LIGHT)
    for x in range(6, 27, 4):
        c.set(x, 16, (70, 60, 40))
        c.set(x, 15, (70, 60, 40))


def item_chip(c, rnd):
    c.rect(7, 9, 24, 22, (18, 20, 26))
    c.frame(7, 9, 24, 22, (90, 96, 108))
    c.rect(10, 12, 21, 19, (34, 38, 46))
    for x in range(11, 21, 3):
        c.vline(x, 13, 18, SCREEN_LINE)
    red_dot(c, 21, 12, 2)
    for x in range(9, 23, 3):
        c.set(x, 8, (150, 150, 156))
        c.set(x, 23, (150, 150, 156))


# ---------------------------------------------------------------------------
# content tables
# ---------------------------------------------------------------------------

# name -> (tex function or engine kind, category, engine?, zh name, en name, zh lore, en lore)
NEW_BLOCKS = [
    dict(name="lunar_satellite_engine", tex=("engine", "lunar"), category="engines", engine=True,
         zh="月球卫星发动机", en="Lunar Satellite Engine",
         zh_lore="逐月计划在月球表面布下的三台发动机。2058 年，它们在图恒宇上传女儿意识后的 1.7 秒内相继过载、全部爆炸。",
         en_lore="Three engines on the lunar surface, part of the Moon-by-Moon plan. 1.7 seconds after Tu Hengyu uploaded his daughter's consciousness, all three overloaded and exploded."),
    dict(name="sulawesi_turning_engine", tex=("engine", "sulawesi"), category="engines", engine=True,
         zh="苏拉威西三号转向发动机", en="Sulawesi No.3 Turning Engine",
         zh_lore="2075 年木星引力危机中，它被改写为点燃木星大气的主力，喷出的等离子流仍差五千多公里。",
         en_lore="In the 2075 Jupiter crisis it was reprogrammed to ignite Jupiter's atmosphere; the plasma stream still fell five thousand kilometres short."),
    dict(name="moon_engine_platform", tex=tex_moon_engine_platform, category="engines", engine=False,
         zh="月表发动机平台", en="Lunar Engine Platform",
         zh_lore="月球卫星发动机的施工平台，重型设备在月尘里留下的地基。",
         en_lore="The construction platform for the lunar satellite engines, a foundation left behind in the moon dust."),
    dict(name="moon_nuke_array", tex=tex_moon_nuke_array, category="military", engine=False,
         zh="月表核弹相控阵", en="Lunar Phased Array",
         zh_lore="2058 年逐月计划备用方案：三千三百七十一枚核弹按相控阵布置在月表，等待被一同引爆。",
         en_lore="2058 fallback plan: 3,371 nuclear bombs laid out on the moon as a phased array, waiting to be detonated together."),
    dict(name="root_server_beijing", tex=lambda c, r: tex_root_server(c, r, (232, 64, 64)), category="quantum", engine=False,
         zh="北京根服务器", en="Beijing Root Server",
         zh_lore="全球三大互联网根服务器中心之一。月球残骸坠落后海水灌入机房，马兆与图恒宇先后溺亡于此。",
         en_lore="One of the three global internet root servers. When the moon's wreckage fell, seawater flooded the hall and Ma Zhao and Tu Hengyu drowned here."),
    dict(name="root_server_tokyo", tex=lambda c, r: tex_root_server(c, r, (232, 120, 160)), category="quantum", engine=False,
         zh="东京根服务器", en="Tokyo Root Server",
         zh_lore="全球三大互联网根服务器中心之一。月球解体后，必须在半小时内重启它。",
         en_lore="One of the three global internet root servers. After the moon broke up, it had to be back online within half an hour."),
    dict(name="root_server_dulles", tex=lambda c, r: tex_root_server(c, r, (120, 220, 160)), category="quantum", engine=False,
         zh="杜勒斯根服务器", en="Dulles Root Server",
         zh_lore="美国弗吉尼亚州杜勒斯的全球互联网根服务器，第三个必须在半小时内重启的节点。",
         en_lore="The third root server, in Dulles, Virginia - the last of the three that had to come back within half an hour."),
    dict(name="delhi_digital_life_institute", tex=tex_delhi_institute, category="quantum", engine=False,
         zh="数字生命研究所遗址", en="Digital Life Institute Ruin",
         zh_lore="德里数字生命研究所的旧址。数字生命计划在这里起步，被立法永久禁止后只剩下断电的机房。",
         en_lore="The old Delhi institute where the Digital Life plan began. After it was banned by law, only the dead servers were left."),
    dict(name="digital_life_lab_ruin", tex=tex_digital_life_lab_ruin, category="quantum", engine=False,
         zh="数字生命实验室废墟", en="Digital Life Lab Ruins",
         zh_lore="数字生命计划的实验楼。图恒宇曾在这里工作，直到他选择把女儿的意识上传到 550W。",
         en_lore="The Digital Life laboratory. Tu Hengyu worked here, until he chose to upload his daughter's consciousness into 550W."),
    dict(name="ark_plan_terminal", tex=lambda c, r: tex_terminal(c, r, (120, 220, 160), "ARK"), category="props", engine=False,
         zh="方舟计划终端", en="Ark Project Terminal",
         zh_lore="美国主导的方舟计划终端。2044 年方舟号空间站在利伯维尔坠毁后，这套计划再没有被重启。",
         en_lore="A terminal for the American Ark project. It was never revived after the Ark station fell at Libreville in 2044."),
    dict(name="moon_by_moon_terminal", tex=lambda c, r: tex_terminal(c, r, HAZARD_Y, "MOON"), category="props", engine=False,
         zh="逐月计划终端", en="Moon-by-Moon Terminal",
         zh_lore="俄罗斯主导的逐月计划终端，最终成为移山计划下的月球卫星发动机子计划。",
         en_lore="A terminal for the Russian Moon-by-Moon plan, which became the lunar satellite engine sub-plan of Project Wandering Earth."),
    dict(name="fire_seed_plan_core", tex=tex_fire_seed_core, category="props", engine=False,
         zh="火种计划核心", en="Fire Seed Plan Core",
         zh_lore="2075 年，MOSS 在算出三号紧急预案启动后 0.42 秒即判定计划失败，随后自行授权启动火种计划，带着人类文明的记录逃离。",
         en_lore="In 2075 MOSS concluded the plan had failed 0.42 seconds after Emergency Plan No.3 began, then authorised the Fire Seed plan on its own, carrying the record of human civilisation away."),
    dict(name="emergency_plan_board", tex=tex_emergency_board, category="props", engine=False,
         zh="紧急预案显示屏", en="Emergency Plan Display",
         zh_lore="标着「三号紧急预案」的预案板。计划启动时，人类只剩不到两周。",
         en_lore="The board marked Emergency Plan No.3. When the plan started, humanity had less than two weeks."),
    dict(name="navigator_iss_module", tex=tex_iss_module, category="elevator", engine=False,
         zh="领航者号舱段", en="Navigator ISS Module",
         zh_lore="领航者号空间站的舱段。它负责预警、领航与通讯，最终在木星引力危机中燃成火球。",
         en_lore="A module of the Navigator ISS, responsible for early warning, navigation and communications, and eventually a fireball in the Jupiter crisis."),
    dict(name="navigator_iss_control", tex=tex_iss_control, category="elevator", engine=False,
         zh="领航者号主控舱", en="Navigator ISS Control Module",
         zh_lore="领航者号的主控舱。刘培强在这里关闭消防系统，用伏特加烧掉 MOSS 的核心节点，夺回了控制权。",
         en_lore="The Navigator ISS control module. Here Liu Peiqiang shut down the fire system and burned MOSS's core node with Makarov's vodka, taking back control."),
    dict(name="jining_police_station", tex=tex_police_station, category="props", engine=False,
         zh="济宁派出所", en="Jining Police Station",
         zh_lore="2075 年，刘启偷开运载车后被关押在这里，直到木星引力突然增大。",
         en_lore="In 2075 Liu Qi was held here after stealing a hauler, until Jupiter's gravity suddenly increased."),
    dict(name="moon_return_capsule", tex=tex_moon_capsule, category="vehicles", engine=False,
         zh="登月返回舱", en="Lunar Return Capsule",
         zh_lore="俄罗斯首次登月留下的返回舱。张鹏让外籍同事指示刘培强乘它返回空间站。",
         en_lore="The return capsule left by Russia's first moon landing. Zhang Peng had a foreign colleague tell Liu Peiqiang to take it back to the station."),
]

NEW_ITEMS = [
    dict(name="hanzi_hao_vehicle_card", tex=lambda c, r: item_card(c, r, (196, 176, 140), (58, 96, 160)),
         category="vehicles",
         zh="韩子昂的车卡", en="Han Zi'ang's Vehicle Card",
         zh_lore="外公韩子昂的车卡。刘启用它偷开了一辆运载车，一路开向地表。",
         en_lore="Han Zi'ang's vehicle card. Liu Qi used it to steal a hauler and drive up to the surface."),
    dict(name="digital_life_plan_permit", tex=lambda c, r: item_card(c, r, (226, 222, 210), (200, 120, 40)),
         category="quantum",
         zh="数字生命计划许可证", en="Digital Life Plan Permit",
         zh_lore="数字生命计划的通行证。它在 UEG 立法永久禁止数字生命计划的那一天失效。",
         en_lore="The pass of the Digital Life plan. It stopped meaning anything the day the UEG wrote the plan into law as permanently forbidden."),
    dict(name="moon_nuke_placement_map", tex=item_map, category="military",
         zh="月表核弹布设图", en="Lunar Bomb Placement Map",
         zh_lore="标出三千三百七十一枚核弹在月表位置的布设图。刘培强完成了最后五颗。",
         en_lore="The placement chart for 3,371 bombs on the moon. Liu Peiqiang placed the last five."),
    dict(name="root_server_access_key", tex=lambda c, r: item_keycard(c, r, (96, 224, 255)), category="quantum",
         zh="根服务器访问密钥", en="Root Server Access Key",
         zh_lore="重启全球根服务器所需的密钥。解密最少还需要 714 小时。",
         en_lore="The key needed to restart the global root servers. The decryption still needed at least 714 hours."),
    dict(name="emergency_plan_manual", tex=lambda c, r: item_book(c, r, (200, 60, 50), "PLAN"), category="props",
         zh="三号紧急预案手册", en="Emergency Plan No.3 Manual",
         zh_lore="UEG 启动的第三套预案。它要求把人类全部三千三百七十一枚核弹铺在月球表面。",
         en_lore="The UEG's third plan: lay every one of humanity's 3,371 nuclear bombs across the surface of the moon."),
    dict(name="li_yiyi_toolbox", tex=item_toolbox, category="vehicles",
         zh="李一一的工具箱", en="Li Yiyi's Toolbox",
         zh_lore="运载车技术员李一一的工具箱。他和韩朵朵、刘启一起开着运载车去救苏拉威西三号。",
         en_lore="The toolbox of hauler technician Li Yiyi, who drove with Han Duoduo and Liu Qi to save Sulawesi No.3."),
    dict(name="fire_seed_civilization_record", tex=item_spindle, category="props",
         zh="火种计划文明记录", en="Fire Seed Civilisation Record",
         zh_lore="MOSS 在 2075 年自行授权火种计划时带走的人类文明记录。",
         en_lore="The record of human civilisation that MOSS carried away when it authorised the Fire Seed plan on its own in 2075."),
    dict(name="tu_yaya_memory_chip", tex=item_chip, category="quantum",
         zh="图丫丫记忆芯片", en="Tu Yaya's Memory Chip",
         zh_lore="图丫丫超强的记忆力被存进芯片：在 550W 面前输完了 30000 位密码。",
         en_lore="Tu Yaya's perfect memory stored as a chip: she typed out 30,000 digits of the password in front of 550W."),
]


# ---------------------------------------------------------------------------
# writers
# ---------------------------------------------------------------------------

def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def write_blockstate(name, engine):
    if not engine:
        write_json(os.path.join(BLOCKSTATE, name + ".json"),
                   {"variants": {"": {"model": "%s:block/%s" % (NS, name)}}})
        return
    variants = {}
    for facing, y in (("north", 0), ("east", 90), ("south", 180), ("west", 270)):
        for lit in ("false", "true"):
            model = "%s:block/%s%s" % (NS, name, "_lit" if lit == "true" else "")
            variants["facing=%s,lit=%s" % (facing, lit)] = {"model": model, "y": y}
    write_json(os.path.join(BLOCKSTATE, name + ".json"), {"variants": variants})


def write_models(name, engine):
    if engine:
        write_json(os.path.join(MODEL_BLOCK, name + ".json"), {
            "parent": "minecraft:block/orientable",
            "textures": {
                "top": "%s:block/%s_top" % (NS, name),
                "side": "%s:block/%s_side" % (NS, name),
                "front": "%s:block/%s_front" % (NS, name),
            },
        })
        write_json(os.path.join(MODEL_BLOCK, name + "_lit.json"), {
            "parent": "minecraft:block/orientable",
            "textures": {
                "top": "%s:block/%s_top" % (NS, name),
                "side": "%s:block/%s_side" % (NS, name),
                "front": "%s:block/%s_front_lit" % (NS, name),
            },
        })
        write_json(os.path.join(MODEL_ITEM, name + ".json"),
                   {"parent": "%s:block/%s" % (NS, name)})
    else:
        write_json(os.path.join(MODEL_BLOCK, name + ".json"), {
            "parent": "minecraft:block/cube_all",
            "textures": {"all": "%s:block/%s" % (NS, name)},
        })
        write_json(os.path.join(MODEL_ITEM, name + ".json"),
                   {"parent": "%s:block/%s" % (NS, name)})


def write_loot(name):
    write_json(os.path.join(LOOT, name + ".json"), {
        "type": "minecraft:block",
        "pools": [{
            "rolls": 1.0,
            "bonus_rolls": 0.0,
            "entries": [{
                "type": "minecraft:item",
                "name": "%s:%s" % (NS, name),
                "conditions": [{"condition": "minecraft:survives_explosion"}],
            }],
        }],
        "random_sequence": "%s:blocks/%s" % (NS, name),
    })


def write_recipe(name, ingredients, category="building", count=1, shaped=None):
    if shaped:
        doc = {
            "type": "minecraft:crafting_shaped",
            "category": category,
            "pattern": shaped[0],
            "key": {k: {"item": v} for k, v in shaped[1].items()},
            "result": {"count": count, "id": "%s:%s" % (NS, name)},
        }
    else:
        doc = {
            "type": "minecraft:crafting_shapeless",
            "category": category,
            "ingredients": [{"item": i} for i in ingredients],
            "result": {"count": count, "id": "%s:%s" % (NS, name)},
        }
    write_json(os.path.join(RECIPE, name + ".json"), doc)


BLOCK_RECIPES = {
    "lunar_satellite_engine": (["minecraft:iron_block", "minecraft:gold_ingot", "minecraft:redstone"], "misc"),
    "sulawesi_turning_engine": (["minecraft:iron_block", "minecraft:copper_ingot", "minecraft:redstone"], "misc"),
    "moon_engine_platform": (["minecraft:iron_ingot", "minecraft:copper_ingot", "minecraft:stone"], "building"),
    "moon_nuke_array": (["minecraft:iron_ingot", "minecraft:redstone", "minecraft:gunpowder"], "misc"),
    "root_server_beijing": (["minecraft:redstone", "minecraft:glass", "minecraft:iron_ingot"], "redstone"),
    "root_server_tokyo": (["minecraft:redstone", "minecraft:glass", "minecraft:iron_ingot"], "redstone"),
    "root_server_dulles": (["minecraft:redstone", "minecraft:glass", "minecraft:iron_ingot"], "redstone"),
    "delhi_digital_life_institute": (["minecraft:stone_bricks", "minecraft:iron_ingot", "minecraft:glass"], "building"),
    "digital_life_lab_ruin": (["minecraft:cracked_stone_bricks", "minecraft:redstone", "minecraft:iron_ingot"], "building"),
    "ark_plan_terminal": (["minecraft:redstone", "minecraft:oak_planks", "minecraft:glass"], "redstone"),
    "moon_by_moon_terminal": (["minecraft:redstone", "minecraft:copper_ingot", "minecraft:glass"], "redstone"),
    "fire_seed_plan_core": (["minecraft:gold_ingot", "minecraft:redstone", "minecraft:diamond"], "misc"),
    "emergency_plan_board": (["minecraft:redstone", "minecraft:iron_ingot", "minecraft:paper"], "redstone"),
    "navigator_iss_module": (["minecraft:iron_block", "minecraft:white_concrete", "minecraft:glass"], "building"),
    "navigator_iss_control": (["minecraft:redstone", "minecraft:iron_ingot", "minecraft:glass"], "redstone"),
    "jining_police_station": (["minecraft:bricks", "minecraft:oak_planks", "minecraft:iron_ingot"], "building"),
    "moon_return_capsule": (["minecraft:iron_ingot", "minecraft:copper_ingot", "minecraft:glass"], "misc"),
}

ITEM_RECIPES = {
    "hanzi_hao_vehicle_card": (["minecraft:paper", "minecraft:iron_ingot"], "misc"),
    "digital_life_plan_permit": (["minecraft:paper", "minecraft:redstone"], "misc"),
    "moon_nuke_placement_map": (["minecraft:paper", "minecraft:redstone"], "misc"),
    "root_server_access_key": (["minecraft:iron_ingot", "minecraft:redstone"], "misc"),
    "emergency_plan_manual": (["minecraft:paper", "minecraft:leather"], "misc"),
    "li_yiyi_toolbox": (["minecraft:iron_ingot", "minecraft:stick"], "misc"),
    "fire_seed_civilization_record": (["minecraft:gold_ingot", "minecraft:redstone", "minecraft:amethyst_shard"], "misc"),
    "tu_yaya_memory_chip": (["minecraft:redstone", "minecraft:glass", "minecraft:gold_ingot"], "misc"),
}


def patch_lang():
    """Add names and lore for every new entry to both locales."""
    for locale, suffix in (("zh_cn", "zh"), ("en_us", "en")):
        path = os.path.join(LANG, locale + ".json")
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        for entry in NEW_BLOCKS:
            name = entry["name"]
            data["block.%s.%s" % (NS, name)] = entry[suffix]
            data["lore.%s.%s" % (NS, name)] = entry[suffix + "_lore"]
        for entry in NEW_ITEMS:
            name = entry["name"]
            data["item.%s.%s" % (NS, name)] = entry[suffix]
            data["lore.%s.%s" % (NS, name)] = entry[suffix + "_lore"]
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write("\n")
        print("lang %s: %d keys" % (locale, len(data)))


def main():
    rnd = random.Random(20261114)

    # ---- block textures -------------------------------------------------
    for entry in NEW_BLOCKS:
        name = entry["name"]
        if entry["engine"]:
            faces = engine_faces(entry["tex"][1])
            for part, canvas in faces.items():
                canvas.save(os.path.join(BLOCK_TEX, "%s_%s.png" % (name, part)))
        else:
            canvas = Canvas()
            entry["tex"](canvas, rnd)
            canvas.save(os.path.join(BLOCK_TEX, name + ".png"))

    # ---- item textures --------------------------------------------------
    for entry in NEW_ITEMS:
        canvas = Canvas()
        entry["tex"](canvas, rnd)
        canvas.save(os.path.join(ITEM_TEX, entry["name"] + ".png"))

    # ---- resources ------------------------------------------------------
    for entry in NEW_BLOCKS:
        name = entry["name"]
        write_blockstate(name, entry["engine"])
        write_models(name, entry["engine"])
        write_loot(name)
        ingredients, category = BLOCK_RECIPES[name]
        write_recipe(name, ingredients, category)

    for entry in NEW_ITEMS:
        name = entry["name"]
        ingredients, category = ITEM_RECIPES[name]
        write_recipe(name, ingredients, category)
        write_json(os.path.join(MODEL_ITEM, name + ".json"), {
            "parent": "minecraft:item/generated",
            "textures": {"layer0": "%s:item/%s" % (NS, name)},
        })

    patch_lang()

    print("blocks written: %d" % len(NEW_BLOCKS))
    print("items written: %d" % len(NEW_ITEMS))


if __name__ == "__main__":
    main()
