# Where every input came from

| Input | Source | Real, typical or assumed | File |
|---|---|---|---|
| Weather: temperature, rain, rain days, clearness index, humidity, wind (monthly) | NASA POWER climatology API, community AG, for 9.88 N, 78.08 E, elevation 219 m | **Real dataset** (monthly means; rain days derived) | climates.json, tce_climate_monthly.csv |
| Sunshine reference for validation | PVGIS (EC Joint Research Centre), ERA5 radiation database, 2005 to 2023, same site | **Real dataset** | pvgis_PVGIS-ERA5.json, 03_Solar_Generation/pv_validation.txt |
| Sun position | astronomical equations (declination, hour angle) | physics | engine (Review3 code_reference/srmc_engine.js) |
| Campus buildings and roads (3D scene) | OpenStreetMap contributors (ODbL) footprints for TCE | **Real data** (visual only) | embedded in the twin |
| Soil: field capacity, wilting point, infiltration, pH, organic carbon, drainage | 9-soil library of typical class values (red sandy loam = Alfisol is the soil common around Madurai) | **Typical values, NOT a laboratory test of the TCE ground** | soils.json, soil_library.csv |
| Crops: light limits, Kc, root depth, depletion fraction p, yield response Ky, yield, price, cost, season | 24-crop library of typical values (FAO-56 and FAO-33 style coefficients) | **Typical values; prices are assumptions** | crops.json, crop_library.csv |
| Module efficiency 21 %, system loss 14 % | typical monocrystalline module and Huld default | typical | engine DEFAULTS |
| Tariff INR 3/kWh, farmer share 30 %, capex INR 60,000/kWp | project assumptions; grid tariff comparison from Mercom India (Tamil Nadu industrial charge INR 7.50/kWh FY 2026) and SECI auction reports | **Assumptions** (sensitivity and Monte Carlo in 03_Solar_Generation/economics_tables) | T5, T7, T8, lcoe_table.csv |
| Sensor readings in the twin, Simulink and the accuracy tests | calculated from the climate data and the shadow and PV physics, plus assumed sensor noise (pyranometer 5 %, PAR 5 %, DHT11 +-2 C / +-5 % RH, soil +-3 %) | **Simulated** | 05_Controller_and_Accuracy |
| Real sensor readings | Review 0 ESP board: DHT11, soil moisture, rain (see review0_prototype/test_results.md); pyranometer, PAR and wind are not measured yet | **Real, partial** | 06_Hardware_and_Sensors |

## What to do to replace the typical values with measurements

1. Soil: send a sample of the TCE ground to a soil testing laboratory (texture, field capacity, wilting point, pH, organic carbon) and edit the soil row in soils.json; the twin and MATLAB read the same file.
2. Weather: log a year with the six-sensor logger (06_Hardware_and_Sensors/data_logging) and compare with NASA POWER and PVGIS; replace the monthly clearness index if they differ.
3. Crops: replace the prices and costs with local market quotes; yield curves with local trial data.
4. Structure: replace the indicative rope and bearing capacities with supplier certificates.
