#!/usr/bin/env python3
"""
generate_vmu_menu_assets.py - Generates pixel-perfect 580x348 VMU Save Manager graphical background
and matching VMUMENU.HTML for the Sega Dreamcast collection.
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

def generate_vmu_image():
    W, H = 580, 348
    img = Image.new("RGB", (W, H), color=(8, 12, 24))
    draw = ImageDraw.Draw(img)

    # Background gradient effect (deep navy to dark slate)
    for y in range(H):
        r = int(8 + (y / H) * 12)
        g = int(12 + (y / H) * 18)
        b = int(24 + (y / H) * 35)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Top Header Bar (y=4 to 38)
    draw_rounded_rect(draw, (6, 4, W - 6, 38), radius=5, fill=(14, 26, 55), outline=(255, 200, 50), width=1)
    
    font_title = get_font(16, bold=True)
    font_sub = get_font(9, bold=False)
    font_btn_title = get_font(11, bold=True)
    font_btn_desc = get_font(8, bold=False)
    font_badge = get_font(8, bold=True)
    font_save_btn = get_font(9, bold=True)
    font_back_btn = get_font(11, bold=True)

    title_text = "GESTOR DE GUARDADOS VMU (100% UNLOCKS)"
    sub_text = "Sega Dreamcast | Descarga directa de archivos de guardado a tu Visual Memory Unit"
    draw.text((W // 2, 16), title_text, fill=(255, 215, 0), font=font_title, anchor="mm")
    draw.text((W // 2, 30), sub_text, fill=(0, 240, 200), font=font_sub, anchor="mm")

    # 5 Game Save Cards
    # Row 1 (2 cards): y=44 to 124
    #   Card 1: MvC2 USA (x=6 to 286)
    #   Card 2: CvS2 English (x=294 to 574)
    # Row 2 (2 cards): y=128 to 208
    #   Card 3: CvS1 Millennium (x=6 to 286)
    #   Card 4: SSF2X (x=294 to 574)
    # Row 3 (1 wide card): y=212 to 292
    #   Card 5: MvC2 Japan (x=6 to 574)
    
    cards = [
        {
            "id": "usamvc2",
            "title": "MARVEL VS. CAPCOM 2 (USA / NENE)",
            "desc": "56 Personajes + Colores + 999,999 Puntos",
            "badge": "MvC2 USA",
            "coords": (6, 44, 286, 124),
            "accent": (255, 60, 60),
            "bg": (24, 12, 28),
            "link": "VMU/USAMVC2.VMI"
        },
        {
            "id": "cvs2",
            "title": "CAPCOM VS. SNK 2 (ENGLISH v1.2)",
            "desc": "100% Unlocks + Shin Akuma & Rugal + Grooves",
            "badge": "CvS2 2001",
            "coords": (294, 44, 574, 124),
            "accent": (255, 180, 0),
            "bg": (32, 24, 10),
            "link": "VMU/CVS2SYST.VMI"
        },
        {
            "id": "cvs1",
            "title": "CAPCOM VS. SNK 1 (MILLENNIUM 2000)",
            "desc": "Todos los Secretos, EX Chars, Bosses y Grooves",
            "badge": "CvS1 PRO",
            "coords": (6, 128, 286, 208),
            "accent": (0, 180, 255),
            "bg": (10, 24, 38),
            "link": "VMU/CVS1J.VMI"
        },
        {
            "id": "ssf2x",
            "title": "SUPER STREET FIGHTER II X (ST)",
            "desc": "Grand Master Challenge + Opciones Arcade",
            "badge": "SSF2X",
            "coords": (294, 128, 574, 208),
            "accent": (50, 220, 100),
            "bg": (10, 30, 20),
            "link": "VMU/SSF2X.VMI"
        },
        {
            "id": "japmvc2",
            "title": "MARVEL VS. CAPCOM 2 (JAPAN / ASIA REGION)",
            "desc": "56 Personajes Desbloqueados para la version original japonesa (T-1212M)",
            "badge": "MvC2 JAP",
            "coords": (6, 212, 574, 292),
            "accent": (180, 100, 255),
            "bg": (22, 14, 38),
            "link": "VMU/JAPMVC2.VMI"
        }
    ]

    for c in cards:
        x0, y0, x1, y1 = c["coords"]
        draw_rounded_rect(draw, (x0, y0, x1, y1), radius=5, fill=c["bg"], outline=c["accent"], width=1)
        
        # Badge
        bx0, by0, bx1, by1 = x0 + 6, y0 + 6, x0 + 72, y0 + 22
        draw_rounded_rect(draw, (bx0, by0, bx1, by1), radius=3, fill=c["accent"])
        draw.text(((bx0 + bx1) // 2, (by0 + by1) // 2), c["badge"], fill=(0, 0, 0), font=font_badge, anchor="mm")

        # Title & Desc
        draw.text((x0 + 78, y0 + 14), c["title"], fill=(255, 255, 255), font=font_btn_title, anchor="lm")
        draw.text((x0 + 10, y0 + 44), c["desc"], fill=(180, 200, 220), font=font_btn_desc, anchor="lm")

        # Save button hint
        sx0, sy0, sx1, sy1 = x1 - 92, y0 + 48, x1 - 8, y0 + 74
        draw_rounded_rect(draw, (sx0, sy0, sx1, sy1), radius=3, fill=(0, 160, 90), outline=(0, 240, 160), width=1)
        draw.text(((sx0 + sx1) // 2, (sy0 + sy1) // 2), "[+] GUARDAR", fill=(255, 255, 255), font=font_save_btn, anchor="mm")

    # Bottom Bar: Volver al Menu Principal (y=300 to 344)
    draw_rounded_rect(draw, (6, 300, W - 6, 344), radius=5, fill=(14, 26, 45), outline=(0, 255, 180), width=1)
    draw.text((W // 2, 322), "[ < VOLVER AL MENU PRINCIPAL ]", fill=(0, 255, 180), font=font_back_btn, anchor="mm")

    return img

if __name__ == "__main__":
    out_dir = "/home/tortita/Coding/Github/Side/mvc2_custom/Games/Frontend/DPWWW"
    img = generate_vmu_image()
    
    p = os.path.join(out_dir, "VMUMENU.JPG")
    img.save(p, "JPEG", quality=92)
    print(f"[✓] Generated clean 580x348 VMUMENU.JPG at {p}")
