# Review 0: the simulated sensors and the solar panels, with proof

Everything in Review 0 runs on the computer. No board, no wiring. Each sensor in the MATLAB dashboard is a **software model of a real, named device**. You can set every one by hand (slider or typed number); until you touch it, it follows the day and sky model.

Honest statement for the judges: **the readings are generated or typed, not measured.** The devices, ranges, accuracies and output signals below are the manufacturers' published numbers.

## The six sensors (seven readings)

| # | Reading in the dashboard | Real device simulated | What the real device does | Range | Accuracy | Output signal | Dashboard slider |
|---|---|---|---|---|---|---|---|
| 1 | Sunlight | **Apogee SP-110** silicon-cell pyranometer | all sunlight, 360-1120 nm | 0-2000 W/m2 (linear to 1750) | +-5 % (calibration), drift < 2 % per year, response < 1 ms | 0.20 mV per W/m2 (5.0 W/m2 per mV) | 0-1200 W/m2 |
| 2 | Plant light (PAR) | **Apogee SQ-110** quantum sensor | photons 410-655 nm, the light plants use | 0-4000 umol/m2/s | +-5 %, drift < 2 % per year, response < 1 ms | 0.20 mV per umol/m2/s | 0-2400 umol/m2/s |
| 3 | Air temperature | **DHT11** | air temperature | 0-50 deg C | +-2 deg C | 40-bit digital word | 0-50 deg C |
| 4 | Air humidity | **DHT11** (same chip) | relative humidity | 20-90 % RH | +-5 % RH | 40-bit digital word | 20-90 % RH |
| 5 | Soil moisture | **DFRobot SEN0193 v1.2** capacitive probe | soil water content | output 2.5 V dry to 1.2 V wet (3.3-5.5 V supply) | needs a dry and a wet calibration | analog 1.2-2.5 V | 0-100 % water |
| 6 | Rain | **YL-83 / FC-37** raindrop plate with LM393 comparator | wet or dry plate | wet / dry | threshold set by a trimmer | digital pin LOW when wet | wet / dry button |
| 7 | Wind speed | **Adafruit 1733** cup anemometer, analog output | wind speed | 0.4 V = 0 m/s, 2.0 V = 32.4 m/s | worst case 1 m/s | analog 0.4-2.0 V | 0-25 m/s |

How a reading is "simulated" in the dashboard: the slider value is the physical quantity, and the dashboard also shows the signal the real device would put out (for example 837 W/m2 on the SP-110 is 167 mV; 20 m/s wind on the Adafruit 1733 is 0.4 + 1.6 x 20 / 32.4 = 1.39 V).

## The solar panels

| Item | Value |
|---|---|
| Make and model | **JinkoSolar Tiger Pro JKM550M-72HL4-V**, monocrystalline silicon |
| Number of panels | **8** (2 rows x 4, landscape across the tube) = **4.4 kWp** (from the hardware pack, `Review1_Design_and_CAD/code_reference/build_hardware_docs.py`) |
| Size and weight | 2274 x 1134 x 35 mm, 28.9 kg (official JinkoSolar datasheet; the structure calculation used 2278 mm and 27.5 kg from retailer listings, a small difference) |
| Maximum power at test conditions (STC) | 550 Wp |
| Voltage and current at maximum power | Vmp 40.90 V, Imp 13.45 A (40.90 x 13.45 = 550 W) |
| Open-circuit voltage, short-circuit current | Voc 49.62 V, Isc 14.03 A |
| Module efficiency | 21.33 % (550 W column of the datasheet) |

What is used where: the dashboard's I-V curve and maximum-power-point tracker use these five numbers (single-diode model, perturb-and-observe tracker). The energy model used by the controller uses a module efficiency of 21 % with the PVGIS-style temperature model. The temperature coefficients in the I-V model are typical values, **not** read from this datasheet.

## Sources (checked 2026-11-01)

- Apogee SP-110 manual (sensitivity 0.20 mV per W/m2, calibration uncertainty +-5 %, non-linearity < 1 % up to 1750 W/m2, response time < 1 ms, spectral range 360-1120 nm): https://s.campbellsci.com/documents/au/manuals/SP-110.pdf
- Apogee SQ-110 manual (sensitivity 0.2 mV per umol, +-5 %, non-linearity < 1 % up to 4000 umol, 410-655 nm): https://s.campbellsci.com/documents/au/manuals/SQ-110.pdf
- DHT11 datasheet figures (0-50 deg C +-2 deg C, 20-90 % RH +-5 % RH), e.g. https://wellpcb.com/dht11-datasheet.html and https://waveshare.com/product/temperature-humidity-sensor.htm. One site (Components101) lists tighter figures; the datasheet-based +-2 deg C / +-5 % RH are used here.
- DFRobot SEN0193 capacitive soil moisture sensor (output 1.2-2.5 V, 3.3-5.5 V supply): https://www.dfrobot.com/product-1385.html
- Adafruit 1733 analog anemometer (0.4 V at 0 m/s, 2.0 V at 32.4 m/s, worst-case accuracy 1 m/s, start speed 0.2 m/s): https://www.adafruit.com/product/1733
- YL-83 / FC-37 rain sensor: no official datasheet exists; vendor pages (5 V supply, LM393 comparator, digital output LOW when wet) e.g. https://botland.com.pl/en/weather-sensors/1732-rain-sensor-module-yl-83.html
- JinkoSolar Tiger Pro JKM550M-72HL4-V (550 Wp, 40.90 V, 13.45 A, 49.62 V, 14.03 A, 21.29 %, 2278 x 1134 x 35 mm): the official JinkoSolar datasheet for the JKM530-550M-72HL4-(V) series (downloaded, Chinese-language edition; Vmp 40.90 V, Imp 13.45 A, Voc 49.62 V, Isc 14.03 A, 2274 x 1134 x 35 mm, 28.9 kg, 21.33 % all read from the file): https://www.jinkosolar.com/uploads/JKM530-550M-72HL4-(V)-F1-CN.pdf . A retailer listing (https://sun.store/en/product/jinko-jkm550m-72hl4-v-silver-frame-1500v-1644) gave 21.29 % and 2278 mm; the datasheet figures are used.

## What the day graphs show (tab "Accuracy")

"Accuracy" is how close the controller's angle gets to the best possible angle on the combined score (half electricity, half crop light), found by trying every angle from 15 to 60 deg in 0.5 deg steps. The "real sensor errors" line gives the controller sensor values that are wrong by realistic amounts (random, sigma = half of the +- limit: sunlight and PAR 2.5 %, DHT11 1 deg C and 2.5 % RH, soil 1.5 %) and scores the angle it picks under the true conditions. One fixed random draw is used, so the picture is repeatable. Rain, storm and night hours follow the safety rules and are not counted. All of this is measured against the controller's own goal in simulation, not against real crop yield.

## Downloaded copies (proof files)

In `Proof/10_Review0_Sensors_and_Panels/sensor_datasheets/`: 01 pyranometer (SP-110 manual PDF), 02 PAR (SQ-110 manual PDF), 03-04 DHT11 datasheet PDF, 05 soil (DFRobot wiki and product page, saved HTML), 06 rain (vendor page, saved HTML; no official datasheet exists), 07 wind (Adafruit 1733 datasheet C2192 PDF and product page), P1 panel (JinkoSolar datasheet PDF). Checked against the files: SP-110 and SQ-110 sensitivity 0.2 mV per unit and +-5 %; DHT11 +-5 %RH and +-2 C at 25 C; Adafruit wind formula (V - 0.4) / 1.6 x 32.4; Jinko Vmp, Imp, Voc, Isc, size, weight.
