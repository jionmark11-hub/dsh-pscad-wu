# PSCAD 元件库模型知识(七大实测领域)

> 内容提炼自 `docs/source-notes/PSCAD学习笔记.md`(2026-08 逐模块"最小模型+实测验证+写入笔记"产出,全部 ✅)。
> 各节给出 组件参数/端口语义/实测踩坑/验证判据,直接用于建模决策与报错诊断;数值均为训练机实测示例。

## 何时加载
建模/改模型中涉及 电力电子开关与 PWM、变压器、输电线路、电机、多机/自定义信号、MMC/HVDC、仿真效率工具 任一主题时加载。

## 1. 详细开关模型(peswitch + SPWM)
- **peswitch**:Type: 0=Diode 1=Thyristor 2=GTO 3=IGBT 4=Transistor;DP/DN 电气端口;SNUB=1 时内部 R-C 缓冲。
  触发:INTR=0 → APUL(Integer 0/1);INTR=1 → IPUL(REAL dim2 插值脉冲:状态+插值时间)。
- **compar**:A(0,0) B(0,2) OUT(4,0);Pulse: 0=Level(REAL 0/1)、1=Pulse(dim2 插值脉冲,配 INTR=1);OPos/ONone/ONeg。
  注意端口条件引用旧参数名 Conv(PSCAD 5.0 已改名 Pulse)。
- **sig_gen**:F 输入(Hz)、O 输出、Max/Min 范围 → PWM 载波。
- **SPWM 标准链**:sig_gen 载波 vs sin 调制波 → compar → 上桥;互补桥=第二个 compar 反接(A=调制波,B=载波)。
- 验证判据:半桥输出直流分量=Vdc/2;基波≈m·Vdc/2;载波边带在 f_sw±f1。
- 坑:内部输出变量 Text 参数(Name/I/It/V/Ton/Toff/Alpha/Gamma)留空 → 空信号名 contention(必须命名);INTEGER 触发不能走 datalabel,必须直连;引线穿过元件端口=短路;零长度线直接接触不建线。

## 2. 变压器(xfmr-3p2w)
- 参数:Tmva、f、**YD1/YD2(0=Y 1=Delta)**、Lead(D 超前/滞后 Y)、Xl(正序漏抗 pu)、Ideal、NLL/CuL、V1/V2(线电压 RMS kV)、View(0=三相 1=单线)、饱和(Enab/Sat/Xair/Im1/Xknee/Fremn)。
- 端口(View=0):A1/B1/C1 低压(x-4)、A2/B2/C2 高压(x+4);Y 接有 G1/G2 中性点(普通电气),D 接 G 端口为 Ground 型。
- 已验证事实(View=1,LCC 换相变压器场景):**N1(dim=3)=原边三相绕组、N2(dim=3)=副边三相绕组;G1/G2(dim=1)=星点/组端口**;原边星点 G1 直接接地,副边 G2 浮动。
- 坑:把 G1/G2 当绕组端口接 dim=3 线 → "dimension mismatch 3 != 1";Y 侧中性点可浮空(源已给参考地)。
- 验证:相峰值=V_L-L·√2/√3;过零法测 Y-D 相位移 ≈30°+负载角;变比含漏抗压降。

## 3. 输电线路(TLine)
- 结构:定义在工程内(如 simpleac:FLAT230),RowDefn(type="TLine") 内含 Line_Berg_Options + 塔几何(导体 CName/RadiusC/DCResC/分裂 BSP、地线、换位 Transp)。
- 实例参数:Length(km)、Freq、Dim(3)、Mode、VR、MVA、CoupleEnab。
- 线路常数文件:.tli(几何输入)/.tlo(输出:模式速度标幺、特征阻抗 Zc、衰减)。
- 物理:传播 ≈0.998c、Zc≈250~650Ω(三相不换位模式不同)、费兰蒂效应(长线轻载末端升压)。
- 坑:**create_definition 对 RowDefn XML 崩溃(PSCAD 5.0.0)** → 用官方示例(simpleac)改造或 load 含 TLine 的 pscx。
- 验证:变 Length 100→200km 对比末端电压;理论时延=Length/(0.998c)。

## 4. 电机(异步启动 / 同步机)
- 主库无异步电机组件(异步机内嵌在官方示例 Ind_Motor_Starting 内,自包含);sync_machine 是同步机。
- 启动流程:tbreakn 时序合闸 → 大电流冲击 → 转速爬升 → 负载转矩切换(Torque Input 0→1.8pu)→ 稳态。
- 通道:Current:1-3、Tload、Speed、Electric torque、Torque Input、TERMINAL VOLTAGE。
- 验证(实测):启动电流 6.2×额定、电磁转矩冲击 18.2pu、稳态转差 9%(1.8pu 负载)、机端电压跌落 11.0→15.0kV 区间。
- 坑:.out 含文本文件头与不等宽行,解析要容错(见验证技能)。

## 5. 多机并联 + ESS 暂态(自定义分段信号)
- 同步机并联:同转速,功角差决定功率分配;励磁一致。
- 自定义分段信号组件(step_gen 类):`IF (TIME .GT. $T0) ...` 驱动控制指令突变(如 EV 指令 60→50kV 阶跃)。
- 实测:PCC 电压 34.70→33.26kV(-4.2%)、VSC 电流 0.02→1.15kA(压差增大)。

## 6. MMC/HVDC(含 CIGRE LCC-HVDC 基准)
- 官方 Cigre_Benchmark.pscx:500kV/1000MW、12 脉动 LCC,整流定电流、逆变定熄弧角(经典值 α≈22°/γ≈18°);通道 DC Volts/Current/Power/Alpha Order/Gamma/AC Volts RMS。
- 桥组件 **g6p200_2**:UP(脉动数)、FP(0=内部触发角跟踪 PI+AO 输入 / 1,2=外部脉冲 / 3=直接 AO)、SNUB(RD/CD)、TfPh(变压器相移补偿,±30°)、GP/GI(触发角跟踪 PI)、RON/ROFF、Tblock。
- MMC 细节见官方 mmc_FiringHalfBridge 等示例与 hvdc_vsc 库(训练期仅做运行验证:128k 开关级模型)。
- 更完整的 LCC 端口语义/同步/参数见 lcc-hvdc-project 技能。

## 7. 仿真效率工具
- **Simulation Sets(仿真集)**:create_simulation_set('SET') + add_tasks + task.overrides(duration=..)(override_duration=True 生效)+ run_all_simulation_sets 批量构建运行 + remove。
- **Snapshot 快照**:SnapType(0=无 1=单次 2=增量同文件 3=增量多文件)、SnapTime;StartType(0=标准 1=从快照)、startup_filename/snapshot_filename。
- 并行多运行:官方 ParallelMultipleRuns 示例。
- 用法模式:先小 case 验证机制,再上大规模(见 pscad-automation §6 长任务纪律)。

## 维护说明
新领域模块验证通过后:在本文件加"模块 N",在 examples/ 落一个可复跑最小脚本,并把验证数据表补进 docs/source-notes/ 对应记录。
