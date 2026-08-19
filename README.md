# theainews-skills

The AI News（https://theainews.cc）的 Codex skill 集合。目前包含封面配图 skill，
未来会持续加入其他 theainews 相关的 skill。

## 目录结构

```text
skills/
└── theainews-cover-image/     # 封面：AI 一次出图（背景 + 标题文字），风格轮换
    ├── SKILL.md
    ├── agents/openai.yaml
    └── references/            # 风格系统、提示词模板、站点约定
```

## 安装（npx）

### 方式一：skills 生态 CLI（推荐）

仓库按 `skills/<skill-name>/SKILL.md` 布局，可被
[`skills`](https://www.npmjs.com/package/skills) CLI 自动发现：

```bash
# 查看本仓库有哪些 skill
npx skills add fire3/theainews-skills --list

# 全局安装到 ~/.codex/skills（Codex 会自动发现）
npx skills add fire3/theainews-skills --skill theainews-cover-image -g -a codex -y

# 安装到当前项目（默认写入 ./.codex/skills/）
npx skills add fire3/theainews-skills --skill theainews-cover-image
```

### 方式二：仓库自带 CLI

```bash
# 列出可用 skill
npx -y github:fire3/theainews-skills list

# 安装到默认位置（$CODEX_HOME/skills，缺省 ~/.codex/skills）
npx -y github:fire3/theainews-skills install theainews-cover-image

# 安装全部 / 强制覆盖 / 指定目录
npx -y github:fire3/theainews-skills install --force
npx -y github:fire3/theainews-skills install theainews-cover-image --dest ~/.codex/skills
```

发布到 npm 后也可直接 `npx -y theainews-skills install <skill>`。

## theainews-cover-image 前置依赖


## 新增 skill

在 `skills/` 下新建 `<skill-name>/SKILL.md`（含 `name` 与 `description`
frontmatter）及所需 resources 即可，`skills` CLI 与本仓库 CLI 都会自动发现。

## 许可证

仓库代码 MIT；字体资源为 OFL-1.1（见 `skills/theainews-cover-image/assets/fonts/LICENSES.md`）。
