#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 emos 自动签到的图标（可复现，改了参数重跑即可）

    python3 tools/make-icon.py            # 输出 assets/icon.png (512) + icon@256.png

设计：深蓝渐变圆角方块 + 萝卜 + 右下角完成勾。
所有图形先按 4 倍尺寸绘制再降采样，保证边缘干净。
"""

import math
import os

from PIL import Image, ImageDraw, ImageFilter

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
S = 2048          # 绘制尺寸（4x）
FINAL = 512       # 最终尺寸
R = S * 0.224     # iOS 风格圆角半径

# 配色
BG_TOP = (16, 26, 46)
BG_BOTTOM = (29, 53, 87)
GLOW = (56, 189, 248)
CARROT_LIGHT = (255, 168, 76)
CARROT_MID = (247, 133, 42)
CARROT_DARK = (214, 99, 24)
LEAF_1 = (74, 222, 128)
LEAF_2 = (34, 197, 94)
BADGE = (34, 197, 94)
WHITE = (255, 255, 255)


def rounded_mask(size, radius, ss=4):
    m = Image.new("L", (size * ss, size * ss), 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([0, 0, size * ss - 1, size * ss - 1], radius=radius * ss, fill=255)
    return m.resize((size, size), Image.LANCZOS)


def gradient(size, top, bottom):
    img = Image.new("RGB", (1, size))
    for y in range(size):
        t = y / max(size - 1, 1)
        # 轻微平方缓动，让上半部分亮一些
        k = t ** 0.85
        img.putpixel((0, y), tuple(round(top[i] + (bottom[i] - top[i]) * k) for i in range(3)))
    return img.resize((size, size), Image.BILINEAR)


def rotate_point(x, y, cx, cy, deg):
    a = math.radians(deg)
    dx, dy = x - cx, y - cy
    return cx + dx * math.cos(a) - dy * math.sin(a), cy + dx * math.sin(a) + dy * math.cos(a)


def leaf(draw, cx, cy, w, h, deg):
    """倾斜的椭圆叶子"""
    box = [cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2]
    layer = Image.new("RGBA", (int(w * 2), int(h * 2)), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(layer)
    d2.ellipse([w / 2, h / 2, w / 2 + w, h / 2 + h], fill=(255, 255, 255, 255))
    layer = layer.rotate(deg, resample=Image.BICUBIC, center=(w, h))
    return layer, (cx - w, cy - h)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    canvas = gradient(S, BG_TOP, BG_BOTTOM).convert("RGBA")

    # 背景光晕
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([S * 0.10, S * 0.02, S * 0.92, S * 0.80], fill=GLOW + (46,))
    glow = glow.filter(ImageFilter.GaussianBlur(S * 0.09))
    canvas = Image.alpha_composite(canvas, glow)

    # 萝卜：上圆 + 下尖三角
    body = Image.new("L", (S, S), 0)
    bd = ImageDraw.Draw(body)
    cx = S * 0.50
    top_y = S * 0.435
    rad = S * 0.178
    tip = (cx + S * 0.02, S * 0.775)
    bd.ellipse([cx - rad, top_y - rad * 0.86, cx + rad, top_y + rad * 0.86], fill=255)
    bd.polygon([(cx - rad * 0.97, top_y - rad * 0.10),
                (cx + rad * 0.97, top_y - rad * 0.10),
                tip], fill=255)

    carrot = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    cd = ImageDraw.Draw(carrot)
    cd.bitmap((0, 0), body, fill=CARROT_MID)
    # 左侧高光 / 右侧暗面
    shade = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    sd.ellipse([cx - rad * 1.05, top_y - rad * 1.0, cx + rad * 0.10, top_y + rad * 1.15],
               fill=CARROT_LIGHT + (150,))
    shine = shade.filter(ImageFilter.GaussianBlur(S * 0.018))
    shine.putalpha(Image.composite(shine.getchannel("A"), Image.new("L", (S, S), 0), body))
    carrot = Image.alpha_composite(carrot, shine)

    dark = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dark)
    dd.polygon([(cx + rad * 0.35, top_y - rad * 0.2),
                (cx + rad * 0.99, top_y - rad * 0.2),
                (tip[0] + S * 0.005, tip[1] - S * 0.01)], fill=CARROT_DARK + (110,))
    dark = dark.filter(ImageFilter.GaussianBlur(S * 0.02))
    dark.putalpha(Image.composite(dark.getchannel("A"), Image.new("L", (S, S), 0), body))
    carrot = Image.alpha_composite(carrot, dark)

    # 三道横向纹理
    rib = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rib)
    for i, (yy, ww) in enumerate([(0.46, 0.78), (0.56, 0.60), (0.65, 0.40)]):
        y = S * yy
        half = S * ww * 0.5 * (rad / (S * 0.155))
        rd.line([(cx - half * 0.72, y), (cx + half * 0.52, y)],
                fill=(180, 76, 12, 90), width=int(S * 0.012), joint="curve")
    rib = rib.filter(ImageFilter.GaussianBlur(S * 0.006))
    rib.putalpha(Image.composite(rib.getchannel("A"), Image.new("L", (S, S), 0), body))
    carrot = Image.alpha_composite(carrot, rib)

    # 叶子（三片）
    leaves = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    specs = [
        (cx - S * 0.093, top_y - rad * 0.72, S * 0.098, S * 0.150, 38, LEAF_2),
        (cx + S * 0.002, top_y - rad * 0.92, S * 0.104, S * 0.205, 0, LEAF_1),
        (cx + S * 0.096, top_y - rad * 0.70, S * 0.098, S * 0.145, -38, LEAF_2),
    ]
    for (lx, ly, w, h, deg, color) in specs:
        size_w, size_h = int(w * 2), int(h * 2)
        layer = Image.new("RGBA", (size_w, size_h), (0, 0, 0, 0))
        d2 = ImageDraw.Draw(layer)
        d2.ellipse([w * 0.5, h * 0.5, w * 1.5, h * 1.5], fill=color + (255,))
        layer = layer.rotate(deg, resample=Image.BICUBIC, center=(w, h))
        leaves.alpha_composite(layer, (int(lx - w), int(ly - h)))
    carrot = Image.alpha_composite(carrot, leaves)

    # 保留一份只含背景的图层，后面做徽标留白时用它精确还原
    bg_only = canvas.copy()
    canvas = Image.alpha_composite(canvas, carrot)

    # 右下角完成勾
    badge_r = S * 0.185
    bx, by = S * 0.735, S * 0.715
    badge = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    # 环形留白：把「只有背景」的图层按圆环形状贴回去，颜色完全贴合渐变
    ring = Image.new("L", (S, S), 0)
    rgd = ImageDraw.Draw(ring)
    rgd.ellipse([bx - badge_r * 1.13, by - badge_r * 1.13,
                 bx + badge_r * 1.13, by + badge_r * 1.13], fill=255)
    rgd.ellipse([bx - badge_r, by - badge_r, bx + badge_r, by + badge_r], fill=0)
    canvas.paste(bg_only, (0, 0), ring)

    bdd = ImageDraw.Draw(badge)
    bdd.ellipse([bx - badge_r, by - badge_r, bx + badge_r, by + badge_r], fill=BADGE + (255,))
    w = int(S * 0.036)
    pts = [(bx - badge_r * 0.44, by + badge_r * 0.02),
           (bx - badge_r * 0.10, by + badge_r * 0.36),
           (bx + badge_r * 0.48, by - badge_r * 0.34)]
    bdd.line(pts, fill=WHITE + (255,), width=w, joint="curve")
    for p in pts:  # 圆头
        bdd.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=WHITE + (255,))
    canvas = Image.alpha_composite(canvas, badge)

    # 圆角裁切 + 细边框
    mask = rounded_mask(S, R)
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    out.paste(canvas, (0, 0), mask)
    big = out.resize((FINAL, FINAL), Image.LANCZOS)
    p512 = os.path.join(OUT_DIR, "icon.png")
    big.save(p512, optimize=True)
    big.resize((256, 256), Image.LANCZOS).save(os.path.join(OUT_DIR, "icon@256.png"), optimize=True)
    big.resize((128, 128), Image.LANCZOS).save(os.path.join(OUT_DIR, "icon@128.png"), optimize=True)

    for f in ("icon.png", "icon@256.png", "icon@128.png"):
        p = os.path.join(OUT_DIR, f)
        print("生成", p, os.path.getsize(p) // 1024, "KB")


if __name__ == "__main__":
    main()
