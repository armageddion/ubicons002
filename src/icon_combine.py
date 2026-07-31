#!/usr/bin/env python3
import itertools
from glob import glob
from pathlib import Path
from PIL import Image, ImageDraw

# ----------------------------------------------------------------------
# 1. CONFIGURATION
# ----------------------------------------------------------------------
ICON_HEIGHT = 41             # height to which every icon is resized (aspect kept)
GAP = 2                      # horizontal gap between icons in a row
CANVAS_SIZE = (400, ICON_HEIGHT)  # final image dimensions
BG_COLOR = (0, 0, 0, 255)     # black (opaque)
MAX_ICONS = 5                # max number of icons in a combined image

# ----------------------------------------------------------------------
# 2. LOAD ALL ICON IMAGES (Icon_*.png in this directory)
# ----------------------------------------------------------------------
icon_paths = sorted(glob("Icon_*.png"))

icons = []
for p in icon_paths:
    img = Image.open(p).convert("RGBA")

    # crop to the visible content so icons with uneven padding line up
    bbox = img.getchannel("A").getbbox()
    if bbox:
        img = img.crop(bbox)

    # resize to a uniform height, keeping the aspect ratio
    width = round(img.size[0] * ICON_HEIGHT / img.size[1])
    img = img.resize((width, ICON_HEIGHT), Image.Resampling.LANCZOS)

    icons.append(img)

assert len(icons) == len(icon_paths)

# ----------------------------------------------------------------------
# 3. GENERATE EVERY COMBINATION OF 1..MAX_ICONS ICONS (no duplicates)
# ----------------------------------------------------------------------
output_dir = Path(__file__).resolve().parent.parent
output_dir.mkdir(exist_ok=True)

total = 0
for n in range(1, MAX_ICONS + 1):
    for combo in itertools.combinations(range(len(icons)), n):
        canvas = Image.new("RGBA", CANVAS_SIZE, BG_COLOR)
        draw = ImageDraw.Draw(canvas)

        # filename: 'X' for selected icons, 'O' otherwise
        filename_code = ''.join('X' if i in combo else 'O' for i in range(len(icons)))

        # right-align the row of icons
        total_width = sum(icons[i].size[0] for i in combo) + GAP * (n - 1)
        start_x = CANVAS_SIZE[0] - total_width
        y = (CANVAS_SIZE[1] - ICON_HEIGHT) // 2  # center vertically

        x = start_x
        for pos_idx in combo:
            icon_img = icons[pos_idx]
            canvas.paste(icon_img, (x, y), icon_img)   # use alpha
            x += icon_img.size[0] + GAP

        filename = output_dir / f"{filename_code}.png"
        canvas.save(filename, "PNG")
        total += 1

print(f"Generated {total} images in '{output_dir}'")
