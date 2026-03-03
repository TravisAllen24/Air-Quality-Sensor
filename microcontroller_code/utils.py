def format_value(value, precision=0):
    """Format the value or return '----' if None."""
    if value is None:
        return "----"
    if isinstance(value, float):
        return str(round(value, precision))
    return str(value)

def format_rtc_datetime(dt):
    """Format struct_time from RTC as YYYY-MM-DD HH:MM:SS string."""
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        dt.tm_year, dt.tm_mon, dt.tm_mday, dt.tm_hour, dt.tm_min, dt.tm_sec
    )




# Individual scoring functions for each variable
def co2_score(co2):
    """CO2 hazard score: 0 (good) to 100 (hazardous)"""
    if co2 is None:
        co2 = 400
    # EPA/ASHRAE: >2000 ppm is hazardous
    if co2 <= 800:
        return 0.0
    elif co2 <= 1200:
        return (co2 - 800) / 400 * 20.0
    elif co2 <= 2000:
        return 20.0 + (co2 - 1200) / 800 * 40.0
    elif co2 <= 5000:
        return 60.0 + (co2 - 2000) / 3000 * 40.0
    else:
        return 100.0

def pm25_score(pm):
    """PM2.5 hazard score: 0 (good) to 100 (hazardous)"""
    pm25 = 0
    if pm and ("pm25 standard" in pm):
        pm25 = pm["pm25 standard"]
    elif pm and ("pm25 env" in pm):
        pm25 = pm["pm25 env"]
    # EPA AQI: >250 is hazardous
    if pm25 <= 12:
        return 0.0
    elif pm25 <= 35:
        return (pm25 - 12) / 23 * 30.0
    elif pm25 <= 55:
        return 30.0 + (pm25 - 35) / 20 * 20.0
    elif pm25 <= 150:
        return 50.0 + (pm25 - 55) / 95 * 30.0
    elif pm25 <= 250:
        return 80.0 + (pm25 - 150) / 100 * 15.0
    else:
        return 95.0 + min((pm25 - 250) / 250 * 5.0, 5.0)

def voc_score(voc_index):
    """VOC index hazard score: 0 (good) to 100 (hazardous)"""
    if voc_index is None:
        voc_index = 0
    # SGP40: 0-100 good, 100-200 moderate, 200-400 bad, >400 hazardous
    if voc_index <= 100:
        return 0.0
    elif voc_index <= 200:
        return (voc_index - 100) / 100 * 30.0
    elif voc_index <= 400:
        return 30.0 + (voc_index - 200) / 200 * 40.0
    elif voc_index <= 500:
        return 70.0 + (voc_index - 400) / 100 * 20.0
    else:
        return 90.0 + min((voc_index - 500) / 500 * 10.0, 10.0)

def temp_score(temp_c):
    """Temperature comfort penalty: 0 (ideal) to 100 (extreme)"""
    if temp_c is None:
        temp_c = 23.0
    # 21-24C ideal, 18-27 mild, <15 or >30 dangerous, <5 or >40 life-threatening
    if 21.0 <= temp_c <= 24.0:
        return 0.0
    elif 18.0 <= temp_c < 21.0:
        return (21.0 - temp_c) / 3.0 * 20.0
    elif 24.0 < temp_c <= 27.0:
        return (temp_c - 24.0) / 3.0 * 20.0
    elif 15.0 <= temp_c < 18.0:
        return 20.0 + (18.0 - temp_c) / 3.0 * 30.0
    elif 27.0 < temp_c <= 30.0:
        return 20.0 + (temp_c - 27.0) / 3.0 * 30.0
    elif 5.0 <= temp_c < 15.0:
        return 50.0 + (15.0 - temp_c) / 10.0 * 30.0  # up to 80
    elif 30.0 < temp_c <= 40.0:
        return 50.0 + (temp_c - 30.0) / 10.0 * 30.0  # up to 80
    elif temp_c < 5.0:
        return 80.0 + min((5.0 - temp_c) / 10.0 * 20.0, 20.0)  # up to 100
    else:  # temp_c > 40.0
        return 80.0 + min((temp_c - 40.0) / 10.0 * 20.0, 20.0)  # up to 100

def rh_score(rh):
    """Humidity comfort penalty: 0 (ideal) to 100 (extreme)"""
    if rh is None:
        rh = 45.0
    # 30-60% ideal, 20-30/60-70 mild, <20/>70 strong, <10/>90 dangerous, <2/>98 life-threatening
    if 30.0 <= rh <= 60.0:
        return 0.0
    elif 20.0 <= rh < 30.0:
        return (30.0 - rh) / 10.0 * 20.0
    elif 60.0 < rh <= 70.0:
        return (rh - 60.0) / 10.0 * 20.0
    elif 10.0 <= rh < 20.0:
        return 20.0 + (20.0 - rh) / 10.0 * 30.0  # up to 50
    elif 70.0 < rh <= 90.0:
        return 20.0 + (rh - 70.0) / 20.0 * 30.0  # up to 50
    elif 2.0 <= rh < 10.0:
        return 50.0 + (10.0 - rh) / 8.0 * 30.0  # up to 80
    elif 90.0 < rh <= 98.0:
        return 50.0 + (rh - 90.0) / 8.0 * 30.0  # up to 80
    elif rh < 2.0:
        return 80.0 + min((2.0 - rh) / 2.0 * 20.0, 20.0)  # up to 100
    else:  # rh > 98.0
        return 80.0 + min((rh - 98.0) / 2.0 * 20.0, 20.0)  # up to 100

def calculate_air_score(co2, temp_c, rh, voc_index, pm):
    """
    Air Quality/Health Score: 0 (excellent) → 100 (hazardous)
    - If any hazard is high, the score is high (worst dominates)
    - Comfort factors (temp, rh) are included but do not mask hazards
    """
    # Individual hazard scores
    s_co2 = co2_score(co2)
    s_pm25 = pm25_score(pm)
    s_voc = voc_score(voc_index)
    s_temp = temp_score(temp_c)
    s_rh = rh_score(rh)

    scores = [s_co2, s_pm25, s_voc, s_temp, s_rh]
    max_score = max(scores)
    mean_score = sum(scores) / len(scores)
    alpha = 0.8  # weight for max vs mean
    air_score = alpha * max_score + (1 - alpha) * mean_score
    air_score = min(max(air_score, 0.0), 100.0)
    return round(air_score, 2)
