# -*- coding: utf-8 -*-
"""Run model, then capture PSCAD window via PrintWindow API."""
import ctypes
import time
from ctypes import wintypes

import mhi.pscad

EXE = r'F:\PSCAD\bin\win64\Pscad.exe'


def dname(c):
    d = c.defn_name
    return d if isinstance(d, str) else (d[1] if d else str(d))


def find_window(title_part):
    user32 = ctypes.windll.user32
    found = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, lparam):
        if user32.IsWindowVisible(hwnd):
            n = user32.GetWindowTextLengthW(hwnd)
            if n > 0:
                buf = ctypes.create_unicode_buffer(n + 1)
                user32.GetWindowTextW(hwnd, buf, n + 1)
                if title_part in buf.value:
                    found.append((hwnd, buf.value))
        return True

    user32.EnumWindows(cb, 0)
    return found


def capture_window(hwnd, path):
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32

    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    w = rect.right - rect.left
    h = rect.bottom - rect.top
    print('    window: %dx%d at (%d,%d)' % (w, h, rect.left, rect.top), flush=True)
    if w <= 0 or h <= 0:
        return False

    hdc_win = user32.GetWindowDC(hwnd)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_win)
    hbmp = gdi32.CreateCompatibleBitmap(hdc_win, w, h)
    gdi32.SelectObject(hdc_mem, hbmp)
    user32.PrintWindow(hwnd, hdc_mem, 2)  # PW_RENDERFULLCONTENT

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [('biSize', wintypes.DWORD), ('biWidth', ctypes.c_long),
                    ('biHeight', ctypes.c_long), ('biPlanes', wintypes.WORD),
                    ('biBitCount', wintypes.WORD), ('biCompression', wintypes.DWORD),
                    ('biSizeImage', wintypes.DWORD), ('biXPelsPerMeter', ctypes.c_long),
                    ('biYPelsPerMeter', ctypes.c_long), ('biClrUsed', wintypes.DWORD),
                    ('biClrImportant', wintypes.DWORD)]

    bih = BITMAPINFOHEADER()
    bih.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bih.biWidth = w
    bih.biHeight = -h
    bih.biPlanes = 1
    bih.biBitCount = 32
    bih.biCompression = 0
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(hdc_mem, hbmp, 0, h, buf, ctypes.byref(bih), 0)

    with open(path, 'wb') as f:
        f.write(b'BM')
        f.write(ctypes.c_uint32(14 + 40 + w * h * 4))
        f.write(ctypes.c_uint16(0))
        f.write(ctypes.c_uint16(0))
        f.write(ctypes.c_uint32(14 + 40))
        f.write(bytes(bih)[:40])
        f.write(buf.raw)
    print('    captured ->', path, flush=True)
    return True


pscad = mhi.pscad.launch(exe=EXE, silence=True, splash=False, timeout=90)
print('connected', flush=True)
pscad.load(r'F:\ESS\ess_ess_main.pscx')
prj = pscad.project('ess_ess_main')
main = prj.canvas('Main')

gf = None
for c in main.components():
    if dname(c) == 'GraphFrame':
        gf = c
        break
print('graph frame:', gf is not None, flush=True)

prj.build()
errs = [m for m in prj.messages() if m.status == 'error']
print('errors:', len(errs), flush=True)
if not errs:
    prj.run()
    print('run finished', flush=True)
    if gf is not None:
        try:
            ok = pscad.navigate_to('ess_ess_main', 'Main', gf.iid, 'RMS waveforms')
            print('navigate_to:', ok, flush=True)
        except Exception as e:
            print('navigate err:', type(e).__name__, e, flush=True)
    # 鼠标移到画布区域并向下滚动, 使 Graph Frame 进入视野
    try:
        pscad.move(700, 300)
        for _ in range(40):
            pscad.wheel(-120)
        time.sleep(2)
        print('scrolled view', flush=True)
    except Exception as e:
        print('scroll err:', type(e).__name__, e, flush=True)
    time.sleep(3)

    wins = find_window('PSCAD 5.0')
    print('PSCAD windows:', wins, flush=True)
    if wins:
        # 选尺寸最大的窗口 (当前实例主窗口)
        best = None
        best_area = 0
        for hwnd, title in wins:
            r = wintypes.RECT()
            ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(r))
            area = (r.right - r.left) * (r.bottom - r.top)
            if area > best_area:
                best_area = area
                best = (hwnd, title)
        print('capturing largest window: %s (%d px^2)' % (best[1], best_area), flush=True)
        capture_window(best[0], r'F:\ESS\pscad_capture.bmp')
print('closing', flush=True)
