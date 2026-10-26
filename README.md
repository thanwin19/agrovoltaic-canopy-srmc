# Agrovoltaic Canopy for Protection and Sustainable Farming

A final-year project (Thiagarajar College of Engineering, Madurai, India; site 9.88° N, 78.08° E). It is a **computer-based study**: models, a digital twin, a controller and its tests, drawings and a research paper. Nothing here has been built or measured in the field yet.

## The idea in one paragraph

Crops and solar panels compete for the same sunlight. A fixed panel angle favours one of them. We hang rows of pivoting solar panels on a stainless-steel wire-rope canopy 4.5 m above the crop. **One motor and one drive wire tilt every row together.** A controller reads **six sensors** (pyranometer, PAR light sensor under the panels, DHT11 temperature and humidity, soil moisture, rain sensor, anemometer) and chooses the panel angle that gives the best equal-weight mix of **electricity and crop light**. In rain the panels lie nearly flat (3°) and the roof drains into a gutter and cistern (rain harvest). In storm wind (15 m/s or more) they turn edge-on at 90°. At night they park. The electricity is assumed to be sold to a nearby industry and the farmer gets a monthly income plus crop income.

## Headline results (all simulated)

| Question | Result |
|---|---|
| How accurately does the controller co-optimise crop light and electricity? | 864 cases with noisy sensors: **99.6 %** of the best possible combined score; **82 %** of the best electricity and **98 %** of the best crop light value. Fixed 45°: 91.2 %. Monthly plan: 98.8 %. Fixed 15° (electricity only): 80.0 %. |
| Does it hold at other climates? | Seven climates from 9.9° to 30.9° N: **99.6 to 99.7 %** at every site (monthly schedule 98.2 to 99.2 %, fixed 45° 89.1 to 91.5 %). Eight noise draws: 99.57 ± 0.04 %. |
| Which sensors matter? | With the crop light model wrong by 20 %, the full controller keeps 99.6 %; without the PAR sensor 98.6 to 99.0 %; without the temperature, humidity and soil stress 98.8 to 99.2 % (`eval_general.js`). |
| Does it hold across conditions? | 99.5 to 99.7 % in every sky, soil and season group; 99.6 % with a dirty, reflecting or dead light sensor (a single-reading controller drops to 97.4 to 98.7 %). |
| Does the MATLAB code agree with the browser twin? | Identical mode and angle in 40 of 40 random cases; the twin and MATLAB engine agree to 0.0000 % on 22 outputs. |
| Physics checks | PV model within +5.0 % of PVGIS (annual); shadow model within 0.010 mean lit-fraction difference of a Blender Cycles ray trace (80 comparisons). |
| Structure | The 12.5 m bay layout **fails** screening (rope 16×, tube 30× over). The 5 m rope grid with a 114.3×4 tube **passes** at 140 km/h wind (tube 0.76, rope 0.37, stay 0.32). Screening level only. |
| Rain harvest | About 4,650 m³/ha/yr harvested, about 94 % of irrigation demand. |
| Soil-probe irrigation | 4.8 to 5.5 % less water than timers every 2 to 7 days, and no water-stress days (timers 15 to 29). |
| Honest limit | In rupees, an electricity-only panel earns the most, and the monthly plan earns slightly more crop income than the live controller. The weight between the two goals is therefore a **design rule** (for example a minimum crop income), not something total income can decide. See `Paper/`. |

## What was built

