# DSH-PSCAD-WU — PSCAD/EMTDC 仿真自动化专家预设

当前版本:**v0.3.0**(变更记录见 `CHANGELOG.md`,发布与更新流程见文末「发布流程(规范化)」)

一个 DSH **agent preset(会话预设)**:把训练对话中实测验证的 PSCAD 使用技能打包成
"人设 + 组合 + 技能 + 示例",让任意电脑的 DSH 都能以官方预设机制使用,并能随后续
训练持续更新。

## 目录结构

```
dsh-pscad-wu/
├── preset.yml                 # 显示名/简介(预设选择器显示)
├── agent.cordis.yml           # 组合:以官方 standard 为母版 + PSCAD 专家人设
├── README.md                  # 本文件:部署/使用/更新工作流
├── skills/                    # ← 技能知识(会话中按需加载)
│   ├── pscad-automation/      #   mhi.pscad 驱动 PSCAD:环境/API/工作流/高频坑
│   ├── pscad-model-library/   #   元件库模型知识:开关/变压器/线路/电机/MMC-HVDC/效率工具
│   ├── pscad-verification/    #   数值验证方法论:.out 解析/FFT/开关计数/理论对照
│   ├── ess-storage-project/   #   ESS 储能并网工程:模型结构/11 输入/实验/验证
│   ├── lcc-hvdc-project/      #   LCC-HVDC:元件语义/CIGRE 参数/纹波/IEEE39 黑盒并网
│   └── pscad-acceptance-test/ #   预设验收与回归流程(四级:预设自检→环境→知识→真机)
├── CHANGELOG.md               # 版本与变更记录
├── install.ps1 / update.ps1 / publish.ps1  # GitHub 一键安装/更新/发布脚本
├── docs/source-notes/         # 训练期原始记录(权威档案,技能文档的出处)
└── examples/                  # 训练机实际跑通的参考脚本(路径需按新机修改)
```

## 在任意电脑上部署(官方预设机制)

1. 把整个 `dsh-pscad-wu` 目录(可打包 zip 或经 git 同步)放到目标机 DSH 用户目录的预设根:
   - Windows:`C:\Users\<用户名>\.dsh\.agent-presets\dsh-pscad-wu\`
   - 与 DSH 自带的 standard/minimal/cordis 平级共存,互不影响。
2. 重启 DSH(或刷新),新建会话时在预设选择器中选择 **DSH-PSCAD-WU**。
   若选择器里该预设显示为 broken,会同时给出原因行——通常是目标机 DSH 版本缺失
   组合里某 `@deepseek-ai/dsh-*` 包,升级/对齐版本即可。
3. 目标机第一次使用前,按 `skills/pscad-automation/SKILL.md` 第 1 节核对环境
   (PSCAD 可执行路径、能 `import mhi.pscad` 的 python、模型工作目录),把实际路径
   写进工作目录的环境说明。

> 说明:DSH 的跨机能力包即"预设目录"。官方没有一条"从别的机器拉取"的命令;
> 传播方式 = 拷贝本目录到各机 `.agent-presets/` 下,该目录本身可放 git 管理版本。

## 使用方法

- 会话里技能按需自动加载(命中任务主题时);也可直接要求加载对应技能。
- 每个 SKILL.md 顶部有"何时加载";技能正文是浓缩操作知识(参数/端口语义/实测踩坑/
  验证判据),先读再动手。
- 完整原始记录在 `docs/source-notes/`;可复跑脚本在 `examples/`(见
  `examples/_README.md` 的文件清单与需改路径)。

## 如何持续训练并更新(核心工作流)

1. **训练**:起一个 DSH-PSCAD-WU 会话,像以前一样让它实测新功能/新领域并验证
   (构建 0 错误 + 可核对数据),产出新的笔记/脚本(放工作区即可)。
2. **沉淀**(训练会话收尾时让 agent 做,或在此会话做):
   - 新主题 → 新建 `skills/<新主题>/SKILL.md`(浓缩:用途 / 方法·参数 / 验证判据 / 踩坑);
   - 旧主题新增内容 → 修订对应 SKILL.md 相应小节;
   - 可复跑示例脚本加入 `examples/`,原始记录入 `docs/source-notes/`。
3. **发布**:把更新后的整个目录同步到各机 `.agent-presets/dsh-pscad-wu/`
   (建议先删除旧目录再放入,保证无残留文件)。
4. **生效细节**:DSH 按 `agent.cordis.yml` 的变更判定"新一代"——只改 skills 文件时,
   新会话可能仍用旧组装。更新技能后**顺带小改 `agent.cordis.yml`(如加一行版本注释)**
   或重启 DSH,即可让之后的新会话拿到新技能;已在运行的会话保持旧组装不变。
5. 默认每台机器可改其私有环境(路径/型号),但那属于机器配置,不要写回预设共享文件。

## 边界与安全

- 预设的权限恰等于其组合内插件的权限(与 standard 同级:shell/文件/网络按宿主策略),
  不放松沙箱与审批。
- `agent.cordis.yml` 是被挂载文件,会话不会写回它;所有"写预设"只发生在上述发布流程。

## 从 GitHub 安装 / 更新(一行命令)

仓库地址:`https://github.com/jionmark11-hub/dsh-pscad-wu`(公开仓库,克隆无需登录)

