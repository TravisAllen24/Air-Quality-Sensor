import math

def format_value(value: int|float|None, precision: int=0) -> str:
    """Format the value or return '----' if None."""
    if value is None:
        return "----"
    if isinstance(value, float):
        return f"{round(value, precision):.{precision}f}"
    return str(value)


def format_rtc_dt(dt) -> str:
    """dt: time.struct_time from RTC
    Format struct_time from RTC as YYYY-MM-DD HH:MM:SS string."""
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        dt.tm_year, dt.tm_mon, dt.tm_mday, dt.tm_hour, dt.tm_min, dt.tm_sec
    )


def c_to_f(temp_c: float|None) -> float|None:
    """Convert Celsius to Fahrenheit, or return None if input is None."""
    if temp_c is None:
        return None
    return temp_c * 9.0 / 5.0 + 32.0


# Dew point calculation function
def calculate_dew_point(temp_c: float|None, rh: float|None) -> float|None:
    """
    Calculate the dew point temperature (°C) given temperature (°C) and relative humidity (%).
    Uses the Magnus formula, suitable for typical indoor conditions.
    Returns None if inputs are invalid.
    """
    if temp_c is None or rh is None or rh <= 0.0 or rh > 100.0:
        return None
    # Magnus formula constants for water vapor over water
    a = 17.62
    b = 243.12  # °C
    try:
        alpha = ((a * temp_c) / (b + temp_c)) + (math.log(rh / 100.0))
        dew_point = (b * alpha) / (a - alpha)
        return round(dew_point, 2)
    except Exception:
        return None

def piecewise_linear(x: float, points: list[tuple[float, float]]) -> float:
    """
    Interpolate x along `points`, a list of (x, y) tuples sorted by x ascending.
    Values outside the range clamp to the nearest endpoint's y.
    """
    if x <= points[0][0]:
        return float(points[0][1])
    if x >= points[-1][0]:
        return float(points[-1][1])
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x0 <= x <= x1:
            return y0 + (x - x0) / (x1 - x0) * (y1 - y0)
    raise ValueError(f"x={x} not covered by points={points}")


CO2_CURVE  = [(800, 100), (1200, 80), (2000, 40), (5000, 0)]
PM25_CURVE = [(12, 100), (35, 70), (55, 50), (150, 20), (250, 5), (500, 0)]
VOC_CURVE  = [(100, 100), (200, 70), (400, 30), (500, 10), (1000, 0)]
NOX_CURVE  = [(0, 100), (500, 0)]

TEMP_LOW  = [(-5, 0), (5, 20), (15, 50), (18, 80), (21, 100)]
TEMP_HIGH = [(24, 100), (27, 80), (30, 50), (40, 20), (50, 0)]
RH_LOW    = [(0, 0), (2, 20), (10, 50), (20, 80), (30, 100)]
RH_HIGH   = [(60, 100), (70, 80), (90, 50), (98, 20), (100, 0)]


def co2_score(co2: int | None) -> float:
    """CO2 quality score: 100 (good) to 0 (hazardous)."""
    return piecewise_linear(co2 if co2 is not None else 400, CO2_CURVE)


def pm25_score(pm: dict | None) -> float:
    """PM2.5 quality score: 100 (good) to 0 (hazardous)."""
    pm25 = pm.get("pm25 standard", pm.get("pm25 env", 0)) if pm else 0
    return piecewise_linear(pm25, PM25_CURVE)


def voc_score(voc_index: int | None) -> float:
    """VOC quality score: 100 (good) to 0 (hazardous)."""
    return piecewise_linear(voc_index if voc_index is not None else 0, VOC_CURVE)


def nox_score(nox_index: int | None) -> float:
    """NOx quality score: 100 (good) to 0 (hazardous)."""
    return piecewise_linear(nox_index if nox_index is not None else 0, NOX_CURVE)


def temp_score(temp_c: float | None) -> float:
    """Temperature comfort score: 100 (ideal) to 0 (extreme)."""
    if temp_c is None:
        temp_c = 23.0
    if temp_c <= 21.0:
        return piecewise_linear(temp_c, TEMP_LOW)
    if temp_c >= 24.0:
        return piecewise_linear(temp_c, TEMP_HIGH)
    return 100.0


def rh_score(rh: float | None) -> float:
    """Humidity comfort score: 100 (ideal) to 0 (extreme)."""
    if rh is None:
        rh = 45.0
    if rh <= 30.0:
        return piecewise_linear(rh, RH_LOW)
    if rh >= 60.0:
        return piecewise_linear(rh, RH_HIGH)
    return 100.0


def air_quality_score(scores, alpha=0.8):
    """Blend quality scores so the worst factor dominates but all factors contribute."""
    worst = min(scores)
    average = sum(scores) / len(scores)
    blended = alpha * worst + (1 - alpha) * average
    return round(min(max(blended, 0.0), 100.0), 2)


def score_to_color(score):
    """Map a 100 (good) → 0 (bad) score to a green → red gradient."""
    score = max(0, min(100, score))
    red = int((1 - score / 100) * 255)
    green = int((score / 100) * 255)
    return (red, green, 0)


def value_to_mag(value, min_value=0, max_value=100, num_pixels=7):
    if value is None:
        return 0
    value = max(min_value, min(max_value, value))
    return int((value - min_value) / (max_value - min_value) * num_pixels)


def get_display_data(co2, temp_c, rh, voc_index, nox_index, pm):
    quality = {
        "temp": temp_score(temp_c),
        "rh": rh_score(rh),
        "co2": co2_score(co2),
        "voc": voc_score(voc_index),
        "nox": nox_score(nox_index),
        "pm": pm25_score(pm),
    }
    quality["air"] = air_quality_score(list(quality.values()))

    return {
        key: {"mag": value_to_mag(score), "color": score_to_color(score)}
        for key, score in quality.items()
    }


def power_guarded(fallback_duration=0.25, fallback_blinks=1):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if self._pixel_power.value:
                return func(self, *args, **kwargs)
            else:
                self.blue_blink(duration=fallback_duration, blinks=fallback_blinks)
        return wrapper
    return decorator


def rgb_color_wheel(wheel_pos):
    """Color wheel to allow for cycling through the rainbow of RGB colors."""
    wheel_pos = wheel_pos % 255

    if wheel_pos < 85:
        return 255 - wheel_pos * 3, 0, wheel_pos * 3
    elif wheel_pos < 170:
        wheel_pos -= 85
        return 0, wheel_pos * 3, 255 - wheel_pos * 3
    else:
        wheel_pos -= 170
        return wheel_pos * 3, 255 - wheel_pos * 3, 0