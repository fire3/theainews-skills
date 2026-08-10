#!/usr/bin/env python3
"""Compose an article cover: AI-generated background + deterministic text overlay.

This is the third stage of the "stable cover" pipeline:

  1. baoyu-cover-image skill designs the cover and writes a *text-free* prompt.
  2. baoyu-image-gen skill renders only the background image.
  3. THIS script overlays the title / category / date locally, so text is
     always pixel-perfect and never depends on the image model's letterforms.

Everything is deterministic: no randomness, no interactive prompts.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageStat

from text_wrap import wrap_title


# --------------------------------------------------------------------------
# Text wrapping helpers (pure logic, unit-testable without PIL)
# --------------------------------------------------------------------------
def fit_title(
    text: str,
    draw,
    font_path: str,
    max_width: int,
    max_height: int,
    max_lines: int = 2,
    max_scale: float = 0.125,
    min_scale: float = 0.055,
) -> tuple[ImageFont.FreeTypeFont, list[str], int]:
    """Pick the largest font size whose wrapped title fits the box.

    Returns (font, lines, font_size). Falls back to the minimum size with an
    ellipsis rather than failing.
    """
    max_size = int(max_height * max_scale)
    min_size = max(16, int(max_height * min_scale))

    for size in range(max_size, min_size - 1, -2):
        font = load_font(font_path, size)
        lines = wrap_title(text, lambda s: draw.textlength(s, font=font), max_width)
        if len(lines) <= max_lines and all(draw.textlength(line, font=font) <= max_width for line in lines):
            return font, lines, size

    # Worst case: clamp to min size, keep max_lines, ellipsize the last line.
    font = load_font(font_path, min_size)
    lines = wrap_title(text, lambda s: draw.textlength(s, font=font), max_width)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        while draw.textlength(lines[-1] + "…", font=font) > max_width and len(lines[-1]) > 1:
            lines[-1] = lines[-1][:-1]
        lines[-1] += "…"
    return font, lines, min_size


def load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    """Load a font and prefer its Bold named instance (variable fonts)."""
    font = ImageFont.truetype(path, size)
    try:
        font.set_variation_by_name("Bold")
    except Exception:
        try:
            font.set_variation_by_axes([700])
        except Exception:
            pass
    return font


# --------------------------------------------------------------------------
# Scrim (legibility layer)
# --------------------------------------------------------------------------


def _linear_alpha(height: int, start_frac: float, strength: float, power: float = 1.35) -> Image.Image:
    """1xH grayscale gradient: 0 above `start_frac`, up to strength at bottom."""
    rows = []
    for y in range(height):
        t = max(0.0, (y - start_frac * height) / (height * (1.0 - start_frac)))
        rows.append(int(255 * strength * (t ** power)))
    img = Image.new("L", (1, height))
    img.putdata(rows)
    return img


def apply_scrim(bg: Image.Image, anchor: str, strength: float) -> Image.Image:
    """Overlay a dark gradient so text stays readable on any background."""
    w, h = bg.size
    black = Image.new("L", (1, 1), 0)
    layers: list[Image.Image] = []

    if anchor in ("bottom", "bottom-left", "bottom-right"):
        grad = _linear_alpha(h, start_frac=0.38, strength=strength).resize((w, h), Image.Resampling.BICUBIC)
        layers.append(grad)
    if anchor in ("left", "bottom-left", "center-left"):
        grad = _linear_alpha(w, start_frac=0.15, strength=strength * 0.75).resize(
            (w, h), Image.Resampling.BICUBIC
        )
        layers.append(grad)
    if anchor in ("right", "bottom-right", "center-right"):
        grad = _linear_alpha(w, start_frac=0.15, strength=strength * 0.75).resize(
            (w, h), Image.Resampling.BICUBIC
        ).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        layers.append(grad)

    if not layers:
        return bg

    mask = layers[0]
    for extra in layers[1:]:
        mask = ImageChops.lighter(mask, extra)
    overlay = Image.merge("RGBA", (black.resize((w, h)), black.resize((w, h)), black.resize((w, h)), mask))
    return Image.alpha_composite(bg.convert("RGBA"), overlay)


def scrim_strength_for(bg: Image.Image, anchor: str, requested: float) -> float:
    """Scale the scrim down when the text zone is already dark.

    Keeps the original background's color and mood: a deep dark background
    needs almost no darkening, while a bright background still gets a strong
    scrim for legibility.
    """
    w, h = bg.size
    if "bottom" in anchor:
        box = (0, int(h * 0.5), int(w * 0.65), h)
    elif "left" in anchor:
        box = (0, int(h * 0.15), int(w * 0.6), int(h * 0.92))
    else:
        box = (0, int(h * 0.35), int(w * 0.65), int(h * 0.85))

    lum = ImageStat.Stat(bg.convert("L").crop(box)).mean[0]
    factor = min(1.0, max(0.2, (lum - 25.0) / 95.0))
    return requested * factor


# --------------------------------------------------------------------------
# Text block rendering
# --------------------------------------------------------------------------


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def contains_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def draw_text_with_shadow(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font,
    fill: tuple[int, int, int],
    shadow_alpha: int = 150,
    shadow_blur: int = 10,
    shadow_offset: int = 4,
) -> None:
    x, y = xy
    w, h = img.size

    # Shadow from a blurred alpha mask (only the glyphs, no color bleed).
    shadow_mask = Image.new("L", (w, h), 0)
    sd = ImageDraw.Draw(shadow_mask)
    sd.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=255)
    shadow_mask = shadow_mask.filter(ImageFilter.GaussianBlur(shadow_blur))
    tint = Image.new("RGBA", (w, h), (0, 0, 0, shadow_alpha))
    img.alpha_composite(Image.composite(tint, Image.new("RGBA", (w, h), (0, 0, 0, 0)), shadow_mask))

    draw.text((x, y), text, font=font, fill=fill)


def letter_spaced_text(draw, xy, text, font, fill, spacing: int):
    """Draw text with fixed letter spacing (nice for short Latin labels)."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + spacing


