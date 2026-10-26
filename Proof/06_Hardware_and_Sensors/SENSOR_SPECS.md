# Sensor specifications (typical values for the parts in the project; check the datasheet of the exact model you buy)

| Sensor | Typical part | Range | Typical accuracy | Output | Used for |
|---|---|---|---|---|---|
| Pyranometer | silicon cell sensor (SP-110 type) | 0 to 1,250 W/m2 | about 5 % | 0 to 400 mV (amplifier or ADS1115) | day or night, brightness, reference for PAR |
| PAR sensor (under the canopy) | quantum sensor (Apogee SQ type) or photodiode | 0 to 2,500 umol/m2/s | about 5 % | mV or 0 to 5 V | light that reaches the crop; corrects the model |
| DHT11 | DHT11 module | 0 to 50 C, 20 to 90 % RH | +-2 C, +-5 % RH | digital one-wire | VPD, plant stress |
| Soil moisture | capacitive v1.2 | 0 to 100 % after calibration | needs two-point calibration | analog | irrigation trigger, shade on dry soil |
| Rain sensor | FC-37 / YL-83 module | wet or dry | threshold set by the pot | digital or analog | flat roof and rain harvest |
| Anemometer | cup type, reed or hall pulse | 0 to 40 m/s | about 5 % | pulses (about 0.667 m/s per Hz) | storm stow at 15 m/s |

The ESP32 firmware (data_logging/SRMC_ESP32_six_sensors.ino) shows the pin map and the calibration constants. Not tested on hardware.
