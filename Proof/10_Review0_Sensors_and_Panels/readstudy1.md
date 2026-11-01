# readstudy1: Review 0 study guide (concepts, units, worked numbers)

Project: **Agrovoltaic Canopy for Protection and Sustainable Farming**, TCE Madurai (9.88 N, 78.08 E).
Read this once the night before. Sections 1-2 give the idea, 3 the units, 4-8 the science, 9 the sensors, 10 the controller, 11 the results, 12 the questions.

---

## 1. The idea in five lines

1. Crops and solar panels both need the sun. A panel at a fixed angle shades the crop too much or wastes electricity.
2. Our panels sit about 4.5 m above the crops and **tilt**. The tilt angle is chosen by a controller from six sensors.
3. The controller picks the angle that gives the best mix of electricity and crop light (half and half, adjustable).
4. Rain: panels go flat (3 deg) so the roof drains into a tank. Storm wind: panels turn edge-on (90 deg).
5. Review 0 proves this on the computer: six sensors are **simulated after real devices**, shown in a MATLAB dashboard, and every sensor can be set by hand.

**Honest status:** simulation. The sensor readings are calculated or typed, not measured. No field trial yet.

---

## 2. Words you must be able to explain

| Word | Plain meaning |
|---|---|
| Agrivoltaics (agrovoltaics) | farming and solar electricity on the same land |
| Tilt angle | how steeply the panel is inclined; 0 deg = flat, 90 deg = vertical (edge-on) |
| Co-optimisation | improving two goals together (electricity and crop light) instead of one |
| Controller | the program that reads the sensors and decides the angle |
| Digital twin | the computer copy of the whole system (our single HTML twin) |
| Simulation | a model that calculates what would happen; no real hardware |
| Pyranometer | sensor for total sunlight |
| PAR sensor | sensor for the light plants use (photosynthetically active radiation) |
| DHT11 | cheap chip that reads air temperature and humidity |
| Soil moisture sensor | reads how wet the soil is |
| Anemometer | wind speed sensor |
| MPPT | maximum power point tracking: keeps a panel at the voltage where it gives most power |
| Datasheet | the manufacturer's document with the device's range, accuracy and output |
| Validation | checking the model against independent data |

---

## 3. Units explained (the table to learn)

| Unit | Stands for | What it measures | Example in our project |
|---|---|---|---|
| deg (degree) | angle | panel tilt, sun height | 43 deg tilt at clear noon |
| W | watt | power (rate of energy) | one panel at best point: about 550 W |
| Wp | watt-peak | panel power under standard test sunlight | 550 Wp per panel |
| kWp | kilowatt-peak | 1000 Wp | 8 x 550 Wp = 4.4 kWp |
| Wh, kWh | watt-hour, kilowatt-hour | energy = power x time | 1 kW for 1 hour = 1 kWh |
| W/m2 | watt per square metre | sunlight power on a surface | noon sun about 800-1000 W/m2 |
| Wh/m2/day | watt-hour per m2 per day | sunlight energy in a day | 15 April: about 6500 Wh/m2/day = 6.5 kWh/m2/day |
| MJ/m2 | megajoule per m2 | energy (NASA POWER units) | 1 MJ = 0.2778 kWh; 1 MJ/m2 per hour = 277.8 W/m2 |
| umol/m2/s | micromole (of photons) per m2 per second | PAR: number of photons plants can use | full sun about 1700-2000 |
| V, mV | volt, millivolt | sensor output signal | SP-110 gives 0.20 mV per W/m2 |
| A | ampere | current | module Imp 13.45 A |
| deg C | degree Celsius | temperature | air 33 deg C |
| % RH | percent relative humidity | how full of water vapour the air is | 48 % RH |
| kPa | kilopascal | pressure; here the air's thirst (VPD) | VPD 2.7 kPa = dry air |
| % (soil) | percent water | soil moisture after calibration | pump on below 35 %, off above 55 % |
| m/s | metre per second | wind speed (x 3.6 = km/h) | 15 m/s = 54 km/h storm limit |
| m3, L | cubic metre, litre | water volume (1 m3 = 1000 L) | rain harvested into the tank |
| INR | Indian rupee | cost | sensing kit INR 13,100 to 67,600 |
| kt | clearness index (no unit, 0-1) | fraction of top-of-atmosphere sunlight reaching the ground | Clear sky 0.62 |
| +- % | plus or minus percent | accuracy of a sensor | pyranometer +-5 % |

---

## 4. Sunlight: where it comes from and how we calculate it

**Terms.** GHI = global horizontal irradiance (all sunlight on flat ground, W/m2). DNI = direct beam. DHI = diffuse (scattered) light. GHI = DHI + DNI x cos(zenith angle).

