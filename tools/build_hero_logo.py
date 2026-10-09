#!/usr/bin/env python3
"""Redraw logos/LEAPPs_logo_with_icons.png for the current set of LEAPPs.

The card, the arc, the leaping figure and the LEAPPs wordmark are kept exactly
as they were: this only replaces the strip that names the parsers and shows
their icons, which is the part that goes stale every time a tool is added.

The positions below were measured on the 2528x1768 artwork. The names are set in
Arial Rounded MT Bold, the closest system font on macOS to the artwork's
lettering, so a redrawn strip will not match the hand-set names exactly. It is
a system font, so this script runs on macOS only.

Usage:  python3 tools/build_hero_logo.py [--out PATH]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "logos" / "LEAPPs_logo_with_icons.png"
FONT = "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf"

# Alphabetical, the order the original artwork used.
TOOLS = ("ALEAPP", "DLEAPP", "GLEAPP", "iLEAPP", "RLEAPP", "VLEAPP")

# The strip being replaced, comfortably inside the card's rounded border.
STRIP = (150, 1170, 2378, 1600)
NAMES_CENTER_Y = 1225         # 1187..1262 in the artwork
NAMES_MAX_WIDTH = 2013        # 257..2269 in the artwork
NAMES_MAX_SIZE = 120
ICON_TOP = 1293               # 1293..1576 in the artwork
ICON_WIDTH = 284
ICON_GAP = 59
SEPARATOR = " | "


def fitted_font(text: str, max_width: int) -> ImageFont.FreeTypeFont:
    """Largest size that keeps `text` within max_width, capped at NAMES_MAX_SIZE."""
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    for size in range(NAMES_MAX_SIZE, 15, -1):
        font = ImageFont.truetype(FONT, size)
        if probe.textlength(text, font=font) <= max_width:
            return font
    raise SystemExit("no font size fits")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(SOURCE))
    args = ap.parse_args()

    card = Image.open(SOURCE).convert("RGBA")
    draw = ImageDraw.Draw(card)
    draw.rectangle(STRIP, fill=(255, 255, 255, 255))

    names = SEPARATOR.join(TOOLS)
    font = fitted_font(names, NAMES_MAX_WIDTH)
    draw.text((card.width / 2, NAMES_CENTER_Y), names, font=font,
              fill=(17, 17, 17, 255), anchor="mm")

    total = len(TOOLS) * ICON_WIDTH + (len(TOOLS) - 1) * ICON_GAP
    x = round((card.width - total) / 2)
    for tool in TOOLS:
        icon = Image.open(ROOT / "logos" / f"{tool}_icon.png").convert("RGBA")
        height = round(ICON_WIDTH * icon.height / icon.width)
        icon = icon.resize((ICON_WIDTH, height), Image.LANCZOS)
        card.alpha_composite(icon, (x, ICON_TOP))
        x += ICON_WIDTH + ICON_GAP

    out = Path(args.out)
    card.save(out)
    print(f"wrote {out} ({out.stat().st_size:,} bytes), names at {font.size}px")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
