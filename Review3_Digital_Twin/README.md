# Review 3 - Digital twin of the six-sensor agrovoltaic canopy

**Goal.** Build a live model of the canopy that reproduces the physics, shows the sensors and controller, and works for any place and soil.

## What was done

- Architecture: one design file and one data library feed the browser twin, the MATLAB engine, the CAD drawings and the Blender scenes.
- Browser twin: 3D scene on the TCE ground (OpenStreetMap footprints), simulated sensor stack (pyranometer, zone light, panel temperature, VPD, soil moisture, rain gauge), hourly controller, rain harvest and irrigation, economics tabs.
- Water: about 4,650 m3 harvested against about 4,930 m3 irrigation demand (about 94 % rain-fed) for the checked design.
- Universal: 7 climates (NASA POWER) and 9 soils, 24 crops; any crop in any soil matrix.
- JavaScript twin vs independent MATLAB implementation: identical results (0.0000 % on 22 quantities). This checks the code, not the physics.
- Visual context: TCE campus buildings, under-canopy view, sky and shadows.

## Where the results are

- Twin screenshots: `results/twin_screenshots/`
- Live twin: `results/live_twin/SRMC_Digital_Twin.html` (run `python -m http.server` in that folder and open it)
- Universal tables and figures: `results/tables/`, `results/figures/`
- Day animation: `results/renders/anim_day_0001-0060.mp4`

## What to say honestly

- The twin is a model, not a real plant: sensor values are simulated.
- The other climates use representative landscapes (illustrative), only TCE uses real building footprints.
- Street-view photos were used only as a visual reference; do not publish them.

## How to reproduce

MATLAB: the scripts in `matlab/` run directly from this folder (open MATLAB, `cd` into `matlab`). They read data and the design file from `../_project_core` and write their outputs to `../_project_core/out/`. Other files in `code_reference/` are read-only copies; the master versions are in `../_project_core`.

- `cd _project_core; python tools/build.py; python -m http.server 8765` then open http://localhost:8765/SRMC_Digital_Twin.html
- `MATLAB: srmc_run(); then node tools/crosscheck.js`

## Documents still needed to turn assumptions into evidence

- Soil test report for the TCE ground
- Your own photographs of the buildings (to replace street-view reference)
- Shade-crop evidence for the chosen crops

## Everything in this folder

| File |
|---|
| `code_reference/app.js` |
| `code_reference/crosscheck.js` |
| `code_reference/srmc_engine.js` |
| `documents/SRMC_Accuracy_Scorecard.html` |
| `matlab/build_simulink_controller.m` |
| `matlab/srmc_master.m` |
| `matlab/srmc_plots.m` |
| `matlab/srmc_run.m` |
| `matlab/srmc_sensitivity.m` |
| `matlab/structural_check.m` |
| `ppt/Review3_Digital_Twin.pptx` |
| `results/figures/architecture.png` |
| `results/figures/fig10_universal_climates.png` |
| `results/figures/fig11_universal_soils.png` |
| `results/figures/fig4_water_balance.png` |
| `results/live_twin/SRMC_Digital_Twin.html` |
| `results/renders/aerial.png` |
| `results/renders/anim_day_0001-0060.mp4` |
| `results/renders/hero.png` |
| `results/tables/T2_universal_climates.csv` |
| `results/tables/T3_universal_soils.csv` |
| `results/tables/summary.md` |
| `results/twin_screenshots/twin_3d_sensors.jpg` |
| `results/twin_screenshots/twin_controller_schedule.jpg` |
| `results/twin_screenshots/twin_crops_soil.jpg` |
| `results/twin_screenshots/twin_economics.jpg` |
| `results/twin_screenshots/twin_sun_light.jpg` |
| `results/twin_screenshots/twin_water_rain.jpg` |
| `results/validation_logs/crosscheck_js_vs_matlab.txt` |
| `results/validation_logs/tool_versions.txt` |


## Update 2026-10-25

- The twin is titled **Agrovoltaic Canopy for Protection and Sustainable Farming** and runs the six-sensor controller by default (checkbox in the controller panel under the 3D view). Sliders: cloud cover, DHT11 temperature and humidity, soil moisture; the rain button is the rain sensor; a decision trace shows why each angle was chosen.
- Year-long test with noisy sensors (864 cases): 99.6 % of the best possible combined score (50 % electricity + 50 % crop light value); electricity 82 % and crop light 98 % of the best. Monthly plan 98.8 %, fixed 45 deg 91.2 %. MATLAB and the web twin make identical decisions (40 of 40).
- Original twin (before this update) is kept in `results/live_twin/_old/`.
- Accuracy scorecard (`documents/SRMC_Accuracy_Scorecard.html`) now includes the controller test. The sensor values are simulated.
