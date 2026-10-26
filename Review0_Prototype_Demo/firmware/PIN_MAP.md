# Wiring: connect these tomorrow (power everything from 3.3 V, one common GND)

Your board is a **NodeMCU ESP8266 (CP2102 USB chip)** - the pins are printed on the board (D0..D8, A0, 3V3, GND, Vin). Install the **CP2102 driver** if the PC does not show a COM port.

## A. NodeMCU ESP8266  ->  sketch `SRMC_ESP8266_NodeMCU`

| Sensor | Sensor pin | NodeMCU pin | Note |
|---|---|---|---|
| DHT11 | VCC (+) | **3V3** | |
| DHT11 | DATA (S/OUT) | **D2** | 3-pin module already has the pull-up; for the bare 4-pin sensor add 10 kOhm from DATA to 3V3 |
| DHT11 | GND (-) | **GND** | |
| Soil moisture module | VCC | **3V3** | powering from 3V3 keeps A0 inside its 0-3.3 V range |
| Soil moisture module | AO (analog) | **A0** | the only analog pin of the ESP8266 |
| Soil moisture module | GND | **GND** | leave DO unconnected |
| Rain sensor module | VCC | **3V3** | |
| Rain sensor module | DO (digital) | **D5** | turn the blue potentiometer until the module LED switches when a drop touches the plate |
| Rain sensor module | GND | **GND** | AO not used (ESP8266 has one ADC) |

Do not use D3, D4 and D8 for sensors (they decide the boot mode). D4 is the on-board LED: it lights while rain is detected.
Never connect a 5 V signal to A0 or any D pin.

## B. ESP32 DevKit  ->  sketch `SRMC_ESP32`

| Sensor | Sensor pin | ESP32 pin |
|---|---|---|
| DHT11 | VCC / DATA / GND | **3V3** / **GPIO4** / **GND** |
| Soil moisture | VCC / AO / GND | **3V3** / **GPIO34** / **GND** |
| Rain sensor | VCC / DO / AO / GND | **3V3** / **GPIO27** / **GPIO35** (optional) / **GND** |

(GPIO34 and GPIO35 are input-only ADC pins - correct for sensors.)

## C. Upload and check (5 minutes)

1. Arduino IDE -> Board manager: install "esp8266 by ESP8266 Community" (for the NodeMCU) or "esp32 by Espressif" (for the ESP32). If the PC has no internet, install them at home tonight.
2. Select the board and the COM port, open the matching `.ino`, press Upload.
3. Open Serial Monitor at **115200 baud**. You must see a line like `SRMC,5231,31.0,54.0,712,0,-1` every second.
   - `tempC = -999` -> DHT11 not read: check D2, 3V3, GND and the 10 kOhm pull-up.
   - `soilRaw` does not change when you push the probe into wet soil -> check A0 and the 3V3 wire.
   - `rainWet` stays 0 with a wet plate -> turn the potentiometer, or set `RAIN_ACTIVE_LOW` to 0.
4. Close the Serial Monitor (MATLAB needs the port), then start `review0_dashboard` in MATLAB.

The photo shows "use 9600 baud" printed on the back of the board: that is the old default of the module. These sketches use **115200**; the MATLAB dashboard has the same default.
