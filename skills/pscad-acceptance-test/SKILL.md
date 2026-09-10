---
name: pscad-acceptance-test
description: DSH-PSCAD-WU 预设的验收与回归流程:预设完整性自检(技能目录/frontmatter/customSkillDirs)、本机环境核对、知识抽查、只读工程分析、最小端到端真机运行,并给出可核对的期望证据与失败处置。Use when the preset itself changed, when onboarding a new machine, or when the user asks to verify/test this preset.
---

# DSH-PSCAD-WU 验收与回归测试

> 用途:预设被改动后(加技能/改组合/换示例/换机器)用一套固定流程确认"没坏、还真能干活"。
> 设计原则:逐级加压,前三级只读,第四级才启动 PSCAD;每级都要给出可核对的证据。

## 何时加载
- 预设内容改动后要回归;
- 换到新电脑第一次使用时;
- 用户说"测一下/验收这个预设"。

## 总则
- **测试期间不要修改预设文件**;发现问题只报告现象与完整报错。
- 禁止臆造路径:找不到 PSCAD / python / 工程就说明并停下。
- 输出统一为三段式表格:`| 级别 | 通过/失败/跳过 | 关键证据(一句话) |`。

## 第 0 级 · 预设完整性自检(只读,不启动 PSCAD)
目的:先确认技能真的会被发现——这里历史上出过两次严重缺陷(组合缺 `customSkillDirs`;SKILL.md 缺 frontmatter)。
1. **自洽比对(无需手工维护数量)**:求出下面两个集合并**必须完全一致(不多不少)**:
   - 磁盘清单:用文件工具列出 `<预设目录>/skills/` 下的子目录(每个都应含 SKILL.md);
   - 目录清单:从本会话 `<available_skills>` 中挑出属于本预设的技能(与磁盘清单同名者)。
   参考(截至 v0.3.1 共 6 个,仅作提示、不作判定依据):pscad-automation / pscad-model-library /
   pscad-verification / ess-storage-project / lcc-hvdc-project / pscad-acceptance-test。
2. 缺失时的定位顺序:
   - **一个都没有** → 查 `agent.cordis.yml` 里 `skill-filesystem` 行是否有
     `customSkillDirs` + `!!js ... new URL('skills/', baseUrl)`(技能提供方**不扫描预设目录**);
   - **少了某个** → 查该 `skills/<名字>/SKILL.md` 顶部是否有 YAML frontmatter,
     `name` 必须与目录同名(kebab-case)、`description` 非空;不合法会被**静默跳过**。
3. 用文件工具确认 `<预设目录>/skills/<名字>/SKILL.md` 存在。预设目录通常在
   `<用户>\.dsh\.agent-presets\dsh-pscad-wu`。
4. **本级别失败时不要继续往下跑。**

## 第 1 级 · 本机环境核对(只读)
- `python -c "import mhi.pscad; print('mhi ok')"`(需 PSCAD 官方 API 的 python);
- 定位 `Pscad.exe`(训练机样例 `F:\PSCAD\bin\win64\Pscad.exe`,新机器必须实测);
- 报告当前工作目录;把真实配置落到工作目录的环境说明(如 `AGENTS.md` 或单一 `local_env.py`),
  并明确声明**不沿用**训练机样例路径。

## 第 2 级 · 知识抽查(以已加载技能内容为准,禁止联网/猜测)
标准题与期望要点(答不上或答错 = 技能未正确加载):
1. `g6p200_2`:KB=1 解锁 / KB=0 闭锁;AO 在 **FP=0 时单位是弧度**(FP=3 才是度);
   CB 是交流同步基准**节点号**(经 nodeloop.X1);TfPh 补偿变压器相移(YD 馈电桥 −30°、YY 桥 0°)。
2. `peswitch`:INTR=0 → APUL(Integer 0/1);INTR=1 → IPUL(REAL dim2 插值脉冲);
   **INTEGER 触发信号不能走 datalabel**(只承载 REAL),必须物理 wire。
3. `.out` 两个坑:开头有**文本文件头**(首行非数据,需剥离);各行宽度可能不一致(需容错)。
4. `source3`:必须**同时**设 `Vm` 与 `Es`(Es 才是实际内部电压,默认 230kV)。
5. `xfmr-3p2w`(View=1):N1/N2(dim=3)是原/副边三相绕组;G1/G2(dim=1)是星点端口。

## 第 3 级 · 只读工程分析(有 .pscx 才做)
- 取最小工程,只读遍历 Main 画布:元件类型清单 + 端口/接线要点;
- 明确不修改、不 build、不 run;工作区为空则如实跳过并说明。

## 第 4 级 · 最小端到端真机运行(会弹 PSCAD 窗口,约 1~3 分钟)
1. 从 `<预设目录>/examples/demo21_pwm_halfbridge.py` 复制模板到工作区临时目录
   (**不要用**历史调试文件;该文件是训练期中间产物,缺触发线/内部信号名,无法独立 Build);
   把脚本顶部 `EXE` / `WORK` 常量改成**本机真实路径**后运行;
2. 流程必须走完:启动 PSCAD → 建模型 → **Build 0 error** → Run;
3. 期望证据(训练机基准,2026-08 实测,可对照):
   - Run 状态码 0,矩阵开关事件数百次量级(实测 ~239);
   - 调制波 `MOD` = 设定值 **0.800**;
   - 60Hz 基波幅值 ≈ **29.31 kV**:对照半桥 SPWM 理论 `m·Vdc/2`(battery 实际输出 ≈67.5kV → 27.0kV),
     偏差 ≈8.5%,**在 15% 容差内即通过**(PWM 波实测基波对理想值的固有偏差,不是错误);
4. 收尾:关闭 PSCAD、删除临时目录里的生成物,保留打印的结论日志。

## 失败处置与报告
- 每个失败项附**完整报错文本** + 你判断的原因(环境问题 / 预设内容缺失 / 示例脚本问题)。
- **不要**自行修改预设或技能文件;把报告交回用户,由作者按发布流程修复并升版本。
- 提醒用户:只改 `skills/` 不会触发新代际,需按 README 的发布流程提升
  `agent.cordis.yml` 顶部 `preset-version` 注释(或重启 DSH)。

## 维护说明
- 新增检查项就往对应级别加条目;新的"期望基准值"写进第 4 级并注明机器与日期。
- 第 0 级用「磁盘清单 vs 会话目录」自洽比对:新增/删除技能时无需改本文件。
