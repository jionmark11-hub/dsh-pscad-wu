# -*- coding: utf-8 -*-
"""
Demo 28: 完整储能模型 (规格书全部控制 + 手动电流控制 + RMS 有效值显示)
- 主电路: 源 + Lg/Rg + 网侧电流表 + LCL + 变流器电流表 + 平均值 VSC
- 控制器: ess_ctl (26 块 Fortran 封装, 含手动电流模式 MAN_EN/ID_M/IQ_M)
- 受控电流源 VSC: inv_park (idr/iqr/theta -> 三相电流指令) + master:src_ccin_1 x3
- RMS 显示: 有功/无功电流及其参考、P/Q、电压、三相电流 -> rms-inst -> pgb -> graph
验证1: 手动模式 ID_M=0.5pu IQ_M=0.2pu -> id=0.68kA iq=0.27kA
验证2: P/Q 外环 P_REF=0.5 -> P=50MW
"""
import sys
import math
import mhi.pscad

EXE = r'F:\PSCAD\bin\win64\Pscad.exe'
WORK = r'F:\ESS'
LIB = 'ess_ctl_demo'
CASE = 'ess_full'
from ess_ctl_components import make_ess_ctl, make_dq2ev, make_inv_park


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
    if a == b:
        return
    main.create_wire(a, b)
    print('    wire %-10s (%d,%d)->(%d,%d)' % (label, a[0], a[1], b[0], b[1]), flush=True)


def ground_other(main, cap, wire_end):
    p1 = cap.port('A'); p2 = cap.port('B')
    dn = p2 if (p1.x, p1.y) == wire_end else p1
    main.create_component('master:ground', x=dn.x, y=dn.y)
    return dn


def make_sig(main, name, x, y):
    dl = main.create_component('master:datalabel', x=x, y=y)
    dl.parameters(Name=name)
    return dl


