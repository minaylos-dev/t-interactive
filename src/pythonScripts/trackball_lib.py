"""
3-axis Trackball — Windows Raw Input API
3 мышки Keychron M4


Координатная система:  X=вправо  Z=вперёд  Y=вверх
"""

import ctypes
import ctypes.wintypes as wt
import threading
import time
import numpy as np

# =============================================================================
# 1. КОНФИГУРАЦИЯ ДАТЧИКОВ
# =============================================================================

def sensor_vectors(polar_deg, azimuth_deg, roll_deg=0, upside_down=True):
    """
    polar_deg   : 0=снизу  90=экватор  180=сверху
    azimuth_deg : угол вокруг оси Z  (0=вдоль X, 90=вдоль Y)
    roll_deg    : физический разворот мышки в креплении
    upside_down : мышка перевёрнута датчиком вверх (зеркалит ось u)
    """
    p = np.radians(polar_deg)
    a = np.radians(azimuth_deg)
    r = np.radians(roll_deg)

    n = np.array([np.sin(p)*np.cos(a),
                  np.sin(p)*np.sin(a),
                  np.cos(p)])

    u0 = np.array([-np.sin(a), np.cos(a), 0.0])
    v0 = np.array([ np.cos(p)*np.cos(a),
                    np.cos(p)*np.sin(a),
                   -np.sin(p)])

    u = np.cos(r)*u0 + np.sin(r)*v0
    v = -np.sin(r)*u0 + np.cos(r)*v0

    if upside_down:
        u = -u

    return n, u, v


# Три мышки в "треноге" под шаром, 120° между ними.
SENSOR_CONFIGS = [
    (sensor_vectors(polar_deg=135.3, azimuth_deg=0,   roll_deg=0), "A (az 0)"  ),
    (sensor_vectors(polar_deg=135.3, azimuth_deg=120, roll_deg=0), "B (az 120)"),
    (sensor_vectors(polar_deg=135.3, azimuth_deg=240, roll_deg=0), "C (az 240)"),
]

PATH_TO_INDEX = {
    r"\\?\HID#VID_3434&PID_D040&MI_00#9&226c4c9f&0&0000#{378de44c-56ef-11d1-bc8c-00a0c91405dd}": 0,  # A (0°)
    r"\\?\HID#VID_3434&PID_D040&MI_00#9&24c9280e&0&0000#{378de44c-56ef-11d1-bc8c-00a0c91405dd}": 1,  # B (120°)
    r"\\?\HID#VID_3434&PID_D040&MI_00#9&dae776&0&0000#{378de44c-56ef-11d1-bc8c-00a0c91405dd}":   2,  # C (240°)
}

# ---------------------------------------------------------------------------
# ТОНКАЯ НАСТРОЙКА
# ---------------------------------------------------------------------------

# Знаки сырых dx/dy для каждой мышки. -1 = инвертировать.
SENSOR_FLIPS = [
    (+1, +1),   # sensor 0
    (+1, +1),   # sensor 1
    (+1, +1),   # sensor 2
]

# Перестановка и знак выходных осей. На входе - вектор ω = (wx, wy, wz)
# из решателя. На выходе - (rx, ry, rz), уходящие в OSC.
# Identity = [(0,+1), (1,+1), (2,+1)]
OUTPUT_REMAP = [(0, +1), (2, -1), (1, -1)]

# Глобальный масштаб. Подгоняется на этапе 4.
# После всех трансформаций единицы out: градусы/сек углового движения шара.
# OUTPUT_SCALE = 360.0/743.4 при среднем DPI
# OUTPUT_SCALE_XYZ = [3*360/349.7, 360/354.5, 3*360/368.4] при среднем DPI
OUTPUT_SCALE = 360/190
OUTPUT_SCALE_XYZ = [3, 360/348, 3] #[3*360/375.3, 360/348, 3*360/350]


