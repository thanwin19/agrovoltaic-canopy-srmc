# Software-in-the-loop tests (simulated inputs)

| id | test | expected | got | result |
|---|---|---|---|---|
| T01 | Parse a good serial line | tempC 31.0, rh 54, soilRaw 712, rain 0 | tempC 31.0, rh 54, soilRaw 712, rain 0 | **PASS** |
| T02 | DHT11 read failure (-999) is flagged, not used | ok line, tempOk = false | ok 1, tempOk 0 | **PASS** |
| T03 | Boot/garbage line is ignored | ok = false | ok 0 | **PASS** |
| T04 | Soil calibration maps dry raw -> 0 %, wet raw -> 100 %, middle -> 50 % | 0 / 100 / 50 % | 0 / 100 / 50 % | **PASS** |
| T05 | VPD at 30 C / 50 % RH (Tetens) | 2.12 kPa +- 0.02 | 2.12 kPa | **PASS** |
| T06 | Rain sensor wet -> rain harvest slope | angle 3.0 deg, mode RAIN HARVEST | 3.0 deg, RAIN HARVEST | **PASS** |
| T07 | Wind >= 15 m/s -> stow 90 deg; 14.9 m/s -> no stow | 90 deg at 15.0; not 90 at 14.9 | 90 deg at 15.0; 43.5 deg at 14.9 | **PASS** |
| T08 | Priority: wind stow overrides rain mode | angle 90 deg | 90 deg, WIND STOW | **PASS** |
| T09 | Night: parked, no PV | angle 15 deg, PV 0 | 15 deg, PV 0 | **PASS** |
| T10 | Optimiser picks the best angle of a brute-force 0.5 deg grid | 43.5 deg (grid optimum) | 43.5 deg | **PASS** |
| T11 | Clear noon: controller PV >= fixed 45 deg PV | gain >= 0 % | +1.9 % | **PASS** |
| T12 | Heat stress (VPD > 2.5 kPa) lowers required crop light: stress index 1, angle changes | stress = 1.00 and angle differs from the cool case | stress 1.00, 34.5 deg vs 43.5 deg | **PASS** |
| T13 | Overcast sky: pyranometer GHI far below clear sky | GHI < 40 % of clear | 243 vs 837 W/m2 | **PASS** |
| T14 | Pump hysteresis: OFF above 55, ON below 35, stays ON until 55 % | 0 0 0 1 1 1 1 0 0 | 0 0 0 1 1 1 1 0 0 | **PASS** |
| T15 | Pump stops when the cistern is empty | pump OFF with tank 0 | pump 0, tank 0 | **PASS** |
| T16 | Zone light and PV equal the JavaScript engine (day 105, 9.5 h, 27 deg) | zones 0.1239 0.1243 0.1275 0.1062; PV 100.2 W/m2 | zones 0.1239 0.1243 0.1275 0.1062 ; PV 100.2 | **PASS** |

16 of 16 tests passed.
