import pygame  # ייבוא ספריית המשחקים פייטגיים
import random  # מספרים אקראיים
import math  # מתמטיקה (גלים, סיבובים)
import json  # שמירה וקריאה של קובץ השמירה
import os  # נתיבי קבצים
import io  # קריאת תמונה מהזיכרון
import base64  # פענוח התמונות המוטמעות
from collections import namedtuple  # מבנה נתונים לשלבים וסקינים

# ---------- תמונות הסקינים ----------
# אם יש לך את רשימת SKIN_DATA, אפשר להדביק אותה כאן במקום הסוגריים הריקים.
# אם משאירים ריק, המשחק מחפש אותה לבד בקבצי .py אחרים שנמצאים באותה תיקייה
# (למשל גיבוי של הקובץ המקורי שלך), ואם לא מוצא - המשחק עדיין עובד, רק בלי תמונות סקינים.
SKIN_DATA = []


def _load_skin_data():
    import ast
    import glob
    here = os.path.dirname(os.path.abspath(__file__))
    me = os.path.abspath(__file__)
    for path in glob.glob(os.path.join(here, "*.py")):
        if os.path.abspath(path) == me:
            continue
        try:
            with open(path, "r", encoding="utf-8") as fh:
                src = fh.read()
            if "SKIN_DATA" not in src:
                continue
            for node in ast.parse(src).body:
                if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "SKIN_DATA" for t in node.targets):
                    data = ast.literal_eval(node.value)
                    if data:
                        return data
        except Exception:
            continue
    return []


if not SKIN_DATA:
    SKIN_DATA = _load_skin_data()
    if not SKIN_DATA:
        print("Note: SKIN_DATA not found - skins will have no images.")

pygame.init()
pygame.font.init()

WIDTH, HEIGHT = 400, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Spider Adventure")

# ================== הגדרות לבדיקה ==================
# שנה כדי להתחיל מניקוד גבוה. 30000 = רקע 1, 55000 = רקע 6, 225000 = רקע 40. להחזיר ל-0 למשחק רגיל.
DEBUG_START_SCORE = 0
# לבדיקת החנות: אם גדול מ-0, הנקודות בבנק לא ירדו מתחתיו. להחזיר ל-0 למשחק רגיל.
DEBUG_MIN_POINTS = 0

# צבעים
SKY_BLUE = (135, 206, 235)
PURPLE_SPACE = (75, 0, 130)
SPACE_BLACK = (5, 5, 15)
VALENTINE_PINK = (255, 150, 180)
LAVA_RED = (180, 40, 10)
ICE_BLUE = (170, 220, 255)
PURPLE_BG = (140, 50, 150)
ORANGE_POISON = (255, 140, 0)
GRASS_GREEN = (34, 139, 34)
DIRT_BROWN = (139, 69, 19)
DIRT_SHADOW = (100, 45, 10)
RADIOACTIVE_GREEN = (30, 255, 50)
BUBBLE_COLOR = (150, 255, 150)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (230, 30, 30)
STAR_COLOR = (255, 255, 200)
SPIDER_BLACK = (15, 15, 15)
BOOSTER_YELLOW = (255, 235, 0)
BOOSTER_RED = (230, 30, 30)
BOOSTER_ORANGE = (255, 130, 0)
BUTTON_COLOR = (50, 205, 50)
HEART_RED = (255, 50, 80)


class Platform:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 75
        self.height = 16


class Booster:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 18
        self.active = True


class CollectibleHeart:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 16
        self.active = True


class Bubble:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = random.randint(3, 7)
        self.speed = random.uniform(1.0, 2.0)


class Star:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = random.randint(1, 3)


class HeartDeco:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = random.randint(8, 16)
        self.color = random.choice([(255, 30, 80), (255, 80, 120), (255, 0, 60)])


class LavaRock:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = random.randint(10, 25)


class IceCrystal:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = random.randint(8, 16)


class DecoParticle:
    """חלקיק קישוט כללי לרקעים החדשים (שלג, גשם, עלים, ניצוצות וכו')"""
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.size = random.randint(2, 6)
        self.idx = random.randint(0, 5)
        self.phase = random.uniform(0, 6.28)


score = 0
high_score = 0
saved_hearts = 0
next_heart_score = 30000


def reset_game(keep_hearts=False):
    global platforms, player_x, player_y, player_y_velocity, water_y, score, water_speed, boosters, next_booster_score, high_score, bubbles, stars, hearts, lava_rocks, ice_crystals, collectible_hearts, next_heart_score, saved_hearts, deco
    if not keep_hearts:
        if score > high_score:
            high_score = score
        score = 0
        saved_hearts = 0
        next_heart_score = 30000

    platforms = []
    for i in range(8):
        p_x = random.randint(20, WIDTH - 95)
        p_y = i * 70 + 50
        platforms.append(Platform(p_x, p_y))

    player_x = platforms[5].x + 20
    player_y = platforms[5].y - 40
    player_y_velocity = 0
    water_y = HEIGHT
    water_speed = 1.2
    boosters = []
    collectible_hearts = []
    bubbles = []

    stars = [Star(random.randint(0, WIDTH), random.randint(-1000, 0)) for _ in range(35)]
    hearts = [HeartDeco(random.randint(20, WIDTH - 20), random.randint(-1500, 0)) for _ in range(14)]
    lava_rocks = [LavaRock(random.randint(20, WIDTH - 20), random.randint(-1500, 0)) for _ in range(10)]
    ice_crystals = [IceCrystal(random.randint(20, WIDTH - 20), random.randint(-1500, 0)) for _ in range(12)]
    deco = [DecoParticle() for _ in range(32)]

    next_booster_score = 750


reset_game()

player_width = 34
player_height = 26
gravity = 0.4
jump_strength = -10
super_jump_strength = -22

font = pygame.font.SysFont(None, 30)
title_font = pygame.font.SysFont(None, 40)
countdown_font = pygame.font.SysFont(None, 80)
clock = pygame.time.Clock()

fog_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)  # משטח שקוף לאפקט ערפל

# =====================================================================
#                      40 הרקעים החדשים (כל אחד 5000 נקודות)
# =====================================================================
THEME_START = 30000
THEME_LEN = 5000


def lerp_color(c1, c2, f):
    f = max(0.0, min(1.0, f))
    return (int(c1[0] + (c2[0] - c1[0]) * f),
            int(c1[1] + (c2[1] - c1[1]) * f),
            int(c1[2] + (c2[2] - c1[2]) * f))


def dark(c, f=0.4):
    return (int(c[0] * f), int(c[1] * f), int(c[2] * f))


# ---------------------------- פלטפורמות ----------------------------
def plat_sand(x, y, w, h, c):
    pygame.draw.rect(screen, c[0], (x, y, w, h), border_radius=8)
    pygame.draw.rect(screen, c[1], (x, y, w, h), 2, border_radius=8)
    pygame.draw.arc(screen, c[2], (x + 6, y + 2, 30, 14), 0, 3.14, 2)
    pygame.draw.arc(screen, c[2], (x + 40, y + 2, 28, 14), 0, 3.14, 2)


