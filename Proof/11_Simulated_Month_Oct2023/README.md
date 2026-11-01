# SIMULATED month: October 2023, TCE (NOT a field measurement)

What is real and what is simulated:

| Part | Status |
|---|---|
| Sunlight, PAR, air temperature, humidity, wind, rain | **real data**: NASA POWER hourly, 9.88 N 78.08 E (satellite / reanalysis, not a sensor at TCE) |
| The six sensor readings | **simulated**: the real weather plus random errors of the size of the datasheet accuracies (sunlight and PAR +-2.5 % sigma, temperature 1 C, humidity 2.5 %, soil 1.5 %, wind 0.5 m/s) |
| Soil moisture | **simulated** water balance (not measured) |
| Controller decisions | computed by `review0_controller.m` from the noisy readings |
| Light under the canopy, daily light integral (DLI) | **calculated** by the shadow model, not measured |

Files: `SIMULATED_hourly_Oct2023_TCE.csv` (340 daylight hours), `SIMULATED_daily_summary_Oct2023.csv`, `SIMULATED_month_summary.json`, `SIMULATED_month_Oct2023.png`. Script: `Review0_Prototype_Demo/matlab/review0_month_sim.m` (seed 11).

Result (honest): over the month the controller made 1.0 % less electricity than a fixed 45 deg panel and a 1.2 % higher crop-light score (0.535 vs 0.528); mean tilt 47.8 deg; DLI under the canopy 10.0 mol/m2/day (fixed 45 deg: 9.8) against 37.3 in the open (about 73 % shade); 40 rain hours at 3 deg; no storm hours (largest hourly mean wind 7.3 m/s). In a cloudy month the gain over a fixed 45 deg panel is small.

**Do not present these files as measured data.** They are simulation output; the paper calls them that.