# --- Защита от слип-спайков на отдельной мышке ---
# Кап на одиночный raw-event. Когда сенсор теряет трекинг, он часто выдаёт
# дикое значение — режем его на источнике. None = без ограничения.
# Подбирается в режиме "raw": крутишь шар максимально быстро как в реальной
# работе, смотришь нормальные dx/dy, ставишь cap в 1.5–2× от увиденного.
MAX_RAW_DELTA = 600

# --- Робастное решение: выкидывание outlier-измерений ---
# Когда одна мышка попадает на "плохое пятно" шара и врёт, её невязка
# с консенсусом двух других резко растёт. Это видно и фильтруется.
SOLVER_ROBUST         = True
SOLVER_OUTLIER_FACTOR = 2.2   # больше = мягче, меньше = агрессивнее
SOLVER_MIN_SIGNAL     = 1.5   # при движении меньше этого — не фильтруем


# =============================================================================
# 2. МАТРИЦА И РЕШАТЕЛЬ
# =============================================================================

def build_solver(sensor_configs, robust=True,
                 outlier_factor=3.0, min_signal=2.0):
    """
    robust          — двухпроходный solver с downweight выбросов.
    outlier_factor  — сенсор считается соврамшим, если его невязка
                      в N раз больше медианной по сенсорам.
    min_signal      — при малом суммарном движении не фильтруем
                      (низкий SNR, невязка = шум, а не сигнал).
    """
    rows = []
    for (n, u, v), _ in sensor_configs:
        rows.append(np.cross(n, u))
        rows.append(np.cross(n, v))
    M = np.array(rows)
    M_pinv = np.linalg.pinv(M)
    n_sensors = len(sensor_configs)

    cond = np.linalg.cond(M)
    print("Матрица измерений M (6x3):")
    print(np.round(M, 3))
    print(f"\nУсловное число: {cond:.2f}", end="  ")
    print("OK" if cond <= 20 else "ВНИМАНИЕ: высокое — пересмотри углы")
    print(f"Робастный режим: {'ВКЛ' if robust else 'выкл'}"
          f"  (factor={outlier_factor}, min_signal={min_signal})\n")

    def solve(m):
        m = np.asarray(m, dtype=float)

        # Pass 1: обычное LS-решение
        omega = M_pinv @ m

        if not robust or np.linalg.norm(m) < min_signal:
            return omega

        # Невязка по каждой мышке: норма (dx,dy)-расхождения с консенсусом
        r = m - M @ omega
        per_sensor = np.array([
            np.hypot(r[2*i], r[2*i+1]) for i in range(n_sensors)
        ])

        med = float(np.median(per_sensor))
        if med < 1e-6:
            return omega

        # Гладкий downweight: чем выше отношение к медиане, тем меньше вес.
        weights = np.ones(n_sensors)
        for i in range(n_sensors):
            ratio = per_sensor[i] / med
            if ratio > outlier_factor:
                weights[i] = (outlier_factor / ratio) ** 2

        # Меньше двух живых сенсоров — пересчитывать опасно, возвращаем то что есть.
        if np.sum(weights > 0.5) < 2:
            return omega

        # Pass 2: взвешенный LS
        w6 = np.repeat(weights, 2)
        W_sqrt = np.sqrt(w6)
        omega_robust, *_ = np.linalg.lstsq(M * W_sqrt[:, None],
                                          m * W_sqrt, rcond=None)
        return omega_robust

    return solve


def self_test(sensor_configs, solve):
    print("--- Самопроверка ---")
    rows = []
    for (n, u, v), _ in sensor_configs:
        rows.append(np.cross(n, u))
        rows.append(np.cross(n, v))
    M = np.array(rows)

    for axis, label in enumerate(["X", "Y", "Z"]):
        w_in = np.zeros(3); w_in[axis] = 1.0
        w_out = solve(M @ w_in)
        ok = np.allclose(w_in, w_out, atol=1e-6)
        print(f"  Ось {label}: {'OK  ' if ok else 'FAIL'}  "
              f"вход={np.round(w_in,1)}  выход={np.round(w_out,3)}")
    print()


# =============================================================================
# 3. WINDOWS RAW INPUT
# =============================================================================

