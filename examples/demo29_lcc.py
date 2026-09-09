# -*- coding: utf-8 -*-
"""
Demo 29 (v3): LCC 12-pulse rectifier + constant-current control.
Topology verified against CIGRE benchmark:
  - source3R View=1 (N3 dim=3) -> xfmr N1 (dim=3 primary winding port)
  - xfmr N2 (dim=3 secondary winding port) -> bridge N (dim=3)
  - xfmr G1/G2 (dim=1 neutral/group ports) FLOAT (as in CIGRE)
  - bridges g6p200_2 View=1, FP=0 (AO = alpha in degrees), TfPh=-30/0
  - DC: b1.DP -> Ld -> ammeter -> Rl -> b2.DN ; b1.DN <-> b2.DP series
  - control: Id -> realpole filter -> sumjct(IND=Id, INF=Iord) -> pi_ctlr -> alpha(deg)
  - KB/CB: consti(0) via datalabel; signals fan out via same-name datalabels
"""
import sys
import mhi.pscad

EXE = r'F:\PSCAD\bin\win64\Pscad.exe'
WORK = r'F:\ESS'
CASE = 'ess_lcc'
# optional argv: IORD value (kA); e.g. python demo29_lcc.py 0.5
IORD_SET = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0


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
    """Multi-vertex wire."""
    main.create_wire(*pts)
    print('    wire %-14s %s' % (label, str(pts)), flush=True)


def make_sig(main, name, x, y):
    dl = main.create_component('master:datalabel', x=x, y=y)
    dl.parameters(Name=name)
    return dl