def render_text_block(
    img: Image.Image,
    *,
    title: str,
    category: str,
    date: str,
    font_path: str,
    cjk_font_path: str,
    anchor: str,
    accent: tuple[int, int, int],
    brand: str,
    max_lines: int = 2,
) -> None:
    w, h = img.size
    draw = ImageDraw.Draw(img)

    margin_x = int(w * 0.06)
    margin_bottom = int(h * 0.075)
    max_title_w = int(w * 0.86)

    title_font_path = cjk_font_path if contains_cjk(title) else font_path
    title_font, lines, size = fit_title(title, draw, title_font_path, max_title_w, h, max_lines=max_lines)
    line_h = int(size * 1.32)
    title_h = line_h * len(lines)

    if anchor == "center":
        title_y = h // 2 - title_h // 2
    elif anchor.startswith("bottom"):
        title_y = h - margin_bottom - title_h
    else:  # left / center-left / top-left
        title_y = int(h * 0.30)

    # Title with soft shadow.
    for i, line in enumerate(lines):
        draw_text_with_shadow(
            img,
            draw,
            (margin_x, title_y + i * line_h),
            line,
            title_font,
            fill=(255, 255, 255, 255),
            shadow_alpha=170,
            shadow_blur=max(6, size // 14),
            shadow_offset=max(3, size // 34),
        )

    # Brand mark (subtle).
    if brand:
        brand_font = load_font(font_path, max(26, int(size * 0.36)))
        brand_y = int(h * 0.075)
        letter_spaced_text(
            draw,
            (margin_x, brand_y),
            brand,
            brand_font,
            fill=(255, 255, 255, 120),
            spacing=int(size * 0.04),
        )


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


CATEGORY_LABELS = {
    "models": "MODELS",
    "tools": "TOOLS",
    "research": "RESEARCH",
    "industry": "INDUSTRY",
    "tutorial": "TUTORIAL",
}


def parse_size(value: str) -> tuple[int, int]:
    try:
        w, h = value.lower().split("x")
        return int(w), int(h)
    except (ValueError, AttributeError):
        raise SystemExit(f"Invalid --size {value!r}; expected e.g. 2560x1440")


def load_config(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def cover_fit(bg: Image.Image, target: tuple[int, int]) -> Image.Image:
    """Resize to fill the target box exactly (center crop), like object-fit: cover."""
    tw, th = target
    scale = max(tw / bg.width, th / bg.height)
    resized = bg.resize((round(bg.width * scale), round(bg.height * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - tw) // 2
    top = (resized.height - th) // 2
    return resized.crop((left, top, left + tw, top + th))


def main(argv: list[str] | None = None) -> int:
    script_dir = Path(__file__).resolve().parent
    skill_root = script_dir.parent
    parser = argparse.ArgumentParser(
        description="Overlay deterministic title text on an AI-generated background cover."
    )
    parser.add_argument("--background", required=True, help="AI-generated background image (any size)")
    parser.add_argument("--output", required=True, help="Final cover output path (.jpg or .png)")
    parser.add_argument("--title", required=True, help="Article title (exact text from frontmatter)")
    parser.add_argument(
        "--category",
        default="",
        help="(deprecated, not rendered) category slug or label",
    )
    parser.add_argument(
        "--date",
        default="",
        help="(deprecated, not rendered) date such as 2026-08-08",
    )
    parser.add_argument("--font", default="", help="CJK font path (default from config or fonts dir)")
    parser.add_argument("--size", default="", help="Output size, e.g. 2560x1440")
    parser.add_argument("--anchor", default="", help="bottom-left | bottom | left | center")
    parser.add_argument("--scrim", type=float, default=None, help="Scrim strength 0..1")
    parser.add_argument("--accent", default="", help="Accent color hex, e.g. #06B6D4")
    parser.add_argument("--brand", default="", help="Small brand mark (empty disables)")
    parser.add_argument("--no-brand", action="store_true", help="Disable brand mark")
    parser.add_argument("--quality", type=int, default=None, help="JPEG quality (1-100)")
    parser.add_argument(
        "--config", default=str(script_dir / "cover.config.json"), help="Config file with defaults"
    )
    args = parser.parse_args(argv)

    config = load_config(Path(args.config))

    size = args.size or config.get("size", "2560x1440")
    anchor = args.anchor or config.get("anchor", "bottom-left")
    scrim = args.scrim if args.scrim is not None else config.get("scrim", 0.6)
    accent = args.accent or config.get("accent", "#06B6D4")
    brand = "" if args.no_brand else (args.brand or config.get("brand", ""))
    quality = args.quality or config.get("quality", 90)
    font_path = args.font or config.get(
        "font", str(skill_root / "assets" / "fonts" / "SpaceGrotesk-VF.ttf")
    )
    if not os.path.isabs(font_path):
        for base in (Path.cwd(), skill_root, script_dir):
            candidate = base / font_path
            if candidate.exists():
                font_path = str(candidate)
                break

    category = args.category
    if category in CATEGORY_LABELS:
        category = CATEGORY_LABELS[category]

    if not os.path.exists(font_path):
        print(f"ERROR: font not found: {font_path}", file=sys.stderr)
        print("Run the skill's scripts/fetch-fonts.sh to vendor the fonts.", file=sys.stderr)
        return 2

    cjk_font_path = str(skill_root / "assets" / "fonts" / "NotoSansCJKsc-Bold.otf")
    if contains_cjk(args.title) and not os.path.exists(cjk_font_path):
        print(
            "ERROR: title contains CJK characters but NotoSansCJKsc-Bold.otf is not bundled.\n"
            "Run the skill's scripts/fetch-fonts.sh to download the CJK fallback font.",
            file=sys.stderr,
        )
        return 2

    bg = Image.open(args.background).convert("RGB")
    target = parse_size(size)
    canvas = cover_fit(bg, target)

    scrim = scrim_strength_for(canvas, anchor, float(scrim))
    canvas = apply_scrim(canvas, anchor, scrim)
    if canvas.mode != "RGBA":
        canvas = canvas.convert("RGBA")

    render_text_block(
        canvas,
        title=args.title,
        category=category,
        date=args.date,
        font_path=font_path,
        cjk_font_path=cjk_font_path,
        anchor=anchor,
        accent=hex_to_rgb(accent),
        brand=brand,
    )

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.suffix.lower() in (".png",):
        canvas.convert("RGB").save(out, format="PNG")
    else:
        canvas.convert("RGB").save(out, format="JPEG", quality=quality, optimize=True, progressive=True)

    summary = {
        "output": str(out),
        "size": f"{target[0]}x{target[1]}",
        "anchor": anchor,
        "scrim": scrim,
    }
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