**Steps used in the dashboard and twin** (nobody measured the sunlight):
1. **Sun position** from astronomy: declination = 23.45 sin(360/365 x (284 + day)); hour angle = 15 deg x (solar hour - 12); the sun's height follows from latitude, declination and hour angle.
2. **Top of the air:** solar constant 1361 W/m2, corrected for the Earth-sun distance of that day.
3. **Through the sky:** multiply by the **clearness index kt** (Clear 0.62, Hazy 0.50, Partly cloudy 0.36, Overcast 0.18). Monthly kt for TCE comes from **NASA POWER** (April about 0.60).
4. **Direct and diffuse split:** Erbs model.
5. **PAR = 0.45 x sunlight x 4.57 umol per joule = about 2.06 x sunlight (in W/m2 giving umol/m2/s).**
   Worked: 837 W/m2 x 2.057 = about 1722 umol/m2/s (the number on the dashboard).

**Checks against real data** (satellite/reanalysis, not a roof sensor):
- 15 April: model 6502 Wh/m2/day, NASA POWER actual day 6539, PVGIS April mean 6337.
- All months of 2023: model vs NASA POWER year average +2.0 %, monthly -6.9 % to +9.9 %.
- PVGIS 2020 single year: model +7.9 %, and +16 to +26 % in Jun-Sep and Dec (one year differs from the long-term climate; multi-year PVGIS gave +5.0 %).
- PAR share of sunlight: NASA 0.444, our value 0.45.
- Our "Clear" is a typical clear April day (noon 837 W/m2), not perfectly cloudless (NASA clear-sky noon 986).

**Data sources:** NASA POWER (power.larc.nasa.gov), PVGIS (EU Joint Research Centre). Files are in Proof/10_Review0_Sensors_and_Panels/sunlight_datasets/.

---

## 5. Plants, air and water

- **PAR:** plants use only wavelengths 400-700 nm. About 45 % of sunlight is PAR.
- **LSR (light share):** under-canopy PAR / above-canopy PAR. More panel shade lowers it.
- **Crop-light score (0-1):** how well each crop zone gets the light it needs (1 = enough for all four zones).
- **VPD (vapour pressure deficit):** how thirsty the air is. Saturation pressure es = 0.6108 exp(17.27 T / (T + 237.3)) kPa; VPD = es x (1 - RH/100).
  Worked: T = 33 deg C, RH = 48 % gives es = 5.1 kPa and VPD about 2.6 kPa. Above about 1.6 kPa plants start to be stressed; above 2.5 kPa strongly.
- **Stress:** hot, dry air or dry soil stresses the crop; it then needs less light, so the controller allows more shade.
- **Irrigation rule:** pump on when soil water is below 35 %, off above 55 % (a gap, called hysteresis, so it does not chatter). Water comes from the rain tank.

---

## 6. The solar panel (JinkoSolar Tiger Pro JKM550M-72HL4-V)

| Item | Value |
|---|---|
| Type | monocrystalline silicon |
| Power at test conditions | 550 Wp |
| Vmp, Imp | 40.90 V, 13.45 A (40.90 x 13.45 = 550 W) |
| Voc, Isc | 49.62 V, 14.03 A |
| Efficiency | 21.33 % = 550 W / (2.274 m x 1.134 m x 1000 W/m2) |
| Size, weight | 2274 x 1134 x 35 mm, 28.9 kg |
| Our array | 8 panels (2 rows x 4) = 4.4 kWp |

