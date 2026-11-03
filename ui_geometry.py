"""Posicionamento no monitor da janela principal, inclusive com origem negativa."""
import sys


def centered_position(parent_rect, child_size, work_area=None):
    px, py, pw, ph = parent_rect
    width, height = child_size
    x, y = px + (pw - width) // 2, py + (ph - height) // 2
    if work_area is not None:
        left, top, right, bottom = work_area
        x = max(left + 8, min(x, right - width - 8))
        y = max(top + 8, min(y, bottom - height - 40))
    return x, y


def monitor_work_area(widget):
    if sys.platform != 'win32':
        return None
    import ctypes
    from ctypes import wintypes

    class MonitorInfo(ctypes.Structure):
        _fields_ = [('cbSize', wintypes.DWORD), ('rcMonitor', wintypes.RECT),
                    ('rcWork', wintypes.RECT), ('dwFlags', wintypes.DWORD)]

    try:
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
        user32.MonitorFromWindow.restype = wintypes.HANDLE
        user32.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.POINTER(MonitorInfo)]
        user32.GetMonitorInfoW.restype = wintypes.BOOL
        monitor = user32.MonitorFromWindow(widget.winfo_id(), 2)  # MONITOR_DEFAULTTONEAREST
        info = MonitorInfo()
        info.cbSize = ctypes.sizeof(info)
        if monitor and user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
            rect = info.rcWork
            return rect.left, rect.top, rect.right, rect.bottom
    except (OSError, AttributeError, ValueError):
        pass
    # Sem API disponível, mantenha o centro relativo à janela principal.
    return None
