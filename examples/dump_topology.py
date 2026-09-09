# -*- coding: utf-8 -*-
"""Dump full topology of a case canvas: component ports + wire vertices (grid units)."""
import sys
import mhi.pscad

EXE = r'F:\PSCAD\bin\win64\Pscad.exe'

pscad = mhi.pscad.launch(exe=EXE, silence=True, splash=False, timeout=90)
pscad.load(sys.argv[1])
prj = pscad.project(sys.argv[2])
main = prj.canvas('Main')

for c in main.components():
    d = c.defn_name
    if d in ('WireOrthogonal', 'WireBranch', 'Bus'):
        v = c.vertices()
        print('WIRE %-14s loc=%-10s verts=%s' % (d, c.location, v))
    elif d in ('OverlayGraph', 'Curve', 'GraphFrame', 'PolyGraph'):
        pass
    else:
        try:
            ports = c.ports()
            pl = ' '.join('%s(%d,%d)' % (n, p.x, p.y) for n, p in ports.items())
            print('CMP %-22s loc=%-10s %s' % (d, c.location, pl))
        except Exception as e:
            print('CMP %-22s loc=%-10s (no ports: %s)' % (d, c.location, type(e).__name__))
