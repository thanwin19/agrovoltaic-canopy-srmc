# Proof index (Agrovoltaic Canopy for Protection and Sustainable Farming): every claim -> evidence file -> how to reproduce

Evidence paths are inside `reviews/evidence/`. Run commands from the `srmc-twin` folder. "Files present" is checked automatically when this file is generated.

| # | Review | Claim | Evidence | Reproduce | Files present |
|---|---|---|---|---|---|
| 1 | R3 | Geometry comes from one design file; pivot height 5.58 m derived from 4.5 m clearance | design/design.json | `node tools/export_blender.js feasible 105 9.5 0` | yes |
| 2 | R3 | 12.5 m bays fail structural screening (rope 16x, stay 40x, 60 mm tube 30x over) | evidence/logs/structural_report.txt; tables/T4_structural.csv; figures/val_structural_utilisation.png | `MATLAB: cd matlab; structural_check()` | yes |
| 3 | R3 | Checked preset (5 m rope grid, 114.3x4 tube, sag L/12, 20 mm stays) passes: 0.94/0.82/0.71/0.05 | evidence/logs/structural_report.txt | `MATLAB: structural_check()` | yes |
| 4 | R3 | AutoCAD drawings: plan, elevation, section, wire drive | evidence/cad/SRMC_feasible_*.dxf, *.png | `python tools/make_dxf.py` | yes |
| 5 | R3 | Bill of materials, 22 items | evidence/cad/SRMC_feasible_BOM.csv | `python tools/make_dxf.py` | yes |
| 6 | R3 | Ray-traced renders of the design | evidence/renders/hero.png, under.png, aerial.png, top.png, rain.png | `bash tools/render_all.sh feasible (Blender at D:/blender.exe)` | yes |
| 7 | R4 | Sun path and solar geometry for 9.88 N | evidence/figures/fig1_sunpath.png | `MATLAB: srmc_run()` | yes |
| 8 | R4 | Annual GHI 2,033 vs PVGIS 1,933 kWh/m2 (+5.2 %, dataset difference) | evidence/logs/pv_validation.txt; pvgis_PVGIS-ERA5.json | `node tools/validate_pv.js` | yes |
| 9 | R4 | PV energy within +5.0 % of PVGIS (Huld model + IAM) | evidence/figures/val_pv_vs_pvgis.png; logs/pv_validation.csv | `node tools/validate_pv.js` | yes |
| 10 | R4 | Shading model vs Blender Cycles: mean abs. difference 0.010, 96 % within 0.10 | evidence/logs/shading_validation.txt; shade_results.json; figures/val_shading_scatter.png | `node tools/shade_ref.js; D:/blender.exe -b -P blender/validate_shading.py` | yes |
| 11 | R4 | Zone light by month 12-41 % (mean 34 %) | evidence/figures/fig2_zone_light.png | `MATLAB: srmc_run()` | yes |
| 12 | R4 | Tilt trade-off: electricity vs crop light | evidence/figures/fig3_tilt_tradeoff.png | `MATLAB: srmc_run()` | yes |
| 13 | R5 | Architecture: one source of truth feeding twin, MATLAB, CAD, Blender | evidence/figures/architecture.png | `python tools/make_evidence.py` | yes |
| 14 | R5 | Running twin with sensors, controller, water, crops, economics | evidence/screens/twin_*.jpg; SRMC_Digital_Twin.html | `python -m http.server 8765 (open http://localhost:8765/SRMC_Digital_Twin.html)` | yes |
| 15 | R5 | JavaScript twin and MATLAB engine give identical results (0.0000 % on 22 quantities) | evidence/logs/crosscheck_js_vs_matlab.txt | `MATLAB srmc_run(); node tools/crosscheck.js` | yes |
| 16 | R5 | Universal: 7 climates, 9 soils | evidence/tables/T2_universal_climates.csv; T3_universal_soils.csv; figures/fig10_universal_climates.png; figures/fig11_universal_soils.png | `MATLAB: srmc_master()` | yes |
| 17 | R5 | Water balance: harvest ~4,650 m3, demand ~4,930 m3, ~94 % rain-fed | evidence/figures/fig4_water_balance.png; screens/twin_water_rain.jpg; tables/summary.md | `MATLAB: srmc_master()` | yes |
| 18 | R6 | Controller schedule: angle chosen each hour of each month | evidence/figures/fig8_controller_schedule.png | `MATLAB: srmc_master()` | yes |
| 19 | R6 | Simulink controller model | evidence/simulink/srmc_controller.slx; srmc_controller_diagram.png | `MATLAB: build_simulink_controller()` | yes |
| 20 | R6 | Simulink test day: 15 deg night, ~24 deg morning, 3 deg rain, 90 deg stow | evidence/simulink/controller_log.csv; srmc_controller_day.png | `MATLAB: build_simulink_controller()` | yes |
| 21 | R6 | Controller vs fixed designs (total 55.0 vs 52.5 vs 68.2 INR lakh/ha) | evidence/tables/T1_controller_comparison.csv; figures/fig6_controller_comparison.png | `MATLAB: srmc_master()` | yes |
| 22 | R6 | Energy/crop weight sweep | evidence/tables/T1b_weight_sweep.csv; figures/fig7_pareto.png | `MATLAB: srmc_master()` | yes |
| 23 | R6 | Weather-year scenarios (rain -30 %, +20 %; sun +-5 %) | evidence/tables/T6_physics_scenarios.csv; figures/fig15_weather_scenarios.png | `MATLAB: srmc_sensitivity()` | yes |
| 24 | R6 | PV-only design earns more rupees than the controller (stated honestly) | evidence/tables/T1_controller_comparison.csv | `MATLAB: srmc_master()` | yes |
| 25 | R7 | Farmer monthly income (solar share monthly + crops at harvest) | evidence/figures/fig9_farmer_income.png; tables/summary.md | `MATLAB: srmc_master()` | yes |
| 26 | R7 | One-at-a-time sensitivity (farmer share and tariff dominate) | evidence/tables/T5_tornado.csv; figures/fig12_tornado_farmer_income.png; figures/fig13_tornado_payback.png | `MATLAB: srmc_sensitivity()` | yes |
| 27 | R7 | Monte Carlo (20,000 draws): farmer income P5/P50/P95 = 1.41/2.12/2.99 lakh per month | evidence/figures/fig14_montecarlo.png; tables/T7_montecarlo_rank_correlation.csv; tables/sensitivity_summary.md | `MATLAB: srmc_sensitivity()` | yes |
| 28 | R7 | Investor payback is the weak link: 15 years needs ~INR 6.2/kWh at 30 % share | evidence/tables/T8_breakeven_tariff.csv | `MATLAB: srmc_sensitivity()` | yes |
| 29 | R7 | Every price in the economics is an assumption | deck R7 slide 3; report section 7 | `n/a` | yes |
| 30 | R3 | Motor-to-panel mechanism animation (motor, drum, drive wire, lever arm, pivot tube) | evidence/renders/mechanism_tilt.gif; twin tab Mechanism | `python tools/make_mechanism_gif.py` | yes |
| 31 | R3 | Close-up of one panel: wire slides d, lever arm swings theta, panel tilts theta | evidence/renders/mechanism_closeup.gif; twin tab Mechanism step A | `python tools/make_closeup_gif.py` | yes |
| 32 | R3 | Guide pulley: with vs without (capstan friction 2.6x vs 1.02x) | evidence/renders/guide_pulley.gif; twin tab Mechanism step C | `python tools/make_pulley_gif.py` | yes |
| 33 | All | Tool versions and file integrity | evidence/logs/tool_versions.txt; SHA256_manifest.csv | `python tools/make_evidence.py` | yes |
| 34 | R6 | Six-sensor controller: year-long test with noisy sensors, 99.6 % of the best combined score (electricity 82 %, crop light 98 %) | Review4_Control_and_Simulation/results/tables/T9_sensor_controller_accuracy.csv; results/figures/fig_accuracy_both_goals.png | `node sensor_controller/eval_sensor_controller.js` | yes |
| 35 | R6 | MATLAB and the web twin make the same decisions (40 of 40 random sensor states) | Review4_Control_and_Simulation/results/crosscheck_sensor_controller_matlab_vs_js.txt | `node sensor_controller/make_crosscheck_cases.js; MATLAB: srmc_sc_crosscheck` | yes |
| 36 | R6 | Simulink six-sensor controller on a test day (cloud, rain, dry soil) | Review4_Control_and_Simulation/results/simulink/srmc_sensor_controller_model.slx; sensor_controller_day.png; sensor_controller_log.csv | `MATLAB: build_simulink_sensor_controller` | yes |
| 37 | R6 | Accuracy repeated in MATLAB (142 cases, same readings): 99.5 % of the best combined score, tilt error 3.4 deg | Review4_Control_and_Simulation/results/tables/T15_accuracy_matlab.csv; results/figures/fig_matlab_accuracy.png | `node sensor_controller/make_accuracy_cases.js; MATLAB: srmc_sc_accuracy` | yes |
| 38 | R6 | Accuracy vs noise, faulty PAR sensor, and yield and rupees (v1 vs v2) | Review4_Control_and_Simulation/results/tables/T12_noise_sweep.csv; T13_fault_test.csv; T14_yield_and_money.csv; results/figures/fig_noise_fault.png; fig_yield_money.png | `node sensor_controller/eval_accuracy_v2.js` | yes |
| 39 | R0 | Real-data logging: six-sensor ESP32 firmware, logger, fake-week rehearsal and weekly self-scoring | Review0_Prototype_Demo/data_logging/README.md; Review0_Prototype_Demo/data_logging/score_week_fake/week_report.html | `data_logging/run_fake_week.bat (rehearsal); run_real_week.bat (real)` | yes |
| 40 | R3 | Mechanism animations and drawings regenerated for the final design (offset lever arm, 6 mm wire, anemometer stow) | Review1_Design_and_CAD/results/mechanism/mechanism_closeup.gif; Review1_Design_and_CAD/results/mechanism/mechanism_tilt.gif; Review1_Design_and_CAD/results/cad_drawings/SRMC_feasible_elevation.dxf | `python code_reference/make_mech_gifs.py; derive_final_dxf.py; make_dxf_final.py` | yes |
| 41 | R6 | Controller safety: sensor-failure fallbacks (rain, soil), move limits, motor wear count (8 tests pass) | Review4_Control_and_Simulation/results/safety_tests.md | `node sensor_controller/test_safety.js` | check |
| 42 | R5 | Water link: soil probe decides irrigation; 4.8 % water saved and no stress days against a timer; probe faults and fallback | Review4_Control_and_Simulation/results/tables/T16_irrigation_probe_vs_timer.csv; results/figures/fig_irrigation_probe_vs_timer.png | `node sensor_controller/irrigation_study.js` | yes |
| 43 | All | Proof folder with data sources, evidence status and judge Q and A | Proof/00_START_HERE.html | `python Review5_Economics_and_Final/code_reference/build_proof.py` | yes |
| 44 | R5 | Digital twin runs the six-sensor controller by default (sensor card, sliders, decision trace) | Review3_Digital_Twin/results/live_twin/SRMC_Digital_Twin.html | `python -m http.server 8765 (open the twin)` | yes |
| 45 | R3 | Strength of wire, joints, poles and motor; weak items changed (winch 10 kN, 6 mm drive wire, M24 turnbuckles, anchors) | Review1_Design_and_CAD/documents/SRMC_Component_Strength_Table.docx; results/structure/wind_sweep_feasible.png | `python code_reference/build_hardware_docs.py` | yes |
| 46 | R3 | 8-panel set (4.4 kWp): weights, installation steps and indicative cost | Review1_Design_and_CAD/documents/SRMC_8Panel_Guide_and_Cost.docx; 8panel_BOM.csv | `python code_reference/build_hardware_docs.py` | yes |
| 47 | R7 | Cost of electricity about INR 6 to 7 per kWh vs tariffs (Mercom, SECI) | Review5_Economics_and_Final/results/figures/lcoe_vs_tariff.png; results/tables/lcoe_table.csv | `assumption-based (capex INR 60,000/kWp, 25 years)` | yes |
