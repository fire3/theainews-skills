---
name: theainews-cover-image
description: Generate The AI News article covers by combining an AI-generated text-free background (via baoyu-image-gen / Seedream) with a locally composited English title (Space Grotesk Bold, max 2 lines). Use when the user asks to create/generate/make a cover image for a The AI News article, regenerate or batch article covers, or design cover backgrounds — especially when image-model text rendering is unreliable.
---

# The AI News Cover Image

Two-stage cover pipeline: the image model renders only the background, and all
text is composited locally so it is always pixel-perfect.

1. Design a text-free background prompt.
2. Generate the background with baoyu-image-gen (Seedream).
3. Composite the English title + brand locally.
4. Verify the final cover and the card crop.

## Prerequisites

- Python 3 + Pillow for compositing.
- Fonts: Space Grotesk (English titles) is bundled under `assets/fonts/`; the
  Noto CJK fallback font is downloaded on demand by `scripts/fetch-fonts.sh`
  and is only needed for Chinese titles.
- Background generation via the baoyu-image-gen skill, or the vendored
  `.baoyu-skills/baoyu-image-gen/scripts/main.ts` in the repo. Seedream needs
  `ARK_API_KEY` (environment or `.baoyu-skills/.env`).

## Workflow

### 1. Read the article

- Parse frontmatter from `src/content/news/<slug>.md` (title, category, slug).
- Default output: `public/covers/<slug>-composed.jpg`. Do NOT overwrite an
  existing cover unless the user asks.
- Site conventions: read `references/site-format.md` when needed.

### 2. Write the background prompt

- Read `references/background-prompt.md` before writing the prompt.
- Set `Text level: none` and explicitly forbid any characters, logos, or
  glyph-like shapes.
- Reserve clean zones: bottom-left 40-45% (title) and top-left 35% (brand);
  prefer deep, saturated dark colors.
- Save the prompt to `.baoyu-skills/baoyu-cover-image/outputs/NN-cover-<slug>-body.md`.

### 3. Generate the background

- If the baoyu-image-gen skill is available, use it.
- Otherwise run the vendored script from the repo root:

```bash
npx -y bun .baoyu-skills/baoyu-image-gen/scripts/main.ts \
  --promptfiles <prompt.md> \
  --image /tmp/cover-bg-<slug>.png \
  --provider seedream \
  --model doubao-seedream-5-0-lite-260128 \
  --size 2560x1440 \
  --quality 2k
```

- Never ask the model to render title text; retry once on failure.

### 4. Composite text locally

```bash
python3 <skill-dir>/scripts/compose_cover.py \
  --background /tmp/cover-bg-<slug>.png \
  --title "Concise English title (max 2 lines)" \
  --output public/covers/<slug>-composed.jpg
```

- Title: adapt the article title to concise English, 2 lines max, keeping the
  most searchable tokens (model/tool names). Use Chinese only if the user
  insists; first run `scripts/fetch-fonts.sh` to get the CJK fallback font.
- Defaults live in `scripts/cover.config.json`: 2560x1440, bottom-left anchor,
  adaptive scrim, brand `THE AI NEWS`.
- Adjust layout with `--anchor`, `--scrim`, `--brand`/`--no-brand`, `--font`,
  `--size`. Re-running this step costs no API credits.

### 5. Verify

- Open the final image and a 728x380 card crop (top/bottom cropped ~15px each).
- Check: no model-baked text; title legible at card size; brand not clipped;
  background keeps its color.
- If legibility is poor, tweak `--scrim`/`--anchor` and re-run step 4.

## References

- `references/background-prompt.md` — layout-aware, text-free background prompts (read before step 2).
- `references/site-format.md` — site dimensions, categories, output paths, brand colors.

## Scripts

- `scripts/compose_cover.py` — deterministic text overlay (Pillow).
- `scripts/fetch-fonts.sh` — vendors Space Grotesk + Noto CJK fonts.
- `scripts/text_wrap.py` — wrapping helper; do not invoke directly.
