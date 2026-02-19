def format_value(value, precision=0):
    """Format the value or return '----' if None."""
    if value is None:
        return "----"
    if isinstance(value, float):
        return str(round(value, precision))
    return str(value)

def calculate_air_score(co2, temp_c, rh, voc_raw, pm):
    """
    Air Comfort/Health Score: 0 (excellent) → 100 (very poor)

    Components:
      - CO2 (ventilation / drowsiness)         : 0–30
      - PM2.5 (health)                         : 0–30
      - VOC (irritants/odors proxy, raw scaled): 0–15
      - Temperature comfort (around ~22–24 C)   : 0–15
      - Humidity comfort (30–60% ideal)        : 0–10

    Notes:
      - VOC is still a heuristic unless you compute a VOC index.
      - Temp/RH are comfort-focused, not medical.
    """

    # Reasonable defaults if a sensor isn't ready
    if co2 is None:
        co2 = 400
    if pm is None:
        pm25 = 0
    if voc_raw is None:
        voc_raw = 0
    if temp_c is None:
        temp_c = 23.0
    if rh is None:
        rh = 45.0

    # --------------------
    # CO2 score (0–30)
    # --------------------
    # 400–800 good, 800–1200 mild, 1200–2000 worse, >2000 poor
    if co2 <= 800:
        co2_score = 0.0
    elif co2 <= 1200:
        co2_score = (co2 - 800) / 400 * 10.0
    elif co2 <= 2000:
        co2_score = 10.0 + (co2 - 1200) / 800 * 20.0
    else:
        co2_score = 30.0

    # --------------------
    # PM2.5 score (0–30)
    # --------------------
    # Rough health bands: <=5 great, 5–12 ok, 12–35 moderate, >35 poor
    # Extract pm25 from the pm dictionary
    pm25 = pm.get("pm25 standard", 0) if pm else 0

    if pm25 <= 5:
        pm_score = 0.0
    elif pm25 <= 12:
        pm_score = (pm25 - 5) / 7 * 8.0
    elif pm25 <= 35:
        pm_score = 8.0 + (pm25 - 12) / 23 * 17.0
    else:
        pm_score = 30.0

    # --------------------
    # VOC raw score (0–15)
    # --------------------
    # Empirical: treat 10k as "clean baseline", 50k as "high"
    voc_norm = min(max((voc_raw - 10000) / 40000, 0.0), 1.0)
    voc_score = voc_norm * 15.0

    # --------------------
    # Temperature comfort (0–15)
    # --------------------
    # Ideal band: 21–24 C (very comfortable for many indoors)
    # Mild discomfort: 18–21 and 24–27
    # Strong discomfort outside that
    if 21.0 <= temp_c <= 24.0:
        temp_score = 0.0
    elif 18.0 <= temp_c < 21.0:
        temp_score = (21.0 - temp_c) / 3.0 * 7.0
    elif 24.0 < temp_c <= 27.0:
        temp_score = (temp_c - 24.0) / 3.0 * 7.0
    else:
        # Outside 18–27 ramps up quickly to max
        # 15C or 30C and beyond => max penalty
        dist = min(max(abs(temp_c - 22.5) - 4.5, 0.0), 7.5)  # 0..7.5
        temp_score = min(7.0 + (dist / 7.5) * 8.0, 15.0)

    # --------------------
    # Humidity comfort (0–10)
    # --------------------
    # Ideal: 30–60%
    # Mild: 20–30 or 60–70
    # Strong: <20 or >70
    if 30.0 <= rh <= 60.0:
        rh_score = 0.0
    elif 20.0 <= rh < 30.0:
        rh_score = (30.0 - rh) / 10.0 * 4.0
    elif 60.0 < rh <= 70.0:
        rh_score = (rh - 60.0) / 10.0 * 4.0
    else:
        # Outside 20–70 ramps to max
        if rh < 20.0:
            rh_score = min(4.0 + (20.0 - rh) / 20.0 * 6.0, 10.0)  # 0% -> 10
        else:  # rh > 70
            rh_score = min(4.0 + (rh - 70.0) / 30.0 * 6.0, 10.0)  # 100% -> 10

    air_score = co2_score + pm_score + voc_score + temp_score + rh_score
    air_score = min(max(air_score, 0.0), 100.0)

    return round(air_score, 2)

