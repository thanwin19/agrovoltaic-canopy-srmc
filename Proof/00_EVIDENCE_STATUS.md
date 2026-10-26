# Evidence status: what is proven, how, and how strongly

| Claim | Strength | Evidence |
|---|---|---|
| PV energy model agrees with PVGIS | **Validated against an independent tool**: +5.0 % per year (sunshine data differ by +5.2 %) | 03_Solar_Generation/pv_validation.txt, figures/val_pv_vs_pvgis.png |
| Shadow and crop-light model | **Validated against Blender Cycles ray tracing**: mean difference 0.010, 96 % of 80 cases within 0.10 | 03_Solar_Generation/shading_validation.txt |
| Twin (JavaScript) = MATLAB engine | **Verified**: 0.0000 % difference on 22 outputs | 03_Solar_Generation/crosscheck_js_vs_matlab.txt |
| Sensor controller decisions: MATLAB = twin | **Verified**: 40 of 40 identical; 140 of 142 identical angles in the accuracy test | 05_Controller_and_Accuracy/crosscheck_sc_matlab_vs_js.txt, accuracy_matlab.json |
| Controller reaches 99.6 % of the best combined score | **Simulation result** (noisy simulated sensors); the score is the controller's own objective | 05_Controller_and_Accuracy/T11_accuracy_v2.csv |
| Structure passes wind check at 140 km/h | **Screening calculation** (IS 875-3 formulas), not certified | 02_Geometry_Wire_Heights/structure |
| Crop yield, water balance, irrigation saving | **Model results** from typical crop and soil values, no field data | 04_Crop_Water_Soil |
| Farmer income, payback, electricity cost | **Assumption-based** (prices assumed) | 03_Solar_Generation/economics_tables |
| Sensor fallbacks, motion limits, wear count | **Tested in simulation** (8 tests) | 05_Controller_and_Accuracy/safety_tests.md |
| ESP32 six-sensor firmware and logger | **Written, not tested on hardware**; rehearsed on a fake week | 06_Hardware_and_Sensors/data_logging |
| Real DHT11, soil, rain readings | **Real** (Review 0 board) | 06_Hardware_and_Sensors/review0_prototype |
