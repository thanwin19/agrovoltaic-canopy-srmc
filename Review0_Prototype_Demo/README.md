# Review 0 - prototype sensors + MATLAB decision demo

Rubric: prototype demonstration 20 | testing/validation evidence 10 | feasibility 5 | SDG and cost 5 | time management 5 | questions 5.

## Start here tomorrow
1. `documents/Review0_Morning_Checklist.md`  (do in order: wire, upload, calibrate, demo, finish)
2. `firmware/PIN_MAP.md`  (pins for the NodeMCU ESP8266 and the ESP32)
3. In MATLAB:  `cd` into the `matlab` folder, then type `review0_dashboard`
   - Source "Simulate" works with no hardware (rehearse tonight).  Source "Serial (ESP)" + COM port + Connect + START live loop uses the real board.
4. `ppt/Review0_Prototype_Demo.pptx`  - 18 slides; slide 14 needs your photos and measured numbers.
5. Print `documents/Review0_Supervisor_OnePager.docx` for the signature.

## What is real and what is simulated
REAL (ESP board): DHT11 temperature + humidity, soil moisture, rain.   SIMULATED (MATLAB, labelled SIM): pyranometer, PAR, wind.   Tilt: drawn on screen only.

## Folder map
| Folder | Content |
|---|---|
| `firmware/` | `SRMC_ESP8266_NodeMCU` and `SRMC_ESP32` sketches (library-free, 115200 baud), `PIN_MAP.md` |
| `matlab/` | `review0_dashboard.m` (live GUI), `review0_controller.m` (decision), `review0_irrigation.m`, `review0_parse.m`, `review0_physics.m` (validated sun/PV/shadow functions), `review0_run_tests.m`, `review0_make_screens.m` |
| `results/` | `test_results.md/.csv` (16 tests), `day_comparison.md/.csv`, figures, `screens/` (dashboard screenshots), `proof/` (validation figures), `live_logs/` (your saved evidence) |
| `ppt/` | deck + `build_review0_deck.py` (regenerates it from the result files) |
| `documents/` | checklist, demo script and likely questions, supervisor one-pager |
| `test_data/` | `bench_log_template.csv` for the morning measurements |

## Commands
- Tests (about 1 min): `review0_run_tests` -> results/test_results.md, day_comparison.md, fig_*.png
- Screenshots: `review0_make_screens` -> results/screens
- Rebuild the deck after editing results: `python ppt/build_review0_deck.py`

## Honest limits
- The firmware and the Serial path of the dashboard could not be tested here without the board; the parser, rules, physics and the Simulate path are tested (16/16).
- Pyranometer/PAR/wind are simulated; results are screening-level, validated against PVGIS and Blender, not against field data.
- Part prices on slide 16 are indicative ranges, to be replaced with your bill.


Project title: **Agrovoltaic Canopy for Protection and Sustainable Farming**.

## Update 2026-10-25: real-data logging

`data_logging/` logs the sensors for a week and scores the week with the six-sensor controller: fake week for rehearsal now (`run_fake_week.bat`), real ESP32 data later (`run_real_week.bat`, firmware `SRMC_ESP32_six_sensors`). See `data_logging/README.md`. Not tested on hardware.
