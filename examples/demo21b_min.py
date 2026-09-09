# -*- coding: utf-8 -*-
"""Isolate: minimal main circuit (battery+Cdc+2 IGBT+load), no trigger wires."""
import sys
import mhi.pscad

EXE = r'F:\PSCAD\bin\win64\Pscad.exe'
WORK = r'F:\ESS'


def dname(c):
    d = c.defn_name
    return d if isinstance(d, str) else (d[1] if d else str(d))


def port_xy(c, name):
    p = c.port(name)
    if p is None:
        for n, pp in c.ports().items():
            if n.startswith(name):
                return (pp.x, pp.y)
        raise RuntimeError('port %s not found' % name)
    return (p.x, p.y)


def wire(main, a, b, label=''):
    main.create_wire(a, b)
    print('    wire %-10s (%d,%d)->(%d,%d)' % (label, a[0], a[1], b[0], b[1]), flush=True)


def main():
    print('==> launching PSCAD ...', flush=True)
    pscad = mhi.pscad.launch(exe=EXE, silence=True, splash=False, timeout=90)
    case = pscad.create_case('ess_pwm_min', folder=WORK)
    case.parameters(time_duration=0.06, time_step=5, sample_step=20)
    main = case.canvas('Main')

    bat = main.create_component('master:battery', x=6, y=20)
    bat.parameters(Type='0', Enom='100.0 [kV]', Qrated='10.0 [kA*hr]',
                   SOCint='100.0', loss='0.1', Inom='20')
    pa_b = bat.port('A'); pb_b = bat.port('B')

    cdc = main.create_component('master:capacitor', x=9, y=17, orient=1)
    cdc.parameters(C='1000.0 [uF]')
    cp1 = cdc.port('A'); cp2 = cdc.port('B')
    wire(main, (6, pa_b.y), (14, pa_b.y), 'DC+ bus')
    wire(main, (cp1.x, cp1.y), (cp1.x, pb_b.y), 'Cdc dn')
    wire(main, (cp1.x, pb_b.y), (pb_b.x, pb_b.y), 'Cdc dn-2')
    wire(main, (pb_b.x, pb_b.y), (6, 31), 'DC- v')
    wire(main, (6, 31), (14, 31), 'DC- h')

    ig_up = main.create_component('master:peswitch', x=14, y=21)
    ig_up.parameters(Name='T1', Type='3', SNUB='0', INTR='0', RON='0.01 [ohm]',
                     ROFF='1.0E6 [ohm]', EFVD='0.001 [kV]', EBO='1.0E5 [kV]',
                     Erw='1.0E5 [kV]', TEXT='0.0 [us]')
    ig_dn = main.create_component('master:peswitch', x=14, y=25, orient=2)
    ig_dn.parameters(Name='T2', Type='3', SNUB='0', INTR='0', RON='0.01 [ohm]',
                     ROFF='1.0E6 [ohm]', EFVD='0.001 [kV]', EBO='1.0E5 [kV]',
                     Erw='1.0E5 [kV]', TEXT='0.0 [us]')
    up_dp = port_xy(ig_up, 'DP'); up_dn = port_xy(ig_up, 'DN')
    dn_dp = port_xy(ig_dn, 'DP'); dn_dn = port_xy(ig_dn, 'DN')
    print('    up DP%s DN%s | dn DP%s DN%s' % (up_dp, up_dn, dn_dp, dn_dn), flush=True)

    wire(main, up_dp, dn_dp, 'phase node')
    wire(main, dn_dn, (14, 31), 'dn DC-')

    amp = main.create_component('master:ammeter', x=20, y=21)
    amp.parameters(Name='Iload')
    rl = main.create_component('master:resistor', x=26, y=21); rl.parameters(R='10.0 [ohm]')
    ll = main.create_component('master:inductor', x=32, y=21); ll.parameters(L='10.0 [mH]')
    wire(main, up_dp, port_xy(amp, 'N1'), 'to load')
    wire(main, port_xy(amp, 'N2'), port_xy(rl, 'A'), 'amm-R')
    wire(main, port_xy(rl, 'B'), port_xy(ll, 'A'), 'R-L')
    wire(main, port_xy(ll, 'B'), (34, 31), 'L DC-')

    case.save()
    case.build()
    errs = [m for m in case.messages() if m.status == 'error']
    for m in case.messages():
        if m.status != 'normal':
            print('    [%s] %s' % (m.status, m.text), flush=True)
    if errs:
        print('!! BUILD FAILED (%d)' % len(errs), flush=True)
        sys.exit(1)
    print('==> minimal circuit BUILD OK', flush=True)


if __name__ == '__main__':
    main()
