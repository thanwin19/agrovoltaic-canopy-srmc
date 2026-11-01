# Review 0 - prototype sensors + MATLAB decision demo

Rubric: prototype demonstration 20 | testing/validation evidence 10 | feasibility 5 | SDG and cost 5 | time management 5 | questions 5.

## Start here (Review 0, 100 % on the computer)
1. In MATLAB: `cd` into the `matlab` folder, then type `review0_dashboard`. The live loop starts by itself.
2. Every sensor is **simulated after a real, named device** and **can be set by hand** (slider or typed number). Until you touch one it follows the day / sky model.
3. Four graph tabs: sensors through a day, panel angle and output, accuracy of the co-optimisation, sensors and panels (datasheet numbers).
4. Proof of the devices, panels and numbers: `documents/SENSOR_AND_PANEL_PROOF.md`.
5. `ppt/Review0_Prototype_Demo.pptx` (deck, built before the hardware was removed: edit the hardware slides) and `documents/Review0_Supervisor_OnePager.docx`.

## What is simulated
All six sensors (Apogee SP-110 pyranometer, Apogee SQ-110 PAR, DHT11, DFRobot SEN0193 soil, YL-83/FC-37 rain, Adafruit 1733 anemometer) and the 8 JinkoSolar Tiger Pro JKM550M-72HL4-V panels (4.4 kWp). No board, no wiring. The hardware files (ESP firmware, serial logger, morning checklist) were moved to `../_archive/hardware_removed_for_review0/`.

## Folder map
| Folder | Content |
|---|---|
| `matlab/` | `review0_dashboard.m` (live GUI), `review0_controller.m` (decision), `review0_irrigation.m`, `review0_physics.m` (validated sun/PV/shadow functions), `review0_mppt.m`, tests and screenshot scripts |
| `results/` | `test_results.md/.csv`, `day_comparison.md/.csv`, figures, `screens/` (dashboard screenshots), dashboard_*.png |
| `ppt/` | deck + `build_review0_deck.py` |
| `documents/` | `SENSOR_AND_PANEL_PROOF.md`, `REVIEW0_TALK_TRACK.md`, supervisor one-pager |
| `data_logging/` | scores a (fake) week of sensor data with the controller |

## Commands
- Tests (about 1 min): `review0_run_tests` -> results/test_results.md, day_comparison.md, fig_*.png
- Screenshots: `review0_make_screens` -> results/screens
- Rebuild the deck after editing results: `python ppt/build_review0_deck.py`

## Honest limits
- No hardware: sensors are software models of real devices; their readings are generated or typed, not measured.
- Pyranometer/PAR/wind are simulated; results are screening-level, validated against PVGIS and Blender, not against field data.
- Part prices on slide 16 are indicative ranges, to be replaced with your bill.


Project title: **Agrovoltaic Canopy for Protection and Sustainable Farming**.

## Update 2026-10-25: real-data logging

`data_logging/` logs the sensors for a week and scores the week with the six-sensor controller: fake week for rehearsal now (`run_fake_week.bat`), real ESP32 data later (`run_real_week.bat`, firmware `SRMC_ESP32_six_sensors`). See `data_logging/README.md`. Not tested on hardware.

## Update 2026-11-01: manual sensors

The dashboard has a **MANUAL SENSORS** row under the canopy drawing: type a value for DHT11 temperature, humidity, soil moisture, pyranometer, PAR and wind (press Enter), a rain toggle, six one-click presets (clear noon, passing clouds, hot dry afternoon, rain, storm, night) and **Back to AUTO**. Typed values act in Simulate mode; with a real ESP connected the real readings win. See `results/dashboard_manual_sensors.png`.

## Update 2026-11-01: Review 0 poster and presentation

`ppt/Review0_Poster_A3.pptx` (+ PDF) and `ppt/Review0_Presentation.pptx` (+ PDF, 17 slides: problem, sensors, panels, controller, dashboard, graphs, accuracy, validation, proof, cost estimate, feasibility, status and remaining work). Built by `ppt/build_review0_poster.py` and `ppt/build_review0_deck_final.py` (helpers in `review0_ppt_common.py`, large-print figures from `make_poster_figs.py`). The older `Project_III_*` files are the Phase II originals and were not changed.
