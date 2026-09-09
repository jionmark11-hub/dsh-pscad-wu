# -*- coding: utf-8 -*-
"""
演示: 不依赖截图, 通过运行数据文件 (.out) 判断模型结果。
流程: 开启通道保存(PlotType=1) -> 运行 -> OutFile 读取 .out -> 数值判断
"""
import mhi.pscad
from mhi.pscad.utilities.file import OutFile

EXE = r'F:\PSCAD\bin\win64\Pscad.exe'


def dname(c):
    d = c.defn_name
    return d if isinstance(d, str) else (d[1] if d else str(d))


pscad = mhi.pscad.launch(exe=EXE, silence=True, splash=False, timeout=90)
pscad.load(r'F:\ESS\ess_ess_main.pscx')
prj = pscad.project('ess_ess_main')

# 1. 开启通道落盘
prj.parameters(PlotType='1')
print('PlotType set to 1 (save channels to disk)', flush=True)

prj.build()
errs = [m for m in prj.messages() if m.status == 'error']
print('errors:', len(errs), flush=True)
prj.run()
print('run finished', flush=True)

# 2. 用 OutFile 读取 .out 数据文件
out = OutFile(r'F:\ESS\ess_ess_main.gf46\ess_ess_main')
out.open()
cols = out.columns()
print('channels:', cols, flush=True)

# 读全部数据
rows = []
while True:
    try:
        r = out.read_values()
        if r is None:
            break
        rows.append(r)
    except Exception:
        break
out.close()
print('rows:', len(rows), flush=True)

# 3. 数值判断: 找 Vpcc_a_rms 通道, 统计稳态
if rows:
    idx = {name: i for i, name in enumerate(cols)}
    print('channel map:', idx, flush=True)
    # 稳态 = 后 60% 数据
    n = len(rows)
    half = int(n * 0.4)
    for ch in ('Vpcc_a_rms', 'Vpcc_b_rms', 'Vpcc_c_rms', 'Ivs_a_rms'):
        if ch in idx:
            vals = [float(r[idx[ch]]) for r in rows[half:]]
            mean = sum(vals) / len(vals)
            pkpk = max(vals) - min(vals)
            print('%-10s mean=%.4f  pk-pk=%.5f  (%.3f%%)' % (ch, mean, pkpk, 100 * pkpk / mean), flush=True)
print('==> DONE', flush=True)
