# -*- coding: utf-8 -*-
"""
Demo 21: 模块1 - 详细开关模型: 单相半桥 PWM 逆变器
- battery(DC 100kV) + Cdc + 2× peswitch(IGBT) + RL 负载
- SPWM: sig_gen(1980Hz 锯齿载波) vs sin_gen(60Hz 调制波, m=0.8) -> compar -> 上桥
        互补 (inv) -> 下桥
- 触发线用命名信号 (datalabel) 跨区连接, 避免与控制线交叉
验证: 输出基波 = m*Vdc/2 = 40kV 峰值; FFT 谐波簇在 1980Hz
"""
import sys
import math
import mhi.pscad
from mhi.pscad.wizard import UserDefnWizard, Signal

EXE = r'F:\PSCAD\bin\win64\Pscad.exe'
WORK = r'F:\ESS'
LIB = 'ess_pwm_demo'
CASE = 'ess_pwm_half'


def dname(c):
    d = c.defn_name
    return d if isinstance(d, str) else (d[1] if d else str(d))


def port_xy(c, name):
    p = c.port(name)
    if p is None:
        for n, pp in c.ports().items():
            if n.startswith(name):
                return (pp.x, pp.y)
        raise RuntimeError('port %s not found on %s' % (name, dname(c)))
    return (p.x, p.y)


def wire(main, a, b, label=''):
    main.create_wire(a, b)
    print('    wire %-10s (%d,%d)->(%d,%d)' % (label, a[0], a[1], b[0], b[1]), flush=True)


def make_sin_gen():
    w = UserDefnWizard('sin_gen')
    w.description = 'Sinusoidal source: out = Amp*sin(2*pi*f*TIME + Ph)'
    w.port.output(2, 0, 'out', Signal.REAL)
    cfg = w.category.add('Configuration')
    cfg.real('Amp', description='Amplitude', value=0.8)
    cfg.real('F', description='Frequency (Hz)', value=60.0)
    cfg.real('Ph', description='Phase (rad)', value=0.0)
    w.graphics.text('sin', 0, -1)
    w.script['Dsdyn'] = '      $out = $Amp*SIN(TWO_PI*$F*TIME + $Ph)'
    return w


def make_inv():
    w = UserDefnWizard('inv')
    w.description = 'Logic inverter: out = 1 - in'
    w.port.input(-2, 0, 'in', Signal.REAL)
    w.port.output(2, 0, 'out', Signal.REAL)
    w.graphics.text('NOT', 0, -1)
    w.script['Dsdyn'] = '      $out = 1.0 - $in'
    return w


def make_int_conv():
    w = UserDefnWizard('int_conv')
    w.description = 'Real to Integer: out = NINT(in)'
    w.port.input(-2, 0, 'in', Signal.REAL)
    w.port.output(2, 0, 'out', Signal.INTEGER)
    w.graphics.text('INT', 0, -1)
    w.script['Dsdyn'] = '      $out = NINT($in)'
    return w


