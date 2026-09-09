# -*- coding: utf-8 -*-
"""Fix overlay graph Y/X axis ranges so RMS curves display properly."""
import sys
import mhi.pscad

EXE = r'F:\PSCAD\bin\win64\Pscad.exe'
PSCX = r'F:\ESS\ess_ess_main.pscx'


def main():
    print('==> launching PSCAD ...', flush=True)
    pscad = mhi.pscad.launch(exe=EXE, silence=True, splash=False, timeout=90)
    pscad.load(PSCX)
    prj = pscad.project('ess_ess_main')
    main = prj.canvas('Main')

    gf = None
    for c in main.components():
        d = c.defn_name
        if isinstance(d, tuple):
            d = d[1] if d else str(d)
        if d == 'GraphFrame':
            gf = c
            break
    if gf is None:
        print('!! no GraphFrame', flush=True)
        sys.exit(1)

    print('==> adjusting axis ranges ...', flush=True)
    try:
        gf.zoom(0.0, 0.6)
        print('    graph x range 0..0.6 s', flush=True)
    except Exception as e:
        print('    zoom err:', type(e).__name__, e, flush=True)

    panels = gf.panels()
    print('    panels:', len(panels), flush=True)
    for i, p in enumerate(panels):
        try:
            cur = p.curves()
            n_cur = len(cur)
            # 面板参数
            if n_cur >= 3:
                p.parameters(ymin='0', ymax='60', title='PCC Voltage RMS [kV]')
                print('    panel %d: voltage RMS panel (3 curves), y 0..60 kV' % i, flush=True)
            elif n_cur == 1:
                p.parameters(ymin='0', ymax='0.1', title='VSC Current RMS [kA]')
                print('    panel %d: current RMS panel (1 curve), y 0..0.1 kA' % i, flush=True)
        except Exception as e:
            print('    panel %d err: %s' % (i, type(e).__name__), flush=True)

    print('==> saving ...', flush=True)
    prj.save()

    print('==> building ...', flush=True)
    prj.build()
    errs = [m for m in prj.messages() if m.status == 'error']
    for m in prj.messages():
        if m.status != 'normal':
            print('    [%s] %s' % (m.status, m.text), flush=True)
    if errs:
        print('!! BUILD FAILED', flush=True)
        sys.exit(1)

    print('==> running 0.5 s ...', flush=True)
    prj.run()
    print(prj.output()[-300:], flush=True)

    print('==> validation ...', flush=True)
    for i, p in enumerate(panels):
        for cu in p.curves():
            if cu.samples > 0:
                tr = cu.trace(0)
                half = tr[len(tr) // 2:]
                rms = (sum(v * v for v in half) / len(half)) ** 0.5
                print('    panel %d curve: RMS = %.3f' % (i, rms), flush=True)
    print('==> DONE', flush=True)


if __name__ == '__main__':
    main()
