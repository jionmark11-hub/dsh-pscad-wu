---
name: lcc-hvdc-project
description: LCC-HVDC 换流器建模与并网工程案例:12 脉动拓扑、CIGRE 基准参数、g6p200_2 与 xfmr-3p2w 端口语义、直流纹波诊断、黑盒 LCC39 接入 IEEE39。Use when modelling line-commutated converters, HVDC links, or integrating an LCC module into a large AC system.
---

# LCC-HVDC 换流器建模与并网(IEEE39 接入)工程案例

> 覆盖:单端 12 脉动 LCC 整流器(ess_lcc)→ CIGRE 基准对照 → 黑盒 LCC39 模块接入 IEEE 39 节点(ieee39_lcc)。
> 原始记录:`docs/source-notes/LCC学习笔记.md`、`LCC_模型验证记录.md`、`LCC_接入IEEE39_验证记录.md`;脚本:`examples/demo29_lcc.py`、`examples/demo31_ieee39_lcc.py`。

## 何时加载
任务涉及 HVDC/LCC 换流器(6/12 脉动、触发角控制、换相失败/纹波)、把 LCC 黑盒接入大交流系统、或对照 CIGRE 基准时。

## 1. 理论速览(建模与判据用)
- 理想空载直流电压:6 脉动 Vd0=1.35·Vll;12 脉动 Vd0=2×1.35×Vll(两桥直流串联,YY+YD 副边相差 30°)。
- 实际电压:Vd=Vd0·cosα − (3/π)·Xc·Id(换相压降);γ=180°−α−μ。
- 控制标准结构:整流定电流(CC,PI 出 α 5°~20°);逆变定熄弧角(CEA,α=180°−β 90°~150°)+ 电流裕度(Imargin 0.1pu)+ VDCOL。
- 无功:LCC 吸收 Q≈0.5~0.6·P,须并联补偿;12 脉动注入 11/13 次等 12k±1 谐波(无滤波 11 次≈9%、13 次≈7.7% 基波)。
- 并网强度:SCR=换流母线短路容量/直流功率;强系统 >5。IEEE39(数十 GVA 短路容量)挂 60MW 级 LCC 时 SCR≫10,满足。

## 2. PSCAD 元件语义(已逐项对照 CIGRE 生成代码验证,纠正过早期错误笔记)
**xfmr-3p2w(View=1,换相变压器)**:N1/N2(dim=3)=原/副边三相绕组;G1/G2(dim=1)=星点端口(原边 G1 接地、副边 G2 浮动);Xl=0.18pu 即换相电抗。
**g6p200_2(6 脉动桥,View=1)**:
- N(dim=3)=交流三相功率(接副边 N2);DP/DN=直流±;
- **CB(Integer 输入)=交流同步基准节点号** —— 触发同步取"原边母线电压",接法:Rbus(三相母线)→ nodeloop(三相机电节点)→ nodeloop.X1(节点号)→ CB;
- **KB=1 解锁运行、KB=0 闭锁**(KB 由比较器在 t>0.04s 置 1;KBR 逻辑见 CIGRE);
- **AO 在 FP=0 时单位是弧度**(如 0.52~1.57=30°~90°),FP=3 才是度;AM/GM 输出 α/γ 测量(弧度);
- TfPh 补偿变压器相移:**YD 馈电桥 TfPh=−30°、YY 馈电桥 TfPh=0°**;SNUB(RD=5000Ω/CD=0.05µF)、GP/GI=10/50(触发角跟踪 PI)、RON/ROFF、Tblock=0.04s。
- 直流侧接地参考:直流负直接接地(CIGRE)或 1MΩ 中点接地(小模型等效,已验证可行)。