def plat_leaf(x, y, w, h, c):
    pygame.draw.ellipse(screen, c[0], (x, y, w, h))
    pygame.draw.ellipse(screen, c[1], (x, y, w, h), 2)
    pygame.draw.line(screen, c[2], (x + 8, y + h // 2), (x + w - 8, y + h // 2), 2)
    for i in range(1, 4):
        pygame.draw.line(screen, c[2], (x + i * w // 4, y + h // 2), (x + i * w // 4 + 6, y + 3), 1)


def plat_coral(x, y, w, h, c):
    pygame.draw.rect(screen, c[0], (x, y + 6, w, h - 6), border_radius=5)
    for i in range(5):
        bx = x + 8 + i * 14
        top = y + (1 if i % 2 else 3)
        pygame.draw.line(screen, c[1], (bx, y + 8), (bx, top), 4)
        pygame.draw.circle(screen, c[2], (bx, top), 3)


def plat_candy(x, y, w, h, c):
    pygame.draw.rect(screen, c[1], (x, y, w, h), border_radius=8)
    for i in range(4, w - 20, 14):
        pygame.draw.polygon(screen, c[0], [(x + i, y + h - 2), (x + i + 8, y + 2), (x + i + 16, y + 2), (x + i + 8, y + h - 2)])
    pygame.draw.rect(screen, c[2], (x, y, w, h), 2, border_radius=8)


def plat_neon(x, y, w, h, c):
    pygame.draw.rect(screen, c[0], (x, y, w, h), border_radius=4)
    pygame.draw.rect(screen, c[1], (x, y, w, h), 2, border_radius=4)
    pygame.draw.line(screen, c[2], (x + 6, y + h // 2), (x + w - 6, y + h // 2), 2)
    pygame.draw.line(screen, c[1], (x - 3, y + h + 2), (x + w + 3, y + h + 2), 1)


def plat_wood(x, y, w, h, c):
    pygame.draw.rect(screen, c[0], (x, y, w, h), border_radius=3)
    pygame.draw.rect(screen, c[1], (x, y, w, h), 2, border_radius=3)
    pygame.draw.line(screen, c[1], (x + 2, y + h // 2), (x + w - 2, y + h // 2), 1)
    for nx in (x + 6, x + w - 7):
        pygame.draw.circle(screen, c[2], (nx, y + 4), 2)
        pygame.draw.circle(screen, c[2], (nx, y + h - 5), 2)


def plat_plank(x, y, w, h, c):
    for i in range(3):
        bx = x + i * w // 3
        pygame.draw.rect(screen, c[0], (bx, y, w // 3 - 1, h))
        pygame.draw.rect(screen, c[1], (bx, y, w // 3 - 1, h), 1)
    pygame.draw.rect(screen, c[2], (x, y + h - 3, w, 3))


def plat_metal(x, y, w, h, c):
    pygame.draw.rect(screen, c[0], (x, y, w, h), border_radius=4)
    pygame.draw.rect(screen, c[1], (x, y, w, h), 2, border_radius=4)
    for rx in (x + 6, x + w // 3, x + 2 * w // 3, x + w - 7):
        pygame.draw.circle(screen, c[2], (rx, y + h // 2), 2)
    pygame.draw.line(screen, c[2], (x + 4, y + 2), (x + w - 4, y + 2), 1)


def plat_magma(x, y, w, h, c):
    pygame.draw.rect(screen, c[0], (x, y, w, h), border_radius=5)
    pygame.draw.rect(screen, c[1], (x, y, w, h), 2, border_radius=5)
    pygame.draw.lines(screen, c[2], False, [(x + 4, y + 8), (x + 18, y + 4), (x + 30, y + 11), (x + 45, y + 5), (x + 58, y + 12), (x + w - 4, y + 7)], 2)


def plat_crystal(x, y, w, h, c):
    pygame.draw.rect(screen, c[1], (x, y + 8, w, h - 8), border_radius=4)
    for i, px in enumerate((x + 3, x + 26, x + 49)):
        col = c[0] if i % 2 == 0 else c[2]
        pygame.draw.polygon(screen, col, [(px, y + h - 2), (px + 11, y), (px + 22, y + h - 2)])
        pygame.draw.polygon(screen, c[1], [(px, y + h - 2), (px + 11, y), (px + 22, y + h - 2)], 1)


def plat_bamboo(x, y, w, h, c):
    pygame.draw.rect(screen, c[0], (x, y + 2, w, h - 4), border_radius=6)
    pygame.draw.rect(screen, c[1], (x, y + 2, w, h - 4), 2, border_radius=6)
    for nx in range(x + 18, x + w - 8, 18):
        pygame.draw.line(screen, c[1], (nx, y + 2), (nx, y + h - 3), 2)
    pygame.draw.line(screen, c[2], (x + 5, y + 6), (x + 14, y + 6), 2)


def plat_cloud(x, y, w, h, c):
    for cx, r in ((x + 14, 7), (x + 30, 8), (x + 48, 8), (x + w - 10, 7)):
        pygame.draw.circle(screen, c[0], (cx, y + h - r), r)
    pygame.draw.rect(screen, c[0], (x + 10, y + h - 8, w - 20, 8))
    pygame.draw.line(screen, c[1], (x + 8, y + h - 1), (x + w - 8, y + h - 1), 2)
    pygame.draw.ellipse(screen, c[2], (x + w // 2 - 12, y - 5, 24, 6), 1)


def plat_gold(x, y, w, h, c):
    pygame.draw.rect(screen, c[0], (x, y, w, h), border_radius=4)
    pygame.draw.rect(screen, c[1], (x, y, w, h), 2, border_radius=4)
    pygame.draw.line(screen, c[2], (x + 6, y + 4), (x + w - 30, y + 4), 2)
    for gx in (x + 20, x + w // 2, x + w - 20):
        pygame.draw.polygon(screen, c[1], [(gx, y + 7), (gx + 4, y + 11), (gx, y + 15), (gx - 4, y + 11)], 1)


def plat_circuit(x, y, w, h, c):
    pygame.draw.rect(screen, c[0], (x, y, w, h), border_radius=3)
    pygame.draw.rect(screen, c[1], (x, y, w, h), 2, border_radius=3)
    pts = [(x + 4, y + 8), (x + 20, y + 8), (x + 26, y + 4), (x + 50, y + 4), (x + 56, y + 11), (x + w - 4, y + 11)]
    pygame.draw.lines(screen, c[2], False, pts, 1)
    pygame.draw.circle(screen, c[2], pts[0], 2)
    pygame.draw.circle(screen, c[2], pts[-1], 2)


def plat_crate(x, y, w, h, c):
    pygame.draw.rect(screen, c[0], (x, y, w, h))
    pygame.draw.rect(screen, c[1], (x, y, w, h), 3)
    pygame.draw.line(screen, c[2], (x + 3, y + 3), (x + w - 3, y + h - 3), 2)
    pygame.draw.line(screen, c[2], (x + w - 3, y + 3), (x + 3, y + h - 3), 2)


def plat_bricks(x, y, w, h, c):
    pygame.draw.rect(screen, c[0], (x, y, w, h))
    pygame.draw.rect(screen, c[1], (x, y, w, h), 2)
    pygame.draw.line(screen, c[1], (x, y + h // 2), (x + w, y + h // 2), 1)
    for bx in range(x + 12, x + w, 19):
        pygame.draw.line(screen, c[1], (bx, y), (bx, y + h // 2), 1)
    for bx in range(x + 22, x + w, 19):
        pygame.draw.line(screen, c[1], (bx, y + h // 2), (bx, y + h), 1)
    pygame.draw.rect(screen, c[2], (x, y, w, 3))


def plat_carved(x, y, w, h, c):
    pygame.draw.rect(screen, c[0], (x, y, w, h), border_radius=2)
    pygame.draw.rect(screen, c[1], (x, y, w, h), 2, border_radius=2)
    for i in range(3):
        gx = x + 8 + i * 22
        pygame.draw.rect(screen, c[2], (gx, y + 4, 12, 8), 2)
        pygame.draw.circle(screen, c[2], (gx + 6, y + 8), 1)


def plat_log(x, y, w, h, c):
    pygame.draw.rect(screen, c[0], (x + 4, y, w - 8, h), border_radius=6)
    pygame.draw.rect(screen, c[1], (x + 4, y, w - 8, h), 2, border_radius=6)
    pygame.draw.ellipse(screen, c[2], (x, y, 12, h))
    pygame.draw.ellipse(screen, c[1], (x, y, 12, h), 2)
    pygame.draw.ellipse(screen, c[1], (x + 3, y + 4, 6, h - 8), 1)
    pygame.draw.line(screen, c[1], (x + 18, y + 5), (x + w - 12, y + 5), 1)
    pygame.draw.line(screen, c[1], (x + 22, y + 11), (x + w - 18, y + 11), 1)


def plat_cosmic(x, y, w, h, c):
    pygame.draw.rect(screen, c[0], (x, y, w, h), border_radius=6)
    pygame.draw.rect(screen, c[1], (x, y, w, h), 2, border_radius=6)
    for sx, sy in ((10, 4), (24, 10), (37, 5), (50, 11), (63, 6), (30, 13)):
        pygame.draw.circle(screen, c[2], (x + sx, y + sy), 1)
    pygame.draw.line(screen, c[2], (x + 44, y + 3), (x + 50, y + 3), 1)


def plat_ring(x, y, w, h, c):
    pygame.draw.ellipse(screen, c[0], (x, y, w, h))
    pygame.draw.ellipse(screen, c[1], (x, y, w, h), 3)
    pygame.draw.ellipse(screen, c[2], (x + 10, y + 5, w - 20, h - 10), 1)


def plat_mushroom(x, y, w, h, c):
    pygame.draw.rect(screen, c[2], (x + w // 2 - 6, y + h - 6, 12, 6))
    pygame.draw.ellipse(screen, c[0], (x, y, w, h + 4))
    for dx, dy in ((16, 6), (36, 4), (56, 7)):
        pygame.draw.circle(screen, c[1], (x + dx, y + dy), 3)


def plat_glass(x, y, w, h, c):
    pygame.draw.rect(screen, c[0], (x, y, w, h), border_radius=4)
    pygame.draw.rect(screen, c[1], (x, y, w, h), 2, border_radius=4)
    for gx in (x + 10, x + 28, x + 46):
        pygame.draw.line(screen, c[2], (gx, y + h - 3), (gx + 8, y + 3), 2)


def plat_lily(x, y, w, h, c):
    pygame.draw.ellipse(screen, c[0], (x, y, w, h))
    pygame.draw.ellipse(screen, c[1], (x, y, w, h), 2)
    pygame.draw.line(screen, c[1], (x + 6, y + h // 2), (x + w // 2, y + h // 2), 1)
    pygame.draw.circle(screen, c[2], (x + w - 20, y + 5), 4)
    pygame.draw.circle(screen, WHITE, (x + w - 20, y + 5), 1)


def plat_books(x, y, w, h, c):
    bw = w // 3
    for i in range(3):
        bx = x + i * bw
        pygame.draw.rect(screen, c[i], (bx, y, bw, h))
        pygame.draw.rect(screen, BLACK, (bx, y, bw, h), 1)
        pygame.draw.line(screen, (240, 230, 190), (bx + 3, y + 5), (bx + bw - 3, y + 5), 1)
        pygame.draw.line(screen, (240, 230, 190), (bx + 3, y + h - 5), (bx + bw - 3, y + h - 5), 1)


def plat_gingerbread(x, y, w, h, c):
    pygame.draw.rect(screen, c[0], (x, y, w, h), border_radius=8)
    pygame.draw.rect(screen, (120, 70, 30), (x, y, w, h), 2, border_radius=8)
    pts = [(x + 6 + i * 8, y + (3 if i % 2 == 0 else 8)) for i in range(8)]
    pygame.draw.lines(screen, c[1], False, pts, 2)
    for bx in (x + 18, x + w // 2, x + w - 18):
        pygame.draw.circle(screen, c[2], (bx, y + 12), 2)


def plat_blocks(x, y, w, h, c):
    bw = w // 3
    for i in range(3):
        bx = x + i * bw
        pygame.draw.rect(screen, c[i], (bx, y, bw, h))
        pygame.draw.rect(screen, BLACK, (bx, y, bw, h), 1)
        pygame.draw.circle(screen, WHITE, (bx + bw // 2, y + h // 2), 3, 1)


def plat_pixel(x, y, w, h, c):
    for i in range(0, w, 8):
        for j in range(0, h, 8):
            col = c[0] if (i // 8 + j // 8) % 2 == 0 else c[1]
            pygame.draw.rect(screen, col, (x + i, y + j, min(8, w - i), 8))
    pygame.draw.rect(screen, c[2], (x, y, w, 3))


def plat_piano(x, y, w, h, c):
    pygame.draw.rect(screen, c[0], (x, y, w, h))
    pygame.draw.rect(screen, c[1], (x, y, w, h), 2)
    for kx in range(x + 10, x + w - 8, 12):
        pygame.draw.rect(screen, c[1], (kx, y, 7, 10))
    pygame.draw.rect(screen, c[2], (x + 2, y + h - 3, w - 4, 2))


def plat_chips(x, y, w, h, c):
    pygame.draw.ellipse(screen, c[0], (x, y, w, h))
    pygame.draw.ellipse(screen, c[2], (x, y, w, h), 2)
    for dx in (8, w // 2 - 4, w - 16):
        pygame.draw.rect(screen, c[1], (x + dx, y + h // 2 - 2, 8, 4))


def plat_cog(x, y, w, h, c):
    pygame.draw.rect(screen, c[0], (x, y, w, h), border_radius=3)
    pygame.draw.rect(screen, c[1], (x, y, w, h), 2, border_radius=3)
    for gx in (x + 14, x + w // 2, x + w - 14):
        pygame.draw.circle(screen, c[2], (gx, y + h // 2), 6)
        pygame.draw.circle(screen, c[1], (gx, y + h // 2), 6, 2)
        pygame.draw.circle(screen, c[1], (gx, y + h // 2), 2)


def plat_rock(x, y, w, h, c):
    pts = [(x, y + h), (x + 6, y + 3), (x + 20, y), (x + 45, y + 2), (x + w - 6, y + 1), (x + w, y + h)]
    pygame.draw.polygon(screen, c[0], pts)
    pygame.draw.polygon(screen, c[1], pts, 2)
    pygame.draw.lines(screen, c[2], False, pts[1:5], 3)


def plat_lunar(x, y, w, h, c):
    pygame.draw.rect(screen, c[0], (x, y, w, h), border_radius=6)
    pygame.draw.rect(screen, c[1], (x, y, w, h), 2, border_radius=6)
    for cx, cw in ((10, 12), (30, 16), (54, 10)):
        pygame.draw.ellipse(screen, c[1], (x + cx, y + 5, cw, 7))
        pygame.draw.ellipse(screen, c[2], (x + cx, y + 5, cw, 7), 1)


RAINBOW_BANDS = [(255, 60, 60), (255, 160, 40), (255, 230, 50), (60, 200, 80), (60, 140, 255), (150, 80, 220)]


def plat_rainbow(x, y, w, h, c):
    for i, col in enumerate(RAINBOW_BANDS):
        pygame.draw.rect(screen, col, (x, y + int(i * h / 6), w, int(h / 6) + 1))
    pygame.draw.rect(screen, c[0], (x, y, w, h), 1, border_radius=3)


def plat_bone(x, y, w, h, c):
    pygame.draw.rect(screen, c[0], (x + 6, y + 4, w - 12, h - 8), border_radius=4)
    for kx in (x + 6, x + w - 6):
        for ky in (y + 4, y + h - 4):
            pygame.draw.circle(screen, c[0], (kx, ky), 5)
            pygame.draw.circle(screen, c[1], (kx, ky), 5, 1)
    pygame.draw.line(screen, c[2], (x + 30, y + 5), (x + 36, y + 11), 2)


def plat_hazard(x, y, w, h, c):
    pygame.draw.rect(screen, c[0], (x, y, w, h))
    for sx in range(x - h, x + w, 14):
        pts = [(sx, y + h), (sx + 7, y + h), (sx + 7 + h, y), (sx + h, y)]
        pts = [(min(max(px, x), x + w), py) for px, py in pts]
        pygame.draw.polygon(screen, c[1], pts)
    pygame.draw.rect(screen, c[1], (x, y, w, h), 2)
    pygame.draw.circle(screen, c[2], (x + 4, y + h // 2), 2)
    pygame.draw.circle(screen, c[2], (x + w - 5, y + h // 2), 2)


PLATFORM_STYLES = {
    "sand": plat_sand, "leaf": plat_leaf, "coral": plat_coral, "candy": plat_candy,
    "neon": plat_neon, "wood": plat_wood, "plank": plat_plank, "metal": plat_metal,
    "magma": plat_magma, "crystal": plat_crystal, "bamboo": plat_bamboo, "cloud": plat_cloud,
    "gold": plat_gold, "circuit": plat_circuit, "crate": plat_crate, "bricks": plat_bricks,
    "carved": plat_carved, "log": plat_log, "cosmic": plat_cosmic, "ring": plat_ring,
    "mushroom": plat_mushroom, "glass": plat_glass, "lily": plat_lily, "books": plat_books,
    "gingerbread": plat_gingerbread, "blocks": plat_blocks, "pixel": plat_pixel,
    "piano": plat_piano, "chips": plat_chips, "cog": plat_cog, "rock": plat_rock,
    "lunar": plat_lunar, "rainbow": plat_rainbow, "bone": plat_bone, "hazard": plat_hazard,
}


# ------------------------------ רעל / נוזל ------------------------------
def wave_fill(wy, c0, c1, amp, freq, spd, t):
    pts = [(0, HEIGHT + 5)]
    for xx in range(0, WIDTH + 11, 10):
        pts.append((xx, wy + math.sin(xx * freq + t * spd) * amp))
    pts.append((WIDTH, HEIGHT + 5))
    pygame.draw.polygon(screen, c0, pts)
    if c1:
        pygame.draw.lines(screen, c1, False, pts[1:-1], 3)


def poi_waves(wy, c, t):
    wave_fill(wy, c[0], c[1], 5, 0.05, 0.004, t)


def poi_lava(wy, c, t):
    wave_fill(wy, c[0], c[1], 7, 0.035, 0.003, t)
    wave_fill(wy + 14, c[1], None, 5, 0.04, -0.003, t)
    wave_fill(wy + 28, c[0], None, 4, 0.05, 0.002, t)


def poi_dunes(wy, c, t):
    wave_fill(wy - 4, c[1], None, 9, 0.016, 0.0006, t)
    wave_fill(wy + 8, c[0], c[2], 8, 0.022, -0.0005, t)


def poi_slime(wy, c, t):
    wave_fill(wy, c[0], c[1], 4, 0.06, 0.004, t)
    for xx in range(20, WIDTH, 60):
        by = wy - 2 - int(3 * abs(math.sin(t * 0.003 + xx)))
        pygame.draw.circle(screen, c[0], (xx, by), 7)
        pygame.draw.circle(screen, c[1], (xx, by), 7, 2)


def poi_goo(wy, c, t):
    pygame.draw.rect(screen, c[0], (0, wy + 6, WIDTH, HEIGHT - wy))
    for i, xx in enumerate(range(0, WIDTH + 24, 24)):
        r = 9 + int(3 * math.sin(t * 0.003 + i))
        pygame.draw.circle(screen, c[0], (xx, wy + 4), r)
        pygame.draw.circle(screen, c[1], (xx - 3, wy + 1), 3)
    pygame.draw.line(screen, c[1], (0, wy + 14), (WIDTH, wy + 14), 1)


def poi_tar(wy, c, t):
    wave_fill(wy, c[0], c[1], 3, 0.04, 0.0015, t)
    for xx in range(15, WIDTH, 45):
        pygame.draw.ellipse(screen, c[2], (xx, wy + 8 + (xx * 7) % 20, 14, 4), 1)


def poi_spikes(wy, c, t):
    pygame.draw.rect(screen, c[0], (0, wy + 10, WIDTH, HEIGHT - wy))
    for xx in range(-10, WIDTH + 20, 20):
        off = int(math.sin(t * 0.005 + xx) * 3)
        pts = [(xx, wy + 12), (xx + 10, wy - 4 + off), (xx + 20, wy + 12)]
        pygame.draw.polygon(screen, c[0], pts)
        pygame.draw.polygon(screen, c[1], pts, 2)


def poi_flames(wy, c, t):
    pygame.draw.rect(screen, c[0], (0, wy + 8, WIDTH, HEIGHT - wy))
    for i, xx in enumerate(range(0, WIDTH + 16, 16)):
        hgt = 12 + int(6 * math.sin(t * 0.01 + xx * 0.7))
        base = wy + 10
        pygame.draw.polygon(screen, c[0], [(xx - 9, base), (xx, wy + 4 - hgt), (xx + 9, base)])
        pygame.draw.polygon(screen, c[1], [(xx - 6, base), (xx, wy + 6 - int(hgt * 0.75)), (xx + 6, base)])
        pygame.draw.polygon(screen, c[2], [(xx - 3, base), (xx, wy + 8 - int(hgt * 0.45)), (xx + 3, base)])


def poi_fog(wy, c, t):
    pygame.draw.rect(screen, c[0], (0, wy + 20, WIDTH, HEIGHT - wy))
    fog_surf.fill((0, 0, 0, 0))
    for i in range(14):
        cx = (i * 47 + t * 0.02 * (1 + i % 3)) % (WIDTH + 80) - 40
        cy = wy + 20 + (i % 3) * 5
        pygame.draw.circle(fog_surf, (c[1][0], c[1][1], c[1][2], 150), (int(cx), int(cy)), 20 + (i % 3) * 7)
    screen.blit(fog_surf, (0, 0))


def poi_electric(wy, c, t):
    pygame.draw.rect(screen, c[0], (0, wy, WIDTH, HEIGHT - wy))
    rnd = random.Random(t // 90)
    pts = [(xx, wy - 4 - rnd.randint(0, 14)) for xx in range(0, WIDTH + 20, 20)]
    pygame.draw.lines(screen, c[1], False, pts, 3)
    pygame.draw.lines(screen, c[2], False, pts, 1)
    for _ in range(3):
        bx = rnd.randint(10, WIDTH - 10)
        bolt = [(bx, wy), (bx + rnd.randint(-15, 15), wy + 20), (bx + rnd.randint(-15, 15), wy + 40)]
        pygame.draw.lines(screen, c[1], False, bolt, 2)


def poi_glitch(wy, c, t):
    pygame.draw.rect(screen, c[0], (0, wy, WIDTH, HEIGHT - wy))
    pygame.draw.line(screen, c[1], (0, wy), (WIDTH, wy), 2)
    rnd = random.Random(t // 100)
    for _ in range(12):
        gx = rnd.randint(0, WIDTH - 40)
        gy = wy + rnd.randint(-8, 50)
        pygame.draw.rect(screen, rnd.choice(c), (gx, gy, rnd.randint(20, 90), rnd.randint(3, 8)))


def poi_tentacles(wy, c, t):
    pygame.draw.rect(screen, c[0], (0, wy + 6, WIDTH, HEIGHT - wy))
    for i, xx in enumerate(range(15, WIDTH, 50)):
        pts = [(xx + math.sin(t * 0.006 + i + k * 0.7) * 10, wy + 8 - k * 4) for k in range(6)]
        pygame.draw.lines(screen, c[1], False, pts, 12)
        pygame.draw.lines(screen, c[0], False, pts, 8)
        for px, py in pts[1:5:2]:
            pygame.draw.circle(screen, c[2], (int(px), int(py)), 2)


def poi_void(wy, c, t):
    pygame.draw.rect(screen, c[0], (0, wy, WIDTH, HEIGHT - wy))
    pygame.draw.line(screen, c[1], (0, wy), (WIDTH, wy), 3)
    pygame.draw.line(screen, c[2], (0, wy + 4), (WIDTH, wy + 4), 1)
    for i in range(4):
        ew = 100 + i * 90 + int(20 * math.sin(t * 0.003 + i))
        pygame.draw.ellipse(screen, c[1], (WIDTH // 2 - ew // 2, wy + 12 + i * 30, ew, 40), 1)


def poi_pixels(wy, c, t):
    pygame.draw.rect(screen, c[0], (0, wy, WIDTH, HEIGHT - wy))
    for k, xx in enumerate(range(0, WIDTH, 16)):
        hh = ((k * 7 + t // 220) % 4) * 4
        pygame.draw.rect(screen, c[1] if k % 2 == 0 else c[2], (xx, wy - hh, 16, hh + 4))


def poi_equalizer(wy, c, t):
    pygame.draw.rect(screen, dark(c[0]), (0, wy, WIDTH, HEIGHT - wy))
    for k, xx in enumerate(range(0, WIDTH, 20)):
        hh = 8 + int(14 * abs(math.sin(t * 0.006 + xx * 0.3)))
        pygame.draw.rect(screen, c[k % 3], (xx + 1, wy - hh + 8, 18, HEIGHT))


def poi_chips(wy, c, t):
    pygame.draw.rect(screen, dark(c[0], 0.5), (0, wy + 10, WIDTH, HEIGHT - wy))
    for row in range(3):
        for k, xx in enumerate(range(-10 + (row % 2) * 15, WIDTH + 30, 30)):
            col = c[(k + row) % 3]
            yy = wy - 6 + row * 8
            pygame.draw.ellipse(screen, col, (xx, yy, 30, 14))
            pygame.draw.ellipse(screen, WHITE, (xx, yy, 30, 14), 1)


def poi_ballpit(wy, c, t):
    pygame.draw.rect(screen, dark(c[0], 0.5), (0, wy + 30, WIDTH, HEIGHT - wy))
    for row in range(4):
        for k, xx in enumerate(range(-9 + (row % 2) * 9, WIDTH + 18, 18)):
            bob = int(2 * math.sin(t * 0.004 + k + row)) if row == 0 else 0
            cy = wy + 9 + row * 10 + bob
            pygame.draw.circle(screen, c[(k + row) % 3], (xx, cy), 9)
            pygame.draw.circle(screen, WHITE, (xx - 3, cy - 3), 2)


def poi_rainbow(wy, c, t):
    for i, col in enumerate(RAINBOW_BANDS):
        wave_fill(wy + i * 8, col, None, 4, 0.05, 0.004 + i * 0.0005, t)


POISON_STYLES = {
    "waves": poi_waves, "lava": poi_lava, "dunes": poi_dunes, "slime": poi_slime,
    "goo": poi_goo, "tar": poi_tar, "spikes": poi_spikes, "flames": poi_flames,
    "fog": poi_fog, "electric": poi_electric, "glitch": poi_glitch,
    "tentacles": poi_tentacles, "void": poi_void, "pixels": poi_pixels,
    "equalizer": poi_equalizer, "chips": poi_chips, "ballpit": poi_ballpit,
    "rainbow": poi_rainbow,
}
NO_BUBBLE_STYLES = {"equalizer", "chips", "ballpit", "pixels", "rainbow"}

# ------------------------------ קישוטי רקע ------------------------------
DECO_VEL = {"snow": 1.0, "rain": 9.0, "leaves": 1.6, "petals": 1.2, "feathers": 0.8,
            "embers": -1.2, "ash": 0.8, "dust": 0.6, "bubbles": -1.0, "sprinkles": 1.5,
            "squares": 1.2, "pages": 1.0, "diamonds": 0.9, "sparkles": 0.3, "stars": 0.1,
            "gears": 0.6, "fireflies": 0.2, "spores": -0.5, "clouds": 0.2}


def update_deco(kind, diff):
    vel = DECO_VEL.get(kind, 1.0)
    t = pygame.time.get_ticks()
    for d in deco:
        d.y += vel + diff * 0.4
        if kind != "rain":
            d.x += math.sin(t * 0.002 + d.phase) * 0.4
        if d.y > HEIGHT + 10:
            d.y = -10
            d.x = random.randint(0, WIDTH)
        elif d.y < -10:
            d.y = HEIGHT + 10
            d.x = random.randint(0, WIDTH)


def draw_deco(kind, cols):
    t = pygame.time.get_ticks()
    for d in deco:
        col = cols[d.idx % len(cols)]
        x, y, s = int(d.x), int(d.y), d.size
        if kind in ("snow", "ash", "spores"):
            pygame.draw.circle(screen, col, (x, y), s)
        elif kind == "dust":
            pygame.draw.circle(screen, col, (x, y), max(1, s // 2))
        elif kind == "embers":
            pygame.draw.circle(screen, col, (x, y), s // 2 + 1)
        elif kind == "bubbles":
            pygame.draw.circle(screen, col, (x, y), s + 2, 1)
        elif kind == "fireflies":
            if (t // 250 + d.idx) % 4:
                pygame.draw.circle(screen, col, (x, y), s // 2 + 1)
                pygame.draw.circle(screen, col, (x, y), s + 2, 1)
        elif kind == "rain":
            pygame.draw.line(screen, col, (x, y), (x - 2, y + 10), 1)
        elif kind in ("leaves", "petals", "feathers"):
            w = max(3, int(abs(math.cos(t * 0.003 + d.phase)) * s * 2))
            pygame.draw.ellipse(screen, col, (x, y, w, s + 2))
        elif kind in ("squares", "sprinkles"):
            pygame.draw.rect(screen, col, (x, y, s * 2, s))
        elif kind == "pages":
            pygame.draw.rect(screen, col, (x, y, s * 2, s * 3))
        elif kind == "diamonds":
            pygame.draw.polygon(screen, col, [(x, y - s - 2), (x + s, y), (x, y + s + 2), (x - s, y)])
        elif kind in ("sparkles", "stars"):
            r = s + 1 if (t // 200 + d.idx) % 2 else s
            pygame.draw.line(screen, col, (x - r, y), (x + r, y), 1)
            pygame.draw.line(screen, col, (x, y - r), (x, y + r), 1)
        elif kind == "gears":
            pygame.draw.circle(screen, col, (x, y), s + 3, 2)
            pygame.draw.line(screen, col, (x - s - 3, y), (x + s + 3, y), 1)
            pygame.draw.line(screen, col, (x, y - s - 3), (x, y + s + 3), 1)
        elif kind == "clouds":
            pygame.draw.circle(screen, col, (x, y), s * 3 + 4)
            pygame.draw.circle(screen, col, (x + s * 2, y + 2), s * 2 + 3)
            pygame.draw.circle(screen, col, (x - s * 2, y + 3), s * 2 + 2)
        else:
            pygame.draw.circle(screen, col, (x, y), s)


# ------------------------------ רשימת 40 השלבים ------------------------------
Theme = namedtuple("Theme", "name top bottom plat pcols poison qcols speed deco dcols")
THEMES = [
    Theme("Desert Dunes", (255, 205, 120), (240, 150, 70), "sand", ((235, 195, 115), (175, 125, 55), (255, 230, 160)), "dunes", ((205, 145, 60), (240, 195, 105), (170, 110, 45)), 0.95, "dust", [(255, 240, 200), (240, 200, 140)]),
    Theme("Jungle Canopy", (25, 100, 45), (80, 170, 80), "leaf", ((50, 150, 60), (20, 90, 30), (150, 230, 100)), "tentacles", ((30, 110, 30), (60, 170, 50), (200, 255, 120)), 1.0, "leaves", [(120, 200, 70), (60, 150, 50)]),
    Theme("Deep Ocean", (0, 35, 95), (0, 105, 165), "coral", ((255, 110, 120), (200, 60, 90), (255, 200, 170)), "waves", ((0, 60, 140), (70, 160, 230), (180, 230, 255)), 1.0, "bubbles", [(180, 230, 255)]),
    Theme("Candy Land", (255, 190, 230), (255, 235, 250), "candy", ((255, 110, 175), (255, 255, 255), (110, 215, 255)), "goo", ((120, 70, 40), (170, 115, 70), (210, 160, 110)), 0.95, "sprinkles", [(255, 80, 80), (80, 200, 255), (255, 230, 80), (120, 255, 150)]),
    Theme("Neon City", (15, 5, 40), (65, 10, 95), "neon", ((20, 20, 45), (255, 0, 200), (0, 255, 255)), "electric", ((15, 10, 70), (0, 255, 255), (255, 0, 255)), 1.05, "rain", [(255, 0, 200), (0, 255, 255)]),
    Theme("Haunted Mansion", (30, 25, 45), (75, 65, 95), "wood", ((70, 50, 45), (35, 25, 25), (160, 160, 185)), "fog", ((70, 190, 150), (160, 255, 215), (220, 255, 240)), 1.0, "fireflies", [(200, 255, 230)]),
    Theme("Steampunk", (120, 80, 40), (195, 145, 75), "metal", ((150, 110, 60), (80, 55, 25), (225, 185, 95)), "tar", ((30, 25, 20), (80, 70, 45), (130, 110, 55)), 1.0, "gears", [(90, 65, 30), (150, 110, 55)]),
    Theme("Crystal Cave", (40, 20, 80), (95, 45, 145), "crystal", ((160, 120, 255), (90, 60, 200), (235, 215, 255)), "spikes", ((170, 50, 220), (230, 120, 255), (255, 200, 255)), 1.05, "diamonds", [(200, 160, 255), (150, 200, 255)]),
    Theme("Obsidian Forge", (30, 10, 10), (95, 22, 12), "magma", ((45, 40, 48), (20, 15, 20), (255, 120, 20)), "flames", ((255, 90, 0), (255, 190, 40), (255, 255, 160)), 1.1, "embers", [(255, 150, 40), (255, 90, 20)]),
    Theme("Sakura Garden", (255, 200, 215), (255, 238, 242), "bamboo", ((150, 205, 100), (90, 145, 60), (215, 245, 155)), "fog", ((235, 100, 150), (255, 165, 200), (255, 225, 240)), 0.95, "petals", [(255, 170, 200), (255, 210, 225)]),
    Theme("Autumn Forest", (200, 110, 40), (240, 175, 75), "log", ((125, 72, 32), (70, 40, 15), (230, 140, 40)), "dunes", ((160, 45, 20), (210, 85, 30), (245, 160, 50)), 1.0, "leaves", [(210, 70, 20), (240, 150, 30), (160, 50, 20)]),
    Theme("Thunderstorm", (40, 50, 70), (95, 105, 130), "cloud", ((115, 120, 140), (60, 65, 85), (255, 255, 120)), "electric", ((55, 55, 110), (255, 255, 100), (255, 255, 255)), 1.1, "rain", [(150, 170, 210)]),
    Theme("Toxic Wasteland", (60, 70, 20), (135, 145, 40), "hazard", ((255, 215, 0), (30, 30, 20), (230, 40, 30)), "slime", ((140, 255, 0), (215, 255, 80), (255, 255, 180)), 1.1, "ash", [(140, 150, 90), (100, 110, 60)]),
    Theme("Golden Palace", (85, 50, 10), (205, 150, 40), "gold", ((255, 205, 60), (150, 100, 10), (255, 250, 190)), "lava", ((255, 170, 0), (255, 225, 90), (255, 250, 200)), 1.0, "sparkles", [(255, 235, 150), (255, 255, 220)]),
    Theme("Circuit Board", (5, 40, 25), (10, 85, 50), "circuit", ((20, 100, 60), (5, 40, 25), (120, 255, 160)), "pixels", ((200, 20, 40), (255, 90, 90), (255, 190, 190)), 1.05, "squares", [(40, 160, 90), (90, 255, 150)]),
    Theme("Pirate Seas", (90, 180, 230), (185, 228, 246), "plank", ((125, 78, 38), (60, 35, 15), (225, 185, 85)), "tentacles", ((15, 55, 95), (40, 100, 150), (200, 230, 250)), 1.0, "clouds", [(255, 255, 255)]),
    Theme("Wild West", (230, 150, 90), (250, 208, 145), "crate", ((165, 115, 65), (90, 55, 25), (215, 175, 105)), "tar", ((25, 20, 15), (70, 55, 35), (120, 95, 55)), 1.0, "dust", [(240, 210, 160), (210, 170, 110)]),
    Theme("Egyptian Pyramids", (255, 215, 130), (255, 242, 195), "bricks", ((225, 195, 125), (150, 120, 60), (40, 165, 205)), "waves", ((20, 110, 130), (60, 175, 190), (200, 240, 235)), 1.0, "sparkles", [(255, 230, 140)]),
    Theme("Aztec Temple", (20, 80, 70), (65, 145, 115), "carved", ((135, 135, 115), (70, 70, 55), (235, 185, 40)), "flames", ((190, 40, 20), (245, 120, 30), (255, 215, 90)), 1.1, "leaves", [(40, 130, 70), (90, 180, 90)]),
    Theme("Viking Fjord", (130, 170, 200), (212, 232, 246), "log", ((115, 82, 52), (60, 40, 20), (200, 205, 215)), "spikes", ((40, 90, 140), (110, 170, 220), (225, 245, 255)), 1.0, "snow", [(255, 255, 255)]),
    Theme("Cyberpunk Rain", (30, 0, 50), (125, 0, 85), "neon", ((25, 15, 40), (255, 230, 0), (255, 0, 120)), "glitch", ((255, 0, 100), (0, 255, 220), (255, 255, 255)), 1.15, "rain", [(255, 60, 160), (80, 255, 230)]),
    Theme("Galaxy Nebula", (20, 0, 60), (95, 20, 135), "cosmic", ((65, 45, 135), (25, 10, 75), (255, 230, 255)), "void", ((12, 0, 35), (160, 110, 255), (255, 255, 255)), 1.05, "stars", [(255, 255, 220), (200, 170, 255)]),
    Theme("Black Hole", (0, 0, 0), (35, 12, 45), "ring", ((40, 30, 50), (255, 160, 40), (255, 230, 150)), "void", ((6, 0, 12), (255, 120, 0), (255, 210, 110)), 1.2, "dust", [(255, 170, 70), (255, 120, 30)]),
    Theme("Mushroom Forest", (60, 20, 70), (125, 55, 115), "mushroom", ((225, 45, 65), (255, 255, 255), (240, 220, 190)), "slime", ((140, 45, 200), (195, 105, 240), (235, 175, 255)), 1.0, "spores", [(220, 170, 255), (255, 220, 255)]),
    Theme("Sunset Beach", (255, 140, 90), (255, 212, 145), "plank", ((190, 140, 85), (110, 70, 35), (240, 200, 130)), "waves", ((20, 130, 150), (90, 205, 215), (235, 252, 252)), 0.95, "clouds", [(255, 225, 200)]),
    Theme("Arctic Aurora", (5, 20, 50), (10, 95, 105), "glass", ((150, 222, 242), (80, 150, 190), (255, 255, 255)), "fog", ((20, 190, 150), (120, 255, 200), (200, 255, 230)), 1.0, "snow", [(220, 255, 255)]),
    Theme("Murky Swamp", (40, 60, 30), (85, 105, 55), "lily", ((60, 150, 60), (30, 90, 30), (255, 150, 200)), "goo", ((75, 90, 20), (120, 140, 30), (175, 185, 70)), 1.0, "fireflies", [(240, 255, 120)]),
    Theme("Magic Library", (60, 30, 20), (115, 72, 42), "books", ((150, 40, 40), (40, 60, 150), (40, 130, 70)), "goo", ((10, 10, 25), (45, 45, 90), (100, 100, 170)), 1.05, "pages", [(250, 240, 210)]),
    Theme("Gingerbread Town", (255, 230, 200), (255, 250, 236), "gingerbread", ((172, 100, 50), (255, 255, 255), (230, 40, 60)), "waves", ((225, 35, 75), (255, 105, 135), (255, 195, 210)), 0.95, "sprinkles", [(255, 80, 110), (255, 255, 255), (120, 220, 140)]),
    Theme("Toy Blocks", (255, 240, 130), (255, 255, 205), "blocks", ((230, 60, 60), (60, 120, 230), (250, 200, 40)), "ballpit", ((255, 100, 100), (100, 200, 255), (255, 230, 80)), 1.0, "squares", [(255, 120, 120), (120, 180, 255), (255, 225, 90)]),
    Theme("Retro Pixel", (20, 20, 60), (55, 55, 125), "pixel", ((90, 200, 90), (30, 100, 30), (255, 255, 255)), "pixels", ((220, 40, 40), (255, 140, 40), (255, 230, 60)), 1.05, "squares", [(255, 255, 255), (150, 150, 255)]),
    Theme("Music Stage", (50, 0, 80), (165, 40, 125), "piano", ((250, 250, 250), (20, 20, 20), (255, 200, 0)), "equalizer", ((255, 60, 160), (60, 255, 200), (255, 230, 60)), 1.1, "sparkles", [(255, 255, 255), (255, 230, 120)]),
    Theme("Casino Night", (10, 70, 40), (22, 115, 65), "chips", ((200, 30, 40), (255, 255, 255), (30, 30, 30)), "chips", ((200, 30, 40), (30, 30, 30), (250, 200, 40)), 1.05, "sparkles", [(255, 215, 0)]),
    Theme("Clockwork Tower", (70, 60, 50), (135, 118, 92), "cog", ((170, 140, 70), (90, 70, 30), (230, 210, 150)), "tar", ((20, 20, 20), (65, 60, 48), (125, 115, 85)), 1.0, "gears", [(100, 85, 55), (160, 140, 90)]),
    Theme("Dino Valley", (130, 200, 120), (222, 242, 162), "rock", ((150, 125, 95), (90, 70, 50), (110, 170, 70)), "lava", ((230, 70, 10), (255, 170, 30), (255, 230, 100)), 1.05, "ash", [(120, 100, 80)]),
    Theme("Moon Base", (10, 10, 25), (52, 52, 75), "lunar", ((170, 170, 182), (100, 100, 118), (60, 60, 78)), "electric", ((35, 0, 0), (255, 40, 40), (255, 200, 200)), 1.1, "stars", [(255, 255, 255)]),
    Theme("Red Mars", (120, 40, 20), (205, 95, 55), "rock", ((192, 102, 62), (110, 50, 30), (242, 172, 122)), "fog", ((180, 80, 50), (225, 135, 95), (245, 185, 145)), 1.05, "dust", [(240, 160, 110)]),
    Theme("Rainbow Sky", (255, 200, 240), (190, 232, 255), "rainbow", ((255, 255, 255), (255, 255, 255), (255, 255, 255)), "rainbow", ((255, 80, 80), (255, 230, 80), (80, 150, 255)), 0.95, "sparkles", [(255, 255, 255), (255, 240, 150)]),
    Theme("Heaven Gates", (200, 230, 255), (255, 255, 240), "cloud", ((255, 255, 255), (200, 220, 245), (255, 225, 110)), "void", ((60, 60, 95), (200, 200, 255), (255, 255, 255)), 1.0, "feathers", [(255, 255, 255)]),
    Theme("Hell Finale", (30, 0, 0), (115, 10, 10), "bone", ((232, 226, 200), (140, 130, 100), (200, 30, 30)), "spikes", ((120, 0, 0), (225, 35, 35), (255, 125, 85)), 1.25, "embers", [(255, 100, 30), (255, 200, 60)]),
]


def get_theme_index(sc):
    if sc < THEME_START:
        return None
    return min((sc - THEME_START) // THEME_LEN, len(THEMES) - 1)


def draw_theme_background(idx, sc):
    th = THEMES[idx]
    top, bottom = th.top, th.bottom
    progress = sc - THEME_START - idx * THEME_LEN
    if progress < 800:  # מעבר חלק מהרקע הקודם
        if idx == 0:
            ptop = pbot = PURPLE_BG
        else:
            ptop, pbot = THEMES[idx - 1].top, THEMES[idx - 1].bottom
        f = progress / 800
        top = lerp_color(ptop, top, f)
        bottom = lerp_color(pbot, bottom, f)
    for yy in range(0, HEIGHT, 8):
        pygame.draw.rect(screen, lerp_color(top, bottom, yy / HEIGHT), (0, yy, WIDTH, 8))


def draw_text(fnt, text, color, pos):
    """טקסט עם צל שחור כדי שיהיה קריא על כל רקע"""
    screen.blit(fnt.render(text, True, BLACK), (pos[0] + 2, pos[1] + 2))
    screen.blit(fnt.render(text, True, color), pos)


# =====================================================================
#                      חנות סקינים (דמויות לשחקן)
# =====================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(BASE_DIR, "save.json")
SKIN_SIZE = 46
SHOP_SIZE = 44
SHOP_BG = (20, 25, 45)

Skin = namedtuple("Skin", "name price file")
SKINS = [
    Skin("Fox", 600000, "skin_01.png"),
    Skin("Fire", 1500000, "skin_02.png"),
    Skin("Alien", 48000, "skin_03.png"),
    Skin("Jelly", 540000, "skin_04.png"),
    Skin("Robo", 480000, "skin_05.png"),
    Skin("Panda", 240000, "skin_06.png"),
    Skin("Crystal", 2100000, "skin_07.png"),
    Skin("Dragon", 4800000, "skin_08.png"),
    Skin("Turtle", 300000, "skin_09.png"),
    Skin("Ghost", 720000, "skin_10.png"),
    Skin("Bat", 210000, "skin_11.png"),
    Skin("Penguin", 180000, "skin_12.png"),
    Skin("Spark", 1800000, "skin_13.png"),
    Skin("Golem", 1320000, "skin_14.png"),
    Skin("Axolotl", 360000, "skin_15.png"),
    Skin("Slime", 30000, "skin_16.png"),
    Skin("Shroom", 90000, "skin_17.png"),
    Skin("Shadow", 1680000, "skin_18.png"),
    Skin("Bee", 270000, "skin_19.png"),
    Skin("Yeti", 840000, "skin_20.png"),
    Skin("Crab", 72000, "skin_21.png"),
    Skin("Astro", 660000, "skin_22.png"),
    Skin("Cactus", 120000, "skin_23.png"),
    Skin("Shark", 900000, "skin_24.png"),
    Skin("Phoenix", 6000000, "skin_25.png"),
]

total_points = 0  # הבנק: סך כל הנקודות שצברת
owned_skins = set()  # סקינים שקנית
selected_skin = -1  # הסקין הפעיל (-1 = העכביש המקורי)
banked_score = 0  # כמה נקודות מהמשחק הנוכחי כבר נכנסו לבנק
shop_message = ""
shop_message_time = 0
facing_left = False



def load_save():
    global total_points, owned_skins, selected_skin, high_score
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        total_points = int(data.get("total", 0))
        owned_skins = set(data.get("owned", []))
        selected_skin = int(data.get("selected", -1))
        high_score = int(data.get("high", 0))
        if selected_skin != -1 and selected_skin not in owned_skins:
            selected_skin = -1
    except Exception:
        pass


def write_save():
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump({"total": total_points, "owned": sorted(owned_skins),
                       "selected": selected_skin, "high": high_score}, f)
    except Exception:
        pass


def bank_score():
    global total_points, banked_score
    gained = score - banked_score
    if gained > 0:
        total_points += gained
    banked_score = score
    write_save()


load_save()
if total_points < DEBUG_MIN_POINTS:
    total_points = DEBUG_MIN_POINTS

skin_imgs = []
skin_imgs_flip = []
shop_imgs = []
shop_imgs_dim = []
for idx, data in enumerate(SKIN_DATA):
    try:
        png_bytes = base64.b64decode(data)
        raw = pygame.image.load(io.BytesIO(png_bytes), "skin.png").convert_alpha()
        game_img = pygame.transform.smoothscale(raw, (SKIN_SIZE, SKIN_SIZE))
        shop_img = pygame.transform.smoothscale(raw, (SHOP_SIZE, SHOP_SIZE))
        dim_img = shop_img.copy()
        dim_img.fill((90, 90, 90, 255), special_flags=pygame.BLEND_RGBA_MULT)
        skin_imgs.append(game_img)
        skin_imgs_flip.append(pygame.transform.flip(game_img, True, False))
        shop_imgs.append(shop_img)
        shop_imgs_dim.append(dim_img)
    except Exception as err:
        print("Skin load failed:", idx, err)
        skin_imgs.append(None)
        skin_imgs_flip.append(None)
        shop_imgs.append(None)
        shop_imgs_dim.append(None)

small_font = pygame.font.SysFont(None, 20)
tiny_font = pygame.font.SysFont(None, 17)

GRID_X0, GRID_Y0 = 20, 70
CELL_W, CELL_H = 72, 88
DEFAULT_BTN = pygame.Rect(20, 527, 170, 48)
BACK_BTN = pygame.Rect(210, 527, 170, 48)


def shop_cell_rect(i):
    col = i % 5
    row = i // 5
    return pygame.Rect(GRID_X0 + col * CELL_W, GRID_Y0 + row * CELL_H, CELL_W - 4, CELL_H - 4)


def fmt_price(n):
    if n >= 1000000:
        return f"{n / 1000000:g}M"
    if n >= 1000:
        return f"{n / 1000:g}K"
    return str(n)


def shop_click(i):
    global total_points, selected_skin, shop_message, shop_message_time
    sk = SKINS[i]
    if i in owned_skins:
        selected_skin = i
        shop_message = f"{sk.name} equipped"
    elif total_points >= sk.price:
        total_points -= sk.price
        owned_skins.add(i)
        selected_skin = i
        shop_message = f"Bought {sk.name}!"
    else:
        shop_message = f"Need {sk.price - total_points} more points"
    shop_message_time = pygame.time.get_ticks()
    write_save()


def draw_shop():
    screen.fill(SHOP_BG)
    title = title_font.render("Skin Shop", True, WHITE)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 12))
    pts = font.render(f"Points: {total_points}", True, (255, 215, 0))
    screen.blit(pts, (WIDTH // 2 - pts.get_width() // 2, 44))
    for i, sk in enumerate(SKINS):
        rect = shop_cell_rect(i)
        owned = i in owned_skins
        equipped = selected_skin == i
        affordable = total_points >= sk.price
        if equipped:
            bg, border, bw = (40, 110, 60), (80, 255, 120), 3
        elif owned:
            bg, border, bw = (45, 55, 85), WHITE, 2
        elif affordable:
            bg, border, bw = (50, 50, 70), (255, 215, 0), 2
        else:
            bg, border, bw = (30, 33, 50), (80, 85, 110), 1
        pygame.draw.rect(screen, bg, rect, border_radius=8)
        pygame.draw.rect(screen, border, rect, bw, border_radius=8)
        img = shop_imgs[i] if (owned or affordable) else shop_imgs_dim[i]
        if img is not None:
            screen.blit(img, (rect.centerx - SHOP_SIZE // 2, rect.y + 3))
        name_txt = tiny_font.render(sk.name, True, WHITE)
        screen.blit(name_txt, (rect.centerx - name_txt.get_width() // 2, rect.y + 49))
        if equipped:
            label, lcol = "Equipped", (120, 255, 150)
        elif owned:
            label, lcol = "Owned", WHITE
        else:
            label = fmt_price(sk.price)
            lcol = (255, 215, 0) if affordable else (255, 110, 110)
        txt = small_font.render(label, True, lcol)
        screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.bottom - 17))
    if shop_message and pygame.time.get_ticks() - shop_message_time < 2000:
        msg = small_font.render(shop_message, True, WHITE)
        screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, 509))
    for btn, color, text in ((DEFAULT_BTN, (120, 70, 160), "Default Spider"), (BACK_BTN, BUTTON_COLOR, "Back")):
        pygame.draw.rect(screen, color, btn, border_radius=10)
        pygame.draw.rect(screen, BLACK, btn, 2, border_radius=10)
        t = font.render(text, True, WHITE)
        screen.blit(t, (btn.centerx - t.get_width() // 2, btn.centery - t.get_height() // 2))


# ======================= העכביש (מצויר ברזולוציה פי 8 ומוקטן) =======================
def _build_spider(t):
    # t = 0 -> רגליים מקופלות (בעלייה), t = 1 -> רגליים פרושות (בנפילה)
    S = 8  # מציירים פי 8 גדול ואז מקטינים: קצוות חלקים לגמרי
    W, H = 64, 48
    surf = pygame.Surface((W * S, H * S), pygame.SRCALPHA)
    cx, cy = 32, 26
    rnd = random.Random(7)  # שערות קבועות, כדי שלא יהבהבו בין פריימים

    def P(x, y):
        return (int((cx + x) * S), int((cy + y) * S))

    def R(v):
        return max(1, int(v * S))

    def ell(x, y, w, h, col):
        px, py = P(x, y)
        pygame.draw.ellipse(surf, col, (px - R(w) // 2, py - R(h) // 2, R(w), R(h)))

    def glow(x, y, w, h, col, alpha):  # אליפסה חצי-שקופה (ברק)
        tmp = pygame.Surface((R(w) + 2, R(h) + 2), pygame.SRCALPHA)
        pygame.draw.ellipse(tmp, (col[0], col[1], col[2], alpha), (1, 1, R(w), R(h)))
        px, py = P(x, y)
        surf.blit(tmp, (px - R(w) // 2 - 1, py - R(h) // 2 - 1))

    def seg(a, b, w0, w1, col):  # קטע רגל מתחדד עם קצוות עגולים
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        pts = [(a[0] + nx * w0 / 2, a[1] + ny * w0 / 2), (b[0] + nx * w1 / 2, b[1] + ny * w1 / 2),
               (b[0] - nx * w1 / 2, b[1] - ny * w1 / 2), (a[0] - nx * w0 / 2, a[1] - ny * w0 / 2)]
        pygame.draw.polygon(surf, col, [P(*p) for p in pts])
        pygame.draw.circle(surf, col, P(*a), R(w0 / 2))
        pygame.draw.circle(surf, col, P(*b), R(w1 / 2))

    def shaded(x, y, w, h, dark, light, n, off):  # אליפסה עם צל וגרדיאנט (נפח)
        for i in range(n):
            f = i / (n - 1)
            ell(x - off[0] * f, y - off[1] * f, w * (1 - 0.7 * f), h * (1 - 0.7 * f), lerp_color(dark, light, f))

    LEG = (26, 22, 24)
    LEG_HI = (112, 94, 82)
    RING = (150, 115, 70)
    hips = [(3, -6), (4, -3), (4, 0), (3, 3)]
    kneeA = [(10, -14), (13, -9), (13, -1), (10, 7)]
    footA = [(17, -16), (22, -10), (21, 1), (14, 11)]
    kneeB = [(11, -17), (16, -12), (16, -2), (12, 9)]
    footB = [(21, -22), (27, -15), (27, 3), (18, 15)]

    def mix(a, b, f):
        return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)

    # ---------- רגליים (מאחורי הגוף) ----------
    for i in range(4):
        for side in (-1, 1):
            tt = min(1.0, max(0.0, t + (0.12 if (i + (side > 0)) % 2 else -0.12)))  # קצת א-סימטריה = חיים
            h = (side * hips[i][0], hips[i][1])
            k0, k1 = mix(kneeA[i], kneeB[i], tt), mix(footA[i], footB[i], tt)
            k = (side * k0[0], k0[1])
            f = (side * k1[0], k1[1])
            seg(h, k, 2.8, 2.2, LEG)
            seg(k, f, 2.2, 0.9, LEG)
            seg((h[0], h[1] - 0.4), (k[0], k[1] - 0.4), 0.7, 0.6, LEG_HI)  # פס ברק
            seg((k[0], k[1] - 0.3), (f[0], f[1] - 0.3), 0.6, 0.3, LEG_HI)
            pygame.draw.circle(surf, RING, P(*k), R(1.0))  # טבעת במפרק הברך
            pygame.draw.circle(surf, LEG, P(*k), R(0.55))
            for q in (0.3, 0.55, 0.8):  # שערות קטנות על הרגל
                bx, by = h[0] + (k[0] - h[0]) * q, h[1] + (k[1] - h[1]) * q
                pygame.draw.line(surf, (70, 58, 52), P(bx, by), P(bx + side * 0.6, by - 1.3), R(0.25))
                bx, by = k[0] + (f[0] - k[0]) * q, k[1] + (f[1] - k[1]) * q
                pygame.draw.line(surf, (70, 58, 52), P(bx, by), P(bx + side * 0.5, by - 1.1), R(0.2))

    # ---------- בטן ----------
    shaded(0, 9, 18, 23, (10, 9, 12), (74, 66, 76), 14, (2.0, 4.0))
    glow(-2.6, 3.8, 5.5, 7.5, (255, 255, 255), 70)  # ברק מבריק על הבטן
    glow(-3.0, 2.6, 2.0, 3.0, (255, 255, 255), 140)
    # סימן שעון חול אדום
    red, red_hi = (205, 20, 24), (255, 90, 70)
    pygame.draw.polygon(surf, red, [P(-3.2, 6.2), P(3.2, 6.2), P(0, 10.2)])
    pygame.draw.polygon(surf, red, [P(-3.8, 14.2), P(3.8, 14.2), P(0, 10.2)])
    pygame.draw.polygon(surf, red_hi, [P(-1.2, 6.8), P(1.2, 6.8), P(0, 8.4)])
    # שערות על קצה הבטן
    for _ in range(26):
        a = rnd.uniform(0, math.pi * 2)
        ex, ey = math.cos(a) * 8.6, 9 + math.sin(a) * 11.2
        pygame.draw.line(surf, (58, 50, 54), P(ex, ey), P(ex * 1.1, 9 + (ey - 9) * 1.1), R(0.25))

    # ---------- מותן, חזה וראש ----------
    ell(0, -0.5, 5, 4.5, (14, 12, 14))
    shaded(0, -4.5, 13, 12, (14, 12, 15), (88, 78, 82), 10, (1.2, 1.8))
    glow(-1.6, -6.4, 4.5, 3.0, (255, 255, 255), 90)

    # ---------- מחושים וניבים ----------
    for side in (-1, 1):
        seg((side * 2.6, -9.0), (side * 4.4, -12.6), 1.5, 1.1, (40, 32, 34))
        pygame.draw.circle(surf, (60, 48, 46), P(side * 4.5, -12.9), R(1.0))
        seg((side * 1.3, -10.4), (side * 0.9, -13.2), 1.4, 0.5, (86, 48, 40))  # ניב
        pygame.draw.circle(surf, (210, 150, 120), P(side * 0.9, -13.3), R(0.3))

    # ---------- 8 עיניים ----------
    for side in (-1, 1):
        pygame.draw.circle(surf, (120, 8, 10), P(side * 1.9, -8.6), R(1.9))
        pygame.draw.circle(surf, (225, 30, 30), P(side * 1.9, -8.6), R(1.5))
        pygame.draw.circle(surf, (255, 235, 235), P(side * 1.9 - 0.45, -9.1), R(0.5))
        for ex, ey, er in ((3.5, -7.6, 0.95), (3.2, -5.8, 0.8), (1.0, -6.6, 0.7)):
            pygame.draw.circle(surf, (35, 6, 8), P(side * ex, ey), R(er + 0.25))
            pygame.draw.circle(surf, (170, 22, 24), P(side * ex, ey), R(er))
            pygame.draw.circle(surf, (255, 220, 220), P(side * ex - 0.2, ey - 0.25), R(0.25))
    return pygame.transform.smoothscale(surf, (W, H))


SPIDER_FRAMES = [_build_spider(t) for t in (0.0, 0.33, 0.66, 1.0)]  # 4 פריימים של תנועת רגליים
SPIDER_CYCLE = [0, 1, 2, 3, 2, 1]  # סדר האנימציה בתפריט


def draw_spider(px, py):
    if game_state == "PLAYING":
        frame = 0 if player_y_velocity < 0 else 3  # בעלייה רגליים מקופלות, בנפילה פרושות
    else:
        frame = SPIDER_CYCLE[(pygame.time.get_ticks() // 140) % len(SPIDER_CYCLE)]  # אנימציה בתפריט
    screen.blit(SPIDER_FRAMES[frame], (px + 17 - 32, py + 13 - 28))  # ממורכז על תיבת ההתנגשות


def draw_player(px, py):
    if selected_skin == -1 or skin_imgs[selected_skin] is None:
        draw_spider(px, py)
        return
    img = skin_imgs_flip[selected_skin] if facing_left else skin_imgs[selected_skin]
    screen.blit(img, (px + player_width // 2 - SKIN_SIZE // 2, py + player_height - SKIN_SIZE + 2))


game_state = "MENU"
running = True
countdown_start_time = 0
shown_theme = None
banner_start = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            if game_state in ("PLAYING", "COUNTDOWN"):
                bank_score()
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            if game_state == "MENU":
                if 100 <= mouse_x <= 300 and 320 <= mouse_y <= 380:
                    score = 0
                    saved_hearts = 0
                    next_heart_score = 30000
                    reset_game(keep_hearts=True)
                    score = DEBUG_START_SCORE
                    next_booster_score = score + 750
                    next_heart_score = (score // 30000 + 1) * 30000
                    shown_theme = None
                    banked_score = DEBUG_START_SCORE  # נקודות הבדיקה לא נכנסות לבנק
                    game_state = "PLAYING"
                elif 100 <= mouse_x <= 300 and 400 <= mouse_y <= 460:
                    game_state = "SHOP"
            elif game_state == "SHOP":
                for i in range(len(SKINS)):
                    if shop_cell_rect(i).collidepoint(mouse_x, mouse_y):
                        shop_click(i)
                if DEFAULT_BTN.collidepoint(mouse_x, mouse_y):
                    selected_skin = -1
                    write_save()
                elif BACK_BTN.collidepoint(mouse_x, mouse_y):
                    game_state = "MENU"
            elif game_state == "GAME_OVER":
                if saved_hearts > 0 and 100 <= mouse_x <= 300 and 260 <= mouse_y <= 320:
                    saved_hearts -= 1
                    revive_y = water_y - 70
                    if revive_y < 50:
                        revive_y = 50
                    if platforms:
                        platforms[0].x = WIDTH // 2 - 37
                        platforms[0].y = revive_y
                    player_x = WIDTH // 2 - player_width // 2
                    player_y = revive_y - player_height
                    player_y_velocity = 0

                    countdown_start_time = pygame.time.get_ticks()
                    game_state = "COUNTDOWN"
                elif 100 <= mouse_x <= 300 and 340 <= mouse_y <= 400:
                    reset_game()
                    game_state = "MENU"

    # אינדקס הרקע החדש הנוכחי (None אם עדיין לא הגענו ל-30,000)
    theme_idx = get_theme_index(score) if game_state in ("PLAYING", "COUNTDOWN") else None
    th_cur = THEMES[theme_idx] if theme_idx is not None else None

    if game_state in ("PLAYING", "COUNTDOWN") and theme_idx != shown_theme:
        shown_theme = theme_idx
        banner_start = pygame.time.get_ticks()

    if game_state in ["PLAYING", "COUNTDOWN"]:
        if score >= 25000:
            current_bg = PURPLE_BG
        elif score < 3000:
            factor = score / 3000
            r = int(SKY_BLUE[0] + (PURPLE_SPACE[0] - SKY_BLUE[0]) * factor)
            g = int(SKY_BLUE[1] + (PURPLE_SPACE[1] - SKY_BLUE[1]) * factor)
            b = int(SKY_BLUE[2] + (PURPLE_SPACE[2] - SKY_BLUE[2]) * factor)
            current_bg = (r, g, b)
        elif score < 7000:
            factor = (score - 3000) / 4000
            r = int(PURPLE_SPACE[0] + (SPACE_BLACK[0] - PURPLE_SPACE[0]) * factor)
            g = int(PURPLE_SPACE[1] + (SPACE_BLACK[1] - PURPLE_SPACE[1]) * factor)
            b = int(PURPLE_SPACE[2] + (SPACE_BLACK[2] - PURPLE_SPACE[2]) * factor)
            current_bg = (r, g, b)
        elif score < 10000:
            current_bg = SPACE_BLACK
        elif score < 15000:
            factor = min(1.0, (score - 10000) / 800)
            r = int(SPACE_BLACK[0] + (VALENTINE_PINK[0] - SPACE_BLACK[0]) * factor)
            g = int(SPACE_BLACK[1] + (VALENTINE_PINK[1] - SPACE_BLACK[1]) * factor)
            b = int(SPACE_BLACK[2] + (VALENTINE_PINK[2] - SPACE_BLACK[2]) * factor)
            current_bg = (r, g, b)
        elif score < 20000:
            factor = min(1.0, (score - 15000) / 1000)
            r = int(VALENTINE_PINK[0] + (LAVA_RED[0] - VALENTINE_PINK[0]) * factor)
            g = int(VALENTINE_PINK[1] + (LAVA_RED[1] - VALENTINE_PINK[1]) * factor)
            b = int(VALENTINE_PINK[2] + (LAVA_RED[2] - VALENTINE_PINK[2]) * factor)
            current_bg = (r, g, b)
        else:
            factor = min(1.0, (score - 20000) / 1000)
            r = int(LAVA_RED[0] + (ICE_BLUE[0] - LAVA_RED[0]) * factor)
            g = int(LAVA_RED[1] + (ICE_BLUE[1] - LAVA_RED[1]) * factor)
            b = int(LAVA_RED[2] + (ICE_BLUE[2] - LAVA_RED[2]) * factor)
            current_bg = (r, g, b)
    else:
        current_bg = SKY_BLUE

    screen.fill(current_bg)
    if theme_idx is not None:
        draw_theme_background(theme_idx, score)

    if game_state == "MENU":
        title_text = title_font.render("Spider Adventure", True, BLACK)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 150))

        high_score_text = font.render(f"High Score: {high_score}", True, BLACK)
        screen.blit(high_score_text, (WIDTH // 2 - high_score_text.get_width() // 2, 230))

        button_rect = pygame.Rect(100, 320, 200, 60)
        pygame.draw.rect(screen, BUTTON_COLOR, button_rect, border_radius=10)
        pygame.draw.rect(screen, BLACK, button_rect, 2, border_radius=10)

        start_text = font.render("Start Game", True, WHITE)
        screen.blit(start_text, (button_rect.centerx - start_text.get_width() // 2, button_rect.centery - start_text.get_height() // 2))

        if selected_skin != -1 and skin_imgs[selected_skin] is not None:
            big = pygame.transform.smoothscale(skin_imgs[selected_skin], (80, 80))
            screen.blit(big, (WIDTH // 2 - 40, 60))
        else:
            draw_spider(WIDTH // 2 - 17, 90)
        points_text = font.render(f"Points: {total_points}", True, BLACK)
        screen.blit(points_text, (WIDTH // 2 - points_text.get_width() // 2, 265))
        shop_rect = pygame.Rect(100, 400, 200, 60)
        pygame.draw.rect(screen, (255, 165, 0), shop_rect, border_radius=10)
        pygame.draw.rect(screen, BLACK, shop_rect, 2, border_radius=10)
        shop_text = font.render("Skins", True, WHITE)
        screen.blit(shop_text, (shop_rect.centerx - shop_text.get_width() // 2, shop_rect.centery - shop_text.get_height() // 2))

    elif game_state == "SHOP":
        draw_shop()

    elif game_state == "GAME_OVER":
        game_over_text = title_font.render("Game Over", True, BLACK)
        screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, 150))

        final_score_text = font.render(f"Score: {score}", True, BLACK)
        screen.blit(final_score_text, (WIDTH // 2 - final_score_text.get_width() // 2, 210))

        if saved_hearts > 0:
            revive_rect = pygame.Rect(100, 260, 200, 50)
            pygame.draw.rect(screen, (255, 100, 150), revive_rect, border_radius=10)
            pygame.draw.rect(screen, BLACK, revive_rect, 2, border_radius=10)
            revive_text = font.render(f"Revive (Hearts: {saved_hearts})", True, WHITE)
            screen.blit(revive_text, (revive_rect.centerx - revive_text.get_width() // 2, revive_rect.centery - revive_text.get_height() // 2))

        menu_rect = pygame.Rect(100, 340, 200, 50)
        pygame.draw.rect(screen, BUTTON_COLOR, menu_rect, border_radius=10)
        pygame.draw.rect(screen, BLACK, menu_rect, 2, border_radius=10)
        menu_text = font.render("Main Menu", True, WHITE)
        screen.blit(menu_text, (menu_rect.centerx - menu_text.get_width() // 2, menu_rect.centery - menu_text.get_height() // 2))

    elif game_state in ["PLAYING", "COUNTDOWN"]:
        scroll_diff = 0
        if game_state == "PLAYING":
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_x -= 6
                facing_left = True
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player_x += 6
                facing_left = False

            if player_x < 0:
                player_x = 0
            elif player_x > WIDTH - player_width:
                player_x = WIDTH - player_width

            player_y_velocity += gravity
            player_y += player_y_velocity

            for p in platforms:
                if (player_x + player_width > p.x and player_x < p.x + p.width and
                        player_y + player_height >= p.y and player_y + player_height <= p.y + p.height + 10 and
                        player_y_velocity > 0):
                    player_y_velocity = jump_strength

            player_rect = pygame.Rect(player_x, player_y, player_width, player_height)

            for b in boosters:
                if b.active:
                    b_rect = pygame.Rect(b.x - b.radius, b.y - b.radius, b.radius * 2, b.radius * 2)
                    if player_rect.colliderect(b_rect):
                        player_y_velocity = super_jump_strength
                        b.active = False

            for h_item in collectible_hearts:
                if h_item.active:
                    h_rect = pygame.Rect(h_item.x - 15, h_item.y - 15, 30, 30)
                    if player_rect.colliderect(h_rect):
                        saved_hearts += 1
                        h_item.active = False

            if player_y < HEIGHT // 2:
                diff = HEIGHT // 2 - player_y
                player_y = HEIGHT // 2
                score += int(diff)
                scroll_diff = diff

                water_speed = 1.2 + (score / 3000)
                if water_speed > 2.0:
                    water_speed = 2.0
                if th_cur is not None:
                    water_speed *= th_cur.speed  # לכל רקע יש מהירות רעל משלו

                if score >= next_booster_score:
                    next_booster_score += 750
                    if platforms:
                        p = random.choice(platforms)
                        boosters.append(Booster(p.x + p.width // 2, p.y - 35))

                if score >= next_heart_score:
                    next_heart_score += 30000
                    if platforms:
                        p = random.choice(platforms)
                        collectible_hearts.append(CollectibleHeart(p.x + p.width // 2, p.y - 35))

                for p in platforms:
                    p.y += diff
                    if p.y > HEIGHT:
                        min_y = min(pl.y for pl in platforms)
                        p.y = min_y - random.randint(50, 75)
                        p.x = random.randint(20, WIDTH - 95)

                for b in boosters:
                    b.y += diff

                for h_item in collectible_hearts:
                    h_item.y += diff

                water_y += diff
                for bubble in bubbles:
                    bubble.y += diff
                for star in stars:
                    star.y += diff * 0.2
                    if star.y > HEIGHT:
                        star.y = -10
                        star.x = random.randint(0, WIDTH)

                if 10000 <= score < 15000:
                    for heart in hearts:
                        heart.y += diff * 0.4
                        if heart.y > HEIGHT:
                            min_heart_y = min((h.y for h in hearts), default=0)
                            heart.y = min_heart_y - random.randint(50, 90)
                            heart.x = random.randint(20, WIDTH - 20)
                            heart.color = random.choice([(255, 30, 80), (255, 80, 120), (255, 0, 60)])

                if 15000 <= score < 20000:
                    for lava in lava_rocks:
                        lava.y += diff * 0.4
                        if lava.y > HEIGHT:
                            min_lava_y = min((l.y for l in lava_rocks), default=0)
                            lava.y = min_lava_y - random.randint(50, 90)
                            lava.x = random.randint(20, WIDTH - 20)

                if 20000 <= score < 25000:
                    for ice in ice_crystals:
                        ice.y += diff * 0.4
                        if ice.y > HEIGHT:
                            min_ice_y = min((i.y for i in ice_crystals), default=0)
                            ice.y = min_ice_y - random.randint(50, 90)
                            ice.x = random.randint(20, WIDTH - 20)

            water_y -= water_speed
            if water_y > HEIGHT:
                water_y = HEIGHT

            if water_y < HEIGHT and (score < 25000 or theme_idx is not None) and random.randint(1, 10) == 1:
                bubble_x = random.randint(10, WIDTH - 10)
                bubbles.append(Bubble(bubble_x, HEIGHT - 10))

            for bubble in bubbles[:]:
                bubble.y -= bubble.speed
                if bubble.y < water_y:
                    bubbles.remove(bubble)

            if th_cur is not None:
                update_deco(th_cur.deco, scroll_diff)

            if player_y + player_height >= water_y:
                if score > high_score:
                    high_score = score
                game_state = "GAME_OVER"
                bank_score()

        # ציור אלמנטים ברקע לפי שלבים
        if score >= 2500 and score < 10000:
            for star in stars:
                pygame.draw.circle(screen, STAR_COLOR, (star.x, star.y), star.size)

        if 10000 <= score < 15000:
            for h in hearts:
                hx, hy, sz = int(h.x), int(h.y), h.size
                pygame.draw.circle(screen, h.color, (hx - sz // 3, hy - sz // 3), sz // 2)
                pygame.draw.circle(screen, h.color, (hx + sz // 3, hy - sz // 3), sz // 2)
                pygame.draw.polygon(screen, h.color, [(hx - sz, hy - sz // 4), (hx + sz, hy - sz // 4), (hx, hy + sz)])

        if 15000 <= score < 20000:
            for lava in lava_rocks:
                pygame.draw.circle(screen, (255, 100, 0), (int(lava.x), int(lava.y)), lava.size)
                pygame.draw.circle(screen, (255, 200, 0), (int(lava.x), int(lava.y)), lava.size // 2)

        if 20000 <= score < 25000:
            for ice in ice_crystals:
                pygame.draw.polygon(screen, (220, 245, 255), [
                    (ice.x, ice.y - ice.size),
                    (ice.x - ice.size // 2, ice.y),
                    (ice.x, ice.y + ice.size),
                    (ice.x + ice.size // 2, ice.y)
                ])

        if th_cur is not None:
            draw_deco(th_cur.deco, th_cur.dcols)

        # ציור פלטפורמות
        for p in platforms:
            if th_cur is not None:
                PLATFORM_STYLES[th_cur.plat](int(p.x), int(p.y), p.width, p.height, th_cur.pcols)
            elif score >= 25000:
                p_rect = pygame.Rect(p.x, p.y, p.width, p.height)
                pygame.draw.rect(screen, WHITE, p_rect, border_radius=4)
                pygame.draw.rect(screen, BLACK, p_rect, 2, border_radius=4)
                pygame.draw.line(screen, RED, (p.x + 4, p.y + 4), (p.x + p.width - 4, p.y + p.height - 4), 3)
                pygame.draw.line(screen, RED, (p.x + p.width - 4, p.y + 4), (p.x + 4, p.y + p.height - 4), 3)
            elif score < 2500:
                pygame.draw.rect(screen, DIRT_SHADOW, (p.x, p.y + p.height - 4, p.width, 4))
                pygame.draw.rect(screen, DIRT_BROWN, (p.x, p.y, p.width, p.height - 4))
                pygame.draw.rect(screen, GRASS_GREEN, (p.x, p.y, p.width, 5))
            elif score < 10000:
                p_rect = pygame.Rect(p.x, p.y, p.width, p.height)
                pygame.draw.rect(screen, (70, 80, 95), p_rect, border_radius=6)
                pygame.draw.rect(screen, (30, 35, 45), p_rect, 2, border_radius=6)
                pygame.draw.line(screen, (0, 235, 255), (p.x + 8, p.y + 5), (p.x + p.width - 8, p.y + 5), 2)
                pygame.draw.line(screen, (255, 215, 0), (p.x + 15, p.y + 11), (p.x + p.width - 15, p.y + 11), 2)
            elif score < 15000:
                p_rect = pygame.Rect(p.x, p.y, p.width, p.height)
                pygame.draw.rect(screen, VALENTINE_PINK, p_rect, border_radius=8)
                pygame.draw.rect(screen, (255, 80, 120), p_rect, 2, border_radius=8)
                for h_x in [p.x + 15, p.x + 37, p.x + 60]:
                    h_y = p.y + 8
                    pygame.draw.circle(screen, (255, 0, 60), (h_x - 3, h_y - 2), 3)
                    pygame.draw.circle(screen, (255, 0, 60), (h_x + 3, h_y - 2), 3)
                    pygame.draw.polygon(screen, (255, 0, 60), [(h_x - 6, h_y - 1), (h_x + 6, h_y - 1), (h_x, h_y + 5)])
            elif score < 20000:
                p_rect = pygame.Rect(p.x, p.y, p.width, p.height)
                pygame.draw.rect(screen, (15, 15, 20), p_rect, border_radius=8)
                pygame.draw.rect(screen, (50, 50, 60), p_rect, 2, border_radius=8)
                pygame.draw.ellipse(screen, (120, 120, 130), (p.x + 6, p.y + 3, 18, 10))
                pygame.draw.ellipse(screen, (90, 90, 100), (p.x + 28, p.y + 4, 22, 9))
                pygame.draw.ellipse(screen, (120, 120, 130), (p.x + 54, p.y + 3, 15, 10))
            else:
                p_rect = pygame.Rect(p.x, p.y, p.width, p.height)
                pygame.draw.rect(screen, ICE_BLUE, p_rect, border_radius=8)
                pygame.draw.rect(screen, (100, 180, 245), p_rect, 2, border_radius=8)
                pygame.draw.polygon(screen, (30, 100, 220), [(p.x + 8, p.y + 13), (p.x + 18, p.y + 3), (p.x + 26, p.y + 13)])
                pygame.draw.polygon(screen, (0, 150, 240), [(p.x + 28, p.y + 13), (p.x + 42, p.y + 4), (p.x + 50, p.y + 13)])
                pygame.draw.polygon(screen, (30, 80, 200), [(p.x + 52, p.y + 13), (p.x + 62, p.y + 3), (p.x + 68, p.y + 13)])

        for b in boosters:
            if b.active:
                pygame.draw.circle(screen, BOOSTER_YELLOW, (int(b.x), int(b.y)), b.radius)
                pygame.draw.polygon(screen, BOOSTER_RED, [
                    (b.x, b.y - 12), (b.x - 10, b.y + 8), (b.x - 4, b.y + 8),
                    (b.x - 4, b.y + 12), (b.x + 4, b.y + 12), (b.x + 4, b.y + 8), (b.x + 10, b.y + 8)
                ])
                pygame.draw.polygon(screen, BOOSTER_ORANGE, [
                    (b.x, b.y - 7), (b.x - 6, b.y + 6), (b.x - 2, b.y + 6),
                    (b.x - 2, b.y + 9), (b.x + 2, b.y + 9), (b.x + 2, b.y + 6), (b.x + 6, b.y + 6)
                ])

        for h_item in collectible_hearts:
            if h_item.active:
                hx, hy = int(h_item.x), int(h_item.y)
                pygame.draw.circle(screen, HEART_RED, (hx - 6, hy - 4), 8)
                pygame.draw.circle(screen, HEART_RED, (hx + 6, hy - 4), 8)
                pygame.draw.polygon(screen, HEART_RED, [(hx - 14, hy - 1), (hx + 14, hy - 1), (hx, hy + 13)])

        # ציור השחקן: העכביש או הסקין שנבחר בחנות
        draw_player(player_x, player_y)

        # ציור נוזל / רעל בתחתית לפי השלב
        if water_y < HEIGHT:
            if th_cur is not None:
                POISON_STYLES[th_cur.poison](int(water_y), th_cur.qcols, pygame.time.get_ticks())
                if th_cur.poison not in NO_BUBBLE_STYLES:
                    for bubble in bubbles:
                        pygame.draw.circle(screen, th_cur.qcols[2], (int(bubble.x), int(bubble.y)), bubble.radius)
            elif score >= 25000:
                pygame.draw.rect(screen, ORANGE_POISON, (0, water_y, WIDTH, HEIGHT - water_y))
            elif score < 15000:
                pygame.draw.rect(screen, RADIOACTIVE_GREEN, (0, water_y, WIDTH, HEIGHT - water_y))
                for bubble in bubbles:
                    pygame.draw.circle(screen, BUBBLE_COLOR, (int(bubble.x), int(bubble.y)), bubble.radius)
            elif score < 20000:
                pygame.draw.rect(screen, (220, 50, 0), (0, water_y, WIDTH, HEIGHT - water_y))
                for bubble in bubbles:
                    pygame.draw.circle(screen, (255, 200, 0), (int(bubble.x), int(bubble.y)), bubble.radius)
            else:
                pygame.draw.rect(screen, ICE_BLUE, (0, water_y, WIDTH, HEIGHT - water_y))
                pygame.draw.line(screen, WHITE, (0, water_y), (WIDTH, water_y), 4)

        draw_text(font, f"Score: {score}", WHITE, (10, 10))
        draw_text(font, f"Hearts: {saved_hearts}", WHITE, (10, 40))

        # שם הרקע מופיע כמה שניות כשנכנסים לשלב חדש
        if theme_idx is not None and pygame.time.get_ticks() - banner_start < 2500:
            banner_text = f"{theme_idx + 1}. {th_cur.name}"
            bw = title_font.size(banner_text)[0]
            draw_text(title_font, banner_text, (255, 255, 120), (WIDTH // 2 - bw // 2, 80))

        if game_state == "COUNTDOWN":
            elapsed = pygame.time.get_ticks() - countdown_start_time
            if elapsed < 1000:
                count_text = "3"
            elif elapsed < 2000:
                count_text = "2"
            elif elapsed < 3000:
                count_text = "1"
            else:
                game_state = "PLAYING"
                count_text = ""

            if count_text:
                rendered_count = countdown_font.render(count_text, True, (255, 255, 0))
                screen.blit(rendered_count, (WIDTH // 2 - rendered_count.get_width() // 2, HEIGHT // 2 - 50))

    pygame.display.flip()
    clock.tick(60)

write_save()  # שמירה אחרונה לפני היציאה
pygame.quit()
