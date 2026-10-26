# Judge questions and where the proof is

**Q. Where did you take the readings? Is this real sensor data?**

A. In the twin, Simulink and the accuracy tests the sensor values are simulated from NASA POWER climate data and the shadow and PV physics, with an assumed noise level. Only the Review 0 ESP board gave real DHT11, soil and rain readings. A logging pipeline (ESP32 firmware, logger, weekly self-scoring) is ready for the six real sensors.

Proof: `01_Data_and_Sources/DATASET_SOURCES.md; 06_Hardware_and_Sensors`

**Q. Which weather dataset did you use?**

A. NASA POWER climatology (community AG) for 9.88 N, 78.08 E, monthly means, checked against PVGIS ERA5 2005 to 2023 for the same site.

Proof: `01_Data_and_Sources/climates.json, tce_climate_monthly.csv, pvgis_PVGIS-ERA5.json`

**Q. Is your soil data accurate? What soil is it?**

A. Red sandy loam (Alfisol), the soil common around Madurai, from a 9-soil library of typical class values. It is NOT a laboratory test of the TCE ground. The twin lets you pick any of the 9 soils and shows how results change; a soil test replaces the values in soils.json.

Proof: `01_Data_and_Sources/soil_library.csv; 04_Crop_Water_Soil/universal_tables/T3_universal_soils.csv`

**Q. What are the wire lengths, heights and weights?**

A. Pivot height 5.58 m, lowest panel edge 4.5 m at 60 degrees, columns 6.73 m on a 5 m grid, carrier rope SS316 16 mm about 153 m (149 kg), stays 20 mm about 223 m, drive wire 6 mm about 33 m, 10 kN winch. SS316 7x19 weighs 0.975 kg/m at 16 mm.

Proof: `02_Geometry_Wire_Heights/geometry_summary.md; cad_drawings; 8panel_hardware_pack`

**Q. How much electricity does it generate?**

A. The 25 m x 25 m demonstration unit (131 kWp) gives about 149 MWh a year; 238 kWh per m2 of panel, 1,134 kWh per kWp. The 8-module set (4.4 kWp) gives about 4,990 kWh a year. The model agrees with PVGIS within 5 %.

Proof: `03_Solar_Generation/solar_generation_summary.md, solar_generation_monthly.csv`

**Q. How did you improve accuracy by co-optimising crop and solar?**

A. Each hour the controller scores every angle (50 % electricity + 50 % crop light) and picks the best, corrected by the PAR sensor and adjusted for plant stress. It reaches 99.6 % of the best possible combined score with a 4.8 degree tilt error (monthly plan 9.5, fixed 45 degrees 16.3), keeps 82 % of the PV-only electricity and 93 % of the crop-only light.

Proof: `05_Controller_and_Accuracy/COOPTIMISATION_SUMMARY.md, T11_accuracy_v2.csv, fig_accuracy_both_goals.png`

**Q. Was the accuracy checked by something independent?**

A. The solar and shadow parts yes (PVGIS and Blender). The controller score is its own objective, so it was also checked in MATLAB (same decisions) and converted into yield and rupees through the crop and economics model.

Proof: `05_Controller_and_Accuracy/accuracy_matlab.json, T14_yield_and_money.csv`

**Q. What happens if a sensor fails?**

A. The controller ignores an implausible PAR reading, a rain sensor stuck wet in dry sunny air, and a soil probe that is missing, out of range, jumping or stuck; it limits how often the panels move and counts motor wear. All tested.

Proof: `05_Controller_and_Accuracy/safety_tests.md, T13_fault_test.csv`

**Q. How does the soil probe save water?**

A. The probe decides when irrigation runs: 5372 m3/ha/yr against 5641 m3 for a timer (4.8 % saved) and no water-stress days. A dead or stuck probe falls back to the timer schedule.

Proof: `04_Crop_Water_Soil/T16_irrigation_probe_vs_timer.csv, fig_irrigation_probe_vs_timer.png`

**Q. Can the structure take the wind?**

A. Screening check at 39 m/s (140 km/h) with the panels held: tube 0.76, rope 0.37, stay 0.30 of their limits. First design (12.5 m bays) failed and was changed. Not a certified design; the tube reaches its limit near 145 km/h. The anemometer stows the panels at 15 m/s.

Proof: `02_Geometry_Wire_Heights/structure, 8panel_hardware_pack/SRMC_Component_Strength_Table.docx`

**Q. Where is the live demonstration?**

A. Open 07_Live_Twin_and_Screenshots/SRMC_Digital_Twin.html in Chrome (works offline). Screenshots of every tab are in the screens folder.

Proof: `07_Live_Twin_and_Screenshots`

**Q. What is simulated and what is real?**

A. See the status table.

Proof: `00_EVIDENCE_STATUS.md`