- **Tilt mechanism**: one drive wire (6 mm SS316) in a closed loop on a 120 mm drum (10 kN worm-gear winch, about 0.25 kW), clamped to a 0.44 m lever arm on every torque tube. The arm is fixed at a **45° offset**, so wire travel is d = L[sin(θ−45°) − sin(3°−45°)] (408 mm to 60°, 606 mm to the 90° stow) and a lever of at least 0.31 m remains at the stow position (a plain arm has none).
- **Six-sensor controller** (`Review4_Control_and_Simulation/sensor_controller/`): rain → flat; wind → stow; night → park; otherwise maximise J = 0.5·PV/PVmax + 0.5·crop/cropmax over 15° to 60° (0.5° steps). The PAR sensor corrects the crop light model; hot dry air and dry soil lower the light the crop needs; median-of-five readings; 2 % hysteresis; a safety layer with sensor-fault fallbacks, move limits (120 s hold, 12 moves/h, 900°/day) and a motor wear count.
- **Digital twin** (`Review3_Digital_Twin/results/live_twin/SRMC_Digital_Twin.html`): browser app, works offline. 3D canopy on the college ground (OpenStreetMap footprints), simulated sensor stack, live controller decisions with reasons, mechanism animation, cistern and soil-probe irrigation, seven climates, nine soils, economics, accuracy tab, fault injection.
- **3D mechanism viewer** (`Review1_Design_and_CAD/results/mechanism_3d/SRMC_Mechanism_3D.html`): real-scale 3D model showing sensors → controller → motor → drum → wire → lever arm → tube → panels, with a tilt slider, weather scenarios and camera close-ups. Rebuild with `code_reference/build_mechanism_3d.py`.
- **MATLAB / Simulink**: engine, structural check, sensitivity, six-sensor controller, cross-check with the web twin, Simulink supervisory model.
- **Prototype stage** (`Review0_Prototype_Demo/`): ESP8266/ESP32 firmware, MATLAB dashboard, 16 software-in-the-loop tests (16/16 pass), a week-logging and scoring tool (rehearsed on a synthetic week only).
- **CAD**: AutoCAD drawings (plan, elevation, section, wire drive) and a 22-item bill of materials from one design file.
- **Evidence**: `Proof/` has every file a judge may ask for, with dataset sources and an evidence-status table (real / validated / simulated / assumed).
- **Research paper**: `Paper/SRMC_Research_Paper.docx` (ProComm template, 8 pages) and PDF, with the scripts that regenerate its figures.

## What is real and what is not

- **Real**: the code, the models, the drawings, the test results in this repository.
- **Validated against independent references**: PV energy (PVGIS ERA5), shadow model (Blender Cycles).
- **Simulated**: all sensor values in the twin, Simulink and accuracy tests (the prototype reads only DHT11, soil and rain on an ESP board; pyranometer, PAR and wind have not been measured), generated wind and storms, crop yield, water balance.
- **Assumed**: every price (tariff INR 3.0/kWh, 30 % farmer share, capex, crop prices), typical soil and crop parameters, the 39 m/s basic wind speed (to be checked on the IS 875 map).
- **Not done**: field data, soil and geotechnical tests, supplier quotes, structural engineer's certification, a prior-art search. Accuracy scores are measured against the controller's own objective, not against field crop yield.

## Repository layout

| Folder | Contents |
|---|---|
| `Review0_Prototype_Demo/` | Prototype sensors, firmware, MATLAB dashboard, tests, data logging |
| `Review1_Design_and_CAD/` | Design file, structure, drawings, BOM, mechanism animations, 3D mechanism viewer |
| `Review2_Solar_and_Shadow/` | Solar, PV and shadow models, validation against PVGIS and Blender |
| `Review3_Digital_Twin/` | Browser digital twin, universal climates and soils, accuracy scorecard |
| `Review4_Control_and_Simulation/` | Six-sensor controller, accuracy and safety tests, water link, Simulink |
| `Review5_Economics_and_Final/` | Economics, Monte Carlo, final report, poster, viva Q&A, proof index |
| `Proof/` | Judge evidence folder (start with `Proof/00_START_HERE.html`) |
| `Paper/` | Research paper and figure scripts |
| `_project_core/` | Design file and data files used by the MATLAB scripts |

Large and temporary files (backups, old zips, the one-minute mechanism video) are not in the repository.

## How to run

```bash
# digital twin (from this folder)
python -m http.server 8765
# then open http://localhost:8765/Review3_Digital_Twin/results/live_twin/SRMC_Digital_Twin.html
# 3D mechanism viewer: open Review1_Design_and_CAD/results/mechanism_3d/SRMC_Mechanism_3D.html in Chrome or Edge

# controller accuracy test (Node)
node Review4_Control_and_Simulation/sensor_controller/eval_accuracy_v2.js
node Review4_Control_and_Simulation/sensor_controller/test_safety.js
node Review4_Control_and_Simulation/sensor_controller/eval_gaps.js
```

