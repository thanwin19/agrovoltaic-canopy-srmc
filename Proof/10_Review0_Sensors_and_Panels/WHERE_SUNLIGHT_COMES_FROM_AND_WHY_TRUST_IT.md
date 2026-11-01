# Where the sunlight comes from, and why you can trust the MATLAB dashboard

## 1. Where does the sunlight number come from?

Nobody measured it. The dashboard **calculates** it, and the "sensor" (Apogee SP-110) is a software stand-in that holds that number or the number you type:

1. **Where the sun is:** standard astronomy (declination and hour angle) for the TCE site, 9.88 N, 78.08 E, for the day and hour on the sliders.
2. **How much sun reaches the top of the air:** solar constant 1361 W/m2, corrected for the Earth-sun distance of that day.
3. **How much gets through the sky:** multiplied by a **clearness index kt**. The dashboard skies are Clear 0.62, Hazy 0.50, Partly cloudy 0.36, Overcast 0.18. The Clear value is set from the real **NASA POWER April average kt = 0.60** for the site.
4. **Direct and diffuse light:** split with the Erbs model.
5. **PAR (plant light):** 45 % of the sunlight, 4.57 umol per joule (so PAR = 2.06 x sunlight).
6. **Typed by you:** if you move the pyranometer or PAR slider, the controller uses exactly your number.

So: sunlight is a physics model fed with real climate data. Real measured sunlight (a real SP-110 on the roof) does not exist yet.

## 2. Datasets downloaded as proof (all in this folder, `sunlight_datasets/`, downloaded 2026-11-01)

| File | What it is | Source |
|---|---|---|
| NASA_POWER_hourly_2023-04-15_LST_TCE.json | hourly all-sky and clear-sky sunlight, PAR, temperature, humidity, wind for 15 Apr 2023 at TCE | NASA POWER API (power.larc.nasa.gov), community AG, units MJ/m2/hour |
| NASA_POWER_monthly_climatology_TCE.json | monthly mean sunlight, clearness index, temperature, humidity, wind, rain | NASA POWER climatology API |
| PVGIS_ERA5_hourly_2020_TCE.csv | hourly direct and diffuse sunlight for 2020 | PVGIS (EU Joint Research Centre), ERA5 database |
| PVGIS_monthly_radiation_TCE.csv | monthly sunlight 2005-2020 | PVGIS MRcalc |
| DASHBOARD_model_ghi_day105.csv | what the dashboard model gives for day 105 (15 April) for the four skies | review0_physics.m |

Earlier data files used by the whole project are in `Proof/01_Data_and_Sources/`. The sensor and panel datasheets are in `sensor_datasheets/`.

## 3. How the dashboard compares with those datasets (figure: TRUST_sunlight_model_vs_NASA_PVGIS.png)

15 April, TCE, flat ground:

| Quantity | Dashboard "Clear" | NASA actual day | NASA clear-sky | PVGIS April mean | PVGIS clearest April-2020 day |
|---|---|---|---|---|---|
| Daily sunlight (Wh/m2) | 6502 | 6539 | 7144 | 6337 | 7544 |
| Noon peak (W/m2) | 837 | 897 | 986 | - | 1043 |

- The dashboard "Clear" day gives the same daily energy as the real **average** April day: within 0.6 % of NASA's actual day and 2.6 % above PVGIS's April mean.
- It is **not a perfectly cloudless sky**. A truly clear day gives 15-25 % more at noon. Say "Clear = a typical clear April day", not "cloudless".
- Shape and timing agree (RMSE 78 W/m2 against NASA's actual day, 104 W/m2 against its clear-sky curve).
- **PAR share:** NASA POWER gives PAR = 0.444 of total sunlight; the dashboard uses 0.45.

Other checks already in the project: yearly electricity against PVGIS +5.0 % (`Proof/03_Solar_Generation/pv_validation.txt`); shadow model against Blender 3-D ray tracing, mean difference 0.010 in lit fraction (`shading_validation.txt`); the web twin and MATLAB give identical results (`crosscheck_js_vs_matlab.txt`); Review 0 tests pass (`Review0_Prototype_Demo/results/test_results.md`).

## 4. Why you can trust it, in one paragraph for the judges

"The sunlight in the dashboard is calculated from the sun's position and a clearness index taken from NASA POWER for our site. We checked it against two independent datasets, NASA POWER and the EU PVGIS: the daily energy agrees within about 1 to 3 percent and the share of plant light agrees (0.44 against 0.45). The sensors are software models of real devices, set from their published datasheets, and every one can be set by hand. We have no field measurement yet, so this is a validated simulation, not a field result."

## 5. Limits (say them, they protect you)

- NASA POWER and PVGIS are satellite and reanalysis products, not a pyranometer on the TCE roof. This is a check, not a field validation.
- One day (15 April) was compared hour by hour; the year is checked monthly through PVGIS (+5 %), with the largest monthly errors (8-11 %) in June to August.
- Clear sky in the dashboard is a typical April clear day, below a perfectly cloudless sky.
- Sensor readings are generated or typed. Real SP-110 data needs the real sensor and logging, which is the next step.

## 6. Month-by-month check (added later)

Full-year hourly NASA POWER data for 2023 (`NASA_POWER_hourly_2023_full_year_TCE.json`) and PVGIS-ERA5 hourly 2020 against the model's mean day of every month (`MONTHLY_sunlight_model_vs_NASA_PVGIS.csv`, figure `TRUST_monthly_sunlight_model_vs_NASA_PVGIS.png`):

- vs NASA POWER 2023: year average +2.0 %, monthly -6.9 % to +9.9 %, hourly shape RMSE 40-91 W/m2 (mean 67).
- vs PVGIS 2020: +7.9 % on average; +16 to +26 % in June to September and December. One reanalysis year differs from the long-term climate (the multi-year PVGIS comparison gave +5.0 %).
- The model is a good *typical* year, not a prediction of one year.
- Real hourly wind at TCE in 2023 never exceeded 10.9 m/s (hourly means at 10 m, no gusts): the 15 m/s storm stow never triggered in that data.
- The twin can **replay 15 real days** of this data (the 15th of each month, the rainiest, windiest and sunniest day) in its sensor panel (`NASA_POWER_replay_days_for_twin.json`).
