---
name: ess-storage-project
description: ESS 储能并网工程案例(受控电流源 VSC + ess_ctl 控制器):模型结构、11 个控制输入、GUI 与脚本两种改参数方式、观察面板与四类标准实验、调优历程。Use when working on the ESS/storage converter PSCAD models or their grid-side P/Q/V control.
---

# ESS 储能并网工程案例(受控电流源 VSC)

> 工程背景:60kV 电网 + 储能变流器(受控电流源方案),交付单文件 `ess_full.pscx`(组件定义已嵌入,打开即用)。
> 原始记录:`docs/source-notes/ESS_完整模型_验证记录.md`、`ESS_PSCAD控制操作说明.md`;脚本:`examples/demo28_ess_full.py`。
> 本技能面向"继续在 ESS 模型上做实验/改控制/扩工况"的会话;换新机器需先按 automation 技能改路径并打开确认。

## 何时加载
任务涉及 ESS/储能变流器模型(ess_full/ess_main 系列)、其控制器(ess_ctl)、或电网侧 P/Q/V 控制实验时。

## 1. 模型结构
```
电网 60kV ──Rg/Lg──┬──Lf/Rf── 受控电流源 VSC(3× master:src_ccin_1 + inv_park,注入 id_ref/iq_ref)
                   └──Cf──┐
                     PCC   ├ [VP 电压表]  控制器测量
                           ├ [IG 网侧电流表] → P/Q 测量(网侧)
                           └ [IC 变流器电流表] → 电流测量
```
控制器 ess_ctl 内部链:测量(PLL 0.707/94.2 → Park → P/Q/V 测量,低通 TPQ=0.02s 滤 LCL 谐振)→ 附加有功 A01-A07 / 附加无功 R01-R05 → 外环 O01-O04(KPP=0.22/KIP=0.01,V/Q 无扰切换)→ 手动电流模式 → 限幅 1.1pu → 内环 I01-I04(0.5/0.0167)。软启动 TSS=0.5s(PLL 锁定前参考=0)。

## 2. 控制输入(画布左下角 11 个 const;1pu 有功=100MW,1pu 电流=1.36kA)
| 信号 | 含义 | 范围建议 | 默认 |
|---|---|---|---|
| P_REF | 外环有功参考(pu) | -1.0~1.0 | 0.0 |
| Q_REF | 外环无功参考(pu) | -1.0~1.0 | 0.0 |
| VD_REF | V 模式 d 轴电压参考 | 0.9~1.1 | 1.0 |
| V_REF | 附加无功电压参考 | 0.9~1.1 | 1.0 |
| MODE_Q | 1=V 模式, 2=Q 模式 | 1/2 | 2 |
| DP_DC/DP_REN/DP_LOAD | 直流侧/新能源/负荷附加有功 | -1.0~1.0 | 0.0 |
| ID_M/IQ_M | 手动电流参考(pu) | -1.1~1.1 | 0.5/0.2 |
| MAN_EN | 1=手动电流, 0=外环 P/Q | 0/1 | 0 |

## 3. 两种改控制的方式
- 方法 A(GUI,推荐):PSCAD 打开模型 → 双击左下角 const(如 P_REF)→ 改 Value(带 pu 单位概念)→ Build → Run → 看 Graph Frame。
- 方法 B(脚本):编辑 `demo28_ess_full.py` 顶部(`MANUAL=0/1`、`refs` 列表默认值)→ `python demo28_ess_full.py`(自动构建+运行+打印稳态)。

## 4. 观察面板(Graph Frame,10+3 面板)
顺序:ID_K(d 轴电流)/IDR_K(d 参考)/IQ_K/IQR_K/P_MW/Q_MVAR/V_KV(PCC)/IC_A/B/C(三相 RMS)/THETA(PLL 角)/IC_A_raw、IG_A_raw。

## 5. 标准实验
1. 外环有功跟踪:MAN_EN=0、P_REF=0 → P≈0、V≈60.1kV;P_REF=0.5 → P 向 50MW 收敛(KIP=0.01 慢积分,时间常数 ~100s,趋势对即可);负值=反向(放电)。
2. 手动电流:MAN_EN=1、ID_M=0.5/IQ_M=0.2 → id/iq 精确跟踪(实测 0.6802/0.2721 kA;P/Q≈50MW/22Mvar)。
3. 附加有功:DP_DC=0.2 → 附加通道 ~0.2pu 叠加到外环。
4. V/Q 切换:MODE_Q=2 用 Q_REF;=1 用 VD_REF。
5. 动态工况:EV 指令阶跃(step_gen:TIME>0.2s 60→50kV)→ PCC 34.70→33.26kV(-4.2%)、VSC 电流 0.02→1.15kA。

## 6. 关键实现事实与坑
- 受控电流源 = **master:src_ccin_1 的 CCBR**;单位 **kA**(Mag 输入);DSDYN 形如 `CCBR($BR,$SS)=$Mag`。**id>0=吸收(充电),注入=−(逆 Park)**,实测符号 id=+id_ref。
- 历史教训:电压源方案(source3 Ctrl=2 动态相位)全部发散(15+ 组实验),故弃用电压源、改用受控电流源绕开相位通道。
- 曾出问题与修复:
  - LCL 谐振(Lf+Cf 694Hz,Q≈346)被注入阶跃激励 → P/Q 测量加一阶低通 TPQ=0.02s;
  - bumpless V/Q 切换首步 DSDYN 时 vd 测量=0 → Q 积分器被预设 +0.15"钉住" → 修复为 |v|>0.1 才执行预设;
  - 组件定义曾放外部库导致单独打开报 `Component 'ess_ctl' does not have a definition` → **定义嵌入 case 内部**,引用格式 `ess_full:ess_ctl`。
- 启动瞬间 "Voltage chatter" 警告是 energize 正常瞬态;手动与外环模式经 MAN_EN 切换,外环下 ID_M/IQ_M 不生效。

## 7. 验证记录要点(2s 稳态,供复现对照)
- 手动模式:ID_K/IDR_K=0.6802/0.6802kA、IQ_K/IQR_K=0.2721/0.2721kA、P/Q=50.49MW/21.89Mvar、V=60.43kV、THETA=376rad/s。
- P/Q 外环零参考:ID=0.0002、IQ=0.0017kA、P=0.079MW、V=60.15kV。
- 模型交付:ess_full.pscx(单文件);源码 ess_ctl_components.py;一键脚本 demo28_ess_full.py。

## 维护说明
新增工况/实验时:把"输入改动→期望→实测→结论"补成 §5/§7 的新条目,并在 docs/source-notes/ESS_PSCAD控制操作说明.md 同步,必要时更新 demo28 脚本顶部默认值。
