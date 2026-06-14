"""Gera ícone do app — gota d'água sobre gradiente azul.
Uso:
    pip install Pillow
    python tools/generate_icon.py
"""
import os
from PIL import Image, ImageDraw

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "icon")
os.makedirs(OUT_DIR, exist_ok=True)

SIZE = 1024


def make_gradient(size, top, bottom):
    img = Image.new("RGB", (size, size), top)
    for y in range(size):
        ratio = y / size
        r = int(top[0] * (1 - ratio) + bottom[0] * ratio)
        g = int(top[1] * (1 - ratio) + bottom[1] * ratio)
        b = int(top[2] * (1 - ratio) + bottom[2] * ratio)
        for x in range(size):
            img.putpixel((x, y), (r, g, b))
    return img


def draw_drop(draw, cx, cy, h, color, outline=None, w=0):
    """Gota: triângulo arredondado em cima + círculo embaixo."""
    r = h * 0.32
    bottom_y = cy + h / 2 - r
    draw.ellipse(
        [cx - r, bottom_y - r, cx + r, bottom_y + r],
        fill=color, outline=outline, width=w,
    )
    top_y = cy - h / 2
    points = [(cx, top_y), (cx - r, bottom_y), (cx + r, bottom_y)]
    draw.polygon(points, fill=color, outline=outline)
    if outline and w:
        draw.line([points[0], points[1]], fill=outline, width=w)
        draw.line([points[0], points[2]], fill=outline, width=w)


def build_main_icon():
    bg = make_gradient(SIZE, (3, 169, 244), (1, 87, 155))
    draw = ImageDraw.Draw(bg, "RGBA")
    drop_h = int(SIZE * 0.62)
    cx, cy = SIZE // 2, SIZE // 2 + int(SIZE * 0.03)
    draw_drop(draw, cx, cy, drop_h, color=(255, 255, 255, 255))
    highlight_h = int(drop_h * 0.35)
    draw_drop(
        draw, cx - int(SIZE * 0.07), cy + int(SIZE * 0.05),
        highlight_h, color=(186, 222, 251, 200),
    )
    out = os.path.join(OUT_DIR, "icon.png")
    bg.save(out, "PNG")
    print(f"Wrote {out}")


def build_foreground():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    drop_h = int(SIZE * 0.46)
    cx, cy = SIZE // 2, SIZE // 2 + int(SIZE * 0.02)
    draw_drop(draw, cx, cy, drop_h, color=(255, 255, 255, 255))
    out = os.path.join(OUT_DIR, "icon_foreground.png")
    img.save(out, "PNG")
    print(f"Wrote {out}")


if __name__ == "__main__":
    build_main_icon()
    build_foreground()