**安装(首次,任意装有 Git 的 Windows 电脑 PowerShell):**
```powershell
git clone https://github.com/jionmark11-hub/dsh-pscad-wu.git "$HOME\.dsh\.agent-presets\dsh-pscad-wu"
```
或一条脚本式安装(自动建目录;已装过则拉更新):
```powershell
irm https://raw.githubusercontent.com/jionmark11-hub/dsh-pscad-wu/main/install.ps1 | iex
```

**更新(已安装机器):**
```powershell
git -C "$HOME\.dsh\.agent-presets\dsh-pscad-wu" pull
```

装完/更新完 → 重启 DSH → 新会话选择 DSH-PSCAD-WU。

## 维护须知:技能被发现的三个必要条件(踩过坑,别删)

1. **`skills/<名字>/SKILL.md` 必须有 YAML frontmatter**,且 `name` 必填、必须与目录名一致(kebab-case),`description` 必填。
   缺少或不合法时,DHS 会**静默跳过**该技能(只在日志里给警告),会话里看不到任何提示。
2. **`agent.cordis.yml` 里 `skill-filesystem` 行必须带 `customSkillDirs` 配置**(用 `baseUrl` 指向预设自己的 `skills/`):
   ```yaml
   - id: skill-filesystem
     name: '@deepseek-ai/dsh-skill-filesystem'
     config:
       customSkillDirs:
         - !!js "process.getBuiltinModule('node:url').fileURLToPath(new URL('skills/', baseUrl))"
   ```
   技能提供方默认只扫 `<项目根>/.dsh/skills`、`.agents/skills`、`<dshHome>/skills` 等根,**不扫预设目录**;
   官方 standard 预设不带技能所以那行没有配置,照搬它就等于技能永远不生效。
3. **技能文件改动不算"组装变更"**:只改 `skills/` 时,新会话可能仍用旧代际——顺带小改 `agent.cordis.yml`
   (如版本注释)或重启 DSH 才会切换。

> 自查方法:新建会话后看系统提示中的 `<available_skills>` 列表是否出现本预设的技能;
> 或把 `skills/<名字>` 临时拷到 `<工作区>/.dsh/skills/` 下,当前会话的技能目录会立刻刷新并列出它(验证通过后删除)。
## 发布流程(规范化)

DSH 的机制决定两条铁律:**预设是"文件即产物"**;**只有 `agent.cordis.yml` 的改动才算"新一代"**——
只改 `skills/` 时新会话可能仍用旧组装。因此把「提升 `agent.cordis.yml` 顶部 `preset-version` 注释」
定为每次发版的**必做动作**,它同时是版本号与代际触发器。

### 第 1 步 训练(掌握新技能)
起一个 DSH-PSCAD-WU 会话,照常实测新领域/新功能,要求走完整验证(构建 0 错误 + 可核对数据或截图),
过程记录与脚本留在工作区。

### 第 2 步 沉淀(把训练成果写成技能)
- 新主题 → 新建 `skills/<新技能名>/SKILL.md`;已有主题 → 修订对应 SKILL.md 的小节;
- 可复跑脚本 → `examples/`;原始记录 → `docs/source-notes/`。

**硬性格式(不满足会被静默丢弃)**
1. SKILL.md 必须以 YAML frontmatter 开头:`name`(= 目录名,kebab-case)+ `description`(必填);
2. 技能目录必须放在预设的 `skills/` 下,且 `agent.cordis.yml` 里 `skill-filesystem` 行的
   `customSkillDirs`(`baseUrl` 表达式)不能删——技能提供方**不扫描预设目录**。

### 第 3 步 升版本
1. `CHANGELOG.md` 顶部加一段 `## [X.Y.Z] - YYYY-MM-DD`(新增/修复/移除/文档);
2. 提升 `agent.cordis.yml` 顶部 `# preset-version: X.Y.Z`,并同步 `preset.yml` 的 `version`;
3. 提交信息统一为 `release: vX.Y.Z —— 一句话`。

### 第 4 步 本机自测
- `git -C F:\ESS\dsh-pscad-wu status -sb` 确认工作区干净;
- 新会话里让 agent 跑 `pscad-acceptance-test` 技能的第 0 级(技能清单应含新技能)与第 1~2 级;
  涉及真机改动再跑第 4 级。

### 第 5 步 推送与分发
```powershell
# 作者机(本仓库 = F:\ESS\dsh-pscad-wu)
cd F:\ESS\dsh-pscad-wu; git add -A; git commit -m "release: v0.3.1 —— ..."; git push
# 其他电脑
git -C "$HOME\.dsh\.agent-presets\dsh-pscad-wu" pull
```
**随后重启 DSH**(或让本次 `agent.cordis.yml` 改动自行换代际),新会话即带新技能。

### 第 6 步 复核 / 回滚
- 复跑验收第 0 级:技能数量与名称是否符合预期;缺了就按第 0 级的定位顺序查(配置 or frontmatter);
- 出问题:在作者机 `git revert <commit>`(或 `git checkout <旧commit> -- .`)→ 重新 push → 各机 pull → 重启;
- 试验性技能建议先在本地改、跑通验收再 push。

> 训练会话里可以直接这样说:"把刚才验证通过的内容沉淀成 `skills/<新技能名>/SKILL.md`(带 name/description
> frontmatter),示例放 `examples/`,原始记录放 `docs/source-notes/`,并更新 `CHANGELOG.md` 与 `agent.cordis.yml`
> 的 `preset-version`。" 之后你在作者机 commit/push 即可。