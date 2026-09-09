# -*- coding: utf-8 -*-
"""
接入 IEEE39: 把 LCC39 黑盒(12脉动LCC整流器+CC控制)并联挂接在 Bus39 (230kV) 上。
- 在 ieee_39_bus case 中重建 LCC39 定义(内部电路复用 demo30 验证过的拓扑)
- Main 页: Bus39 母线 T 接 -> LCC39.AC ; IORD const ; VDCO/IDCO/ALPHAO 显示
"""
import sys
import mhi.pscad
from mhi.pscad.wizard import UserDefnWizard, Signal

EXE = r'F:\PSCAD\bin\win64\Pscad.exe'
WORK = r'F:\ESS'
CASE39 = r'F:\ESS\ieee_39_bus.pscx'
# mode: 1 = defn only (no instance); 2 = instance, AC not connected; 3 = full connect
MODE = int(sys.argv[1]) if len(sys.argv) > 1 else 3


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
    print('    wire %-14s (%d,%d)->(%d,%d)' % (label, a[0], a[1], b[0], b[1]), flush=True)


def wirev(main, pts, label=''):
    main.create_wire(*pts)
    print('    wire %-14s %s' % (label, str(pts)), flush=True)


def make_sig(main, name, x, y):
    dl = main.create_component('master:datalabel', x=x, y=y)
    dl.parameters(Name=name)
    return dl


def make_lcc39_defn(case):
    w = UserDefnWizard('LCC39')
    w.module = True
    w.description = '12-pulse LCC rectifier black-box with CC control (230kV AC)'
    w.port.electrical(-6, 0, 'AC', dim=3)
    w.port.input(-4, -4, 'IORD', Signal.REAL)
    w.port.output(4, 4, 'VDCO', Signal.REAL)
    w.port.output(4, 2, 'IDCO', Signal.REAL)
    w.port.output(4, 0, 'ALPHAO', Signal.REAL)
    return w.create_definition(case)