MATLAB: `cd` into a review folder's `matlab/` and run `srmc_master()`, `srmc_sensitivity()`, `srmc_sc_crosscheck()`, `structural_check()`.

---

# Original folder guide

# Agrovoltaic Canopy for Protection and Sustainable Farming: review folders

Fully computer-based study of a six-sensor agrovoltaic canopy (pyranometer, PAR, DHT11, soil moisture, rain sensor tilt the panels to optimise crop light and electricity; a gutter harvests rain). It is a wire-driven canopy (SS316 wire-rope catenary, panels that tilt or lie flat for rain harvesting), simulated for the TCE ground, Madurai, with the electricity sold to a nearby industry and a monthly income for the farmer.

## Review schedule

| # | Review | Show this | Planned date | Done |
|---|---|---|---|---|
| 1 | Design and CAD | `Review1_Design_and_CAD/ppt/Review1_Design_and_CAD.pptx` | ______ | [ ] |
| 2 | Solar and shadow | `Review2_Solar_and_Shadow/ppt/Review2_Solar_and_Shadow.pptx` | ______ | [ ] |
| 3 | Digital twin | `Review3_Digital_Twin/ppt/Review3_Digital_Twin.pptx` | ______ | [ ] |
| 4 | Control and simulation | `Review4_Control_and_Simulation/ppt/Review4_Control_and_Simulation.pptx` | ______ | [ ] |
| 5 | Economics and final | `Review5_Economics_and_Final/ppt/Review5_Economics_and_Final.pptx` | ______ | [ ] |

Each folder holds: `ppt/` (the deck, speaker notes inside), `results/` (figures, tables, logs, drawings, renders), `documents/` (reports and write-ups), `code_reference/` (read-only copies of the key scripts) and a `README.md` (what was done, what to say, how to reproduce).

## Review 0 (prototype sensors + MATLAB demo)

`Review0_Prototype_Demo/` : ESP8266/ESP32 firmware, MATLAB live dashboard with virtual pyranometer and PAR, 16 logic tests, 18-slide deck, supervisor one-pager and a morning checklist. Start with its README.

## Shared work area

`_project_core/` contains all working code and the master evidence (engine, MATLAB, design file, data, Blender scenes, tools, the live twin). The review folders were made by copying finished results from it. If you rerun anything, run it inside `_project_core` and re-copy.

## One rule for every review

Say clearly: this is a **simulation study**; prices and the farmer share are **assumptions**; the models were validated against PVGIS and Blender ray tracing, **not against field measurements**.

## Order to present (suggested)

1. Design and CAD  ->  2. Solar and shadow  ->  3. Digital twin  ->  4. Control and simulation  ->  5. Economics and final (report, poster, viva Q&A)


## Proof folder

`Proof/` holds a copy of every file a judge may ask for, a Q and A with the file that answers each question (`Proof/00_START_HERE.html`), the dataset sources (`01_Data_and_Sources/DATASET_SOURCES.md`) and an evidence-status table (real, validated, simulated or assumed). Old backups and scratch files are in `_archive/`.

## Update 2026-10-25: six-sensor controller

- Title: **Agrovoltaic Canopy for Protection and Sustainable Farming**. Main idea: six sensors decide the panel tilt; the goal is to optimise crop light AND electricity.
- Code, test and results: `Review4_Control_and_Simulation/sensor_controller/` (controller, year-long accuracy test, cross-check, twin patch). Year-long test with noisy sensors (864 cases): 99.6 % of the best possible combined score (50 % electricity + 50 % crop light value); electricity 82 % and crop light 98 % of the best. Monthly plan 98.8 %, fixed 45 deg 91.2 %. MATLAB and the web twin make identical decisions (40 of 40).
- The final live twin is `Review3_Digital_Twin/results/live_twin/SRMC_Digital_Twin.html` (six-sensor controller ON by default). Serve it with `python -m http.server 8765` in this folder.
- `_project_core/` was restored with only the design file and data files so the MATLAB scripts run (they read `../_project_core/design` and `../_project_core/data`).
- Hardware after the strength check: 10 kN winch, 6 mm SS316 drive wire, M24 turnbuckles, bigger anchors (see Review1 documents).