def main():
    print('==> launching PSCAD ...', flush=True)
    pscad = mhi.pscad.launch(exe=EXE, silence=True, splash=False, timeout=90)

    # 库: sin_gen + inv + int_conv
    lib = pscad.create_library(LIB, folder=WORK)
    make_sin_gen().create_definition(lib)
    make_inv().create_definition(lib)
    make_int_conv().create_definition(lib)
    lib.save()
    print('library ready: sin_gen, inv, int_conv', flush=True)

    case = pscad.create_case(CASE, folder=WORK)
    case.parameters(time_duration=0.06, time_step=5, sample_step=20)
    main = case.canvas('Main')

    # ================= 主电路 =================
    # DC 源: battery 100kV
    bat = main.create_component('master:battery', x=6, y=20)
    bat.parameters(Type='0', Enom='100.0 [kV]', Qrated='10.0 [kA*hr]',
                   SOCint='100.0', loss='0.1', Inom='20', SOC='SOC_bat')
    pa_b = bat.port('A'); pb_b = bat.port('B')
    print('    battery A(%d,%d) B(%d,%d)' % (pa_b.x, pa_b.y, pb_b.x, pb_b.y), flush=True)
    # battery.B 是 Ground 型端口, 无需外部 ground

    # Cdc: DC+ 到 DC- (battery.B), 移到空旷区 (20,10), 引线绕开所有线段
    cdc = main.create_component('master:capacitor', x=20, y=10, orient=1)
    cdc.parameters(C='1000.0 [uF]')
    cp1 = cdc.port('A'); cp2 = cdc.port('B')
    print('    Cdc: A(%d,%d) B(%d,%d)' % (cp1.x, cp1.y, cp2.x, cp2.y), flush=True)
    # DC+ 母线 (6,19)->(14,19)
    wire(main, (6, pa_b.y), (14, pa_b.y), 'DC+ bus')
    # Cdc.B(20,12) -> (20,20) -> (14,20) -> (14,19) [DC+]
    wire(main, (cp2.x, cp2.y), (cp2.x, 20), 'Cdc up v')
    wire(main, (cp2.x, 20), (14, 20), 'Cdc up h')
    wire(main, (14, 20), (14, pa_b.y), 'Cdc up v2')
    # Cdc.A(20,10) -> (4,10) -> (4,31) -> (14,31) [DC-]
    wire(main, (cp1.x, cp1.y), (4, cp1.y), 'Cdc dn h')
    wire(main, (4, cp1.y), (4, 31), 'Cdc dn v')
    wire(main, (4, 31), (14, 31), 'Cdc dn h2')
    # DC- 母线: battery.B(6,21) -> (6,31) -> (14,31); 显式接地
    wire(main, (pb_b.x, pb_b.y), (6, 31), 'DC- bus v')
    wire(main, (6, 31), (14, 31), 'DC- bus h')
    main.create_component('master:ground', x=14, y=31)

    # 上桥 IGBT: DN=DC+ 母线, DP=相节点, INTR=0 (APUL Integer 触发)
    ig_up = main.create_component('master:peswitch', x=14, y=21)
    ig_up.parameters(Name='T1', Type='3', SNUB='0', INTR='0', RON='0.01 [ohm]',
                     ROFF='1.0E6 [ohm]', EFVD='0.001 [kV]', EBO='1.0E5 [kV]',
                     Erw='1.0E5 [kV]', TEXT='0.0 [us]',
                     I='I_T1', It='It_T1', V='V_T1', Ton='Ton_T1', Toff='Toff_T1',
                     Alpha='Al_T1', Gamma='Gm_T1')
    up_dp = port_xy(ig_up, 'DP'); up_dn = port_xy(ig_up, 'DN'); up_ap = port_xy(ig_up, 'APUL')
    print('    up IGBT: DP%s DN%s APUL%s' % (up_dp, up_dn, up_ap), flush=True)

    # 下桥 IGBT (旋转 180): DP=相节点, DN=地
    ig_dn = main.create_component('master:peswitch', x=14, y=25, orient=2)
    ig_dn.parameters(Name='T2', Type='3', SNUB='0', INTR='0', RON='0.01 [ohm]',
                     ROFF='1.0E6 [ohm]', EFVD='0.001 [kV]', EBO='1.0E5 [kV]',
                     Erw='1.0E5 [kV]', TEXT='0.0 [us]',
                     I='I_T2', It='It_T2', V='V_T2', Ton='Ton_T2', Toff='Toff_T2',
                     Alpha='Al_T2', Gamma='Gm_T2')
    dn_dp = port_xy(ig_dn, 'DP'); dn_dn = port_xy(ig_dn, 'DN'); dn_ap = port_xy(ig_dn, 'APUL')
    print('    dn IGBT: DP%s DN%s APUL%s' % (dn_dp, dn_dn, dn_ap), flush=True)

    # 相节点母线: 上 DP -> 下 DP
    wire(main, up_dp, dn_dp, 'phase node')
    # 下 IGBT DN(14,27) -> DC- 母线 (14,31)
    wire(main, dn_dn, (14, 31), 'dn to DC-')

    # 负载: 相节点 -> ammeter -> R -> L -> DC-
    amp = main.create_component('master:ammeter', x=20, y=21)
    amp.parameters(Name='Iload')
    rl = main.create_component('master:resistor', x=26, y=21); rl.parameters(R='10.0 [ohm]')
    ll = main.create_component('master:inductor', x=32, y=21); ll.parameters(L='10.0 [mH]')
    wire(main, up_dp, port_xy(amp, 'N1'), 'to load')
    wire(main, port_xy(amp, 'N2'), port_xy(rl, 'A'), 'amm-R')
    wire(main, port_xy(rl, 'B'), port_xy(ll, 'A'), 'R-L')
    wire(main, port_xy(ll, 'B'), (34, 31), 'L to DC-')

    # ================= PWM 控制 =================
    # 载波: const(1980) 接触 sig_gen.F; sig_gen.O -> datalabel(CARR) [REAL 命名信号]
    c_f = main.create_component('master:const', x=24, y=7); c_f.parameters(Value='1980.0')
    sg = main.create_component('master:sig_gen', x=28, y=7)
    sg.parameters(Max='1.0', Min='-1.0')
    dl_carr = main.create_component('master:datalabel', x=32, y=7)
    dl_carr.parameters(Name='CARR')
    wire(main, port_xy(sg, 'O'), port_xy(dl_carr, 'A'), 'carrier')
    # 调制波: sin_gen -> datalabel(MOD)
    sgen = main.create_component('ess_pwm_demo:sin_gen', x=34, y=7)
    sgen.parameters(Amp='0.8', F='60.0', Ph='0.0')
    dl_mod = main.create_component('master:datalabel', x=38, y=7)
    dl_mod.parameters(Name='MOD')
    wire(main, port_xy(sgen, 'out'), port_xy(dl_mod, 'A'), 'mod')

    # compar1 (Pulse=0 Level, REAL 0/1): A=载波 B=调制波 -> int_conv1 -> 上桥
    cmp1 = main.create_component('master:compar', x=42, y=7)
    cmp1.parameters(Pulse='0', INTR='0', OPos='1.0', ONone='0.0', ONeg='0.0')
    dl_carr1 = main.create_component('master:datalabel', x=40, y=7)
    dl_carr1.parameters(Name='CARR')
    dl_mod1 = main.create_component('master:datalabel', x=40, y=9)
    dl_mod1.parameters(Name='MOD')
    wire(main, port_xy(dl_carr1, 'A'), port_xy(cmp1, 'A'), 'carr1')
    wire(main, port_xy(dl_mod1, 'A'), port_xy(cmp1, 'B'), 'mod1')
    ic1 = main.create_component('ess_pwm_demo:int_conv', x=50, y=7)
    wire(main, port_xy(cmp1, 'OUT'), port_xy(ic1, 'in'), 'up conv')

    # compar2 (互补: A=调制波 B=载波) -> int_conv2 -> 下桥
    cmp2 = main.create_component('master:compar', x=42, y=12)
    cmp2.parameters(Pulse='0', INTR='0', OPos='1.0', ONone='0.0', ONeg='0.0')
    dl_carr2 = main.create_component('master:datalabel', x=40, y=12)
    dl_carr2.parameters(Name='CARR')
    dl_mod2 = main.create_component('master:datalabel', x=40, y=14)
    dl_mod2.parameters(Name='MOD')
    wire(main, port_xy(dl_carr2, 'A'), port_xy(cmp2, 'A'), 'carr2')
    wire(main, port_xy(dl_mod2, 'A'), port_xy(cmp2, 'B'), 'mod2')
    ic2 = main.create_component('ess_pwm_demo:int_conv', x=50, y=12)
    wire(main, port_xy(cmp2, 'OUT'), port_xy(ic2, 'in'), 'dn conv')

    # 触发线 (INTEGER, 直接布线绕行):
    # 上桥: ic1.out(52,7) -> (52,3) -> (16,3) -> 上 IGBT APUL(16,19)
    wire(main, (52, 7), (52, 3), 'up v1')
    wire(main, (52, 3), (16, 3), 'up h')
    wire(main, (16, 3), up_ap, 'up v2')
    # 下桥: ic2.out(52,12) -> (54,12) -> (54,1) -> (12,1) -> 下 IGBT APUL
    wire(main, (52, 12), (54, 12), 'dn h1')
    wire(main, (54, 12), (54, 1), 'dn v1')
    wire(main, (54, 1), (12, 1), 'dn h2')
    wire(main, (12, 1), dn_ap, 'dn v2')

    # ================= 测量 =================
    vg = main.create_component('master:voltmetergnd', x=14, y=23)
    vg.parameters(Name='Vout')
    pgbs = {}
    for nm, yy, u, mn, mx in (('Vout', 33, 'kV', -120, 120), ('Iload', 36, 'kA', -10, 10),
                              ('MOD', 42, 'pu', -1.5, 1.5)):
        dl = main.create_component('master:datalabel', x=40, y=yy)
        dl.parameters(Name=nm)
        pgb = main.create_component('master:pgb', x=43, y=yy)
        pgb.parameters(Name=nm, Group='PWM', Display='1', Scale='1.0', Units=u, Min=mn, Max=mx)
        wire(main, port_xy(dl, 'A'), port_xy(pgb, 'Signl'), 'sig ' + nm)
        pgbs[nm] = pgb
    gf, og, curve_v = main.create_graph(pgbs['Vout'], x=46, y=33)
    og2, curves_i = gf.add_overlay_graph(pgbs['Iload'])
    og4, curves_mod = gf.add_overlay_graph(pgbs['MOD'])

    print('==> saving & building ...', flush=True)
    case.save()
    case.build()
    errs = [m for m in case.messages() if m.status == 'error']
    for m in case.messages():
        if m.status != 'normal':
            print('    [%s] %s' % (m.status, m.text), flush=True)
    if errs:
        print('!! BUILD FAILED (%d errors)' % len(errs), flush=True)
        sys.exit(1)

    print('==> running 0.06 s (5us step) ...', flush=True)
    case.run()
    print(case.output()[-400:], flush=True)

    print('==> validation (FFT) ...', flush=True)
    cv = curve_v
    if cv.samples > 0:
        # 半桥输出直流分量 = Vdc/2 (从 Vout 波形均值反推 Vdc)
        dom = list(cv.domain())
        tr = list(cv.trace(0))
        n = len(tr)
        half = n // 2
        t, x = dom[half:], tr[half:]
        vdc_est = 2.0 * (sum(x) / len(x))
        print('    Vdc estimate (2*mean Vout) = %.2f kV' % vdc_est, flush=True)
        # MOD 幅值
        t_m = list(curves_mod[0].domain())
        v_m = list(curves_mod[0].trace(0))
        half_m = v_m[len(v_m) // 2:]
        mod_pk = max(abs(v) for v in half_m)
        print('    MOD peak = %.3f (expect 0.8)' % mod_pk, flush=True)
        def amp_at(f):
            c = sum(v * math.cos(2 * math.pi * f * tt) for v, tt in zip(x, t))
            s = sum(v * math.sin(2 * math.pi * f * tt) for v, tt in zip(x, t))
            return 2 * math.hypot(c, s) / len(x)
        f1 = amp_at(60)
        fc1 = amp_at(1980 - 60)
        fc2 = amp_at(1980 + 60)
        expect = 0.5 * vdc_est * mod_pk
        print('    Vout fundamental (60Hz) = %.2f kV (expect m*Vdc/2 = %.2f)' % (f1, expect), flush=True)
        print('    carrier sidebands: %.3f / %.3f kV' % (fc1, fc2), flush=True)
        ok = 0.85 * expect < f1 < 1.15 * expect and 0.7 < mod_pk < 0.9
        print('    VALIDATION %s' % ('PASS' if ok else 'FAIL'), flush=True)
    print('==> DONE', flush=True)


if __name__ == '__main__':
    main()
