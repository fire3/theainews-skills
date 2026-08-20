---
name: theainews-cover-image
description: 为 The AI News 文章直接生成整张封面图：用chromebot出图，背景与标题文字全部由模型渲染。风格与版式各自按文章栏目、最近历史轮换，避免封面千篇一律。Use when the user asks to create/generate/make a cover image for a The AI News article, regenerate or batch article covers, or design cover backgrounds.
---

# The AI News Cover Image

一次出图的封面流水线：利用chromebot工具渲染完整封面——
背景、标题、副标题、可选统计卡片与品牌字标全部由模型直接生成。

1. 读取文章。
2. 写出完整生成提示词（风格规范 + 逐字文本 + 版式 + 约束）。
3. 用 RapidOCR 校验文字；出错就改提示词重新生成。
4. 用 chromebot（默认 doubao）出图。
5. 输出到 `public/covers/<slug>.jpg` 并接入文章 frontmatter。

## 前置依赖

- chromebot（默认使用 `--engine doubao`）
- 打开 CDP 模式的 chrome 浏览器（默认 CDP 端口 localhost:9222）
- OCR：RapidOCR（`rapidocr-onnxruntime`），配合 `opencv-python-headless`（`cv2`）做图片读取与文字识别。

### CDP 探测（严格规定）

- 开始生成前，先探测 `localhost:9222`（如 `curl http://localhost:9222/json/version`）
  确认 CDP 服务可用。
- **若探测失败：必须停下，明确提醒用户先启动 CDP 模式的 chrome 浏览器**（例如
  `chrome --remote-debugging-port=9222`），等待用户确认后再继续。
- **严禁**使用 Playwright、chromedriver 或任何脚本自行拉起/托管 CDP 服务；
  chromebot 只能连接用户已启动的浏览器，不得代为启动。

## 工作流

### 1. 读取文章

- 解析 `src/content/news/<slug>.md` 的 frontmatter：title、description、
  category、tags、现有 `image`。
- 摘出 2–3 个关键事实（数字、模型名、亮点）用于副标题/统计卡片。
- 默认输出 `public/covers/<slug>.jpg/png/webp`。

### 2. 选择风格与版式（关键：两者都不要固定）

- **严禁**连续两张封面使用同一风格，也严禁无脑回落到深海军蓝。
- 风格确定后，再按 `references/style-system.md`「版式池」选择一套构图骨架。
- **严禁连续两张封面使用同一版式**；不要默认回落到「底部三张统计卡片」。
- 最近 3 张封面中，风格与版式都要各自错开（连同强调色一起轮换）。

### 3. 设计图内文字

- 封面标题：简洁中文（建议 ≤14 字），用户要求英文时用英文；保留可搜索的
  模型/工具名。
- 副标题：一行，2–3 个关键事实（数字、配置、定位）。
- 数据/要点按所选版式组织（2–3 个短句），只有选 `L-bottom-cards` 才做成
  底部等距卡片；其余版式把数据融入大数字、分栏或要点竖排。
- 可选品牌字标 `THEAINEWS` 左上角（英文短串，不加空格，模型渲染稳定）。
- 提示词中不写十六进制色码或带编码的颜色，配色一律用文字描述（如「深海军蓝」「亮青」），防止编码被当成图内文字渲染泄露。
- 图内文字总量要小；所有字符串在生成前必须定稿。
- 对易错的品牌/模型名在提示词中逐字母拼写（如 F-I-R-E-C-R-A-W-L），但提示词
  本身保持精简。

### 4. 写生成提示词

- 调用后端前，先把完整、自包含的提示词存到 `prompts/01-cover-<slug>.md`
  （可复现记录）。
- 提示词必须包含：所选风格的完整规范（背景/排版/配色/视觉元素）、**所选版式**、
  逐字文本、安全边距、以及「图形上禁止出现任何文字」的约束。
- 结构参考 `references/prompt-template.md`。

### 5. 生成整张封面（chromebot，默认 doubao）

- 用 `chromebot image --engine doubao --prompt "..." --out public/covers --name <slug>` 生成；失败重试一次。
- 若 OCR/目视发现文字错误：写新的提示词文件（如 `01-cover-<slug>-v2.md`）、
  输出到新路径重新生成；**禁止**在位图上叠字或覆盖修正。

### 6. 校验

- 用 RapidOCR（`rapidocr-onnxruntime` + `opencv-python-headless`/`cv2`）编写脚本
  逐条核对图内文字：每个引号内的字符串必须逐字正确，
  图形（图标、装饰、卡片）上不能有多余文字。

### 7. 接入站点

- 转出 `public/covers/<slug>.jpg`（2560×1440，JPEG quality 90）。
- 在文章 frontmatter 增加/更新 `image` 与 `imageAlt`。
- 在站点仓库内跑 `pnpm build` 验证，按 AGENTS.md 提交推送。

## 风格池（绝不固定）

## References

- `references/style-system.md` — 风格预设与选择规则（步骤 2 前必读）。
- `references/prompt-template.md` — 一次出图的完整提示词结构。
