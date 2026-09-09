# -*- coding: utf-8 -*-
"""Re-run ess_full and print full runtime output."""
import mhi.pscad

EXE = r'F:\PSCAD\bin\win64\Pscad.exe'
pscad = mhi.pscad.launch(exe=EXE, silence=True, splash=False, timeout=90)
pscad.load(r'F:\ESS\ess_ctl_demo.pslx')
pscad.load(r'F:\ESS\ess_full.pscx')
prj = pscad.project('ess_full')
prj.build()
errs = [m for m in prj.messages() if m.status == 'error']
print('errors:', len(errs), flush=True)
if errs:
    for m in prj.messages():
        if m.status != 'normal':
            print('  [%s] %s' % (m.status, m.text), flush=True)
    raise SystemExit(1)
prj.run()
out = prj.output()
print('===== FULL OUTPUT (%d chars) =====' % len(out), flush=True)
print(out, flush=True)
print('===== END =====', flush=True)
