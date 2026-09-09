# LCC 黑盒接入 IEEE39 节点系统 — 验证记录

- 日期：2026-08-26
- 系统：IEEE 39 节点（新英格兰 39 母线，PSS/E 数据导入，230kV 主网 + 10 台发电机，60Hz）
- 接入：`ieee39_lcc.pscx`（= 原 `ieee_39_bus.pscx` + 内嵌 LCC39 模块定义 + Bus39 接入）
- 原文件未改动（备份：`F:\ESS\ieee_39_bus_orig.pscx`）

## 一、LCC 黑盒模块 LCC39

**封装方式**：PSCAD 模块定义（UserCmpDefn，`wizard.module=True`），电气接口用
`w.port.electrical('AC', dim=3)` —— 模块内部自动生成 **master:xnode 'AC'**，
与 CIGRE Rectifier、IEEE39 支路模块同构。

**端口**：
- `AC`（电气 3 相输入，230kV）
- `IORD`（REAL 输入，直流电流指令 kA）
- `VDCO` / `IDCO` / `ALPHAO`（REAL 输出观测：kV / kA / 度）

**内部**（验证过的 ess_lcc 拓扑，230kV 版）：
```
xnode AC -> nodeloop(同步, X1->CB) -> 换相变 230/25kV YY+YD (Xl=0.18pu)
  -> 2x g6p200_2 (View=1, FP=0, TfPh=0/-30, KB=1 物理直连)
  -> 直流: DP1->Ld(0.2H)->IDCO电流表->Rl(60Ω)->DN2 ; DN1<->DP2 串联 ; 中点1MΩ接地
  -> 控制: IDCO->realpole(G=1)->sumjct(IDF-IORD)->pi_ctlr->α(rad)->AO
```

## 二、Bus39 接入

- Bus39 = 230kV 母线 @grid(21,55)..(27,55)，经 T1_39（母线1）与 T9_39（母线9）连接
- LCC 并联挂接：3 相 T 接走廊 `(24,55)->(24,44)->(10,44)->(10,60)`（逐段验证无交叉）
- LCC 实例放 Main 左侧空白区 (10,60)

## 三、验证结果（1.0 s 仿真，time_step=5µs，状态码 0）

| 通道 | 稳态均值（t>0.8s） | 说明 |
|------|-------------------|------|
| VDCO | 30.05 kV | 半桥对地；总 Vd ≈ 60.1 kV |
| IDCO | **1.002 kA** | 定电流控制跟踪 IORD=1.0 kA ✓ |
| ALPHAO | 22.7° | α 稳态（接入后母线电压略降 → α 比独立测试 17.7° 略大，物理合理）|
| LCC 子系统开关 | 1682 次 | 12 脉动正常换相 ✓ |
| 发电机子系统 | 301 次/1s | 与基线（661 次/2s）一致 ✓ |

## 四、调试要点记录（供后续参考）

1. **load 进来的 case 不能调 `case.save()`** —— 会弹 "Save Project As" 对话框导致
   API 卡死（PSCAD CPU 持续增长但无文件输出）。**必须用 `case.save_as(新名)`**，
   之后 `pscad.project(新名)` 重新获取句柄。
2. **IEEE39 Main 母线区极密**：Bus39 下方 x=22/26/27/30/31/34/38/41 全是支路引线
   通道，y=55/61/66/78/81/87 全是母线 —— 任何 wire 交叉都会报
   "dimension mismatch / type contention / splice"。**用扫描脚本找空白区 +
   逐段验证走廊**（本方案走廊 4 段均验证过）。
3. **模块内部 INTEGER 信号（consti->KB）必须物理 wire 直连**，经 datalabel(REAL)
   同名合并会在模块内部报 type contention。
4. **输出端口 wire 与端口同名 datalabel 会双重源**（contention）；外部观测用
   端口名+'_P' 的 datalabel。
5. 构建 IEEE39+LCC 需 ~5-10 分钟（27 子系统），运行 1s @5µs 约 1-2 分钟 ——
   用后台任务 + 日志文件观察。

## 五、文件

- `F:\ESS\ieee39_lcc.pscx` —— 最终交付（含 LCC39 定义 + Bus39 接入 + 显示）
- `F:\ESS\demo31_ieee39_lcc.py` —— 构建脚本（`python demo31_ieee39_lcc.py 3`）
- `F:\ESS\ieee_39_bus_orig.pscx` —— 原系统备份
- `F:\ESS\ieee39_lcc_log8.txt` —— 最终运行日志
- `F:\ESS\LCC学习笔记.md` —— 学习笔记（含接入条件第八节）
