# Review 4 - Six-sensor control algorithm and simulation results

**Goal.** Show how six sensors (pyranometer, PAR, DHT11, soil moisture, rain, anemometer) control the tilt to optimise crop light and electricity, how close it gets to the optimum, and what it gains over fixed designs.

## What was done

- SRMC-DT controller: every hour it picks the tilt angle (15-60 deg, 0.5 deg resolution) that maximises w x PV energy + (1-w) x crop-light value; flat 3 deg fall to the gutter in rain.
- Controller schedule for every hour of every month; Simulink model of the controller and a test day with rain and a wind gust (stow).
- Controller vs fixed designs (per hectare per year, TCE): total 55.0 lakh (controller), 52.5 lakh (fixed 45 deg), 68.2 lakh (PV-max fixed 15 deg).
- Energy/crop weight sweep and weather-year scenarios (rain -30 %, +20 %; sun +-5 %).

## Where the results are

- Figures: `results/figures/`
- Tables: `results/tables/` (T1 controller comparison, T1b weight sweep, T6 weather scenarios)
- Simulink model, diagram and test-day log: `results/simulink/`

## What to say honestly

- The controller beats the fixed 45 deg design (about 5 % total, about 55 % crop income) but a PV-only design earns MORE rupees at the assumed prices; the case for SRMC-DT rests on crop, water and soil benefits that are not priced.
- The six-sensor controller reads simulated sensors (sliders and climate data) in the twin and Simulink; Review 0 reads real DHT11, soil and rain on an ESP board. Pyranometer and PAR have not been measured.
- The combined score is the controller's own objective, so it shows how well the sensors reproduce the optimum, not crop yield.

## How to reproduce

MATLAB: the scripts in `matlab/` run directly from this folder (open MATLAB, `cd` into `matlab`). They read data and the design file from `../_project_core` and write their outputs to `../_project_core/out/`. Other files in `code_reference/` are read-only copies; the master versions are in `../_project_core`.

- `MATLAB (cd into matlab in this review folder): srmc_master()`
- `MATLAB: build_simulink_controller()`
- `MATLAB: srmc_sensitivity()` (weather scenarios)

## Documents still needed to turn assumptions into evidence

- Local weather data for realistic scenarios
- Crop price series

## Everything in this folder

| File |
|---|
| `matlab/build_simulink_controller.m` |
| `matlab/srmc_master.m` |
| `matlab/srmc_plots.m` |
| `matlab/srmc_run.m` |
| `matlab/srmc_sensitivity.m` |
| `matlab/structural_check.m` |
| `ppt/Review4_Control_and_Simulation.pptx` |
| `results/figures/fig15_weather_scenarios.png` |
| `results/figures/fig5_zone_yield.png` |
| `results/figures/fig6_controller_comparison.png` |
| `results/figures/fig7_pareto.png` |
| `results/figures/fig8_controller_schedule.png` |
| `results/simulink/controller_log.csv` |
| `results/simulink/debug.log` |
| `results/simulink/srmc_controller.slx` |
| `results/simulink/srmc_controller_day.png` |
| `results/simulink/srmc_controller_diagram.png` |
| `results/tables/T1_controller_comparison.csv` |
| `results/tables/T1b_weight_sweep.csv` |
| `results/tables/T6_physics_scenarios.csv` |


## Update 2026-10-25: six-sensor controller (SRMC-SC)

**Rule.** Rain wet = flat roof 3 deg; pyranometer below 20 W/m2 = night park 15 deg; otherwise try every angle 15 to 60 deg (0.5 deg) and pick the best J = 0.5 PV/PVmax + 0.5 crop/cropmax. PAR corrects the modelled crop light (ratio 0.7 to 1.3); DHT11 VPD and soil moisture give a stress that lowers the light the crop needs; hysteresis 2 % protects the motor. The hourly plan (SRMC-DT) stays as the planner and the fallback.

**Result.** Year-long test with noisy sensors (864 cases): 99.6 % of the best possible combined score (50 % electricity + 50 % crop light value); electricity 82 % and crop light 98 % of the best. Monthly plan 98.8 %, fixed 45 deg 91.2 %. MATLAB and the web twin make identical decisions (40 of 40).

| Strategy | Electricity % of best | Crop light value % of best | Combined score % |
|---|---|---|---|
| SRMC-SC (ideal sensors) | 81.9 | 98.1 | 99.7 |
| SRMC-SC (noisy sensors) | 82.1 | 97.7 | 99.6 |
| SC v1 (one reading, no guard) | 81.8 | 97.5 | 99.4 |
| Monthly schedule (SRMC-DT) | 82.2 | 96.3 | 98.8 |
| Fixed 45 deg | 81.0 | 84.6 | 91.2 |
| Fixed 15 deg (PV-max) | 99.2 | 45.2 | 80.0 |
| Sun tracking (E-W) | 88.6 | 64.3 | 84.0 |

**Safety and water link.** `makeSafe` in `sensor_controller.js` adds fallbacks for the soil probe and rain sensor, move limits (120 s, 12 an hour, 900 deg a day) and a motor wear count (`test_safety.js`, 8 tests, `results/safety_tests.md`); `irrigation.js` and `irrigation_study.js` let the soil probe decide irrigation and show the water saved against a timer (`results/T16_irrigation_probe_vs_timer.csv`).
**Files.** `sensor_controller/sensor_controller.js` (the controller), `sensor_controller/eval_sensor_controller.js` (year-long test), `matlab/srmc_sensor_controller.m` + `matlab/srmc_sc_crosscheck.m` (MATLAB version and cross-check), `matlab/build_simulink_sensor_controller.m` + `matlab/sl_sc_step.m` (Simulink), `sensor_controller/eval_accuracy_v2.js` (accuracy, noise, fault and yield study), `matlab/srmc_sc_accuracy.m` (accuracy in MATLAB), `results/tables/T11_accuracy_v2.csv` to `T15_accuracy_matlab.csv`, `results/figures/fig_accuracy_both_goals.png`, `results/simulink/srmc_sensor_controller_model.slx`.

**Reproduce.** `node sensor_controller/eval_sensor_controller.js` (about 25 s); `node sensor_controller/make_crosscheck_cases.js` then MATLAB `srmc_sc_crosscheck`; MATLAB `build_simulink_sensor_controller`; `python sensor_controller/patch_twin.py` rebuilds the twin from the saved original.

**Honest limits.** Simulated sensors; noise model assumed (pyranometer 5 %, PAR 5 %, DHT11 +-2 C / +-5 % RH, soil +-3 %); wind stow needs the 45 deg offset lever arm (design change; the twin mechanism animation still shows the original arm); the combined score is the controller own objective.
