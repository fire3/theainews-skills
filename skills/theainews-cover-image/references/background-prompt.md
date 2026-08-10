---
type: cover
text: none
---

# Background-only prompt guide

The image model renders ONLY the background. The final cover text (English
title, brand mark) is composited locally, so the prompt must leave clean zones
and must never ask the model to render characters.

# Content Context
Article title: {FULL_TITLE}
Content summary: {2-3 sentence summary of key points}
Keywords: {5-8 keywords}

# Visual Design
Cover theme: {2-3 words visual interpretation}
Type: {type}            # conceptual / metaphor / scene / minimal / hero
Palette: {palette}      # dark / cool / elegant / vivid / retro / ...
Rendering: {rendering}  # digital / flat-vector / painterly / ...
Text level: none
Mood: {mood}
Aspect ratio: 16:9
Language: zh

# Text Elements
No text elements. Do NOT render any letters, numbers, words, logos, labels,
watermarks, symbols, or glyph-like shapes anywhere in the image. Text will be
overlaid in post-production.

# Reserved Zones (layout-aware)
- Bottom-left 40–45% of the frame: keep clean, low-detail, and relatively dark
  or uniform — the English title (max 2 lines) is placed here.
- Top-left 35%: keep clean — the THE AI NEWS brand mark is placed here.
- Do not place the focal subject in the bottom-left zone; center it or shift it
  slightly right.
- Prefer deep, saturated colors over gray: the site brand uses dark navy with
  electric violet / cyan accents. A dark colored background keeps white title
  text readable without heavy scrimming.

# Mood Application
{mood}: {mood-specific guidance from the cover skill}

# Composition
{type} composition:
- {type-specific layout guidance from the cover skill}
Visual composition:
- Main visual: {visual metaphor derived from the article}
- Layout: main subject occupies the center-to-right area; keep the bottom-left
  40-45% and top-left 35% clean and low-detail for the composited text.
  16:9 horizontal composition.
- Decorative: {palette-specific decorative elements}
Color scheme: {colors from palette, adjusted by mood}
Color constraint: Colors are rendering guidance only; do NOT display color
names, hex codes, or palette labels as visible text in the image.
Rendering notes: {key rendering characteristics}
Palette notes: {key palette characteristics}

# Text Integrity
Strictly no text: the final image must contain zero readable characters of any
language. Plain visual elements only.
