# The AI News site conventions

## Articles

- Path: `src/content/news/<yyyy-mm-dd-slug>.md`
- Frontmatter: `title`, `description`, `pubDate`, `author`, `category`, `tags`,
  optional `image` (`/covers/...`), `imageAlt`, optional `topStory`.

## Cover images

- Output size: 2560x1440 (16:9), JPEG quality 90.
- Location: `public/covers/<slug>.jpg`.
- Homepage card renders 728x380 with `object-fit: cover` — the 16:9 source is
  cropped ~15px from top and bottom, so keep text clear of the outer 3-4% edge.
- Article detail page renders the full image width, height auto.

## Categories

| slug | Chinese label | English label |
|------|--------------|---------------|
| models | 模型 | MODELS |
| tools | 工具 | TOOLS |
| research | 研究 | RESEARCH |
| industry | 行业 | INDUSTRY |
| tutorial | 教程 | TUTORIAL |

## Brand

- Brand mark: `THE AI NEWS`, optional, top-left, rendered by the model in a
  type style consistent with the selected cover style; dark styles use
  light/white text, light styles use dark text.
- Site accents (cyan `#06B6D4` / violet `#8B5CF6`) are only the default;
  the actual palette is decided by `references/style-system.md` and must vary
  across covers. Never default to the dark-navy + cyan/violet look.

## Generation backend

- baoyu-image-gen with Seedream: model `doubao-seedream-5-0-lite-260128`,
  size 2560x1440, quality 2k. Requires `ARK_API_KEY` (Volcengine Ark).
- Vendored skill scripts live at `.baoyu-skills/baoyu-image-gen/scripts/main.ts`.
- One-pass generation: the model renders background AND all title text in a
  single call. No local compositing, no fonts, no Pillow.