def main():
    print('==> launching PSCAD ...', flush=True)
    pscad = mhi.pscad.launch(exe=EXE, silence=True, splash=False, timeout=90)

    # 组件定义直接嵌入 case 内 (单文件可运行, 无需外部库)
    case = pscad.create_case(CASE, folder=WORK)
    make_ess_ctl().create_definition(case)
    make_dq2ev().create_definition(case)
    make_inv_park().create_definition(case)
    print('definitions embedded in case: ess_ctl, dq2ev, inv_park', flush=True)
    case.parameters(time_duration=2.0)
    main = case.canvas('Main')

    # ================= 主电路 (ess_ess_main 验证布局) =================
    src = main.create_component('master:source3', x=5, y=25)
    src.parameters(Name='Grid', Type='1', Ctrl='0', Imp='0', R1s='0.001 [ohm]',
                   MVA='100.0 [MVA]', Vm='60.0 [kV]', F='60.0 [Hz]', Tc='0.02 [s]',
                   Es='60.0 [kV]', F0='60.0 [Hz]', Ph='0.0 [deg]', ZSeq='0', View='0')
    pa = src.port('A'); pb = src.port('B'); pc = src.port('C'); pn = src.port('N')
    main.create_component('master:ground', x=pn.x, y=pn.y)

    # ================= 受控电流源 VSC (master:src_ccin_1, 3 相, x=30 远离控制区) =================
    cs_y = {'A': 22, 'B': 25, 'C': 28}
    css = {}
    for ph, yy in cs_y.items():
        cs = main.create_component('master:src_ccin_1', x=30, y=yy)
        cs.parameters(Name='CS_' + ph, Cntrl='1')
        pa_ = cs.port('A'); pb_ = cs.port('B'); pm_ = cs.port('Mag')
        main.create_component('master:ground', x=pb_.x, y=pb_.y)
        css[ph] = (pa_.x, pa_.y, pm_.x, pm_.y)
        print('    CS_%s A(%d,%d) B(%d,%d) Mag(%d,%d)' %
              (ph, pa_.x, pa_.y, pb_.x, pb_.y, pm_.x, pm_.y), flush=True)

    # 每相支路: 源 -> Rg -> Lg -> [IG ammeter] -> [VP voltmeter] -> Lf -> Rf -> [IC ammeter] -> CS.A
    for name, ps in (('A', pa), ('B', pb), ('C', pc)):
        yy = ps.y
        rg = main.create_component('master:resistor', x=10, y=yy); rg.parameters(R='0.36 [ohm]')
        lg = main.create_component('master:inductor', x=15, y=yy); lg.parameters(L='4.77 [mH]')
        lf = main.create_component('master:inductor', x=20, y=yy); lf.parameters(L='14.3 [mH]')
        rf = main.create_component('master:resistor', x=25, y=yy); rf.parameters(R='0.18 [ohm]')
        amp_ig = main.create_component('master:ammeter', x=18, y=yy)
        amp_ig.parameters(Name='IG_' + name)
        amp_ic = main.create_component('master:ammeter', x=29, y=yy)
        amp_ic.parameters(Name='IC_' + name)
        vg = main.create_component('master:voltmetergnd', x=17, y=yy)
        vg.parameters(Name='VP_' + name)
        wire(main, (ps.x, ps.y), port_xy(rg, 'A'), 'src-Rg')
        wire(main, port_xy(rg, 'B'), port_xy(lg, 'A'), 'Rg-Lg')
        wire(main, port_xy(lg, 'B'), port_xy(amp_ig, 'N1'), 'Lg-IG')
        wire(main, port_xy(amp_ig, 'N2'), port_xy(lf, 'A'), 'IG-Lf')
        wire(main, port_xy(lf, 'B'), port_xy(rf, 'A'), 'Lf-Rf')
        if name == 'B':
            # Cf B 抽头 (28,25): Rf-B -> (28,25) -> IC-B.N1
            wire(main, port_xy(rf, 'B'), (28, 25), 'Rf-CfB')
            wire(main, (28, 25), port_xy(amp_ic, 'N1'), 'CfB-IC')
        else:
            wire(main, port_xy(rf, 'B'), port_xy(amp_ic, 'N1'), 'Rf-IC')
        n2 = port_xy(amp_ic, 'N2')
        ax, ay, _, _ = css[name]
        if name == 'A':
            wire(main, n2, (n2[0], ay), 'IC-CS A v')
            wire(main, (n2[0], ay), (ax, ay), 'IC-CS A h')
        elif name == 'B':
            wire(main, n2, (ax, ay), 'IC-CS B')
        else:
            wire(main, n2, (n2[0], ay), 'IC-CS C v')
            wire(main, (n2[0], ay), (ax, ay), 'IC-CS C h')

    # Cf (A/C 在 PCC 侧, B 在 Rf 侧抽头 (28,25))
    wire(main, (17, 23), (17, 21), 'A Cf')
    cfa = main.create_component('master:capacitor', x=17, y=19, orient=1); cfa.parameters(C='3.68 [uF]')
    ground_other(main, cfa, (17, 21))
    wire(main, (28, 25), (28, 21), 'B Cf')
    cfb = main.create_component('master:capacitor', x=28, y=19, orient=1); cfb.parameters(C='3.68 [uF]')
    ground_other(main, cfb, (28, 21))
    wire(main, (17, 27), (17, 29), 'C Cf')
    cfc = main.create_component('master:capacitor', x=17, y=29, orient=1); cfc.parameters(C='3.68 [uF]')
    ground_other(main, cfc, (17, 29))

    # ================= 控制器 ess_ctl @(42,40) =================
    ctl = main.create_component('ess_full:ess_ctl', x=42, y=40)
    ctl.parameters(SBASE='100.0', VBASE='60.0', IBASE='0.962', FBASE='60.0', LF='0.15',
                   KPM='0.707', KIM='94.2', KPP='0.22', KIP='0.01',
                   TEST='0.05', KP='1.0', KE='0.5', EMAX='10.0',
                   KV='1.0', KD='2.0', TF='0.02',
                   KPC='0.5', KIC='0.0167', ILIM='1.1', VLIM='2.0',
                   TTH='0.05', TSS='0.5', TPQ='0.02')
    print('    ess_ctl placed at (42,40)', flush=True)

    # 测量 -> 命名信号 -> 控制器输入
    meas_ports = {'va': 'VP_A', 'vb': 'VP_B', 'vc': 'VP_C',
                  'ia': 'IC_A', 'ib': 'IC_B', 'ic': 'IC_C',
                  'iga': 'IG_A', 'igb': 'IG_B', 'igc': 'IG_C'}
    ctl_in_y = {}
    for port_name, sig in meas_ports.items():
        pxy = port_xy(ctl, port_name)
        dl = make_sig(main, sig, pxy[0] - 2, pxy[1])
        wire(main, port_xy(dl, 'A'), pxy, sig)
        ctl_in_y[port_name] = pxy[1]

    # 参考控制区 (左下): const 常量 (GUI 中双击图标改 Value 即改控制) -> 控制器
    # 注意: const 的 Name 参数即信号名, 留空由 datalabel 命名; 修改控制值只改 Value 参数
    MANUAL = 0   # 1 = 初始手动电流模式 (MAN_EN=1); 0 = 初始外环 P/Q 模式
    refs = [
        ('p_ref', 'P_REF', 0.0),        # 外环有功参考 (1pu=100MW)
        ('q_ref', 'Q_REF', 0.0),        # 外环无功参考 (1pu=100Mvar)
        ('vd_ref', 'VD_REF', 1.0),      # V 模式 d 轴电压参考
        ('v_ref', 'V_REF', 1.0),        # 附加无功电压参考
        ('mode_q', 'MODE_Q', 2.0),      # 外环模式: 1=V 2=Q
        ('dp_dc', 'DP_DC', 0.0),        # 直流侧功率 (附加有功)
        ('dp_ren', 'DP_REN', 0.0),      # 新能源功率 (附加有功)
        ('dp_load', 'DP_LOAD', 0.0),    # 负荷功率 (附加有功)
        ('id_m', 'ID_M', 0.5),          # 手动 d 轴电流 (1pu=1.36kA 峰值)
        ('iq_m', 'IQ_M', 0.2),          # 手动 q 轴电流
        ('manual_en', 'MAN_EN', 1 if MANUAL else 0),  # 1=手动 0=外环
    ]
    for i, (port_name, sig, val) in enumerate(refs):
        yy = 42 + i * 2
        cn = main.create_component('master:const', x=2, y=yy)
        cn.parameters(Value=str(val))
        make_sig(main, sig, 6, yy)
        wire(main, port_xy(cn, 'OUT'), (6, yy), sig)
        # 控制器旁 datalabel -> 输入端口
        pxy = port_xy(ctl, port_name)
        dl2 = make_sig(main, sig, pxy[0] - 2, pxy[1])
        wire(main, port_xy(dl2, 'A'), pxy, sig)
        ctl_in_y[port_name] = pxy[1]

    # ================= inv_park: idr/iqr/theta -> 三相电流指令 (A) -> CS Mag =================
    # theta 信号源: 控制器 theta 输出 (44,22) -> THETA
    dl_th = make_sig(main, 'THETA', 46, 22)
    wire(main, (44, 22), port_xy(dl_th, 'A'), 'theta out')
    inv = main.create_component('ess_full:inv_park', x=62, y=40)
    # 输入: 控制器输出 idr_k/iqr_k/theta (命名信号已存在)
    for port_name, sig in (('idr', 'IDR_K'), ('iqr', 'IQR_K'), ('theta', 'THETA')):
        pxy = port_xy(inv, port_name)
        dl2 = make_sig(main, sig, pxy[0] - 2, pxy[1])
        wire(main, port_xy(dl2, 'A'), pxy, sig)
    # 输出 -> 命名信号 -> CS Mag 端口 (点接触)
    for ph, port_name in (('A', 'ia'), ('B', 'ib'), ('C', 'ic')):
        op = port_xy(inv, port_name)
        dl = make_sig(main, 'I%s_CMD' % ph, op[0] + 2, op[1])
        wire(main, op, port_xy(dl, 'A'), 'inv %s' % ph)
        _, _, mx, my = css[ph]
        dlm = make_sig(main, 'I%s_CMD' % ph, mx, my)
        print('    Mag %s at (%d,%d)' % (ph, mx, my), flush=True)

    # ================= RMS 显示区 =================
    # 观测: idr_k, id_k, iqr_k, iq_k, p_mw, q_mvar, v_kv
    disp = [('idr_k', 'IDR_K', 'kA', 0, 2.0), ('id_k', 'ID_K', 'kA', 0, 2.0),
            ('iqr_k', 'IQR_K', 'kA', -2.0, 2.0), ('iq_k', 'IQ_K', 'kA', -2.0, 2.0),
            ('p_mw', 'P_MW', 'MW', -150, 150), ('q_mvar', 'Q_MVAR', 'MVAR', -150, 150),
            ('v_kv', 'V_KV', 'kV', 0, 100)]
    pgbs = {}
    for port_name, sig, unit, mn, mx in disp:
        pxy = port_xy(ctl, port_name)
        dl = make_sig(main, sig, pxy[0] + 2, pxy[1])
        wire(main, pxy, port_xy(dl, 'A'), 'obs ' + sig)
        rms = main.create_component('master:rms-inst', x=50, y=pxy[1])
        rms.parameters(Name=sig + '_rms', Type='1', freq='60.0 [Hz]', NSAM='64')
        wire(main, port_xy(dl, 'A'), port_xy(rms, 'IN'), sig + '->rms')
        pgb = main.create_component('master:pgb', x=56, y=pxy[1])
        pgb.parameters(Name=sig, Group='ESS', Display='1', Scale='1.0',
                       Units=unit, Min=mn, Max=mx)
        wire(main, port_xy(rms, 'OUT'), port_xy(pgb, 'Signl'), sig + ' rms')
        pgbs[sig] = pgb

    # 三相电流 RMS (右侧 x=66)
    ic_pgbs = {}
    for i, ph in enumerate(('A', 'B', 'C')):
        yy = 20 + i * 2
        dl = make_sig(main, 'IC_' + ph, 66, yy)
        rms = main.create_component('master:rms-inst', x=70, y=yy)
        rms.parameters(Name='IC%s_rms' % ph, Type='1', freq='60.0 [Hz]', NSAM='64')
        wire(main, port_xy(dl, 'A'), port_xy(rms, 'IN'), 'IC%s' % ph)
        pgb = main.create_component('master:pgb', x=76, y=yy)
        pgb.parameters(Name='Phase %s Current RMS' % ph, Group='ESS 3ph',
                       Display='1', Scale='1.0', Units='kA', Min=0, Max=2.0)
        wire(main, port_xy(rms, 'OUT'), port_xy(pgb, 'Signl'), 'IC%s rms' % ph)
        ic_pgbs[ph] = pgb

    # THETA 探针 (PLL 角) + 三相原始电流监视
    dlth = make_sig(main, 'THETA', 80, 12)
    pgb_th = main.create_component('master:pgb', x=83, y=12)
    pgb_th.parameters(Name='THETA', Group='DIAG', Display='1', Scale='1.0', Units='rad', Min=-7, Max=20)
    wire(main, port_xy(dlth, 'A'), port_xy(pgb_th, 'Signl'), 'THETA probe')
    dl_ic = make_sig(main, 'IC_A', 80, 4)
    pgb_ic = main.create_component('master:pgb', x=83, y=4)
    pgb_ic.parameters(Name='IC_A_raw', Group='DIAG', Display='1', Scale='1.0', Units='kA', Min=-1e6, Max=1e6)
    wire(main, port_xy(dl_ic, 'A'), port_xy(pgb_ic, 'Signl'), 'IC raw')
    dl_ig = make_sig(main, 'IG_A', 80, 6)
    pgb_ig = main.create_component('master:pgb', x=83, y=6)
    pgb_ig.parameters(Name='IG_A_raw', Group='DIAG', Display='1', Scale='1.0', Units='kA', Min=-1e6, Max=1e6)
    wire(main, port_xy(dl_ig, 'A'), port_xy(pgb_ig, 'Signl'), 'IG raw')

    # Graph frame: 多面板
    gf, og, cv = main.create_graph(pgbs['ID_K'], x=62, y=44)
    gf.add_overlay_graph(pgbs['IDR_K'])
    gf.add_overlay_graph(pgbs['IQ_K'])
    gf.add_overlay_graph(pgbs['IQR_K'])
    gf.add_overlay_graph(pgbs['P_MW'])
    gf.add_overlay_graph(pgbs['Q_MVAR'])
    gf.add_overlay_graph(pgbs['V_KV'])
    gf.add_overlay_graph(ic_pgbs['A'])
    gf.add_overlay_graph(ic_pgbs['B'])
    gf.add_overlay_graph(ic_pgbs['C'])
    gf.add_overlay_graph(pgb_th)
    gf.add_overlay_graph(pgb_ic)
    gf.add_overlay_graph(pgb_ig)

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

    print('==> running 0.5 s (P/Q outer mode, P_REF=0) ...', flush=True)
    case.run()
    print(case.output()[-200:], flush=True)

    print('==> validation ...', flush=True)
    panels = gf.panels()
    for i, p in enumerate(panels):
        for cu in p.curves():
            if cu.samples > 0:
                d = list(cu.domain())
                x = list(cu.trace(0))
                seg = [(tt, v) for tt, v in zip(d, x) if tt > 1.4]
                if seg:
                    mean = sum(v for _, v in seg) / len(seg)
                    print('    panel %d curve: steady mean = %.4f' % (i, mean), flush=True)
    print('==> DONE', flush=True)


if __name__ == '__main__':
    main()
