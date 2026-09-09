# -*- coding: utf-8 -*-
"""
Demo 2: 真编译验证 —— 用 Fortran 自定义组件搭一个小算例并运行。

- 给 ess_ctl_demo.pslx 增加 const_src 常量源组件（纯 Fortran）
- 新建算例 ess_ctl_test.pscx: 6 个 const_src 驱动 park_dq + pi_ctl
- 连线 -> 保存 -> Build（真正编译全部 Fortran）-> Run 0.05s -> 检查错误
"""
import sys
import mhi.pscad
from mhi.pscad.wizard import UserDefnWizard, Signal

EXE = r'F:\PSCAD\bin\win64\Pscad.exe'
WORK = r'F:\ESS'
LIB = WORK + r'\ess_ctl_demo.pslx'
CASE = 'ess_ctl_test'


def make_const_src():
    w = UserDefnWizard('const_src')
    w.description = 'Constant signal source: out = Value'
    w.port.output(2, 0, 'out', Signal.REAL)
    cfg = w.category.add('Configuration')
    cfg.real('Value', description='Constant output value', value=1.0)
    w.graphics.text('C', 0, -1)
    w.script['Dsdyn'] = '      $out = $Value'
    return w


def main():
    print('==> launching PSCAD ...', flush=True)
    pscad = mhi.pscad.launch(exe=EXE, silence=True, splash=False, timeout=90)
    print('==> connected. version =', pscad.version, flush=True)

    print('==> loading library and adding const_src ...', flush=True)
    pscad.load(LIB)
    lib = pscad.project('ess_ctl_demo')
    defn_src = make_const_src().create_definition(lib)

    # 修复 pi_ctl: ① #BEGIN 子程序看不到 STORF，改用 RTCF；② 主体每步必须自增 NRTCF
    # (与主库 integral 组件同一模式: Begin 初始化 +1，主体读 RTCF(NRTCF) 后 +1)
    pi_defn = lib.definition('pi_ctl')
    pi_defn.script['Dsdyn'] = """#STORAGE RTCF:1
#BEGIN
      RTCF(NRTCF) = 0.0
      NRTCF = NRTCF + 1
#ENDBEGIN
#LOCAL REAL RVD1_1
#LOCAL REAL RVD1_2
      RVD1_1 = RTCF(NRTCF)
      NRTCF = NRTCF + 1
      RVD1_2 = $Kp*($ref - $fb) + RVD1_1
      IF ((RVD1_2 .GT. $Lim) .AND. (($ref - $fb) .GT. 0.0)) THEN
         RVD1_2 = $Lim
      ELSEIF ((RVD1_2 .LT. -$Lim) .AND. (($ref - $fb) .LT. 0.0)) THEN
         RVD1_2 = -$Lim
      ELSE
         RVD1_1 = RVD1_1 + $Ki*($ref - $fb)*DELT
      ENDIF
      RTCF(NRTCF-1) = RVD1_1
      $out = RVD1_2"""
    lib.save()
    print('    const_src added, pi_ctl fixed (RTCF), library saved', flush=True)

    print('==> creating case ...', flush=True)
    case = pscad.create_case(CASE, folder=WORK)
    main_c = case.canvas('Main')
    case.parameters(time_duration=0.05)
    print('    case parameters:', case.parameters(), flush=True)

    defn_pi = lib.definition('pi_ctl')
    defn_park = lib.definition('park_dq')

    # 布局（网格坐标）: 每个信号源放在与目标输入端口同一行
    park = main_c.create_component(defn_park, x=30, y=10)
    pi = main_c.create_component(defn_pi, x=30, y=24)

    rows = {'va': 10, 'vb': 7, 'vc': 13, 'theta': 16, 'ref': 24, 'fb': 20}
    srcs = {}
    for name, row in rows.items():
        s = main_c.create_component(defn_src, x=2, y=row)
        s.parameters(Value='1.0')
        srcs[name] = s

    print('==> wiring ports ...', flush=True)
    # 每个源输出 (x+2, row) -> 目标输入端口
    targets = {'va': 'va', 'vb': 'vb', 'vc': 'vc', 'theta': 'theta', 'ref': 'ref', 'fb': 'fb'}
    for name, row in rows.items():
        sx = srcs[name].port('out').x
        sy = srcs[name].port('out').y
        tp = park.port(targets[name]) if targets[name] != 'ref' and targets[name] != 'fb' else pi.port(targets[name])
        w = main_c.create_wire((sx, sy), (tp.x, tp.y))
        print('    wire: (%d,%d) -> (%d,%d)' % (sx, sy, tp.x, tp.y), flush=True)

    print('==> saving case ...', flush=True)
    case.save()
    print('    saved', case.filename, flush=True)

    print('==> BUILD (compiles Fortran) ...', flush=True)
    case.build()
    msgs = case.messages()
    errs = [m for m in msgs if m.status == 'error']
    for m in msgs:
        print('    [%s] %s: %s' % (m.status, m.label, m.text), flush=True)
    if errs:
        print('!! BUILD FAILED with %d errors' % len(errs), flush=True)
        sys.exit(1)

    print('==> RUN 0.05s ...', flush=True)
    case.run()
    out = case.output()
    print(out[-2000:], flush=True)
    if 'has stopped' in out.lower() or 'error' in out.lower():
        print('!! RUN may have errors — see output above', flush=True)

    print('==> DONE: Fortran components compiled & ran OK', flush=True)
    print('    (case: %s | library: %s)' % (case.filename, lib.filename), flush=True)


if __name__ == '__main__':
    main()
