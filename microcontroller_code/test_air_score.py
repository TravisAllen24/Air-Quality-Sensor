"""
Test script for air quality scoring functions in utils.py
"""
from utils import calculate_air_score, co2_score, pm25_score, voc_score, temp_score, rh_score

# Test cases: (co2, temp_c, rh, voc_index, pm_dict)
test_cases = [
    # All ideal
    (500, 22, 45, 50, {"pm25 standard": 5}),
    # High CO2 only
    (2500, 22, 45, 50, {"pm25 standard": 5}),
    # High PM2.5 only
    (500, 22, 45, 50, {"pm25 standard": 300}),
    # High VOC only
    (500, 22, 45, 600, {"pm25 standard": 5}),
    # Bad temp only
    (500, 50, 45, 50, {"pm25 standard": 5}),
    # Bad humidity only
    (500, 22, 100, 50, {"pm25 standard": 5}),
    # Multiple hazards
    (2500, 35, 90, 600, {"pm25 standard": 300}),
    # Mildly elevated all
    (1000, 25, 65, 120, {"pm25 standard": 20}),
    # Edge: all missing
    (None, None, None, None, None),
]

print("Test Air Quality Score Table:")
print("CO2\tTemp\tRH\tVOC\tPM2.5\tScore\tCO2s\tPMs\tVOCs\tTs\tRHs")
for co2, temp, rh, voc, pm in test_cases:
    score = calculate_air_score(co2, temp, rh, voc, pm)
    s_co2 = co2_score(co2)
    s_pm = pm25_score(pm)
    s_voc = voc_score(voc)
    s_temp = temp_score(temp)
    s_rh = rh_score(rh)
    pm25 = pm["pm25 standard"] if pm and "pm25 standard" in pm else None
    print(f"{co2}\t{temp}\t{rh}\t{voc}\t{pm25}\t{score}\t{s_co2:.1f}\t{s_pm:.1f}\t{s_voc:.1f}\t{s_temp:.1f}\t{s_rh:.1f}")

print("\nLegend: Score = overall air score, CO2s = CO2 score, PMs = PM2.5 score, VOCs = VOC score, Ts = Temp score, RHs = RH score")