- **STC (standard test conditions):** 1000 W/m2 sunlight, 25 deg C cell, air mass 1.5. A panel in the field gives less when hot.
- **Voc** = open-circuit voltage (no load). **Isc** = short-circuit current. **Vmp, Imp** = voltage and current at the maximum power point (MPP).
- **I-V curve:** current vs voltage; power = V x I is highest at the "knee" (the red dot on the twin's curve).
- **Cell temperature:** hotter cells make less power. Cell temp = air temp + G x exp(-3.473 - 0.0594 x wind) (Huld model).
- **MPPT (perturb and observe):** the converter nudges the voltage up or down and keeps going in the direction that raises power.
- **kWp vs kW:** kWp is the rating at test conditions; real power now is lower or higher.

---

## 7. The tilt mechanism (how the wire tilts the panels)

- One motor and winch pulls **one steel wire**. Each panel's pivot tube has a short **lever arm** (L = 0.44 m, fixed at a 45 deg offset). The arm tip rides in a **slotted carriage** clamped to the wire.
- The wire stays straight at one height and only slides sideways; the slot lets the tip rise and fall a little as it swings on its arc (about 113 mm over the whole range).
- Wire travel for panel angle theta: **d = L x [sin 45 deg + sin(theta - 45 deg)]**.
  Worked: theta = 15 deg: d = 0.44 x (0.7071 - 0.5) = 0.091 m = 91 mm. theta = 45 deg: d = 0.44 x 0.7071 = 0.311 m. theta = 60 deg: 0.44 x 0.966 = 0.425 m.
- All panels move together by the same angle; the encoder counts every 0.5 deg.
- Angles: tracking range 15-60 deg, rain 3 deg, storm 90 deg, night park 15 deg.

---

## 8. Reading sensor specifications

| Term | Meaning |
|---|---|
| Range | smallest to largest value the sensor can measure |
| Accuracy (+-) | how far a reading may be from the true value |
| Resolution | smallest change it can show (DHT11: 1 deg C) |
| Sensitivity | output per unit input (SP-110: 0.20 mV per W/m2) |
| Non-linearity | how far the response departs from a straight line (<1 % to 1750 W/m2) |
| Drift | slow change over time (<2 % per year, so recalibrate) |
| Response time | how fast it reacts (<1 ms) |
| Cosine error | error when sun is low (+-5 % at 75 deg from overhead) |
| Calibration | adjusting the sensor against a reference (soil probe: dry and wet readings) |
| ADC | analog-to-digital converter: turns a voltage into a number for the board |
| RMSE | root mean square error: typical size of the difference between model and data |

---

## 9. The six sensors (seven readings) and how each works

| # | Reading | Real device simulated | How it works | Datasheet numbers | Signal |
|---|---|---|---|---|---|
| 1 | Sunlight | Apogee SP-110 | silicon photodiode under a diffuser | 0-2000 W/m2, +-5 %, 360-1120 nm | 0.20 mV per W/m2 |
| 2 | Plant light | Apogee SQ-110 | photodiode with a filter that matches plant response | 0-4000 umol/m2/s, +-5 %, 410-655 nm | 0.20 mV per umol |
| 3 | Air temperature | DHT11 | thermistor (resistance changes with temperature) | 0-50 deg C, +-2 deg C | digital word |
| 4 | Humidity | DHT11 (same chip) | capacitor that changes with moisture | 20-90 % RH, +-5 % RH | digital word |
| 5 | Soil moisture | DFRobot SEN0193 v1.2 | capacitive probe (wetter soil raises capacitance) | 2.5 V dry to 1.2 V wet | analog |
| 6 | Rain | YL-83 / FC-37 plate + LM393 | bare tracks conduct when wet; comparator makes a digital level | wet or dry | pin LOW when wet |
| 7 | Wind | Adafruit 1733 | spinning cups, analog output | 0.4 V = 0 m/s, 2.0 V = 32.4 m/s, +-1 m/s | 0.4-2.0 V |

**Worked signals (what the dashboard shows):**
- Pyranometer 837 W/m2 -> 0.20 x 837 = 167 mV.
- Wind 20 m/s -> 0.4 + 1.6 x 20 / 32.4 = 1.39 V (speed = (V - 0.4) / 1.6 x 32.4).
- Soil 48 % -> 2.5 - 1.3 x 0.48 = 1.88 V.

**In the simulation:** the slider is the physical quantity; the dashboard also shows the signal the real device would output. Every sensor can be typed (MANUAL tag) or follow the day/sky model (AUTO tag).
**Datasheets** are downloaded in Proof/10_Review0_Sensors_and_Panels/sensor_datasheets/. The rain sensor has only vendor pages (no official datasheet).

---

## 10. The controller (what it does, in order)

1. **Wind >= 15 m/s:** stow at 90 deg (edge-on, wind passes through).
2. **Rain sensor wet:** 3 deg, rain runs to the gutter and tank.
3. **Night:** park at 15 deg.
4. **Otherwise optimise:** try every angle from 15 to 60 deg in 0.5 deg steps and choose the one with the highest score

   **J(a) = w x PV(a)/PVmax + (1 - w) x Crop(a)/Cropmax**, with w = 0.5 by default (the slider "energy share").
   - PV(a): electricity per m2 of panel at angle a (shading between rows, incidence angle, cell temperature).
   - Crop(a): average light score over four crop zones.
   - Stress lowers the light the crop needs by up to 30 %, so the choice moves toward more shade.
5. **Safety layer:** ignores sensor values that make no sense (for example rain reported in dry bright sun), limits how fast the angle moves, and cross-checks wind with the wire tension.

**Why this is new:** the angle is chosen by sensors to co-optimise crop light and electricity, with plant stress as an input and a safety layer for faulty sensors; every decision is explained in plain words.

---

## 11. Results to remember

**Accuracy** = how close the chosen angle is to the best possible angle on the score J, found by trying every angle. 100 % = as good as the best angle.

| Design | Combined score | Electricity | Crop light | Angle error |
|---|---|---|---|---|
| Fixed 15 deg (max power) | 80.0 % | 99.2 % | 45.2 % | 34.0 deg |
| Sun tracking | 84.0 % | 88.6 % | 64.3 % | 25.0 deg |
| Fixed 45 deg | 91.2 % | 81.0 % | 84.6 % | 16.3 deg |
| Monthly plan, no sensors | 98.8 % | 82.2 % | 96.3 % | 9.5 deg |
| **Our controller (noisy sensors)** | **99.6 %** | 82.1 % | 97.7 % | **4.8 deg** |

- 864 noisy test cases (sensor noise: sunlight and PAR 5 %, DHT11 +-2 deg C and +-5 % RH, soil +-3 %). File: Proof/05_Controller_and_Accuracy/T11_accuracy_v2.csv.
- Review 0 dashboard, one clear April day with datasheet-sized errors: ours 99.4 %, fixed 45 deg 87.0 %, sun tracking 87.5 %.
- Tests: 29 of 29 pass (16 decision/physics + 13 sensor/MPPT). PVGIS yearly electricity +5.0 %. Shadow vs Blender mean difference 0.010.
- Real hourly wind at TCE in 2023 never exceeded 10.9 m/s (10 m, no gusts), so the 15 m/s storm stow never triggered in that year's data.
- Cost if real (estimates): sensing kit INR 67,600 (research-grade) or 13,100 (low-cost); 8 panels about INR 70,000 at INR 16 per Wp.

**Always add:** simulation; accuracy is against the controller's own goal, not crop yield.

---

## 12. Questions a judge may ask, with short answers

1. **What is the problem?** Crops and panels compete for sun; fixed panels give up either crop light or electricity.
2. **What is new?** Sensor-driven angle that co-optimises crop light and electricity, with stress and a safety layer, explained in words.
3. **Are the sensors real?** No. They are software models of real devices (named, datasheets stored). Hardware is next.
4. **Where does the sunlight come from?** Sun position plus a clearness index from NASA POWER, checked against NASA POWER and PVGIS.
5. **Why trust it?** 15 April within 0.6 % of NASA's actual day; all months within 10 % of NASA 2023; PAR share 0.444 vs 0.45. It is a typical year, not a prediction.
6. **What does 99.6 % mean?** The controller's score is 99.6 % of the best possible score over 864 noisy cases.
7. **Why half and half?** It is a slider (w); a farmer can favour crop or electricity.
8. **What is J?** The combined score of electricity and crop light.
9. **What is VPD?** How thirsty the air is; high VPD stresses plants.
10. **What is MPPT?** Keeps the panel at the voltage with the most power.
11. **What is a pyranometer?** Total sunlight sensor; PAR sensor measures only plant-usable light.
12. **Why a wire to tilt all panels?** One motor moves every panel together by the same angle.
13. **Why stow at 90 deg in storm?** Edge-on panels let the wind pass; a flat stow could be safer or not: a wind-tunnel or CFD run is needed.
14. **Why is Clear 837 W/m2 and not 1000?** It is a typical clear April day (kt 0.62), not cloudless.
15. **Which panel?** JinkoSolar Tiger Pro JKM550M-72HL4-V, 8 panels, 4.4 kWp.
16. **What does it cost if real?** About INR 13,100 to 67,600 for the sensing kit (estimates, not quotes).
17. **What are the limits?** Simulation only; readings are generated or typed; satellite data not a roof sensor; accuracy against our own goal; prices assumed.
18. **What is next?** Real sensors and a month of logged data, wind check, crop-light measurement, paper.
19. **What if a sensor fails?** The safety layer rejects implausible readings and holds the last safe angle.
20. **Why DHT11 if it is only +-2 deg C?** It is cheap and good enough; the accuracy test includes that error.

---

## 13. Numbers to memorise

99.6 % | 91.2 % fixed 45 deg | 4.8 deg error | 29/29 tests | 864 cases | 8 x 550 Wp = 4.4 kWp | 40.90 V, 13.45 A | 21.33 % | 15-60 deg tracking, 3 deg rain, 90 deg storm | 15 m/s = 54 km/h | soil pump 35 % on, 55 % off | PAR = 0.45 of sunlight | kt Clear 0.62 | +2.0 % vs NASA 2023 | wind max 10.9 m/s in 2023.

---

## 14. Where to open things (for the judges)

- Dashboard: Review0_Prototype_Demo/matlab/review0_dashboard.m (type review0_dashboard in MATLAB).
- Twin: Review3_Digital_Twin/results/live_twin/SRMC_Digital_Twin.html (tab "Sensors and proof").
- Proof: Proof/10_Review0_Sensors_and_Panels/ (datasheets, datasets, figures, Evidence Book, checksums in Proof/MANIFEST.csv).
- Poster and slides: Review0_Prototype_Demo/ppt/Review0_Poster_A3.pptx, Review0_Presentation.pptx.
- Code and results: GitHub thanwin19/agrovoltaic-canopy-srmc.
