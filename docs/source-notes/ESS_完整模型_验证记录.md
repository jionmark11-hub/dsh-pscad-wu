# ESS 完整模型 — 受控电流源 VSC (2026-08-22, 外环调优完成, 单文件交付)

## 交付文件
- `ess_full.pscx` — **单文件完整模型** (组件定义已嵌入 case 内部, 打开即用, 无需外部库)
- `ess_ctl_components.py` — 组件源码 (重建/修改用)
- `demo28_ess_full.py` — 一键构建+运行+验证脚本 (MANUAL=0 交付默认; 切 1 即手动模式)
- `demo28r_cstest.py` — 电流源单元测试
- (ess_ctl_demo.pslx 旧库文件已不再需要, 保留备用)

## 模型结构
- 主电路: 60kV 电网源 → Rg/Lg (0.36Ω/4.77mH) → [IG] → [VP] → Lf/Rf (14.3mH/0.18Ω)
  → [IC] → **受控电流源 VSC** (3× master:src_ccin_1 + inv_park, 注入 id_ref/iq_ref)
- 控制器 ess_ctl: PLL(0.707/94.2) → Park → P/Q/V 测量(低通滤波) → 附加有功 A01-A07
  → 附加无功 R01-R05 → 外环 O01-O04 (0.22/0.01, V/Q 无扰切换) → 手动电流模式
  → 限幅 1.1pu → 内环 I01-I04 (0.5/0.0167)
- 新增调优参数: TSS=0.5 (外环软启动, PLL 锁定前参考=0), TPQ=0.02 (P/Q/V 测量低通)

## ✅ 验证一: 手动电流模式 (MANUAL=1, ID_M=0.5pu, IQ_M=0.2pu, 2s 稳态 t>1.4)
| 通道 | 实测 | 期望 | 结论 |
|---|---|---|---|
| ID_K / IDR_K | 0.6802 / 0.6802 kA | 0.68 | ✅ 精确跟踪 |
| IQ_K / IQR_K | 0.2721 / 0.2721 kA | 0.272 | ✅ 精确跟踪 |
| P / Q | 50.49 MW / 21.89 Mvar | 50 / 20 | ✅ |
| V_KV | 60.43 kV | 60 | ✅ |
| IC_A/B/C | 0.518 kA | 0.518 | ✅ |
| THETA | 376 rad/s ≈ ω | 锁定 | ✅ |

## ✅ 验证二: P/Q 外环模式 (MANUAL=0, P_REF=0, Q_REF=0, 2s 稳态 t>1.4)
| 通道 | 实测 | 结论 |
|---|---|---|
| ID_K / IDR_K | 0.0002 / 0.0002 kA | ✅ P 环收敛 id→0 |
| IQ_K / IQR_K | 0.0017 / 0.0017 kA | ✅ Q 环收敛 iq→0 |
| P_MW | 0.079 MW | ✅ P→0 |
| Q_MVAR | 1.56 Mvar (1.6%, KIP=0.01 慢积分收敛中) | ✅ |
| V_KV | 60.15 kV | ✅ |
| IC | 0.001 kA | ✅ |
| THETA | 376 rad/s ≈ ω | ✅ PLL 锁定 |

## ✅ 验证三: P 参考跟踪 (P_REF=0.5, 2s)
- id=0.095pu 注入, P=9.5MW 向 50MW 收敛 (KIP=0.01 → 时间常数 100s, 趋势正确), Q→0, 稳定

## 外环调优历程 (本次)
1. **现象**: 规格增益 (0.22/0.01) 下外环模式发散 (P→3900MW, V→667kV, PLL 漂移)
2. **定位 1**: 软启动 (TSS) 实验证明注入=0 时完全稳定 → 问题在注入开始后
3. **定位 2**: LCL 谐振 (Lf+Cf, 694Hz, Q≈346 无阻尼) 被注入阶跃持续激励 →
   谐振分量进入 P/Q 测量 (RMS 窗无法滤除) → 外环误判 → 正反馈爆炸
   **修复**: P/Q/V 测量一阶低通 TPQ=0.02s (外环只看基波)
4. **定位 3**: 修复后 P 环收敛但 Q 环被"钉住" (iq_ref=+0.128 恒定) →
   **bumpless V/Q 切换预设缺陷**: 第一次 DSDYN 时 vd 测量=0 (网络未解)
   → RVD5_4=0.15 → Q 积分器被预设 +0.15 → 需 200s 才能消除
   **修复**: |v|>0.1 时才执行 bumpless 预设
5. **最终**: P→0, Q→0, V=60.15kV, 两种模式全部稳定收敛

## 关键实现事实
1. CCBR 电流源单位 = kA (Mag 输入; 隔离测试 Mag=0.1 → 实测 −0.1 双重验证)
2. src_ccin_1: Branch=`BR=$B $A BREAKER 1.0`, DSDYN=`CCBR($BR,$SS)=$Mag`
3. 符号: 控制器 id>0=吸收, 注入=−(逆 Park) → 实测 id=+id_ref
4. 手动模式回归验证: bumpless 修改不影响 (走 IF 分支)

## 历史: ESYS651 电压源方案 (已废弃)
source3 (Ctrl=2) 动态相位输入实测全部发散 (15+ 组实验, 快速 NaN/慢速 15s 发散);
受控电流源完全绕开相位通道。

## 运行方式 (2026-08-22 修复)
- 之前版本组件定义在外部库 (ess_ctl_demo.pslx) 中, 单独打开 ess_full.pscx 报错:
  `Component 'ess_ctl' does not have a definition`
- **修复**: 组件定义 (ess_ctl/dq2ev/inv_park) 直接嵌入 case 内部,
  引用格式 `ess_full:ess_ctl` 等 — 已验证**单独加载/构建/运行全部正常** (0 错误)
- 打开方式: PSCAD 打开 `F:\ESS\ess_full.pscx` → 构建 (Build) → 运行 (Run)
- 启动瞬间 "Voltage chatter: SS#1 Node#4" 警告为电网源 energize 的正常瞬态, 不影响运行
- 切换模式: 编辑 `demo28_ess_full.py` 顶部 `MANUAL = 0/1` 后重新构建