**CIGRE 基准可抄参数(50Hz/345kV)**:整流变 603.73MVA 345/213.456kV、逆变变 591.79MVA 230/209.229kV,Xl=0.18pu;CC PI(GP=0.7506、TI=0.0544s、输出 0.52~1.57rad、初值 90°)、CEA PI(GP=0.63、TI=0.01524s、0.52~1.92rad、初值 110°);平波电抗 0.5968H/极;电流滤波 realpole(G=0.5 是 CIGRE pu 标幺配合,**自有名值 kA 时必须 G=1**)。

## 3. 单端整流案例(ess_lcc,验证通过)
拓扑:60kV/60Hz source3 → 换相变 YY+YD(60/25kV,Xl=0.18)→ 2×g6p200_2 直流串联 → Ld(0.2H)→ 电流表 → Rl(60Ω);控制:IDC → realpole(G=1,T=0.0012s)→ sumjct(与 IORD 比较)→ pi_ctlr(0.75/0.0544,限 5°~90°,初值 30°)→ AO。
- source3 必须 **Vm 与 Es 同时设**(Es 实际内部电压,默认 230kV,只设 Vm 会输出 230kV!)。
- 稳态核对(工况 IORD=1.0kA):IDC=1.012kA、α=14.5°、VDC_LCC(半桥对地)≈30.3kV(理论 33.75·cos14.5°−压降)、γ≈149.7°;IORD=0.5kA → α≈61.8°。
- 动态:IORD 1.0→0.5 时 α 14.5°→61.8°、Id 1.01→0.51kA,负反馈方向正确。
- **纹波诊断**(用户常见疑问"为何 Vd 振荡"):VDC_LCC 测的是单桥 6 脉动对地 → 主频 355.7Hz≈6×60;12 脉动总纹波主频 720Hz、峰峰值随 α 增大(α=5°≈3kV、62°≈31kV);电流纹波仅 ~0.9%(Ld 工作正常)→ **是固有换相脉动不是失稳**,无需调 PI;减小靠加大 Ld/CIGRE 0.5968H、直流侧并联 10~50µF 电容(最有效)、加交流 11/13 次滤波器。

## 4. 黑盒并网(IEEE39,验证通过)
- 封装:**UserDefnWizard + w.module=True**,电气接口 `w.port.electrical(x, y, 'AC', dim=3)` → 模块内自动生成 **master:xnode 'AC'**(与 CIGRE Rectifier 同构);内部电路与 xnode 同名电气连接,外部实例即三相电气端口。
- LCC39 端口:AC(电气 3 相,230kV)、IORD(REAL 指令 kA)、VDCO/IDCO/ALPHAO(观测输出);内部即 §3 拓扑的 230kV 版(换相变 230/25kV,Xl=0.18)。
- 接入母线:Bus39(230kV,母线区极密:支路引线通道与母线横线交错)→ 先扫描空白区,走廊逐段验证无交叉(如 `(24,55)->(24,44)->(10,44)->(10,60)` 四段);T 接不需要额外节点元件。
- 实测(1.0s@5µs,状态码 0):VDCO=30.05kV(半桥;总 ≈60.1kV)、IDCO=1.002kA 跟踪 IORD=1.0 ✓、ALPHAO=22.7°(母线电压略降致 α 比独立测试大,物理合理)、LCC 子系统开关 1682 次/1s(12 脉动正常)、发电机子系统计数与基线一致。
- 坑(重要):
  - load 进来的 case 禁 `save()`,必须 `save_as(新名)` 再重取句柄;
  - 模块内部 INTEGER(consti→KB)必须物理 wire,经 datalabel 会 contention;
  - 输出端口 wire 与同名 datalabel 双重源 → 外部观测用 端口名+'_P';
  - 大系统构建 5~10 分钟/运行 1~2 分钟 → 后台任务+日志(automation 技能 §6);
  - 原文件先备份(如 ieee_39_bus_orig.pscx),交付文件独立命名。

## 5. 维护说明
新增换流器类型(VSC-HVDC/MMC)、两端结构、滤波器设计等内容时:按"理论/元件语义/验证数据/坑"四段式在此追加小节,脚本入 examples/,原始记录入 docs/source-notes/。
