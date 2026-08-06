"""
Generate 8 realistic product images (200x200) using Pillow.
Replaces simple placeholders with more detailed, product-like images.
"""
import os, sys, io, base64, math
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

SIZE = 200
OUT_DIR = os.path.expanduser("~/projects/retail-sense/images/products")
os.makedirs(OUT_DIR, exist_ok=True)

# Try to find a usable font
FONT_PATHS = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Arial.ttf",
]
font_small = None
font_large = None
for fp in FONT_PATHS:
    if os.path.exists(fp):
        try:
            font_small = ImageFont.truetype(fp, 11)
            font_large = ImageFont.truetype(fp, 14)
            break
        except:
            pass

if font_small is None:
    font_small = ImageFont.load_default()
    font_large = ImageFont.load_default()


def circle_mask(draw, cx, cy, r, fill):
    """Draw a filled circle."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)


def draw_rounded_rect(draw, xy, r, fill, outline=None, width=1):
    """Draw a rounded rectangle."""
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle([x1, y1, x2, y2], radius=r, fill=fill, outline=outline, width=width)


def add_noise(img, amount=8):
    """Add subtle noise texture."""
    import random
    pixels = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if a > 0:
                n = random.randint(-amount, amount)
                pixels[x, y] = (
                    max(0, min(255, r + n)),
                    max(0, min(255, g + n)),
                    max(0, min(255, b + n)),
                    a,
                )


# ============================================================
# 1. DOG TAG (刻字狗牌) - Silver metal disc with laser engraving
# ============================================================
def make_dog_tag():
    img = Image.new("RGBA", (SIZE, SIZE), (245, 240, 235, 255))
    draw = ImageDraw.Draw(img)

    # Background: dark fabric/wood texture
    for y in range(SIZE):
        for x in range(SIZE):
            v = 60 + int(15 * math.sin(x * 0.05) * math.cos(y * 0.05))
            draw.point((x, y), (v, int(v * 0.95), int(v * 0.85), 255))

    # Silver metal plate (rounded rectangle)
    cx, cy = SIZE // 2, SIZE // 2
    plate_w, plate_h = 120, 80
    plate_x1, plate_y1 = cx - plate_w // 2, cy - plate_h // 2
    plate_x2, plate_y2 = cx + plate_w // 2, cy + plate_h // 2

    # Shadow
    draw.rounded_rectangle(
        [plate_x1 + 3, plate_y1 + 3, plate_x2 + 3, plate_y2 + 3],
        radius=15, fill=(0, 0, 0, 80)
    )

    # Metal gradient
    for i in range(plate_h):
        t = i / plate_h
        gray = int(140 + 60 * math.sin(t * math.pi))
        y_pos = plate_y1 + i
        draw.line(
            [(plate_x1 + 10, y_pos), (plate_x2 - 10, y_pos)],
            fill=(gray, gray, gray + 5, 255)
        )

    # Metal border
    draw.rounded_rectangle(
        [plate_x1, plate_y1, plate_x2, plate_y2],
        radius=15, outline=(100, 100, 105, 255), width=2
    )

    # Engraving lines (laser-etched look)
    for i, (text, y_off) in enumerate([
        ("MAX", -18), ("★", -5), ("123-456", 8), ("☎ 555-0199", 20)
    ]):
        tw = draw.textlength(text, font=font_small) if hasattr(draw, 'textlength') else len(text) * 7
        draw.text(
            (cx - tw // 2, cy + y_off), text,
            fill=(60, 58, 55, 255), font=font_small
        )

    # Bone icon (small)
    bone_cx, bone_cy = cx + 40, cy - 18
    circle_mask(draw, bone_cx - 8, bone_cy, 5, (90, 88, 85, 255))
    circle_mask(draw, bone_cx + 8, bone_cy, 5, (90, 88, 85, 255))
    draw.rectangle([bone_cx - 8, bone_cy - 3, bone_cx + 8, bone_cy + 3], fill=(90, 88, 85, 255))

    # Hole at top
    hole_cx, hole_cy = cx, cy - plate_h // 2 - 2
    circle_mask(draw, hole_cx, hole_cy, 5, (50, 48, 45, 255))
    circle_mask(draw, hole_cx, hole_cy, 3, (80, 78, 75, 255))

    # Key ring
    draw.ellipse(
        [hole_cx - 10, hole_cy - 12, hole_cx + 10, hole_cy + 8],
        outline=(120, 120, 125, 255), width=2
    )

    # Highlight/reflection
    for i in range(15):
        alpha = int(40 - i * 2.5)
        draw.line(
            [(plate_x1 + 20 + i, plate_y1 + 8 + i), (plate_x1 + 20 + i, plate_y1 + 30 + i)],
            fill=(255, 255, 255, max(0, alpha))
        )

    return img


# ============================================================
# 2. LED COLLAR (发光项圈) - Green glowing LED collar on dark bg
# ============================================================
def make_led_collar():
    img = Image.new("RGBA", (SIZE, SIZE), (10, 10, 15, 255))
    draw = ImageDraw.Draw(img)

    # Dark background with subtle gradient
    for y in range(SIZE):
        t = y / SIZE
        v = int(10 + 20 * t)
        draw.line([(0, y), (SIZE, y)], fill=(v, v, v + 5, 255))

    # Glow aura
    cx, cy = SIZE // 2, SIZE // 2
    for r in range(80, 30, -2):
        alpha = int(8 * (1 - (r - 30) / 50))
        draw.ellipse([cx - r, cy - r + 15, cx + r, cy + r + 15], fill=(0, 255, 50, alpha))

    # Collar band (curved)
    points = []
    for angle_deg in range(30, 331, 3):
        angle = math.radians(angle_deg)
        r = 65 + 10 * math.sin(angle * 3)  # slight wavy
        px = cx + r * math.cos(angle)
        py = cy + 10 + r * math.sin(angle)
        points.append((px, py))

    # Draw thick collar band
    for i in range(len(points) - 1):
        draw.line([points[i], points[i + 1]], fill=(20, 20, 25, 255), width=12)

    # Draw glowing LED strip
    for i in range(len(points) - 1):
        draw.line([points[i], points[i + 1]], fill=(0, 220, 40, 255), width=4)

    # Individual LED dots
    for i in range(0, len(points), 5):
        px, py = points[i]
        # Glow
        for gr in range(5, 1, -1):
            draw.ellipse(
                [px - gr, py - gr, px + gr, py + gr],
                fill=(0, 255, 60, 40)
            )
        draw.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(0, 255, 80, 255))

    # Buckle/clasp
    buckle_x, buckle_y = cx, cy + 10 + 70
    draw.rounded_rectangle(
        [buckle_x - 15, buckle_y - 8, buckle_x + 15, buckle_y + 8],
        radius=4, fill=(60, 60, 65, 255), outline=(100, 100, 105, 255), width=1
    )
    draw.rectangle(
        [buckle_x - 6, buckle_y - 4, buckle_x + 6, buckle_y + 4],
        fill=(80, 80, 85, 255)
    )

    # USB charging port indicator
    draw.ellipse([buckle_x + 10, buckle_y - 3, buckle_x + 14, buckle_y + 1], fill=(0, 200, 0, 255))

    return img


# ============================================================
# 3. ENAMEL PLATE (珐琅名牌) - Vintage copper with enamel patterns
# ============================================================
def make_enamel_plate():
    img = Image.new("RGBA", (SIZE, SIZE), (240, 235, 225, 255))
    draw = ImageDraw.Draw(img)

    # Soft background (velvet/fabric)
    for y in range(SIZE):
        v = int(230 + 10 * math.sin(y * 0.1))
        draw.line([(0, y), (SIZE, y)], fill=(v, v - 5, v - 10, 255))

    cx, cy = SIZE // 2, SIZE // 2 + 5

    # Shield shape
    shield_points = [
        (cx, cy - 70),      # top center
        (cx - 45, cy - 50), # top left
        (cx - 50, cy - 20), # mid left
        (cx - 50, cy + 10), # lower left
        (cx, cy + 55),      # bottom point
        (cx + 50, cy + 10), # lower right
        (cx + 50, cy - 20), # mid right
        (cx + 45, cy - 50), # top right
    ]

    # Shadow
    draw.polygon([(p[0] + 3, p[1] + 3) for p in shield_points], fill=(0, 0, 0, 60))

    # Copper base
    draw.polygon(shield_points, fill=(184, 115, 51, 255), outline=(139, 69, 19, 255))

    # Copper gradient overlay - simplified
    # Inner decorative border
    inner_points = [(int(p[0] * 0.85 + cx * 0.15), int(p[1] * 0.85 + (cy + 5) * 0.15)) for p in shield_points]
    draw.polygon(inner_points, outline=(100, 60, 20, 255), fill=None)

    # Enamel pattern - floral design in blue/white
    # Center circle
    circle_mask(draw, cx, cy - 5, 18, (30, 60, 140, 230))
    circle_mask(draw, cx, cy - 5, 14, (255, 255, 255, 255))
    circle_mask(draw, cx, cy - 5, 8, (200, 180, 50, 255))

    # Petal-like decorations
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        petal_x = cx + int(25 * math.cos(rad))
        petal_y = cy - 5 + int(25 * math.sin(rad))
        draw.ellipse(
            [petal_x - 6, petal_y - 10, petal_x + 6, petal_y + 10],
            fill=(30, 70, 160, 220)
        )
        # Petal outline
        draw.ellipse(
            [petal_x - 7, petal_y - 11, petal_x + 7, petal_y + 11],
            outline=(255, 255, 255, 180), width=1
        )

    # Small dots around
    for angle in range(15, 360, 30):
        rad = math.radians(angle)
        dot_x = cx + int(38 * math.cos(rad))
        dot_y = cy - 5 + int(38 * math.sin(rad))
        draw.ellipse([dot_x - 2, dot_y - 2, dot_x + 2, dot_y + 2], fill=(255, 255, 255, 255))

    # Border
    draw.polygon(shield_points, outline=(139, 69, 19, 255), fill=None)

    # Inner border
    inner_points = [(p[0] * 0.85 + cx * 0.15, p[1] * 0.85 + (cy + 5) * 0.15) for p in shield_points]
    draw.polygon(inner_points, outline=(100, 60, 20, 255), fill=None)

    # Ring at top
    ring_cx, ring_cy = cx, cy - 72
    draw.ellipse(
        [ring_cx - 8, ring_cy - 10, ring_cx + 8, ring_cy + 6],
        outline=(139, 69, 19, 255), width=3
    )

    return img


# ============================================================
# 4. LEASH SET (牵引绳套装) - Brown leather with stitching + metal buckle
# ============================================================
def make_leash_set():
    img = Image.new("RGBA", (SIZE, SIZE), (250, 248, 245, 255))
    draw = ImageDraw.Draw(img)

    # Background - light table surface
    for y in range(SIZE):
        v = int(240 + 15 * math.sin(y * 0.02))
        draw.line([(0, y), (SIZE, y)], fill=(v, v - 2, v - 5, 255))

    cx, cy = SIZE // 2, SIZE // 2

    # Leash - leather strip (curved)
    # Draw leather strip from bottom-left to top
    leather_points = []
    for t in range(60):
        frac = t / 60
        angle = math.radians(200 + frac * 140)
        r = 55 + 10 * math.sin(frac * math.pi * 2)
        px = cx + int(r * math.cos(angle)) - 30
        py = cy + int(r * math.sin(angle)) - 80 + frac * 160
        leather_points.append((px, py))

    # Draw leather band (thick)
    for i in range(len(leather_points) - 1):
        draw.line(
            [leather_points[i], leather_points[i + 1]],
            fill=(139, 90, 43, 255), width=18
        )

    # Leather texture - darker streaks
    for i in range(len(leather_points) - 1):
        if i % 3 == 0:
            offset_x = int(3 * math.sin(i * 0.5))
            offset_y = int(3 * math.cos(i * 0.5))
            px = leather_points[i][0] + offset_x
            py = leather_points[i][1] + offset_y
            draw.line([(px, py), (px, py + 2)], fill=(100, 60, 20, 100), width=1)

    # Stitching
    for i in range(0, len(leather_points) - 1, 4):
        p1 = leather_points[i]
        p2 = leather_points[min(i + 2, len(leather_points) - 1)]
        dx = p2[1] - p1[1]
        dy = p1[0] - p2[0]
        d = math.sqrt(dx * dx + dy * dy) or 1
        stitch_dist = 6
        offset_x = int(dx / d * stitch_dist)
        offset_y = int(dy / d * stitch_dist)
        draw.line(
            [(p1[0] + offset_x, p1[1] + offset_y), (p2[0] + offset_x, p2[1] + offset_y)],
            fill=(220, 200, 140, 255), width=2
        )
        draw.line(
            [(p1[0] - offset_x, p1[1] - offset_y), (p2[0] - offset_x, p2[1] - offset_y)],
            fill=(220, 200, 140, 255), width=2
        )

    # Metal buckle - clasp at one end
    buckle_x, buckle_y = leather_points[-1][0], leather_points[-1][1]
    draw.rounded_rectangle(
        [buckle_x - 10, buckle_y - 8, buckle_x + 10, buckle_y + 8],
        radius=3, fill=(160, 160, 165, 255), outline=(100, 100, 105, 255), width=1
    )
    # Buckle slot
    draw.rectangle(
        [buckle_x - 4, buckle_y - 5, buckle_x + 4, buckle_y + 5],
        fill=(80, 80, 85, 255)
    )

    # Metal clip at other end
    clip_x, clip_y = leather_points[0][0], leather_points[0][1]
    draw.arc(
        [clip_x - 8, clip_y - 10, clip_x + 8, clip_y + 6],
        start=0, end=180, fill=(160, 160, 165, 255), width=3
    )
    # Hook
    draw.line(
        [(clip_x - 8, clip_y - 2), (clip_x - 4, clip_y - 8), (clip_x + 4, clip_y - 8), (clip_x + 8, clip_y - 2)],
        fill=(140, 140, 145, 255), width=2
    )

    # Metal D-ring
    ring_x, ring_y = cx - 35, cy - 40
    draw.ellipse(
        [ring_x - 10, ring_y - 8, ring_x + 10, ring_y + 8],
        outline=(160, 160, 165, 255), width=3
    )

    # Leather highlight
    for i in range(len(leather_points) - 1):
        if i % 10 == 0:
            px, py = leather_points[i]
            draw.line([(px, py), (px + 2, py + 2)], fill=(200, 150, 80, 60), width=1)

    return img


# ============================================================
# 5. BOW TIE (宠物领结) - Red velvet bow tie with gold accents
# ============================================================
def make_bow_tie():
    img = Image.new("RGBA", (SIZE, SIZE), (248, 245, 240, 255))
    draw = ImageDraw.Draw(img)

    # Background - soft cream
    for y in range(SIZE):
        v = int(245 + 5 * math.sin(y * 0.05))
        draw.line([(0, y), (SIZE, y)], fill=(v, v - 2, v - 8, 255))

    cx, cy = SIZE // 2, SIZE // 2

    # Draw bow tie - left wing
    left_wing = [(cx - 70, cy - 30), (cx - 10, cy - 15), (cx - 5, cy), (cx - 10, cy + 15), (cx - 70, cy + 30)]
    draw.polygon(left_wing, fill=(180, 20, 30, 255))

    # Velvet texture - horizontal lines
    for y in range(cy - 30, cy + 30, 3):
        x1 = max(0, cx - 70)
        x2 = min(SIZE, cx - 5)
        draw.line([(x1, y), (x2, y)], fill=(160, 15, 25, 40), width=1)

    # Right wing
    right_wing = [(cx + 70, cy - 30), (cx + 10, cy - 15), (cx + 5, cy), (cx + 10, cy + 15), (cx + 70, cy + 30)]
    draw.polygon(right_wing, fill=(180, 20, 30, 255))

    for y in range(cy - 30, cy + 30, 3):
        x1 = cx + 5
        x2 = min(SIZE, cx + 70)
        draw.line([(x1, y), (x2, y)], fill=(160, 15, 25, 40), width=1)

    # Center knot
    knot = [(cx - 12, cy - 10), (cx + 12, cy - 10), (cx + 10, cy + 10), (cx - 10, cy + 10)]
    draw.polygon(knot, fill=(140, 10, 20, 255), outline=(100, 5, 15, 255))
    # Knot folds
    draw.line([(cx, cy - 10), (cx, cy + 10)], fill=(120, 8, 15, 180), width=1)

    # Gold accent in center
    gold_knot = [(cx - 5, cy - 4), (cx + 5, cy - 4), (cx + 4, cy + 4), (cx - 4, cy + 4)]
    draw.polygon(gold_knot, fill=(212, 175, 55, 255), outline=(180, 140, 30, 255))

    # Gold shimmer
    draw.line([(cx - 1, cy - 3), (cx - 1, cy + 3)], fill=(255, 220, 80, 180), width=1)

    # Bow tie tails
    tail_l_x1, tail_l_y1 = cx - 8, cy + 10
    tail_l_x2, tail_l_y2 = cx - 30, cy + 50
    draw.polygon(
        [(tail_l_x1, tail_l_y1), (tail_l_x1 - 5, tail_l_y2), (tail_l_x2, tail_l_y2 + 5), (tail_l_x1 - 2, tail_l_y1 + 5)],
        fill=(160, 15, 25, 255)
    )

    tail_r_x1, tail_r_y1 = cx + 8, cy + 10
    tail_r_x2, tail_r_y2 = cx + 30, cy + 50
    draw.polygon(
        [(tail_r_x1, tail_r_y1), (tail_r_x1 + 5, tail_r_y2), (tail_r_x2, tail_r_y2 + 5), (tail_r_x1 + 2, tail_r_y1 + 5)],
        fill=(160, 15, 25, 255)
    )

    # Band/strap
    band_y = cy - 35
    draw.rectangle([cx - 45, band_y - 6, cx + 45, band_y + 6], fill=(40, 40, 45, 255))
    draw.rectangle([cx - 45, band_y - 3, cx + 45, band_y + 3], fill=(60, 60, 65, 255))

    # Adjuster buckle on band
    draw.rectangle(
        [cx - 8, band_y - 4, cx + 8, band_y + 4],
        fill=(180, 180, 185, 255), outline=(120, 120, 125, 255), width=1
    )

    return img


# ============================================================
# 6. ACRYLIC TAG (亚克力牌) - Transparent acrylic with UV print
# ============================================================
def make_acrylic_tag():
    img = Image.new("RGBA", (SIZE, SIZE), (235, 230, 225, 255))
    draw = ImageDraw.Draw(img)

    # Background - dark velvet to show transparency
    for y in range(SIZE):
        v = int(30 + 20 * math.sin(y * 0.03))
        draw.line([(0, y), (SIZE, y)], fill=(v, v + 5, v + 15, 255))

    cx, cy = SIZE // 2, SIZE // 2

    # Acrylic plate (slightly transparent rounded rect)
    plate_w, plate_h = 110, 80
    # Shadow
    draw.rounded_rectangle(
        [cx - plate_w // 2 + 3, cy - plate_h // 2 + 3, cx + plate_w // 2 + 3, cy + plate_h // 2 + 3],
        radius=12, fill=(0, 0, 0, 40)
    )

    # Acrylic base - semi-transparent
    base_img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    base_draw = ImageDraw.Draw(base_img)
    base_draw.rounded_rectangle(
        [cx - plate_w // 2, cy - plate_h // 2, cx + plate_w // 2, cy + plate_h // 2],
        radius=12, fill=(255, 255, 255, 70)
    )
    img = Image.alpha_composite(img, base_img)
    draw = ImageDraw.Draw(img)

    # Acrylic border (subtle white)
    draw.rounded_rectangle(
        [cx - plate_w // 2, cy - plate_h // 2, cx + plate_w // 2, cy + plate_h // 2],
        radius=12, outline=(255, 255, 255, 120), width=1
    )

    # Edge highlight (acrylic bevel)
    draw.rounded_rectangle(
        [cx - plate_w // 2 + 2, cy - plate_h // 2 + 2, cx + plate_w // 2 - 2, cy + plate_h // 2 - 2],
        radius=10, outline=(255, 255, 255, 50), width=1
    )

    # UV printed text/info (opaque on acrylic)
    lines = [
        ("Pet ID", cy - 20, (40, 100, 180, 255)),
        ("Buddy", cy - 2, (20, 20, 30, 255)),
        ("☎ 555-0199", cy + 18, (40, 100, 180, 255)),
    ]
    for text, y_pos, color in lines:
        tw = draw.textlength(text, font=font_large) if hasattr(draw, 'textlength') else len(text) * 9
        draw.text((cx - tw // 2, y_pos), text, fill=color, font=font_large if text == "Buddy" else font_small)

    # QR code imitation (small squares)
    qr_x, qr_y = cx + 25, cy - 30
    for i in range(5):
        for j in range(5):
            if (i + j) % 3 != 0:
                draw.rectangle(
                    [qr_x + i * 4, qr_y + j * 4, qr_x + i * 4 + 3, qr_y + j * 4 + 3],
                    fill=(30, 30, 35, 220)
                )

    # Hole
    hole_y = cy - plate_h // 2 - 5
    draw.ellipse([cx - 4, hole_y - 4, cx + 4, hole_y + 4], outline=(255, 255, 255, 150), width=1)
    draw.ellipse([cx - 2, hole_y - 2, cx + 2, hole_y + 2], fill=(40, 40, 50, 100))

    # Reflection on acrylic
    for i in range(20):
        refl_x = plate_x1 = cx - plate_w // 2 + 15
        refl_y = cy - plate_h // 2 + 15 + i
        alpha = max(0, 60 - i * 3)
        draw.line(
            [(refl_x, refl_y), (refl_x + 40, refl_y)],
            fill=(255, 255, 255, alpha), width=1
        )

    return img


# ============================================================
# 7. BRACELET (宠物手链) - Woven texture with colorful beads
# ============================================================
def make_bracelet():
    img = Image.new("RGBA", (SIZE, SIZE), (250, 248, 245, 255))
    draw = ImageDraw.Draw(img)

    # Background
    for y in range(SIZE):
        v = int(248 + 5 * math.sin(y * 0.03))
        draw.line([(0, y), (SIZE, y)], fill=(v, v - 2, v - 8, 255))

    cx, cy = SIZE // 2, SIZE // 2 - 5

    # Bracelet band (woven cord)
    band_points = []
    for angle_deg in range(-30, 391, 3):
        angle = math.radians(angle_deg)
        r = 60 + 5 * math.sin(angle * 2)
        px = cx + r * math.cos(angle)
        py = cy + r * math.sin(angle)
        band_points.append((px, py))

    # Draw band base
    for i in range(len(band_points) - 1):
        draw.line([band_points[i], band_points[i + 1]], fill=(60, 40, 20, 255), width=14)

    # Woven texture - cross pattern
    for i in range(0, len(band_points) - 1, 8):
        p = band_points[i]
        p_next = band_points[min(i + 8, len(band_points) - 1)]
        draw.line([p, p_next], fill=(100, 75, 40, 255), width=3)

    # Woven texture - opposite direction
    for i in range(4, len(band_points) - 1, 8):
        p = band_points[i]
        p_next = band_points[min(i + 8, len(band_points) - 1)]
        draw.line([p, p_next], fill=(80, 55, 25, 255), width=2)

    # Beads on the bracelet
    bead_colors = [
        (220, 50, 50),   # red
        (50, 130, 220),  # blue
        (220, 180, 40),  # gold
        (50, 180, 70),   # green
        (200, 100, 50),  # orange
        (150, 50, 180),  # purple
        (50, 200, 200),  # teal
        (230, 80, 120),  # pink
    ]

    total_points = len(band_points)
    for b_idx in range(10):
        pt_idx = int(total_points * b_idx / 10)
        if pt_idx < len(band_points):
            bx, by = band_points[pt_idx]
            color = bead_colors[b_idx % len(bead_colors)]
            # Bead glow
            for br in range(6, 2, -1):
                draw.ellipse(
                    [bx - br, by - br, bx + br, by + br],
                    fill=(color[0], color[1], color[2], 80)
                )
            # Bead
            draw.ellipse([bx - 3, by - 3, bx + 3, by + 3], fill=(*color, 255))
            # Shine
            draw.ellipse([bx - 1, by - 2, bx + 1, by], fill=(255, 255, 255, 180))

    # Charm pendant
    charm_x, charm_y = cx, cy + 70
    draw.ellipse([charm_x - 8, charm_y - 4, charm_x + 8, charm_y + 4], fill=(220, 180, 40, 255))
    draw.ellipse([charm_x - 6, charm_y - 2, charm_x + 6, charm_y + 2], fill=(255, 220, 80, 255))
    # Charm bone shape
    bone_y = charm_y - 10
    circle_mask(draw, charm_x - 5, bone_y, 3, (220, 180, 40, 255))
    circle_mask(draw, charm_x + 5, bone_y, 3, (220, 180, 40, 255))
    draw.rectangle([charm_x - 5, bone_y - 2, charm_x + 5, bone_y + 2], fill=(220, 180, 40, 255))

    # Clasp
    clasp_x, clasp_y = band_points[0][0], band_points[0][1]
    draw.rectangle(
        [clasp_x - 5, clasp_y - 4, clasp_x + 5, clasp_y + 4],
        fill=(180, 180, 185, 255), outline=(120, 120, 125, 255), width=1
    )

    return img


# ============================================================
# 8. TREATS (换牙零食) - Jerky/bone texture treats
# ============================================================
def make_treats():
    img = Image.new("RGBA", (SIZE, SIZE), (240, 235, 225, 255))
    draw = ImageDraw.Draw(img)

    # Warm background
    for y in range(SIZE):
        v = int(240 + 8 * math.sin(y * 0.03))
        draw.line([(0, y), (SIZE, y)], fill=(v, v - 8, v - 15, 255))

    import random
    random.seed(42)

    # Draw 3 bone-shaped treats
    bone_positions = [
        (55, 75, 40),
        (130, 70, 35),
        (140, 135, 35),
    ]

    for bx, by, bsize in bone_positions:
        bw = bsize
        bh = int(bsize * 0.7)

        # Shadow
        draw.ellipse([bx - bw // 2 + 2, by + 2, bx + bw // 2 + 2, by + bh + 2], fill=(0, 0, 0, 30))

        # Bone body
        bone_color = (180, 110, 55, 255)

        # Left knob
        circle_mask(draw, bx - bw // 2 + 6, by + bh // 2, bh // 3, bone_color)
        circle_mask(draw, bx - bw // 2 + 6, by + bh // 2 - bh // 2, bh // 3, bone_color)
        # Knob fill
        draw.rectangle(
            [bx - bw // 2 + 6 - bh // 3, by + bh // 2 - bh // 2 + 1, bx - bw // 2 + 6 + bh // 3, by + bh // 2 - 1],
            fill=bone_color
        )

        # Right knob
        circle_mask(draw, bx + bw // 2 - 6, by + bh // 2, bh // 3, bone_color)
        circle_mask(draw, bx + bw // 2 - 6, by + bh // 2 - bh // 2, bh // 3, bone_color)
        draw.rectangle(
            [bx + bw // 2 - 6 - bh // 3, by + bh // 2 - bh // 2 + 1, bx + bw // 2 - 6 + bh // 3, by + bh // 2 - 1],
            fill=bone_color
        )

        # Shaft
        shaft_color = (190, 120, 60, 255)
        draw.rectangle(
            [bx - bw // 2 + 6, by + bh // 2 - bh // 2, bx + bw // 2 - 6, by + bh // 2],
            fill=shaft_color
        )

        # Jerky texture - darker streaks
        for i in range(8):
            sx = bx - bw // 2 + 10 + random.randint(0, bw - 25)
            sy = by + random.randint(0, bh - 5)
            draw.line(
                [(sx, sy), (sx + random.randint(3, 10), sy + random.randint(-2, 2))],
                fill=(140, 80, 35, random.randint(80, 150)), width=2
            )

        # Light highlights
        for i in range(3):
            hx = bx - bw // 2 + 10 + random.randint(0, bw - 30)
            hy = by + random.randint(2, bh // 2 - 4)
            draw.line(
                [(hx, hy), (hx + random.randint(2, 6), hy)],
                fill=(220, 170, 100, random.randint(50, 100)), width=1
            )

        # Bone outline
        outline_color = (120, 70, 30, 255)
        # Left knob outlines
        circle_mask(draw, bx - bw // 2 + 6, by + bh // 2, bh // 3, None)
        draw.ellipse(
            [bx - bw // 2 + 6 - bh // 3, by + bh // 2 - bh // 3, bx - bw // 2 + 6 + bh // 3, by + bh // 2 + bh // 3],
            outline=outline_color, width=1
        )
        draw.ellipse(
            [bx - bw // 2 + 6 - bh // 3, by + bh // 2 - bh // 2 - bh // 3, bx - bw // 2 + 6 + bh // 3, by + bh // 2 - bh // 2 + bh // 3],
            outline=outline_color, width=1
        )
        # Right knob outlines
        draw.ellipse(
            [bx + bw // 2 - 6 - bh // 3, by + bh // 2 - bh // 3, bx + bw // 2 - 6 + bh // 3, by + bh // 2 + bh // 3],
            outline=outline_color, width=1
        )
        draw.ellipse(
            [bx + bw // 2 - 6 - bh // 3, by + bh // 2 - bh // 2 - bh // 3, bx + bw // 2 - 6 + bh // 3, by + bh // 2 - bh // 2 + bh // 3],
            outline=outline_color, width=1
        )
        # Shaft outlines
        draw.line(
            [(bx - bw // 2 + 6, by + bh // 2 - bh // 2), (bx + bw // 2 - 6, by + bh // 2 - bh // 2)],
            fill=outline_color, width=1
        )
        draw.line(
            [(bx - bw // 2 + 6, by + bh // 2), (bx + bw // 2 - 6, by + bh // 2)],
            fill=outline_color, width=1
        )

    # Small crumb pieces
    for i in range(15):
        cx_cr = random.randint(20, 180)
        cy_cr = random.randint(20, 180)
        cr_size = random.randint(2, 5)
        cr_color = random.choice([
            (180, 110, 55, 255),
            (170, 100, 40, 255),
            (200, 130, 70, 255),
            (160, 90, 35, 255),
        ])
        draw.ellipse(
            [cx_cr, cy_cr, cx_cr + cr_size, cy_cr + cr_size],
            fill=cr_color
        )

    return img


# ============================================================
# Generate all images and save
# ============================================================
products = {
    "dog-tag": make_dog_tag,
    "led-collar": make_led_collar,
    "enamel-plate": make_enamel_plate,
    "leash-set": make_leash_set,
    "bow-tie": make_bow_tie,
    "acrylic-tag": make_acrylic_tag,
    "bracelet": make_bracelet,
    "treats": make_treats,
}

base64_dict = {}

for name, make_fn in products.items():
    img = make_fn()
    # Convert RGBA to RGB with white background for JPEG
    rgb_img = Image.new("RGB", (SIZE, SIZE), (255, 255, 255))
    rgb_img.paste(img, mask=img.split()[3])

    # Save to file
    filepath = os.path.join(OUT_DIR, f"{name}.jpg")
    rgb_img.save(filepath, "JPEG", quality=92)

    # Get base64
    buf = io.BytesIO()
    rgb_img.save(buf, format="JPEG", quality=92)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("ascii")
    base64_dict[name] = b64

    print(f"Generated {name}.jpg ({len(b64)} chars base64)")

# Update product_images.py
py_path = os.path.expanduser("~/projects/retail-sense/retail_sense/product_images.py")

with open(py_path, "r") as f:
    content = f.read()

# Build new IMAGES dict
images_str = "IMAGES = {\n"
for name in products.keys():
    b64 = base64_dict[name]
    images_str += f'    "{name}": """{b64}""",\n'
images_str += "}\n"

# Use marker-based replacement: replace from "IMAGES = {" to the closing "}"
import re
new_content = re.sub(
    r'IMAGES = \{.*?\n\}',
    images_str.strip(),
    content,
    flags=re.DOTALL
)

with open(py_path, "w") as f:
    f.write(new_content)

print(f"\nUpdated {py_path}")
print("Done!")