def build_lcc_inside(cv, iord_sig='IORD'):
    """LCC internals (verified in demo30). Returns signal names."""
    ac = None
    for c in cv.components():
        dn = dname(c)
        if dn == 'xnode':
            try:
                nm = c.parameters().get('Name', '')
            except Exception:
                nm = ''
            if nm == 'AC':
                loc = c.location
                ac = (loc[0], loc[1])
                break
    if ac is None:
        raise RuntimeError('AC xnode not found')
    print('    AC xnode at', ac, flush=True)

    nl = cv.create_component('master:nodeloop', x=ac[0], y=ac[1] - 1, orient=3)
    nl.parameters(View='1')
    x1 = None
    for n, pp in nl.ports().items():
        if n.startswith('X1'):
            x1 = (pp.x, pp.y)
    print('    nodeloop X1 at', x1, flush=True)

    t1 = cv.create_component('master:xfmr-3p2w', x=14, y=16)
    t1.parameters(Name='T_YY', Tmva='60.0 [MVA]', f='60.0 [Hz]', YD1='0', YD2='0',
                  Xl='0.18 [pu]', Ideal='1', V1='230.0 [kV]', V2='25.0 [kV]', View='1')
    t2 = cv.create_component('master:xfmr-3p2w', x=14, y=50)
    t2.parameters(Name='T_YD', Tmva='60.0 [MVA]', f='60.0 [Hz]', YD1='0', YD2='1',
                  Xl='0.18 [pu]', Ideal='1', V1='230.0 [kV]', V2='25.0 [kV]', View='1')
    for t in (t1, t2):
        g1 = port_xy(t, 'G1')
        cv.create_component('master:ground', x=g1[0], y=g1[1])

    b1 = cv.create_component('master:g6p200_2', x=26, y=14)
    b1.parameters(Name='BRG1', UP='1', FP='0', SNUB='1', TfPh='0.0', View='1',
                  Tblock='0.04', FR='60.0 [Hz]', GP='10.0', GI='50.0', KP='0',
                  RON='0.01 [ohm]', ROFF='1.0E8 [ohm]', EFVD='0.0 [kV]', EBO='1.0E5 [kV]',
                  RWSAFB='0', RWV='1.0E5', PFB='0', TEXT='0.0 [us]', RD='5000.0 [ohm]',
                  CD='0.05 [uF]')
    b2 = cv.create_component('master:g6p200_2', x=26, y=54)
    b2.parameters(Name='BRG2', UP='1', FP='0', SNUB='1', TfPh='-30.0', View='1',
                  Tblock='0.04', FR='60.0 [Hz]', GP='10.0', GI='50.0', KP='0',
                  RON='0.01 [ohm]', ROFF='1.0E8 [ohm]', EFVD='0.0 [kV]', EBO='1.0E5 [kV]',
                  RWSAFB='0', RWV='1.0E5', PFB='0', TEXT='0.0 [us]', RD='5000.0 [ohm]',
                  CD='0.05 [uF]')

    for t, y, b in ((t1, 16, b1), (t2, 50, b2)):
        n1 = port_xy(t, 'N1')
        wirev(cv, [ac, (ac[0], ac[1] - 1), (ac[0], y), n1], 'AC-N1(%d)' % y)
        n2 = port_xy(t, 'N2')
        bn = port_xy(b, 'N')
        wirev(cv, [n2, (n2[0], y), bn], 'N2-N(%d)' % y)

    dl_x1 = make_sig(cv, 'CBSYN', x1[0] + 2, x1[1])
    wire(cv, x1, (x1[0] + 2, x1[1]), 'CBSYN out')
    for bi, b in enumerate((b1, b2)):
        cb = port_xy(b, 'CB')
        d2 = make_sig(cv, 'CBSYN', cb[0] - 2, cb[1])
        wire(cv, (cb[0] - 2, cb[1]), cb, 'CBSYN->CB')
        kb = port_xy(b, 'KB')
        ck = cv.create_component('master:consti', x=40 + bi * 2, y=22)
        ck.parameters(Value='1')
        ckout = port_xy(ck, 'OUT')
        wirev(cv, [ckout, (ckout[0], kb[1]), kb], 'KB direct')

    dp1, dn1 = port_xy(b1, 'DP'), port_xy(b1, 'DN')
    dp2, dn2 = port_xy(b2, 'DP'), port_xy(b2, 'DN')
    wire(cv, dn1, dp2, 'series DN1-DP2')
    rg = cv.create_component('master:resistor', x=30, y=34)
    rg.parameters(R='1.0E6 [ohm]')
    wirev(cv, [(dn1[0], dn1[1]), (26, 34), port_xy(rg, 'A')], 'mid-rg')
    rgB = port_xy(rg, 'B')
    gg = cv.create_component('master:ground', x=rgB[0], y=rgB[1] + 1)
    wire(cv, rgB, (rgB[0], rgB[1] + 1), 'rg-gnd')
    ld = cv.create_component('master:inductor', x=34, y=9)
    ld.parameters(L='0.2 [H]')
    amp = cv.create_component('master:ammeter', x=38, y=9)
    amp.parameters(Name='IDCO')
    rl = cv.create_component('master:resistor', x=42, y=9)
    rl.parameters(R='60.0 [ohm]')
    vd = cv.create_component('master:voltmetergnd', x=30, y=9)
    vd.parameters(Name='VDCO')
    wire(cv, dp1, port_xy(ld, 'A'), 'DP-LdA')
    wire(cv, port_xy(ld, 'B'), port_xy(amp, 'N1'), 'LdB-ampN1')
    wire(cv, port_xy(amp, 'N2'), port_xy(rl, 'A'), 'ampN2-RlA')
    wirev(cv, [port_xy(rl, 'B'), (46, 9), (46, 59), dn2], 'RlB-DN2')
    wire(cv, dp1, port_xy(vd, 'N1'), 'V+')

    flt = cv.create_component('master:realpole', x=52, y=30)
    flt.parameters(G='1.0', T='0.0012 [s]', YO='0.0')
    sj = cv.create_component('master:sumjct', x=58, y=34)
    pi = cv.create_component('master:pi_ctlr', x=62, y=34)
    pi.parameters(GP='0.75', TI='0.0544 [s]', YHI='1.5708', YLO='0.0873', YINIT='0.5236',
                  Mthd='0', INTR='0')
    fi = port_xy(flt, 'I')
    dl_idc = make_sig(cv, 'IDCO', fi[0] - 2, fi[1])
    wire(cv, (fi[0] - 2, fi[1]), fi, 'IDCO->flt')
    fo = port_xy(flt, 'O')
    dl_idf = make_sig(cv, 'IDF', fo[0] - 2, fo[1])
    wire(cv, fo, (fo[0] - 2, fo[1]), 'IDF out')
    sj_ports = {n: (pp.x, pp.y) for n, pp in sj.ports().items()}
    sj_ind = sj_ports.get('IND')
    sj_inf = sj_ports.get('INF')
    sj_out = sj_ports.get('OUT')
    dl_idf2 = make_sig(cv, 'IDF', sj_ind[0] - 2, sj_ind[1])
    wire(cv, (sj_ind[0] - 2, sj_ind[1]), sj_ind, 'IDF->IND')
    dl_iord = make_sig(cv, iord_sig, sj_inf[0] - 2, sj_inf[1])
    wire(cv, (sj_inf[0] - 2, sj_inf[1]), sj_inf, 'IORD->INF')
    pin_ = port_xy(pi, 'IN')
    pout = port_xy(pi, 'OUT')
    wire(cv, sj_out, pin_, 'err->pi')
    dl_ang = make_sig(cv, 'ALPHA_RAD', pout[0] + 2, pout[1])
    wire(cv, pout, (pout[0] + 2, pout[1]), 'ALPHA out')
    for b in (b1, b2):
        ao = port_xy(b, 'AO')
        dl_a = make_sig(cv, 'ALPHA_RAD', ao[0] + 2, ao[1])
        wire(cv, ao, (ao[0] + 2, ao[1]), 'AO sig')
    gain = cv.create_component('master:gain', x=66, y=38)
    gain.parameters(G='57.2958')
    gi = port_xy(gain, 'IN')
    go = port_xy(gain, 'OUT')
    dl_g = make_sig(cv, 'ALPHA_RAD', gi[0] - 2, gi[1])
    wire(cv, (gi[0] - 2, gi[1]), gi, 'ALPHA_RAD->gain')
    dl_g2 = make_sig(cv, 'ALPHAO', go[0] + 2, go[1])
    wire(cv, go, (go[0] + 2, go[1]), 'ALPHAO out')
    print('    LCC internals built', flush=True)