user32   = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
kernel32.GetModuleHandleW.restype  = wt.HINSTANCE
kernel32.GetModuleHandleW.argtypes = [wt.LPCWSTR]

user32.CreateWindowExW.restype  = wt.HWND
user32.CreateWindowExW.argtypes = [
    wt.DWORD, wt.LPCWSTR, wt.LPCWSTR, wt.DWORD,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    wt.HWND, wt.HANDLE, wt.HINSTANCE, ctypes.c_void_p,
]

WPARAM   = ctypes.c_size_t
LPARAM   = ctypes.c_ssize_t
LRESULT  = ctypes.c_ssize_t

user32.DefWindowProcW.restype  = LRESULT
user32.DefWindowProcW.argtypes = [wt.HWND, wt.UINT, WPARAM, LPARAM]

user32.GetRawInputData.restype  = wt.UINT
user32.GetRawInputData.argtypes = [
    wt.HANDLE, wt.UINT, ctypes.c_void_p, ctypes.POINTER(wt.UINT), wt.UINT
]

user32.GetRawInputDeviceInfoW.restype  = wt.UINT
user32.GetRawInputDeviceInfoW.argtypes = [
    wt.HANDLE, wt.UINT, ctypes.c_void_p, ctypes.POINTER(wt.UINT)
]

WM_INPUT        = 0x00FF
WM_DESTROY      = 0x0002
RIM_TYPEMOUSE   = 0
RID_INPUT       = 0x10000003
RIDEV_INPUTSINK = 0x00000100
RIDI_DEVICENAME = 0x20000007

WNDPROC_TYPE = ctypes.WINFUNCTYPE(LRESULT, wt.HWND, wt.UINT, WPARAM, LPARAM)


class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [("usUsagePage", wt.USHORT),
                ("usUsage",     wt.USHORT),
                ("dwFlags",     wt.DWORD),
                ("hwndTarget",  wt.HWND)]


class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [("dwType",  wt.DWORD),
                ("dwSize",  wt.DWORD),
                ("hDevice", wt.HANDLE),
                ("wParam",  WPARAM)]


class _BUTTONS(ctypes.Structure):
    _fields_ = [("usButtonFlags", wt.USHORT),
                ("usButtonData",  wt.SHORT)]


class _BUTTONS_UNION(ctypes.Union):
    _fields_ = [("ulButtons", wt.ULONG),
                ("s",         _BUTTONS)]


class RAWMOUSE(ctypes.Structure):
    _fields_ = [("usFlags",            wt.USHORT),
                ("_u",                 _BUTTONS_UNION),
                ("ulRawButtons",       wt.ULONG),
                ("lLastX",             wt.LONG),
                ("lLastY",             wt.LONG),
                ("ulExtraInformation", wt.ULONG)]


class RAWINPUT(ctypes.Structure):
    _fields_ = [("header", RAWINPUTHEADER),
                ("mouse",  RAWMOUSE)]


def get_device_path(hDevice):
    size = wt.UINT(0)
    user32.GetRawInputDeviceInfoW(hDevice, RIDI_DEVICENAME, None, ctypes.byref(size))
    buf = ctypes.create_unicode_buffer(size.value)
    user32.GetRawInputDeviceInfoW(hDevice, RIDI_DEVICENAME, buf, ctypes.byref(size))
    return buf.value


def list_devices():
    class RAWINPUTDEVICELIST(ctypes.Structure):
        _fields_ = [("hDevice", wt.HANDLE), ("dwType", wt.DWORD)]

    count = wt.UINT(0)
    user32.GetRawInputDeviceList(None, ctypes.byref(count),
                                 ctypes.sizeof(RAWINPUTDEVICELIST))
    arr = (RAWINPUTDEVICELIST * count.value)()
    user32.GetRawInputDeviceList(arr, ctypes.byref(count),
                                 ctypes.sizeof(RAWINPUTDEVICELIST))

    mice = [d for d in arr if d.dwType == RIM_TYPEMOUSE]
    print(f"\nRaw Input мышей: {len(mice)}")
    for d in mice:
        print(f"  {get_device_path(d.hDevice)}")


