# -*- coding: utf-8 -*-
"""Run ess_lcc and quantify the VDC ripple (min/max/std, ripple frequency)."""
import mhi.pscad

EXE = r'F:\PSCAD\bin\win64\Pscad.exe'

pscad = mhi.pscad.launch(exe=EXE, silence=True, splash=False, timeout=90)
case = pscad.project('ess_lcc') if False else None
# rebuild via script logic: open existing case
pscad.load(r'F:\ESS\ess_lcc.pscx')
case = pscad.project('ess_lcc')
print('==> building ...', flush=True)
case.build()
errs = [m for m in case.messages() if m.status == 'error']
if errs:
    print('BUILD FAILED', len(errs))
    raise SystemExit(1)
print('==> running ...', flush=True)
case.run()
out = case.output()
print(out[-300:], flush=True)

print('==> ripple analysis (t > 0.4s) ...', flush=True)
cv = case.canvas('Main')
for c in cv.components():
    dn = c.defn_name
    if isinstance(dn, tuple):
        dn = dn[1]
    if dn == 'GraphFrame':
        try:
            for pi in c.panels():
                for cu in pi.curves():
                    if cu.samples > 0:
                        d = list(cu.domain())
                        x = list(cu.trace(0))
                        seg = [(t, v) for t, v in zip(d, x) if t > 0.4]
                        if seg:
                            vs = [v for _, v in seg]
                            mean = sum(vs) / len(vs)
                            vmin = min(vs)
                            vmax = max(vs)
                            # count zero crossings of (v-mean) -> estimate fundamental ripple freq
                            zc = 0
                            prev = (seg[0][1] - mean) > 0
                            for t, v in seg[1:]:
                                cur = (v - mean) > 0
                                if cur != prev:
                                    zc += 1
                                    prev = cur
                            T = (seg[-1][0] - seg[0][0])
                            f = zc / 2 / T if T > 0 else 0
                            print('curve: mean=%.3f min=%.3f max=%.3f pp=%.3f std=%.3f  fund_freq=%.1f Hz'
                                  % (mean, vmin, vmax, vmax - vmin,
                                     (sum((v - mean) ** 2 for v in vs) / len(vs)) ** 0.5, f))
        except Exception as e:
            print('err:', e)
print('==> DONE')
