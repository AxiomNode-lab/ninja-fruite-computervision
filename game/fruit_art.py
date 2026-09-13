"""Cached, antialiased fruit artwork and alpha compositing (no emoji fonts)."""

from functools import lru_cache

import cv2
import numpy as np
from PIL import Image, ImageDraw

from config import FRUIT_COLORS


@lru_cache(maxsize=64)
def fruit_sprite(fruit_type, radius):
    size = int(radius * 2.6)
    scale = 3
    image = Image.new("RGBA", (size * scale, size * scale))
    draw = ImageDraw.Draw(image)
    center = size * scale / 2
    r = radius * scale
    b, g, red = FRUIT_COLORS.get(fruit_type, (50, 150, 230))
    color = (red, g, b)
    # Concentric offset shading makes a smooth lit skin, cached per fruit type.
    for step in range(100, 0, -1):
        ratio = step / 100
        offset = (1 - ratio) * r * .26
        shade = tuple(int(min(255, c * (.65 + (1 - ratio) * .5) + (1 - ratio) * 60)) for c in color)
        draw.ellipse((center - offset - r * ratio, center - offset - r * ratio,
                      center - offset + r * ratio, center - offset + r * ratio), fill=(*shade, 255))
    if fruit_type == "watermelon":
        for offset in [-.65, -.25, .25, .65]:
            draw.arc((center + offset * r - r * .2, center - r * .9,
                      center + offset * r + r * .2, center + r * .9), 80, 280,
                     fill=(30, 80, 35, 255), width=scale * 2)
    if fruit_type in ("orange", "lemon", "strawberry", "pineapple"):
        for i in range(40):
            angle = i * 2.39996
            dist = (i / 40) ** .5 * r * .86
            x, y = center + np.cos(angle) * dist, center + np.sin(angle) * dist
            draw.ellipse((x - 2, y - 3, x + 2, y + 3), fill=(255, 225, 150, 160))
    draw.ellipse((center - .55 * r, center - .65 * r, center - .1 * r, center - .4 * r), fill=(255, 255, 255, 95))
    draw.line((center, center - r * .8, center - .08 * r, center - r * 1.17), fill=(113, 76, 40), width=scale * 3)
    draw.ellipse((center, center - r * 1.15, center + r * .65, center - r * .85), fill=(109, 180, 67))
    image = image.resize((size, size), Image.Resampling.LANCZOS)
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGBA2BGRA)


def composite(frame, sprite, x, y, opacity=1.0):
    """Clip at frame edges so partially visible fruit still draws correctly."""
    h, w = sprite.shape[:2]
    left, top = int(x - w / 2), int(y - h / 2)
    x0, y0 = max(0, left), max(0, top)
    x1, y1 = min(frame.shape[1], left + w), min(frame.shape[0], top + h)
    if x1 <= x0 or y1 <= y0:
        return frame
    source = sprite[y0 - top:y1 - top, x0 - left:x1 - left]
    alpha = source[:, :, 3:4].astype(float) / 255 * opacity
    frame[y0:y1, x0:x1] = source[:, :, :3] * alpha + frame[y0:y1, x0:x1] * (1 - alpha)
    return frame