class RawInputReader(threading.Thread):
    def __init__(self, path_to_index, max_raw_delta=None):
        super().__init__(daemon=True)
        self.path_to_index = path_to_index
        self.max_raw_delta = max_raw_delta   # кап на одиночное событие; None = выкл
        self._lock    = threading.Lock()
        self._buffers = {i: [0, 0] for i in path_to_index.values()}
        # Кэш hDevice → sensor index (или None для чужих мышей).
        # Доступ только из потока message pump, лок не нужен.
        self._handle_to_index = {}
        self._hwnd    = None
        self._ready   = threading.Event()

    def pop(self, sensor_index):
        with self._lock:
            buf = self._buffers[sensor_index]
            dx, dy = buf
            buf[0] = buf[1] = 0
        return dx, dy

    def wait_ready(self, timeout=3.0):
        return self._ready.wait(timeout)

    def run(self):
        wndproc_cb = WNDPROC_TYPE(self._wnd_proc)

        class WNDCLASSEX(ctypes.Structure):
            _fields_ = [("cbSize",        wt.UINT),
                        ("style",         wt.UINT),
                        ("lpfnWndProc",   WNDPROC_TYPE),
                        ("cbClsExtra",    ctypes.c_int),
                        ("cbWndExtra",    ctypes.c_int),
                        ("hInstance",     wt.HINSTANCE),
                        ("hIcon",         wt.HANDLE),
                        ("hCursor",       wt.HANDLE),
                        ("hbrBackground", wt.HANDLE),
                        ("lpszMenuName",  wt.LPCWSTR),
                        ("lpszClassName", wt.LPCWSTR),
                        ("hIconSm",       wt.HANDLE)]

        wc = WNDCLASSEX()
        wc.cbSize        = ctypes.sizeof(WNDCLASSEX)
        wc.lpfnWndProc   = wndproc_cb
        wc.hInstance     = kernel32.GetModuleHandleW(None)
        wc.lpszClassName = "TrackballRawInput"
        user32.RegisterClassExW(ctypes.byref(wc))

        HWND_MESSAGE = wt.HWND(-3)
        self._hwnd = user32.CreateWindowExW(
            0, wc.lpszClassName, "Trackball",
            0, 0, 0, 0, 0, HWND_MESSAGE, None, wc.hInstance, None)

        rid = RAWINPUTDEVICE()
        rid.usUsagePage = 1
        rid.usUsage     = 2
        rid.dwFlags     = RIDEV_INPUTSINK
        rid.hwndTarget  = self._hwnd
        user32.RegisterRawInputDevices(
            ctypes.byref(rid), 1, ctypes.sizeof(RAWINPUTDEVICE))

        print("Raw Input: окно создано, ждём данных...")
        self._ready.set()

        msg = wt.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == WM_INPUT:
            self._handle_raw_input(lparam)
            return 0
        if msg == WM_DESTROY:
            user32.PostQuitMessage(0)
            return 0
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _handle_raw_input(self, lparam):
        hRawInput = wt.HANDLE(lparam)
        size = wt.UINT(0)
        user32.GetRawInputData(hRawInput, RID_INPUT,
                               None, ctypes.byref(size),
                               ctypes.sizeof(RAWINPUTHEADER))
        if size.value == 0:
            return

        buf = ctypes.create_string_buffer(size.value)
        ret = user32.GetRawInputData(hRawInput, RID_INPUT,
                                     buf, ctypes.byref(size),
                                     ctypes.sizeof(RAWINPUTHEADER))
        if ret == 0xFFFFFFFF:
            return

        ri = RAWINPUT.from_buffer_copy(buf)
        if ri.header.dwType != RIM_TYPEMOUSE:
            return

        # Кэшируем hDevice → idx чтобы не дёргать GetRawInputDeviceInfoW
        # на каждом событии.
        handle_key = int(ri.header.hDevice or 0)
        if handle_key in self._handle_to_index:
            idx = self._handle_to_index[handle_key]
        else:
            path = get_device_path(ri.header.hDevice)
            idx  = self.path_to_index.get(path)
            self._handle_to_index[handle_key] = idx

        if idx is None:
            return

        # Слип-кап на источнике: режем одиночное безумное значение.
        dx = ri.mouse.lLastX
        dy = ri.mouse.lLastY
        cap = self.max_raw_delta
        if cap is not None:
            if   dx >  cap: dx =  cap
            elif dx < -cap: dx = -cap
            if   dy >  cap: dy =  cap
            elif dy < -cap: dy = -cap

        with self._lock:
            self._buffers[idx][0] += dx
            self._buffers[idx][1] += dy


