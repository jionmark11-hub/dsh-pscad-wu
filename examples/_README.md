# examples/ 参考脚本说明

> 全部来自训练机(F:\ESS)实际跑通/验证过的脚本,**原样归档**,是各技能文档的直接出处。
> ⚠️ 文件内 `EXE = r'F:\PSCAD\bin\win64\Pscad.exe'`、`WORK = r'F:\ESS'` 等路径是训练机
> 样例——复制使用前先改成目标机实际路径(建议统一在脚本顶部改这两个常量)。
> ⚠️ 个别脚本是训练过程的"中间隔离/调试文件",**不一定能独立 Build 成功**;引用前先看
> docstring 是否标注 Isolate/调试,拿不准就选标注了完整演示的脚本。
> 运行方式均为 `python <file>.py [可选参数]`(需要能 `import mhi.pscad` 的 python)。

| 文件 | 演示内容 | 对应技能 |
|---|---|---|
| demo2_compile_test.py | UserDefnWizard 自定义 Fortran 元件(含 RTCF 修复样板)+ 库/算例 + Build/Run 全流程 | pscad-automation |
| demo21_pwm_halfbridge.py | 从零建 PWM 半桥:master 元件、自定义 sin_gen/inv/int_conv、datalabel、pGB 曲线、compar SPWM。**独立可跑,想拿"最小可跑模板"就从它裁剪**(已作验收实测) | pscad-automation / model-library |
| demo14_capture.py | PSCAD 窗口 PrintWindow 截屏(找窗口→按面积取最大→存 .bmp) | pscad-automation |
| demo20_outfile.py | 工程 PlotType 参数与 OutFile 读取思路 | pscad-verification |
| demo28m_runonly.py | 最小"加载→Build→Run→打印完整输出"骨架 | pscad-automation |
| demo28_ess_full.py | ESS 单文件模型一键构建+运行+稳态打印(MANUAL/refs 顶部可改) | ess-storage-project |
| demo29_lcc.py | 12 脉动 LCC 整流器构建(带参数 IORD,`python demo29_lcc.py 0.5`) | lcc-hvdc-project |
| demo31_ieee39_lcc.py | IEEE39+LCC39 黑盒构建(`python demo31_ieee39_lcc.py 3`,构建 5-10 分钟,建议后台) | lcc-hvdc-project |
| demo11_fix_axis.py | 改 pGB 曲线轴(ymin/ymax/title) | pscad-verification |
| dump_topology.py | 只读解析 .pscx XML 结构(不动 GUI) | pscad-verification |
| check_ripple.py | 纹波/FFT 特征校验(12 脉动 360/720Hz 判据) | pscad-verification / lcc-hvdc-project |

## 约定
- 新建参考脚本也放本目录,文件名沿用 demoNN_主题.py 或 check_/probe_ 前缀习惯;
- 在文件 docstring 第一行写"演示什么 / 需要改哪些路径 / 运行参数";
- 大系统(构建>1 分钟)脚本默认支持后台运行 + 日志落盘。
