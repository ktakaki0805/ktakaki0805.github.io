"""Create a minimal 1200 × 630 PNG for sharing an article on social media.

Images are committed alongside articles; rendering the website needs no fonts.
"""

import argparse
from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT = 1200, 630
MARGIN = 88
DEFAULT_FONTS = (
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
    "C:/Windows/Fonts/YuGothR.ttc",
)


def wrap_title(title, font, width):
    """Keep Latin words together and allow Japanese to wrap between characters."""
    lines, line = [], ""
    for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9'’_-]*|\s+|.", title):
        # Split a word only if it cannot fit on an otherwise empty line.
        parts = list(token) if font.getlength(token) > width else [token]
        for part in parts:
            if line and font.getlength(line + part) > width:
                lines.append(line.rstrip())
                line = ""
            line = (line + part).lstrip()
    if line:
        lines.append(line.rstrip())
    return lines


def generate(title, output, font_path, site_name):
    title = " ".join(title.split())
    if not title:
        raise ValueError("The title must not be empty.")

    for size in range(64, 27, -2):
        font = ImageFont.truetype(str(font_path), size)
        lines = wrap_title(title, font, WIDTH - 2 * MARGIN)
        line_height = round(size * 1.5)
        if len(lines) * line_height <= 320:
            break
    else:
        raise ValueError("The title is too long; use a shorter title for the image.")

    image = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(image)
    # Center the title in the area above the small site-name footer.
    top = (520 - len(lines) * line_height) // 2
    for index, line in enumerate(lines):
        draw.text((MARGIN, top + index * line_height), line,
                  font=font, fill="#1A1A1A", anchor="lt")
    footer_font = ImageFont.truetype(str(font_path), 26)
    if footer_font.getlength(site_name) > WIDTH - 2 * MARGIN:
        raise ValueError("The site name is too long.")
    draw.line((MARGIN, 510, WIDTH - MARGIN, 510), fill="#E4E4E4", width=1)
    draw.text((MARGIN, 538), site_name, font=footer_font,
              fill="#5C5C5C", anchor="lt")
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", optimize=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True, help="Plain-text article title")
    parser.add_argument("--output", required=True, type=Path, help="Output PNG path")
    parser.add_argument("--site-name", default="ktakaki0805")
    parser.add_argument("--font", type=Path, help="Path to a Japanese-capable TTF/OTF/TTC font")
    args = parser.parse_args()
    font_path = args.font or next((Path(p) for p in DEFAULT_FONTS if Path(p).is_file()), None)
    if font_path is None or not font_path.is_file():
        parser.error("Install Noto Sans CJK JP (Ubuntu: fonts-noto-cjk), or pass --font PATH.")
    try:
        generate(args.title, args.output, font_path, args.site_name)
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print(f"Created {args.output} ({WIDTH} × {HEIGHT})")


if __name__ == "__main__":
    main()
