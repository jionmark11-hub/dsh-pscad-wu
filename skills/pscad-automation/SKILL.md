---
name: pscad-automation
description: 用 Python 官方 API mhi.pscad 驱动 PSCAD 5 的完整自动化方法:环境核对、对象模型与 API 速查、标准建模工作流、布线几何规则、15 条实测踩坑与长任务纪律。Use when a task drives PSCAD from scripts (launch, create_case, wire, build, run, read output, capture GUI) or when diagnosing PSCAD build errors.
---

# PSCAD 自动化建模与运行(mhi.pscad)

> 训练来源:2026-08 于 F:\ESS 的多轮实测对话。内容全部来自"最小复现 + 对照官方示例/CIGRE 生成代码"验证过的脚本(demo*.py 序列),而非手册摘抄。
> 参考代码:预设 `examples/` 目录;原始记录:`docs/source-notes/PSCAD学习笔记.md`。

## 何时加载本技能
任何需要"用脚本驱动 PSCAD 完成 建模型/改模型/布线/构建/运行/截图"的任务,先读本文件,并按文末环境清单确认本机环境。

## 1. 环境核对清单(每台机器必查)
PSCAD 5 的自动化靠 `mhi.pscad`(PSCAD 官方 Python API,随 PSCAD 5 安装的 python 提供)。
训练机环境(仅样例,不可假定):
- PSCAD 安装:`F:\PSCAD\`;可执行文件 `F:\PSCAD\bin\win64\Pscad.exe`
- Python:`python`(训练机为 C:\Python314\python.exe)可执行 `import mhi.pscad`
- 模型工作目录:训练机为 `F:\ESS`(存放 .pscx/.pslx/.gf46 等)

换新机器先验证:
```bash
python -c "import mhi.pscad as m; print('ok', [x for x in dir(m) if not x.startswith('_')][:10])"
```
把每台机器的实际 EXE/PYTHON/WORK 写进工作目录的 AGENTS.md 或 `local_env.py` 一类的单一配置点,不要在任务中途到处硬编码。预设与示例里的 `F:\PSCAD\...`、`F:\ESS\...` 一律只是训练机样例。

## 2. 对象模型与关键 API(以实际脚本为准,写前用小脚本自测)
```python
import mhi.pscad
pscad = mhi.pscad.launch(exe=EXE, silence=True, splash=False, timeout=90)  # 启动并连接 Pscad.exe(GUI)
pscad.version
pscad.load(r'path\to\file.pscx')      # 打开既有 case(.pscx/.pslx 均可)
pscad.create_case('CASE_NAME', folder=WORK)   # 新建空白算例
pscad.create_library('LIB.pslx', folder=WORK) # 新建元件库
prj  = pscad.project('CASE_NAME')     # 按工程名取句柄(load/create 后)
case = prj                           # case 与 project 同义使用
```
- `case.parameters(time_duration=0.06, time_step=5, sample_step=20)` —— 单位:秒/µs/µs;time_step=5 表示 5µs。
- `case.canvas('Main')` / `prj.canvas('Main')` → 画布 main
- 元件:
  - 主库元件按字符串名:`main.create_component('master:battery', x=6, y=20)`(见 §4 清单)
  - 库/工程内自定义元件:`main.create_component('ess_pwm_demo:sin_gen', x=34, y=7)` 即 `工程名:定义名`
  - 传定义对象也可:`main.create_component(defn_obj, x=.., y=..)`
  - 方向 `orient=`(整数,旋转/镜像);参数一律字符串形式带单位:`bat.parameters(Type='0', Enom='100.0 [kV]', Qrated='10.0 [kA*hr]')`;取参数 `p = c.parameters()`
- 端口:`p = c.port('A')`,有 `p.x/p.y`;布线 `main.create_wire((x1,y1),(x2,y2))`
- 文件:`case.filename`、`case.save()`、`case.save_as('NEWNAME')`(见坑 4:load 进来的工程禁用 save,用 save_as)
- 构建/运行/取消息输出:
  ```python
  case.build()
  for m in case.messages(): print(m.status, m.label, m.text)   # status 含 'error'/'normal'
  errs = [m for m in case.messages() if m.status == 'error']
  case.run()                          # 阻塞到仿真结束(长仿真用后台任务,见 §6)
  case.output()                       # 运行时输出文本(尾部 -400~-2000 字符常用)
  ```
- 自建元件(UserDefnWizard):脚本化定义 Fortran 组件/模块,见 §3 与 `examples/demo2_compile_test.py`。
- GUI 辅助(截图验证用,仅 Windows):
  - `pscad.navigate_to('proj','Main', gf.iid, 'RMS waveforms')` 切到 Graph Frame 面板
  - `pscad.move(700, 300)`、`pscad.wheel(-120)` 模拟鼠标滚动
  - 窗口截屏:ctypes `PrintWindow` 抓 PSCAD 窗口位图存 .bmp(见 `examples/demo14_capture.py`;PSCAD 5.0 主窗口标题含 "PSCAD 5.0")
  - 自绘 Graph Frame 曲线面板:对画布上 components() 迭代找 GraphFrame/overlay,用 `gf.parameters(title=..)`、`p.parameters(ymin=..,ymax=..,title=..)` 改轴
- 输出文件读取:`from mhi.pscad.utilities.file import OutFile`(见坑 7 与 pscad-verification 技能)

## 3. 标准工作流(建一个能跑的新模型)
1. 规划拓扑与坐标:触发/控制线走画布外围绕行,电气区居中;两条长线用不同 x 竖线,避免重叠
2. 需要自定义 Fortran 元件时,先 `create_library`,用 `UserDefnWizard` 定义并 `create_definition(lib)`:
   ```python
   from mhi.pscad.wizard import UserDefnWizard, Signal
   w = UserDefnWizard('sin_gen')
   w.port.output(2, 0, 'out', Signal.REAL)
   cfg = w.category.add('Configuration'); cfg.real('Amp', value=0.8)
   w.graphics.text('sin', 0, -1)
   w.script['Dsdyn'] = '      $out = $Amp*SIN(TWO_PI*$F*TIME + $Ph)'   # $xx 引用参数
   w.create_definition(lib)   # 或 w.module=True 后创建"模块"(黑盒电气接口,见 lcc-hvdc-project)
   ```
   自定义控制器类元件常用端口:input(-2,0)/output(2,0)/electrical;信号类型 Signal.REAL/INTEGER/LOGICAL。
3. `create_case` → `case.parameters(...)` → 依次放电源、主电路元件、测量、控制器、显示(pgb)
4. 布线:先 `port()` 取坐标再 `create_wire`;零长度线(两端口同格)直接接触即可,不要 create_wire
5. `save()` → `build()` → **必须 0 error** 才 `run()`
6. `run()` 后取 `output()`/`.out` 数据做数值验证(见 pscad-verification),需要给人看再截图

## 4. 主库元件名速查(实测可用,写代码直接引用)
`master:battery` `master:capacitor` `master:resistor` `master:inductor` `master:ground`
`master:peswitch`(电力电子开关) `master:ammeter`(电流表,Name 即命名信号) `master:voltmetergnd`(对地电压表)
`master:const`(常数) `master:sig_gen`(锯齿/方波发生器,PWM 载波) `master:compar`(比较器)
`master:datalabel`(命名信号/扇出) `master:pgb`(画图曲线,pgb.parameters(Group=..,Scale=..,Units=..))
另有工程内/库内定义引用:`工程名:定义名`。
注:xfmr-3p2w、TLine、g6p200_2、nodeloop、realpole、pi_ctlr、source3 等复杂组件多以"库内定义 + 实例"方式使用;其中 **TLine/RowDefn 不可用 create_definition 直接造**(见坑 8),应从官方示例复制改造。

## 5. 高频坑位(实测踩过,按出现频率排序)
| # | 现象/报错 | 原因与对策 |
|---|---|---|
| 1 | `Signal '' type contention` | 元件内部输出变量 Text 参数(如 peswitch 的 I/It/V/Ton/Alpha/Gamma)留空 → 必须填唯一名字 |
| 2 | `Path between terminals 'A' and 'B' is a short circuit` | 引线从某端口竖直穿过元件本体又接到另一端 → 绕行布线 |
| 3 | datalabel 传 INTEGER 报 contention | datalabel 只能承载 REAL;INTEGER 触发信号必须物理 wire 直连(REAL→INTEGER 用自定义 `$out=NINT($in)`) |
| 4 | load 后 `save()` 卡死/弹 Save As 对话框 | **load 进来的工程只能 `save_as(新名)`**,之后用 `pscad.project(新名)` 重新取句柄 |
| 5 | `'Vdc'` 相关异常 | 'Vdc' 是 EMTDC 保留名,测直流电压改名(如 Vdc_meas) |
| 6 | GND type contention | battery.B 等已是 Ground 型端口,不要再接 ground 组件;ground 组件二选一 |
| 7 | .out 解析错位 | .out 开头有文本文件头(read_values 首行是文本);行宽不一致需容错(见验证技能) |
| 8 | `create_definition` 崩溃(RowDefn/部分 XML) | PSCAD 5.0.0 对某些定义 XML 崩溃 → 用官方示例改造或 load 含该元件的 pscx |
| 9 | source3 输出电压不对 | **Vm 与 Es 必须同时设**(Es 是实际内部电压,默认 230kV,只设 Vm 会按 230kV 输出);Ctrl=0(Fixed) |
| 10 | 空信号名/空参数 | SOC、Name、输出 Text 参数等留空产生 '' 空信号 → 全部命名 |
| 11 | "dimension mismatch 3 != 1" | dim=3 三相端口与 dim=1 单相线混连;分清绕组端口(N1/N2,dim=3)与星点端口(G1/G2,dim=1) |
| 12 | 模块内部 INTEGER 同名 datalabel 合并报 contention | INTEGER/控制信号不进 datalabel;外部观测用 端口名+'_P' 的 datalabel 避免双重源 |
| 13 | 长 wire 交叉母线/支路报 splice/contention | 高密度画布(IEEE39 母线区)先扫描空白区、逐段验证走廊 |
| 14 | "Voltage chatter" 警告 | 电源 energize/阀组缓冲的数值噪声提示,通常不影响结果;判断依据看状态码与输出 |
| 15 | 构建/运行卡死(CPU 高、无输出) | 多半是弹了模态对话框(save 问题/坏参数);后台任务+日志观察,必要时杀进程 |

## 6. 长任务执行纪律
- 大型工程(IEEE39+LCC,27 子系统)**构建需 5~10 分钟、运行 1s@5µs 约 1~2 分钟**。不要前台阻塞等结果:
  - 用后台任务跑 `python xxx.py > log.txt 2>&1`,周期性查看日志尾部与进程状态;
  - PSCAD 一次只跑一个实例,并发前先确认无残留 Pscad.exe。
- 对 GUI 的误操作(弹窗)会占住 PSCAD;脚本内加超时与异常打印,失败保留现场日志。

## 7. 出错处置循环
1. build 有 error → 逐条打 messages(含 label/text),对照 §5 坑表定位,先修"信号命名/端口类型/布线几何"三类最常见问题
2. run 后无预期波形 → 先查 output() 文本:状态码、'has stopped'、报错行
3. 数值不对 → 先怀疑量纲(单位后缀、pu vs 有名值、度 vs 弧度),用理论公式粗算对照(见验证技能)
4. 修完重 build/run,保留"前后对照"日志;模型每步改动可回退(备份 .pscx/.bakx)

## 8. 维护说明
本文件由训练对话沉淀。新增经验:在对应小节补条目(带"实测"字样与日期),同步一个可复跑的最小示例到 examples/,并在 §5 表尾追加。
