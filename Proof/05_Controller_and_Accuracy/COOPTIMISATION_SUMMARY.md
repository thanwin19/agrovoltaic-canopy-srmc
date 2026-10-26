# How co-optimising crop and solar improves the result

The controller scores every tilt angle with 50 % electricity + 50 % crop light value and picks the best one, hour by hour. Two single-goal designs show what is given up by choosing one goal only (per hectare per year, TCE, planner results from MATLAB, file T1_controller_comparison.csv):

| Design | PV kWh/m2 | Mean crop light | Crop net INR lakh | Total INR lakh |
|---|---|---|---|---|
| PV only (fixed 15 deg) | 291 | 13.7 % | -0.05 | 68.2 |
| Crop only (w = 0) | 224 | 36.3 % | 2.86 | 51.2 |
| **Co-optimised (w = 0.5)** | **238** | **33.7 %** | **2.53** | **55.0** |

The co-optimised design keeps 82 % of the PV-only electricity and 93 % of the crop-only light, and turns the crop income from negative (PV only) to INR 2.53 lakh. A PV-only design still earns more rupees in total at the assumed prices; the case for co-optimising rests on crop, water and soil values.

Accuracy of the sensor-driven controller against the best possible angle (864 cases, noisy sensors): combined score 99.6 %, electricity 82.1 %, crop light value 97.7 %, tilt error 4.8 deg (monthly plan 9.5 deg, fixed 45 deg 16.3 deg). Files: T11_accuracy_v2.csv, fig_accuracy_both_goals.png, accuracy_matlab.csv (same test repeated in MATLAB).

Water link: soil probe irrigation uses 5372 m3/ha/yr against 5641 m3 for a 4-day timer (4.8 % saved) with 0 water-stress days instead of 20 (file T16_irrigation_probe_vs_timer.csv).
