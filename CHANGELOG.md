# 变更记录(CHANGELOG)

本仓库是 DSH agent preset「**DSH-PSCAD-WU**」(预设 id / 目录名:`dsh-pscad-wu`)。
版本号同时标注在两处:

- `preset.yml` 的 `version` 字段(人类可读,DSH 忽略多余字段);
- `agent.cordis.yml` 顶部注释 `# preset-version: X.Y.Z` ——**这一行是权威版本号,也是"触发新代际"的规范动作**
  (DSH 只按组合文件的变更判定新一代;只改 `skills/` 时新会话可能仍用旧组装)。

发布流程见 `README.md` 的「发布流程(规范化)」。

---

## [0.3.1] - 2026-09-09

### 变更
- `pscad-acceptance-test` 第 0 级改为**自洽比对**:磁盘 `skills/` 目录集合必须与会话技能目录中属于本预设的技能集合完全一致(不多不少),不再依赖手工维护的技能数量清单;新增/删除技能后无需改该文件。
- 本次仅改技能文档,按规范提升 `preset-version` 以触发新代际。

## [0.3.0] - 2026-09-09

### 新增
- 第 6 个技能 **`pscad-acceptance-test`**:把四级验收流程(预设完整性自检 → 环境核对 → 知识抽查 →
  真机端到端运行)沉淀为可复跑技能,改完预设一条指令即可回归。
- 本 `CHANGELOG.md` 与版本号规范(`preset.yml` version + `agent.cordis.yml` preset-version 注释)。

### 变更
- persona 的技能清单加入验收技能,并写明"改动预设后先跑验收自检"。
- `README.md`:增加版本号、目录树补验收技能、新增「发布流程(规范化)」与「版本与变更记录」说明。

## [0.2.0] - 2026-09-09

### 修复
- **技能完全无法被发现(严重)**:`agent.cordis.yml` 中 `skill-filesystem` 行缺少 `customSkillDirs` 配置。
  技能提供方默认只扫描 `<项目根>/.dsh/skills`、`.agents/skills`、`<dshHome>/skills`,**不扫描预设目录**;
  已按官方 `cordis` 预设写法补上 `!!js ... new URL('skills/', baseUrl)`。
- **5 个 SKILL.md 缺少必填 YAML frontmatter**:技能文件必须以 frontmatter 开头且 `name`(与目录同名的
  kebab-case)与 `description` 必填,否则被静默跳过;已全部补齐。

### 移除
- `examples/demo21b_min.py`:训练期"中间隔离/调试"文件(无触发线、peswitch 内部输出变量未命名),
  无法独立 Build;示例说明改为推荐 `examples/demo21_pwm_halfbridge.py` 作为最小可跑模板。

### 文档
- `README.md` 新增「维护须知:技能被发现的三个必要条件」。

## [0.1.1] - 2026-09-09

### 变更
- 命名修正:插件名 `dah-PSCAD-WU` → **`DSH-PSCAD-WU`**;预设 id/目录 `dah-pscad-wu` → **`dsh-pscad-wu`**;
  GitHub 仓库同步改名为 `dsh-pscad-wu`(旧地址自动跳转)。

### 新增
- GitHub 一行安装/更新能力:`install.ps1`(幂等:未装则克隆、已装则拉取)、`update.ps1`、作者端 `publish.ps1`;
  三个脚本以 **UTF-8 with BOM** 保存并通过 PowerShell 7 与 Windows PowerShell 5.1 解析验证。
- `README.md` 增加「从 GitHub 安装 / 更新(一行命令)」。

## [0.1.0] - 2026-09-09

### 新增
- 首个版本:以官方 `standard` 预设为母版、替换为 PSCAD/EMTDC 仿真自动化专家人设的 agent preset
  (`preset.yml` + `agent.cordis.yml`,保留完整编码工具集)。
- 5 个技能:`pscad-automation` / `pscad-model-library` / `pscad-verification` /
  `ess-storage-project` / `lcc-hvdc-project`(内容源自训练对话实测沉淀)。
- `docs/source-notes/`:7 份训练期原始记录(权威档案)。
- `examples/`:12 个训练机实测跑通的参考脚本 + 对照说明。
- 部署到 `<dshHome>/.agent-presets/dsh-pscad-wu` 并通过官方名单挂载校验(`standingKeyFor` → MOUNT_OK)。