def main():
    print('==> launching PSCAD ...', flush=True)
    pscad = mhi.pscad.launch(exe=EXE, silence=True, splash=False, timeout=90)
    case = pscad.create_case(CASE, folder=WORK)
    case.parameters(time_duration=0.5)
    main = case.canvas('Main')

    # ============ AC source (source3 View=1, Ctrl=0: N3 dim=3, no EV/EP ports) ============
    src = main.create_component('master:source3', x=5, y=25)
    src.parameters(Name='AC', MVA='200.0 [MVA]', Vm='60.0 [kV]', Es='60.0 [kV]',
                   F='60.0 [Hz]',
                   Tc='0.02 [s]', ZSeq='0', Imp='0', Ctrl='0', View='1',
                   Z1='1.0 [ohm]', Phi1='80.0', R1p='1.0 [ohm]', L1p='0.1 [H]',
                   Z0='1.0 [ohm]', Phi0='80.0', R0p='3.737 [ohm]', L0p='0.1 [H]')
    n3 = src.port('N3')
    print('    src N3 at (%d,%d)' % (n3.x, n3.y), flush=True)
    # source neutral grounded (CIGRE pattern: ground at source N port)
    sn = src.port('N')
    main.create_component('master:ground', x=sn.x, y=sn.y)

    # ============ commutating transformers (View=1: N1/N2 = winding 3ph ports) ============
    t1 = main.create_component('master:xfmr-3p2w', x=14, y=16)
    t1.parameters(Name='T_YY', Tmva='60.0 [MVA]', f='60.0 [Hz]', YD1='0', YD2='0',
                  Xl='0.18 [pu]', Ideal='1', V1='60.0 [kV]', V2='25.0 [kV]', View='1')
    t2 = main.create_component('master:xfmr-3p2w', x=14, y=50)
    t2.parameters(Name='T_YD', Tmva='60.0 [MVA]', f='60.0 [Hz]', YD1='0', YD2='1',
                  Xl='0.18 [pu]', Ideal='1', V1='60.0 [kV]', V2='25.0 [kV]', View='1')
    # G1/G2 (neutral/group ports): G1 (primary star) GROUNDED as in CIGRE; G2 floats
    for t in (t1, t2):
        g1 = port_xy(t, 'G1')
        main.create_component('master:ground', x=g1[0], y=g1[1])
    for t, y in ((t1, 16), (t2, 50)):
        n1 = port_xy(t, 'N1')
        wirev(main, [(n3.x, n3.y), (n3.x, y), n1], 'src-N1(%d)' % y)

    # ============ 6-pulse bridges x2 (View=1, FP=0: AO = alpha in RADIANS, CIGRE-exact) ============
    # TfPh: YY-fed bridge -> 0 ; YD-fed bridge -> -30 (CIGRE convention)
    b1 = main.create_component('master:g6p200_2', x=26, y=14)
    b1.parameters(Name='BRG1', UP='1', FP='0', SNUB='1', TfPh='0.0', View='1',
                  Tblock='0.04', FR='60.0 [Hz]', GP='10.0', GI='50.0', KP='0',
                  RON='0.01 [ohm]', ROFF='1.0E8 [ohm]', EFVD='0.0 [kV]', EBO='1.0E5 [kV]',
                  RWSAFB='0', RWV='1.0E5', PFB='0', TEXT='0.0 [us]', RD='5000.0 [ohm]',
                  CD='0.05 [uF]')
    b2 = main.create_component('master:g6p200_2', x=26, y=54)
    b2.parameters(Name='BRG2', UP='1', FP='0', SNUB='1', TfPh='-30.0', View='1',
                  Tblock='0.04', FR='60.0 [Hz]', GP='10.0', GI='50.0', KP='0',
                  RON='0.01 [ohm]', ROFF='1.0E8 [ohm]', EFVD='0.0 [kV]', EBO='1.0E5 [kV]',
                  RWSAFB='0', RWV='1.0E5', PFB='0', TEXT='0.0 [us]', RD='5000.0 [ohm]',
                  CD='0.05 [uF]')
    # xfmr secondary N2 (dim=3) -> bridge N (dim=3)
    for t, b, y in ((t1, b1, 14), (t2, b2, 54)):
        n2 = port_xy(t, 'N2')
        bn = port_xy(b, 'N')
        wirev(main, [n2, (n2[0], y), bn], 'N2-N(%d)' % y)

    # ============ DC side ============
    dp1, dn1 = port_xy(b1, 'DP'), port_xy(b1, 'DN')
    dp2, dn2 = port_xy(b2, 'DP'), port_xy(b2, 'DN')
    # midpoint series: b1.DN <-> b2.DP
    wire(main, dn1, dp2, 'series DN1-DP2')
    # DC ground reference: midpoint tap -> 1 MOhm -> ground (solver reference)
    rg = main.create_component('master:resistor', x=34, y=34)
    rg.parameters(R='1.0E6 [ohm]')
    wirev(main, [(26, 34), port_xy(rg, 'A')], 'mid-rg')
    rgB = port_xy(rg, 'B')
    gg = main.create_component('master:ground', x=rgB[0], y=rgB[1] + 1)
    wire(main, rgB, (rgB[0], rgB[1] + 1), 'rg-gnd')
    # load path: b1.DP -> Ld -> ammeter -> Rl -> b2.DN
    ld = main.create_component('master:inductor', x=34, y=9)
    ld.parameters(L='0.2 [H]')
    amp = main.create_component('master:ammeter', x=38, y=9)
    amp.parameters(Name='IDC')
    rl = main.create_component('master:resistor', x=42, y=9)
    rl.parameters(R='60.0 [ohm]')
    vd = main.create_component('master:voltmetergnd', x=30, y=9)
    vd.parameters(Name='VDC_LCC')
    # series chain (wire endpoints must not pass over other ports):
    # DP1 -> Ld.A ; Ld.B -> amp.N1 ; amp.N2 -> Rl.A ; Rl.B -> DN2
    wire(main, dp1, port_xy(ld, 'A'), 'DP-LdA')
    wire(main, port_xy(ld, 'B'), port_xy(amp, 'N1'), 'LdB-ampN1')
    wire(main, port_xy(amp, 'N2'), port_xy(rl, 'A'), 'ampN2-RlA')
    wirev(main, [port_xy(rl, 'B'), (46, 9), (46, 59), dn2], 'RlB-DN2')
    # voltmeter (grounded) across DC+: N1 at b1.DP
    wire(main, dp1, port_xy(vd, 'N1'), 'V+')

    # ============ control: Id -> realpole -> (Iord - Id) -> PI -> alpha ============
    # CIGRE convention: sumjct IND=Id_meas, INF=Iord, OUT=IND-INF
    flt = main.create_component('master:realpole', x=52, y=30)
    flt.parameters(G='1.0', T='0.0012 [s]', YO='0.0')
    iord = main.create_component('master:const', x=52, y=42)
    iord.parameters(Value=str(IORD_SET))
    sj = main.create_component('master:sumjct', x=58, y=34)
    pi = main.create_component('master:pi_ctlr', x=62, y=34)
    pi.parameters(GP='0.75', TI='0.0544 [s]', YHI='1.5708', YLO='0.0873', YINIT='0.5236',
                  Mthd='0', INTR='0')

    # ammeter Name='IDC' / voltmeter Name='VDC_LCC' create the named signals;
    # datalabels elsewhere with the same name merge with them (ESS pattern).
    # flt input: label IDC at flt.I
    fi = port_xy(flt, 'I')
    dl_idc1 = make_sig(main, 'IDC', fi[0] - 2, fi[1])
    wire(main, (fi[0] - 2, fi[1]), fi, 'IDC->flt')
    # IORD: const OUT -> label
    iout = port_xy(iord, 'OUT')
    dl_iord1 = make_sig(main, 'IORD', iout[0] + 2, iout[1])
    wire(main, iout, (iout[0] + 2, iout[1]), 'IORD out')
    # sumjct: IND <- IDF (flt output), INF <- IORD
    fo = port_xy(flt, 'O')
    dl_idf = make_sig(main, 'IDF', fo[0] - 2, fo[1])
    wire(main, fo, (fo[0] - 2, fo[1]), 'IDF out')
    sj_ind = None
    sj_inf = None
    sj_out = None
    for n, pp in sj.ports().items():
        if n == 'IND':
            sj_ind = (pp.x, pp.y)
        elif n == 'INF':
            sj_inf = (pp.x, pp.y)
        elif n == 'OUT':
            sj_out = (pp.x, pp.y)
    print('    sumjct IND=%s INF=%s OUT=%s' % (sj_ind, sj_inf, sj_out), flush=True)
    dl_idf2 = make_sig(main, 'IDF', sj_ind[0] - 2, sj_ind[1])
    wire(main, (sj_ind[0] - 2, sj_ind[1]), sj_ind, 'IDF->IND')
    dl_iord2 = make_sig(main, 'IORD', sj_inf[0] - 2, sj_inf[1])
    wire(main, (sj_inf[0] - 2, sj_inf[1]), sj_inf, 'IORD->INF')
    # pi: IN <- sumjct OUT ; OUT -> TRIG_ANG
    pin_ = port_xy(pi, 'IN')
    pout = port_xy(pi, 'OUT')
    wire(main, sj_out, pin_, 'err->pi')
    dl_ang = make_sig(main, 'TRIG_ANG', pout[0] + 2, pout[1])
    wire(main, pout, (pout[0] + 2, pout[1]), 'TRIG_ANG out')

    # AO / KB for both bridges (labels-only fan-out for AO)
    for bi, b in enumerate((b1, b2)):
        ao = port_xy(b, 'AO')
        dl_a = make_sig(main, 'TRIG_ANG', ao[0] + 2, ao[1])
        wire(main, ao, (ao[0] + 2, ao[1]), 'AO sig')
        # KB: consti(1) -> datalabel -> KB (KB=1 = UNBLOCKED; CIGRE KBR=1)
        pk = port_xy(b, 'KB')
        ck = main.create_component('master:consti', x=52 + bi * 8, y=74)
        ck.parameters(Value='1')
        sig = 'KBCB%d_KB' % bi
        ckout = port_xy(ck, 'OUT')
        d1 = make_sig(main, sig, ckout[0] + 2, ckout[1])
        wire(main, ckout, (ckout[0] + 2, ckout[1]), sig)
        d2 = make_sig(main, sig, pk[0] + 2, pk[1])
        wire(main, (pk[0] + 2, pk[1]), pk, sig)
    # CB: Integer input carrying the AC NODE NUMBER of the primary-side 3-phase
    # bus (CIGRE pattern: Rbus -> nodeloop.N -> nodeloop.X1 (node number) -> CB).
    # Place a nodeloop on the source 3-phase wire; fan out its X1 via labels.
    nl = main.create_component('master:nodeloop', x=7, y=18, orient=3)
    nl.parameters(View='1')
    x1 = None
    for n, pp in nl.ports().items():
        if n.startswith('X1'):
            x1 = (pp.x, pp.y)
    if x1 is None:
        print('!! nodeloop: no X1 port', flush=True)
        sys.exit(2)
    dl_x1 = make_sig(main, 'CBSYN', x1[0] + 2, x1[1])
    wire(main, x1, (x1[0] + 2, x1[1]), 'CBSYN out')
    for bi, b in enumerate((b1, b2)):
        cb = port_xy(b, 'CB')
        d2 = make_sig(main, 'CBSYN', cb[0] - 2, cb[1])
        wire(main, (cb[0] - 2, cb[1]), cb, 'CBSYN->CB')

    # ============ displays ============
    # bridge diagnostics: AM (alpha meas) / GM (gamma meas) -> named signals
    for bi, b in enumerate((b1, b2)):
        for pname, sig in (('AM', 'AM%d' % bi), ('GM', 'GM%d' % bi)):
            pk = port_xy(b, pname)
            dl = make_sig(main, sig, pk[0] + 2, pk[1])
            wire(main, pk, (pk[0] + 2, pk[1]), sig)
    # TRIG_ANG (rad) -> degrees via gain 57.2958
    gain = main.create_component('master:gain', x=66, y=38)
    gain.parameters(G='57.2958')
    gi = port_xy(gain, 'IN')
    go = port_xy(gain, 'OUT')
    dl_g = make_sig(main, 'TRIG_ANG', gi[0] - 2, gi[1])
    wire(main, (gi[0] - 2, gi[1]), gi, 'TRIG_ANG->gain')
    dl_g2 = make_sig(main, 'ALPHA_DEG', go[0] + 2, go[1])
    wire(main, go, (go[0] + 2, go[1]), 'ALPHA_DEG out')
    disp = [('VDC_LCC', 'VDC_LCC', 'kV'), ('IDC', 'IDC', 'kA'),
            ('ALPHA_DEG', 'ALPHA_DEG', 'deg'), ('GM0', 'GM0', 'deg'), ('GM1', 'GM1', 'deg')]
    pgbs = {}
    for i, (sig, name, unit) in enumerate(disp):
        x0, y0 = 70, 60 + i * 2
        dl = make_sig(main, sig, x0, y0)
        pgb = main.create_component('master:pgb', x=x0 + 3, y=y0)
        pgb.parameters(Name=name, Group='LCC', Display='1', Scale='1.0', Units=unit,
                       Min=-100, Max=200)
        wire(main, (x0, y0), port_xy(pgb, 'Signl'), name)
        pgbs[name] = pgb
    gf, og, cv = main.create_graph(pgbs['VDC_LCC'], x=x0 + 10, y=60)
    for k in ('IDC', 'ALPHA_DEG', 'GM0', 'GM1'):
        gf.add_overlay_graph(pgbs[k])

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

    print('==> running 0.5 s ...', flush=True)
    case.run()
    out = case.output()
    with open(r'F:\ESS\lcc_run_out.txt', 'w', encoding='utf-8') as f:
        f.write(out)
    print(out[-800:], flush=True)

    print('==> validation ...', flush=True)
    for i, p in enumerate(gf.panels()):
        for cu in p.curves():
            if cu.samples > 0:
                d = list(cu.domain()); x = list(cu.trace(0))
                seg = [(tt, v) for tt, v in zip(d, x) if tt > 0.4]
                if seg:
                    mean = sum(v for _, v in seg) / len(seg)
                    print('    panel %d: steady mean = %.4f' % (i, mean), flush=True)
    print('==> DONE', flush=True)


if __name__ == '__main__':
    main()
