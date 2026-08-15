#!/usr/bin/env python3
"""
generate_menu_assets.py - Generates pixel-perfect 580x348 arcade graphical menu backgrounds
for Sega Dreamcast Dricas / Planetweb browser (Zero scrollbars).
Outputs:
  - Games/Frontend/DPWWW/MAINMENU.JPG (580x348)
  - Games/Frontend/DPWWW/FIGHTPACK_MENU.JPG (580x348)
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
    W, H = 580, 348
    img = Image.new("RGB", (W, H), color=(6, 12, 28))
    draw = ImageDraw.Draw(img)

    # Background gradient effect
    for y in range(H):
        r = int(6 + (y / H) * 14)
        g = int(12 + (y / H) * 20)
        b = int(28 + (y / H) * 45)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Top Header Bar (y=4 to 38)
    draw_rounded_rect(draw, (6, 4, W - 6, 38), radius=5, fill=(12, 28, 65), outline=(0, 240, 200), width=1)
    
    font_title = get_font(16, bold=True)
    font_sub = get_font(9, bold=False)
    font_btn_title = get_font(12, bold=True)
    font_btn_desc = get_font(9, bold=False)
    font_badge = get_font(9, bold=True)
    font_subbtn = get_font(8, bold=True)
    font_footer = get_font(10, bold=True)

    title_text = "CAPCOM FIGHTING COLLECTION"
    sub_text = "Sega Dreamcast | 4-in-1 Multi-Game & Cross-Soundtrack Edition"
    draw.text((W // 2, 16), title_text, fill=(255, 215, 0), font=font_title, anchor="mm")
    draw.text((W // 2, 30), sub_text, fill=(0, 240, 200), font=font_sub, anchor="mm")

    # 4 Game Cards Grid (2x2)
    # Left col: x=6 to 286, Right col: x=294 to 574
    # Top row: y=42 to 170, Bottom row: y=174 to 302
    cards = [
        {
            "id": 1,
            "title": "MARVEL VS CAPCOM 2",
            "subtitle": "Nene Mod + Custom Palettes",
            "coords": (6, 42, 286, 170),
            "accent": (255, 60, 60),
            "bg": (20, 10, 30),
            "launch_coords": (8, 44, 284, 144),
            "sub_coords": (8, 146, 284, 168),
            "sub_label": "[OST] Cambiar Soundtrack",
            "badge": "1. MvC2"
        },
        {
            "id": 2,
            "title": "CAPCOM VS SNK 2",
            "subtitle": "Millionaire 2001 - English v1.2",
            "coords": (294, 42, 574, 170),
            "accent": (255, 180, 0),
            "bg": (30, 24, 10),
            "launch_coords": (296, 44, 572, 144),
            "sub_coords": (296, 146, 572, 168),
            "sub_label": "[OST] Soundtracks  |  [+] Bonus",
            "badge": "2. CvS2"
        },
        {
            "id": 3,
            "title": "CAPCOM VS SNK 1",
            "subtitle": "Millennium Fight 2000 Pro / J",
            "coords": (6, 174, 286, 302),
            "accent": (0, 180, 255),
            "bg": (10, 24, 35),
            "launch_coords": (8, 176, 284, 276),
            "sub_coords": (8, 278, 284, 300),
            "sub_label": "[OST] Cambiar Soundtrack",
            "badge": "3. CvS1"
        },
        {
            "id": 4,
            "title": "SUPER STREET FIGHTER II X",
            "subtitle": "Grand Master Challenge (ST)",
            "coords": (294, 174, 574, 302),
            "accent": (50, 220, 100),
            "bg": (10, 30, 20),
            "launch_coords": (296, 176, 572, 276),
            "sub_coords": (296, 278, 572, 300),
            "sub_label": "[OST] Cambiar Soundtrack",
            "badge": "4. SSF2X"
        }
    ]

    for c in cards:
        x0, y0, x1, y1 = c["coords"]
        # Outer Card Box
        draw_rounded_rect(draw, (x0, y0, x1, y1), radius=5, fill=c["bg"], outline=c["accent"], width=1)
        
        # Badge
        bx0, by0, bx1, by1 = x0 + 5, y0 + 5, x0 + 64, y0 + 22
        draw_rounded_rect(draw, (bx0, by0, bx1, by1), radius=3, fill=c["accent"])
        draw.text(((bx0 + bx1) // 2, (by0 + by1) // 2), c["badge"], fill=(0, 0, 0), font=font_badge, anchor="mm")

        # Title & Subtitle inside launch area
        draw.text((x0 + 72, y0 + 13), c["title"], fill=(255, 255, 255), font=font_btn_title, anchor="lm")
        draw.text((x0 + 10, y0 + 40), c["subtitle"], fill=(180, 200, 220), font=font_btn_desc, anchor="lm")

        # Play action button hint
        px0, py0, px1, py1 = x1 - 74, y0 + 56, x1 - 8, y0 + 86
        draw_rounded_rect(draw, (px0, py0, px1, py1), radius=3, fill=(0, 180, 120), outline=(0, 255, 180), width=1)
        draw.text(((px0 + px1) // 2, (py0 + py1) // 2), "> JUGAR", fill=(0, 20, 10), font=font_btn_title, anchor="mm")

        # Sub-button strip (Soundtracks)
        sx0, sy0, sx1, sy1 = c["sub_coords"]
        draw_rounded_rect(draw, (sx0, sy0, sx1, sy1), radius=3, fill=(15, 25, 45), outline=(60, 100, 150), width=1)
        draw.text(((sx0 + sx1) // 2, (sy0 + sy1) // 2), c["sub_label"], fill=(0, 240, 200), font=font_subbtn, anchor="mm")

    # Bottom Navigation Bar (Toolbar) - 2 wide buttons (No extras/replays)
    # y=308 to 344
    # Button 1: VMU Saves: (6, 308, 286, 344)
    # Button 2: Dedicatoria: (294, 308, 574, 344)
    
    bot_buttons = [
        {"coords": (6, 308, 286, 344), "text": "[*] VMU SAVES (Desbloqueos)", "color": (255, 200, 50)},
        {"coords": (294, 308, 574, 344), "text": "[♥] AGRADECIMIENTOS & DEDICATORIA", "color": (255, 120, 180)},
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
    print(f"[✓] Generated pixel-perfect 580x348 menus: {p1} and {p2}")