# =============================================================================
# 4. ОСНОВНОЙ КЛАСС
# =============================================================================

class Trackball3Axis:

    def __init__(self, sensor_configs, path_to_index,
                 sensor_flips=None, output_remap=None,
                 output_scale_xyz=None, output_scale=1.0,
                 output_rate_hz=60, smoothing=0.0,
                 max_raw_delta=None,
                 solver_robust=True,
                 solver_outlier_factor=3.0,
                 solver_min_signal=2.0,
                 debug_mode="off"):
        """
        debug_mode:
            "off"       — обычная работа, callback в OSC
            "raw"       — печатает сырые dx,dy каждой мышки + ω
            "axes"      — крупный читаемый вывод ω для проверки направлений
            "integrate" — интегрирует ω в углы для проверки масштаба
        """
        self.sensor_configs = sensor_configs
        self.path_to_index  = path_to_index
        self.flips      = sensor_flips or [(+1,+1)]*len(sensor_configs)
        self.remap      = output_remap  or [(i,+1) for i in range(3)]
        self.scale      = output_scale
        self.scale_xyz  = np.array(output_scale_xyz or [1.0, 1.0, 1.0])
        self.dt         = 1.0 / output_rate_hz
        self.alpha      = smoothing
        self.debug_mode = debug_mode

        self.solve = build_solver(sensor_configs,
                                  robust=solver_robust,
                                  outlier_factor=solver_outlier_factor,
                                  min_signal=solver_min_signal)
        self_test(sensor_configs, self.solve)

        self.reader     = RawInputReader(path_to_index,
                                         max_raw_delta=max_raw_delta)
        self.omega_body = np.zeros(3)   # сглаженная ω в "сыром" базисе решателя
        self.angles_deg = np.zeros(3)   # интегрированные углы, в градусах
        self.rot        = np.eye(3)     # накопленная матрица вращения шара

    def connect(self):
        self.reader.start()
        if not self.reader.wait_ready():
            print("ОШИБКА: Raw Input поток не запустился.")
            return False
        print(f"Все {len(self.path_to_index)} датчика зарегистрированы.\n")
        return True

    def _apply_output_transform(self, omega):
        """Перестановка осей + знаки + общий gain + покомпонентный масштаб."""
        out = np.zeros(3)
        for i, (src, sign) in enumerate(self.remap):
            out[i] = sign * omega[src]
        return out * self.scale * self.scale_xyz

    def _integrate(self, out):
        """Обновить self.rot и self.angles_deg по текущему out.

        out — угловая скорость шара в выходном базисе, единицы: градусы/сек.
        За тик длиной self.dt поворот составляет |out|*dt градусов.
        """
        omega_mag = np.linalg.norm(out)
        if omega_mag < 1e-10:
            return
        angle_deg = omega_mag * self.dt
        angle_rad = np.radians(angle_deg)
        axis = out / omega_mag
        K = np.array([[ 0,       -axis[2],  axis[1]],
                      [ axis[2],  0,       -axis[0]],
                      [-axis[1],  axis[0],  0      ]])
        dR = np.eye(3) + np.sin(angle_rad)*K + (1-np.cos(angle_rad))*(K @ K)
        self.rot = dR @ self.rot
        # Реортогонализация чтобы не накапливать дрейф.
        U, _, Vt = np.linalg.svd(self.rot)
        self.rot = U @ Vt
        self.angles_deg += out * self.dt

    def run(self, callback=None):
        print(f"Работает... режим={self.debug_mode}  Ctrl+C для остановки.\n")
        try:
            tick = 0
            while True:
                t0 = time.perf_counter()

                # Собираем измерения с учётом знаков
                meas = np.zeros(6)
                raw_per_sensor = []
                for idx in range(len(self.sensor_configs)):
                    dx, dy = self.reader.pop(idx)
                    sx, sy = self.flips[idx]
                    meas[idx*2]   = sx * dx
                    meas[idx*2+1] = sy * dy
                    raw_per_sensor.append((dx, dy))

                raw = self.solve(meas)
                self.omega_body = self.alpha * self.omega_body + (1-self.alpha) * raw
                out = self._apply_output_transform(self.omega_body)

                # Интегрирование нужно только тем режимам, что его используют.
                if self.debug_mode in ("off", "integrate"):
                    self._integrate(out)

                # Вывод по режиму
                if self.debug_mode == "raw":
                    self._print_raw(raw_per_sensor, out, tick)
                elif self.debug_mode == "axes":
                    self._print_axes(out, tick)
                elif self.debug_mode == "integrate":
                    self._print_integrate(out, self.angles_deg, tick)
                elif self.debug_mode == "off":
                    if callback:
                        callback(out, self.angles_deg)

                tick += 1
                sleep_t = self.dt - (time.perf_counter() - t0)
                if sleep_t > 0:
                    time.sleep(sleep_t)

        except KeyboardInterrupt:
            print("\nОстановка.")

    # --- режимы отладки ---

    def _print_raw(self, raw_per_sensor, out, tick):
        """Сырые dx/dy всех мышек + итоговый ω. Печатает только если есть движение."""
        any_motion = any(dx or dy for dx, dy in raw_per_sensor)
        big_omega  = np.max(np.abs(out)) > 0.5
        if not (any_motion or big_omega):
            return
        parts = []
        for i, (dx, dy) in enumerate(raw_per_sensor):
            label = self.sensor_configs[i][1]
            mark  = "*" if (dx or dy) else " "
            parts.append(f"{mark}{label}: dx={dx:+4d} dy={dy:+4d}")
        print("  |  ".join(parts) +
              f"  ||  rx={out[0]:+7.2f} ry={out[1]:+7.2f} rz={out[2]:+7.2f}")

    def _print_axes(self, out, tick):
        """Крупный вывод осей для проверки направлений."""
        if tick % 6 != 0:   # ~10 Гц
            return
        rx, ry, rz = out
        if max(abs(rx), abs(ry), abs(rz)) < 0.5:
            return
        dom_idx = int(np.argmax(np.abs(out)))
        dom  = ["X", "Y", "Z"][dom_idx]
        sign = "+" if out[dom_idx] > 0 else "-"
        bar_x = self._bar(rx)
        bar_y = self._bar(ry)
        bar_z = self._bar(rz)
        print(f"RX {bar_x}  {rx:+7.2f}")
        print(f"RY {bar_y}  {ry:+7.2f}")
        print(f"RZ {bar_z}  {rz:+7.2f}    доминирует: {sign}{dom}\n")

    def _print_integrate(self, out, angles_deg, tick):
        """Интегрированные углы — для проверки соотношения 1 оборот шара ↔ накопление."""
        if tick % 6 != 0:
            return
        ax, ay, az = angles_deg
        rx, ry, rz = out
        print(f"ω: rx={rx:+7.2f} ry={ry:+7.2f} rz={rz:+7.2f}    "
              f"∫: αx={ax:+9.1f} αy={ay:+9.1f} αz={az:+9.1f}")

    @staticmethod
    def _bar(v, scale=100.0, width=21):
        """Псевдографический индикатор от -scale до +scale."""
        v = max(-scale, min(scale, v))
        pos = int(round((v / scale) * (width // 2)))
        cells = [" "] * width
        mid = width // 2
        cells[mid] = "|"
        if pos >= 0:
            for i in range(mid+1, mid+1+pos):
                cells[i] = "█"
        else:
            for i in range(mid+pos, mid):
                cells[i] = "█"
        return "[" + "".join(cells) + "]"

# =============================================================================
# 5. ПУБЛИЧНЫЙ API — для импорта из других скриптов
# =============================================================================

class Trackball:
    
    def __init__(self):
        # Текущие значения — это и есть то, что ты будешь читать.
        self.rx = 0.0   # угол по X, градусы (накопленный)
        self.ry = 0.0   # угол по Y
        self.rz = 0.0   # угол по Z
        self.wx = 0.0   # угловая скорость по X, градусы/сек
        self.wy = 0.0   # угловая скорость по Y
        self.wz = 0.0   # угловая скорость по Z

        self._tb     = None
        self._thread = None

    def start(self):
        """Запустить трекбол. Вызывается один раз."""
        self._tb = Trackball3Axis(
            sensor_configs=SENSOR_CONFIGS,
            path_to_index=PATH_TO_INDEX,
            sensor_flips=SENSOR_FLIPS,
            output_remap=OUTPUT_REMAP,
            output_scale=OUTPUT_SCALE,
            output_scale_xyz=OUTPUT_SCALE_XYZ,
            output_rate_hz=60,
            smoothing=0.6,
            max_raw_delta=MAX_RAW_DELTA,
            solver_robust=SOLVER_ROBUST,
            solver_outlier_factor=SOLVER_OUTLIER_FACTOR,
            solver_min_signal=SOLVER_MIN_SIGNAL,
            debug_mode="off",
        )

        if not self._tb.connect():
            raise RuntimeError("Не удалось запустить трекбол")

        # Поток крутит трекбол в фоне и вызывает _update на каждом тике
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self):
        self._tb.run(callback=self._update)

    def _update(self, out, angles_deg):
        # Углы — из матрицы вращения, Euler XYZ
        R = self._tb.rot
        sin_ry = float(np.clip(-R[2, 0], -1.0, 1.0))
        ry = np.degrees(np.arcsin(sin_ry))
        if abs(sin_ry) < 0.99999:
            rx = np.degrees(np.arctan2(R[2, 1], R[2, 2]))
            rz = np.degrees(np.arctan2(R[1, 0], R[0, 0]))
        else:
            rx = np.degrees(np.arctan2(-R[1, 2], R[1, 1]))
            rz = 0.0

        self.rx = float(rx)
        self.ry = float(ry)
        self.rz = float(rz)
        self.wx = float(out[0])
        self.wy = float(out[1])
        self.wz = float(out[2])

# =============================================================================
# 6. ТОЧКА ВХОДА — запуск напрямую для диагностики
# =============================================================================
# Для использования из другого скрипта импортируй класс Trackball (см. секцию 5).

if __name__ == "__main__":

    # ---- РЕЖИМ ОТЛАДКИ ----
    # "raw"        — этап 1-2: смотрим сырые dx/dy и куда они идут в ω
    # "axes"       — этап 3: крутим вокруг X/Y/Z и видим, какая ось отзывается
    # "integrate"  — этап 4: считаем оборот шара, проверяем масштаб
    # "off"        — тишина (фактически ничего не делает, если нет callback)
    MODE = "integrate"

    # list_devices(); exit()

    tb = Trackball3Axis(
        sensor_configs=SENSOR_CONFIGS,
        path_to_index=PATH_TO_INDEX,
        sensor_flips=SENSOR_FLIPS,
        output_remap=OUTPUT_REMAP,
        output_scale=OUTPUT_SCALE,
        output_scale_xyz=OUTPUT_SCALE_XYZ,
        output_rate_hz=60,
        smoothing=0.6,
        max_raw_delta=MAX_RAW_DELTA,
        solver_robust=SOLVER_ROBUST,
        solver_outlier_factor=SOLVER_OUTLIER_FACTOR,
        solver_min_signal=SOLVER_MIN_SIGNAL,
        debug_mode=MODE,
    )

    if tb.connect():
        tb.run()