def main():
    print('==> launching PSCAD ...', flush=True)
    pscad = mhi.pscad.launch(exe=EXE, silence=True, splash=False, timeout=90)
    pscad.load(CASE39)
    case = pscad.project('ieee_39_bus')
    print('==> case loaded', flush=True)
    if MODE == 0:
        print('==> MODE 0: pristine save+build ...', flush=True)
        case.save()
        case.build()
        errs = [m for m in case.messages() if m.status == 'error']
        for m in case.messages():
            if m.status != 'normal':
                print('    [%s] %s' % (m.status, m.text), flush=True)
        if errs:
            print('!! BUILD FAILED (%d errors)' % len(errs), flush=True)
            sys.exit(1)
        print('==> build OK', flush=True)
        sys.exit(0)
    print('==> creating LCC39 defn ...', flush=True)
    defn = make_lcc39_defn(case)
    print('    defn:', defn, flush=True)
    cv = case.canvas('LCC39')
    build_lcc_inside(cv)

    main = case.canvas('Main')

    if MODE >= 2:
        # Bus39 @(21,55)..(27,55). The area below it is a comb of buses/leads
        # (x=22/26/27/30/31/34/38/41 leads; Bus4/5/6/8/9/11/12/14).
        # Verified-clean corridor: (24,55)->(24,44)->(10,44)->(10,60).
        #   x=24 vertical y44..55: no leads (T1_39 lead is x=26; T9_39 x=22)
        #   y=44 horizontal x10..24: clear (T1_39 box starts y=45; Bus3 y=43)
        #   x=10 vertical y44..60: far-left open area
        # LCC box at (4..16, 56..64) -- open area.
        inst = main.create_component('ieee_39_bus:LCC39', x=10, y=60)
        acp = inst.port('AC')
        print('    LCC AC port at', (acp.x, acp.y), flush=True)
        if MODE >= 3:
            wirev(main, [(24, 55), (24, 44), (10, 44), (10, 60), (acp.x, acp.y)], 'Bus39-LCC')
        # IORD: const (4,66) -> label (8,66) -> (8,56) -> IORD port (6,56)
        iord = main.create_component('master:const', x=4, y=66)
        iord.parameters(Value='1.0')
        iout = port_xy(iord, 'OUT')
        dl = make_sig(main, 'IORD', 8, 66)
        wire(main, iout, (8, 66), 'IORD out')
        ip = inst.port('IORD')
        wirev(main, [(8, 66), (8, ip.y), (ip.x, ip.y)], 'IORD->port')
        # displays: outputs (14,64)/(14,62)/(14,60) -> horizontal -> pgbs (17,..)
        pgbs = {}
        for i, (sig, portname, yy) in enumerate((('VDCO', 'VDCO', 64), ('IDCO', 'IDCO', 62), ('ALPHAO', 'ALPHAO', 60))):
            x0, y0 = 17, yy
            op = inst.port(portname)
            dlsig = sig + '_P'
            wirev(main, [(op.x, op.y), (x0, op.y)], '%s out' % sig)
            dl = make_sig(main, dlsig, x0, y0)
            pgb = main.create_component('master:pgb', x=x0 + 3, y=y0)
            pgb.parameters(Name=dlsig, Group='LCC', Display='1', Scale='1.0', Units='',
                           Min=-100, Max=200)
            wire(main, (x0, y0), port_xy(pgb, 'Signl'), dlsig)
            pgbs[sig] = pgb
        gf, og, cv2 = main.create_graph(pgbs['VDCO'], x=x0 + 10, y=60)
        for k in ('IDCO', 'ALPHAO'):
            gf.add_overlay_graph(pgbs[k])
    else:
        gf = None

    # shorten run to 1.0 s for validation speed (IEEE39 default is 2 s @ 5us)
    try:
        case.parameters(time_duration=1.0)
    except Exception as e:
        print('    time_duration set err:', e, flush=True)

    print('==> saving as ieee39_lcc ...', flush=True)
    # load'ed projects cannot be save()'d (dialog pops); use save_as
    case.save_as('ieee39_lcc', folder=r'F:\ESS')
    case = pscad.project('ieee39_lcc')
    print('==> building ...', flush=True)
    case.build()
    errs = [m for m in case.messages() if m.status == 'error']
    for m in case.messages():
        if m.status != 'normal':
            print('    [%s] %s' % (m.status, m.text), flush=True)
    if errs:
        print('!! BUILD FAILED (%d errors)' % len(errs), flush=True)
        sys.exit(1)
    print('==> build OK', flush=True)

    print('==> running 1.0 s ...', flush=True)
    case.run()
    out = case.output()
    with open(r'F:\ESS\ieee39_lcc_run_out.txt', 'w', encoding='utf-8') as f:
        f.write(out)
    print(out[-700:], flush=True)

    print('==> validation ...', flush=True)
    # after save_as the old handles are invalid; re-acquire and read the graph
    try:
        case2 = pscad.project('ieee39_lcc')
        cv3 = case2.canvas('Main')
        for c in cv3.components():
            dn = dname(c)
            if dn == 'GraphFrame':
                try:
                    for p in c.panels():
                        for cu in p.curves():
                            if cu.samples > 0:
                                d = list(cu.domain()); x = list(cu.trace(0))
                                seg = [(tt, v) for tt, v in zip(d, x) if tt > 0.8]
                                if seg:
                                    mean = sum(v for _, v in seg) / len(seg)
                                    print('    panel: steady mean = %.4f' % mean, flush=True)
                except Exception as e:
                    print('    graph read err:', e, flush=True)
    except Exception as e:
        print('    re-acquire err:', e, flush=True)
    print('==> DONE', flush=True)


if __name__ == '__main__':
    main()
