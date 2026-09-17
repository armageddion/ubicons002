#!/usr/bin/env python3
import itertools
from dataclasses import dataclass
from pathlib import Path
from PIL import Image, ImageDraw

# ----------------------------------------------------------------------
# 1. CONFIGURATION
# ----------------------------------------------------------------------
GAP = 2                      # horizontal gap between icons in a row
BG_COLOR = (0, 0, 0, 255)    # black (opaque)
MAX_ICONS = 5                # max number of icons in a combined image

# ----------------------------------------------------------------------
# 2. ICON SOURCES
# ----------------------------------------------------------------------
# 16-icon set. The first seven columns are fixed to:
# 0 Vegetarian, 1 Vegan, 2 No Alcohol, 3 No Dairy, 4 No Gluten, 5 No Nuts, 6 Halal
# The remaining nine icons are kept in a deterministic order.
ICON_ORDER_16 = [
    "Icon_Vegetarian.png",
    "Icon_Vegen.png",
    "Icon_NoAlcohol.png",
    "Icon_NoDairy.png",
    "Icon_NoGluten.png",
    "Icon_NoNuts.png",
    "Icon_Halal.png",
    "Icon_Ketogenic.png",
    "Icon_NoEggs.png",
    "Icon_NoFish.png",
    "Icon_NoMustard.png",
    "Icon_NoPeanuts.png",
    "Icon_NoPork.png",
    "Icon_NoSesame.png",
    "Icon_NoShellfish.png",
    "Icon_NoSoy.png",
]
LEN16_SRC_DIR = Path(__file__).resolve().parent.parent / "length_16" / "src"
LEN16_OUT_DIR = Path(__file__).resolve().parent.parent / "length_16"

# 7-icon set, in the same order as the first seven icons above.
ICON_ORDER_5 = [
    "Vegetarian_Black_Transparent.png",
    "Vegen_Black_Transparent.png",
    "NoAlcohol_Black_Transparent.png",
    "NoDairy_Black_Transparent.png",
    "NoGluten_Black_Transparent.png",
    "NoNuts_Black_Transparent.png",
    "Halal_Black_Transparent.png",
]
LEN5_SRC_DIR = Path(__file__).resolve().parent.parent / "length_5" / "src"
LEN5_OUT_DIR = Path(__file__).resolve().parent.parent / "length_5"


@dataclass
class SetConfig:
    name: str
    icon_dir: Path
    filenames: list
    output_dir: Path
    icon_height: int
    canvas_width: int | None = None   # None = fit exactly the MAX_ICONS widest icons
    invert: bool = False


SETS = [
    SetConfig("16-icon", LEN16_SRC_DIR, ICON_ORDER_16, LEN16_OUT_DIR,
              icon_height=41, canvas_width=400),
    SetConfig("5-icon", LEN5_SRC_DIR, ICON_ORDER_5, LEN5_OUT_DIR,
              icon_height=82, invert=True),
]

# ----------------------------------------------------------------------
# 3. HELPERS
# ----------------------------------------------------------------------
def load_icons(icon_dir, filenames, icon_height, invert):
    icons = []
    for name in filenames:
        p = icon_dir / name
        if not p.exists():
            raise FileNotFoundError(f"Missing icon: {p}")
        img = Image.open(p).convert("RGBA")

        # invert RGB (keep alpha) so black renderings become white like the 16-set
        if invert:
            r, g, b, a = img.split()
            img = Image.merge("RGBA", (r.point(lambda v: 255 - v),
                                       g.point(lambda v: 255 - v),
                                       b.point(lambda v: 255 - v),
                                       a))

        # crop to the visible content so icons with uneven padding line up
        bbox = img.getchannel("A").getbbox()
        if bbox:
            img = img.crop(bbox)

        # resize to a uniform height, keeping the aspect ratio
        width = round(img.size[0] * icon_height / img.size[1])
        img = img.resize((width, icon_height), Image.Resampling.LANCZOS)

        icons.append(img)
    assert len(icons) == len(filenames)
    return icons


def generate(cfg):
    """Generate every combination of 1..MAX_ICONS icons (no duplicates)."""
    icons = load_icons(cfg.icon_dir, cfg.filenames, cfg.icon_height, cfg.invert)
    cfg.output_dir.mkdir(exist_ok=True)

    if cfg.canvas_width is None:
        # fit the row of the MAX_ICONS widest icons exactly
        widest = sorted((img.size[0] for img in icons), reverse=True)[:MAX_ICONS]
        canvas_width = sum(widest) + GAP * (MAX_ICONS - 1)
    else:
        canvas_width = cfg.canvas_width
    canvas_size = (canvas_width, cfg.icon_height)

    total = 0
    for n in range(1, MAX_ICONS + 1):
        for combo in itertools.combinations(range(len(icons)), n):
            canvas = Image.new("RGBA", canvas_size, BG_COLOR)
            draw = ImageDraw.Draw(canvas)

            # filename: 'X' for selected icons, 'O' otherwise
            filename_code = ''.join('X' if i in combo else 'O' for i in range(len(icons)))

            # right-align the row of icons
            row_width = sum(icons[i].size[0] for i in combo) + GAP * (n - 1)
            start_x = canvas_width - row_width
            y = (canvas_size[1] - cfg.icon_height) // 2  # center vertically

            x = start_x
            for pos_idx in combo:
                icon_img = icons[pos_idx]
                canvas.paste(icon_img, (x, y), icon_img)   # use alpha
                x += icon_img.size[0] + GAP

            filename = cfg.output_dir / f"{filename_code}.png"
            canvas.save(filename, "PNG")
            total += 1

    print(f"Generated {total} images in '{cfg.output_dir}' "
          f"(canvas {canvas_size[0]}x{canvas_size[1]})")
    return total

# ----------------------------------------------------------------------
# 4. GENERATE BOTH SETS
# ----------------------------------------------------------------------
for cfg in SETS:
    generate(cfg)