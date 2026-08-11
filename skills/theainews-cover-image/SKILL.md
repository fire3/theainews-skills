---
name: theainews-cover-image
description: 为 The AI News 文章直接生成整张封面图：用 baoyu-image-gen（Seedream）一次出图，背景与标题文字全部由模型渲染，不做本地合成。风格按文章栏目与最近历史轮换，避免封面千篇一律。Use when the user asks to create/generate/make a cover image for a The AI News article, regenerate or batch article covers, or design cover backgrounds.
---

# The AI News Cover Image

一次出图的封面流水线：图片模型在单次 baoyu-image-gen 调用里渲染完整封面——
背景、标题、副标题、可选统计卡片与品牌字标全部由模型直接生成。**不再使用
本地文字合成**：不需要 Pillow、不需要字体文件、不需要 scrim/anchor 参数。

1. 读取文章，选择风格（见 `references/style-system.md`）。
2. 写出完整生成提示词（风格规范 + 逐字文本 + 版式 + 约束）。
3. 用 baoyu-image-gen 生成整张封面。
4. OCR / 目视校验文字；出错就改提示词重新生成，绝不修补位图。
5. 输出到 `public/covers/<slug>.jpg` 并接入文章 frontmatter。

## 为什么改成一键出图

- 每篇文章得到的是**设计过**的封面，而不是模板换字。
- 风格按栏目 + 轮换选择，杜绝统一的深色海军蓝审美。
- 少一个本地合成环节：无字体、无 Python/Pillow 依赖，出错面更小。

## 前置依赖

- baoyu-image-gen：优先使用已安装的 skill；或使用站点仓库内置脚本
  `.baoyu-skills/baoyu-image-gen/scripts/main.ts`。
- Seedream 需要 `ARK_API_KEY`（环境变量或 `.baoyu-skills/.env`）。
- 不再需要 Python、Pillow 或任何字体资源。

## 工作流

### 1. 读取文章

- 解析 `src/content/news/<slug>.md` 的 frontmatter：title、description、
  category、tags、现有 `image`。
- 摘出 2–3 个关键事实（数字、模型名、亮点）用于副标题/统计卡片。
- 默认输出 `public/covers/<slug>.jpg`；除非用户明确要求，否则不覆盖已有封面
  （覆盖前先备份旧文件）。

### 2. 选择风格（关键：不要固定）

- 生成前必读 `references/style-system.md`。
- 按栏目取推荐风格 → 应用防重复规则（跳过最近 3 张封面用过的风格）→ 轮换
  该风格的强调色变体。
- `--style <name>` 或用户在请求中点名的风格优先。
- **严禁**连续两张封面使用同一风格，也严禁无脑回落到深海军蓝。

### 3. 设计图内文字

- 封面标题：简洁中文（建议 ≤14 字），用户要求英文时用英文；保留可搜索的
  模型/工具名。
- 副标题：一行，2–3 个关键事实（数字、配置、定位）。
- 可选 2–3 个统计卡片，数字单独高亮。
- 可选品牌字标 `THE AI NEWS` 左上角（英文短串，模型渲染稳定）。
- 图内文字总量要小；所有字符串在生成前必须定稿。
- 对易错的品牌/模型名在提示词中逐字母拼写（如 F-I-R-E-C-R-A-W-L），但提示词
  本身保持精简。

### 4. 写生成提示词

- 调用后端前，先把完整、自包含的提示词存到 `prompts/01-cover-<slug>.md`
  （可复现记录）。
- 提示词必须包含：所选风格的完整规范（背景/排版/配色/视觉元素）、逐字文本、
  版式与安全边距、以及「图形上禁止出现任何文字」的约束。
- 结构参考 `references/prompt-template.md`。

### 5. 生成整张封面

```bash
npx -y bun .baoyu-skills/baoyu-image-gen/scripts/main.ts \
  --promptfiles prompts/01-cover-<slug>.md \
  --image /tmp/cover-<slug>.png \
  --provider seedream \
  --model doubao-seedream-5-0-lite-260128 \
  --size 2560x1440 \
  --quality 2k
```

- API 失败重试一次。
- 若 OCR/目视发现文字错误：写新的提示词文件（如 `01-cover-<slug>-v2.md`）、
  输出到新路径重新生成；**禁止**在位图上叠字或覆盖修正。

### 6. 校验

- 用 OCR（或目视）逐条核对图内文字：每个引号内的字符串必须逐字正确，
  图形（图标、装饰、卡片）上不能有多余文字。
- 检查 728×380 卡片裁切：标题/品牌在安全区内，上下边缘 3–4% 无文字。
- 生成后只允许裁切/缩放/转格式（如 JPEG q90），不允许改文字或构图。

### 7. 接入站点

- 转出 `public/covers/<slug>.jpg`（2560×1440，JPEG quality 90）。
- 在文章 frontmatter 增加/更新 `image` 与 `imageAlt`。
- 在站点仓库内跑 `pnpm build` 验证，按 AGENTS.md 提交推送。

## 风格池（绝不固定）

完整规范与选择规则见 `references/style-system.md`。速查：

| 风格 | 气质 | 典型栏目 |
|---|---|---|
| dark-atmospheric | 电影感深海军蓝 + 青/紫光效 | models、发布 |
| bold-editorial | 高对比深色杂志 + 活力强调色 | industry、发布 |
| editorial-infographic | 浅色杂志编辑风（白底 + 蓝/珊瑚） | tools、解读 |
| blueprint | 工程蓝图网格 + 工程蓝 | research、架构 |
| scientific | 冷色技术严谨风 | research |
| corporate | 藏蓝 + 金色商务风 | industry |
| minimal | 中性留白 + 单强调色 | 简报、综述 |
| sketch-notes | 暖色手绘教育风 | tutorial |

选择规则：栏目映射 → 跳过最近 3 张用过的风格 → 轮换强调色变体 →
`--style` 覆盖。

## References

- `references/style-system.md` — 风格预设与选择规则（步骤 2 前必读）。
- `references/site-format.md` — 站点尺寸、栏目、输出路径、后端。
- `references/prompt-template.md` — 一次出图的完整提示词结构。
