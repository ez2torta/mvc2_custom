#!/usr/bin/env python3
"""
generate_menu_assets.py - Generates arcade graphical menu backgrounds for Sega Dreamcast Dricas browser.
Outputs:
  - Games/Frontend/DPWWW/MAINMENU.JPG (600x360)
  - Games/Frontend/DPWWW/FIGHTPACK_MENU.JPG (600x360)
"""

import os
from PIL import Image, ImageDraw, ImageFont

def get_font(size, bold=False):
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]
    for p in font_paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

def draw_rounded_rect(draw, coords, radius, fill, outline=None, width=1):
    x0, y0, x1, y1 = coords
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=outline, width=width)

def generate_main_menu():
    W, H = 600, 360
    img = Image.new("RGB", (W, H), color=(6, 12, 28))
    draw = ImageDraw.Draw(img)

    # Background gradient effect
    for y in range(H):
        r = int(6 + (y / H) * 14)
        g = int(12 + (y / H) * 20)
        b = int(28 + (y / H) * 45)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Top Header Bar
    draw_rounded_rect(draw, (8, 6, W - 8, 44), radius=6, fill=(12, 28, 65), outline=(0, 240, 200), width=2)
    
    font_title = get_font(18, bold=True)
    font_sub = get_font(10, bold=False)
    font_btn_title = get_font(13, bold=True)
    font_btn_desc = get_font(10, bold=False)
    font_badge = get_font(10, bold=True)
    font_subbtn = get_font(9, bold=True)
    font_footer = get_font(10, bold=True)

    title_text = "CAPCOM FIGHTING COLLECTION 4-IN-1"
    sub_text = "Sega Dreamcast | Multi-Game & Multi-Soundtrack Edition"
    draw.text((W // 2, 18), title_text, fill=(255, 215, 0), font=font_title, anchor="mm")
    draw.text((W // 2, 35), sub_text, fill=(0, 240, 200), font=font_sub, anchor="mm")

    # 4 Game Cards Grid (2x2)
    # Left col: x=10 to 295, Right col: x=305 to 590
    # Top row: y=50 to 180, Bottom row: y=186 to 316
    cards = [
        {
            "id": 1,
            "title": "MARVEL VS CAPCOM 2",
            "subtitle": "Nene Mod + Custom Palettes",
            "coords": (10, 50, 295, 178),
            "accent": (255, 60, 60),
            "bg": (20, 10, 30),
            "launch_coords": (12, 52, 293, 150),
            "sub_coords": (12, 153, 293, 176),
            "sub_label": "[OST] Cambiar Soundtrack",
            "badge": "1. MvC2"
        },
        {
            "id": 2,
            "title": "CAPCOM VS SNK 2",
            "subtitle": "Millionaire 2001 - English v1.2",
            "coords": (305, 50, 590, 178),
            "accent": (255, 180, 0),
            "bg": (30, 24, 10),
            "launch_coords": (307, 52, 588, 150),
            "sub_coords": (307, 153, 588, 176),
            "sub_label": "[OST] Soundtracks  |  [+] Bonus & VMU",
            "badge": "2. CvS2"
        },
        {
            "id": 3,
            "title": "CAPCOM VS SNK 1",
            "subtitle": "Millennium Fight 2000 Pro / J",
            "coords": (10, 184, 295, 312),
            "accent": (0, 180, 255),
            "bg": (10, 24, 35),
            "launch_coords": (12, 186, 293, 284),
            "sub_coords": (12, 287, 293, 310),
            "sub_label": "[OST] Cambiar Soundtrack",
            "badge": "3. CvS1"
        },
        {
            "id": 4,
            "title": "SUPER STREET FIGHTER II X",
            "subtitle": "Grand Master Challenge (ST)",
            "coords": (305, 184, 590, 312),
            "accent": (50, 220, 100),
            "bg": (10, 30, 20),
            "launch_coords": (307, 186, 588, 284),
            "sub_coords": (307, 287, 588, 310),
            "sub_label": "[OST] Cambiar Soundtrack",
            "badge": "4. SSF2X"
        }
    ]

    for c in cards:
        x0, y0, x1, y1 = c["coords"]
        # Outer Card Box
        draw_rounded_rect(draw, (x0, y0, x1, y1), radius=6, fill=c["bg"], outline=c["accent"], width=2)
        
        # Badge
        bx0, by0, bx1, by1 = x0 + 6, y0 + 6, x0 + 72, y0 + 24
        draw_rounded_rect(draw, (bx0, by0, bx1, by1), radius=4, fill=c["accent"])
        draw.text(((bx0 + bx1) // 2, (by0 + by1) // 2), c["badge"], fill=(0, 0, 0), font=font_badge, anchor="mm")

        # Title & Subtitle inside launch area
        draw.text((x0 + 80, y0 + 15), c["title"], fill=(255, 255, 255), font=font_btn_title, anchor="lm")
        draw.text((x0 + 12, y0 + 44), c["subtitle"], fill=(180, 200, 220), font=font_btn_desc, anchor="lm")

        # Play action button hint
        px0, py0, px1, py1 = x1 - 80, y0 + 60, x1 - 10, y0 + 92
        draw_rounded_rect(draw, (px0, py0, px1, py1), radius=4, fill=(0, 180, 120), outline=(0, 255, 180), width=1)
        draw.text(((px0 + px1) // 2, (py0 + py1) // 2), "> JUGAR", fill=(0, 20, 10), font=font_btn_title, anchor="mm")

        # Sub-button strip (Soundtracks)
        sx0, sy0, sx1, sy1 = c["sub_coords"]
        draw_rounded_rect(draw, (sx0, sy0, sx1, sy1), radius=3, fill=(15, 25, 45), outline=(60, 100, 150), width=1)
        draw.text(((sx0 + sx1) // 2, (sy0 + sy1) // 2), c["sub_label"], fill=(0, 240, 200), font=font_subbtn, anchor="mm")

    # Bottom Navigation Bar (Toolbar)
    # y=318 to 354
    # Buttons:
    # 1. VMU Saves: (10, 320, 195, 354)
    # 2. Soundtracks / Extras: (205, 320, 395, 354)
    # 3. Dedicatoria & Creditos: (405, 320, 590, 354)
    
    bot_buttons = [
        {"coords": (10, 320, 195, 354), "text": "[*] VMU SAVES", "color": (255, 200, 50)},
        {"coords": (205, 320, 395, 354), "text": "[~] EXTRAS & REPLAYS", "color": (100, 200, 255)},
        {"coords": (405, 320, 590, 354), "text": "[♥] AGRADECIMIENTOS", "color": (255, 120, 180)},
    ]

    for b in bot_buttons:
        bx0, by0, bx1, by1 = b["coords"]
        draw_rounded_rect(draw, (bx0, by0, bx1, by1), radius=4, fill=(16, 24, 48), outline=b["color"], width=1)
        draw.text(((bx0 + bx1) // 2, (by0 + by1) // 2), b["text"], fill=b["color"], font=font_footer, anchor="mm")

    return img

if __name__ == "__main__":
    out_dir = "/home/tortita/Coding/Github/Side/mvc2_custom/Games/Frontend/DPWWW"
    img = generate_main_menu()
    
    p1 = os.path.join(out_dir, "MAINMENU.JPG")
    p2 = os.path.join(out_dir, "FIGHTPACK_MENU.JPG")
    img.save(p1, "JPEG", quality=92)
    img.save(p2, "JPEG", quality=92)
    print(f"Generated {p1} and {p2}")
