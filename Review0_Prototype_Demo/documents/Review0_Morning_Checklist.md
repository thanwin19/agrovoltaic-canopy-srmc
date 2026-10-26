# Review 0 - morning checklist (do in this order)

Bring: laptop (MATLAB + Arduino IDE), USB cable, NodeMCU ESP8266 (+ ESP32 spare), DHT11, soil module, rain module, 6+ jumper wires, a cup of water, a dry cloth, a reference thermometer (phone app is acceptable), phone for photos, the printed one-pager for the signature.

## A. Wire (15 min) - details in firmware/PIN_MAP.md
- [ ] DHT11: VCC -> 3V3, DATA -> D2, GND -> GND
- [ ] Soil: VCC -> 3V3, AO -> A0, GND -> GND
- [ ] Rain: VCC -> 3V3, DO -> D5, GND -> GND
- [ ] Photo of the wiring (needed on slide 14)

## B. Upload and check (10 min)
- [ ] Arduino IDE: board "NodeMCU 1.0 (ESP-12E Module)", correct COM port (install CP2102 driver if no port)
- [ ] Open firmware/SRMC_ESP8266_NodeMCU/SRMC_ESP8266_NodeMCU.ino -> Upload
- [ ] Serial Monitor at 115200: lines like SRMC,5231,31.0,54.0,712,0,-1 appear once per second
- [ ] Screenshot of the Serial Monitor (slide 14)
- [ ] Close the Serial Monitor (MATLAB needs the port)
- [ ] If the ESP8266 misbehaves, repeat with the ESP32 sketch and pins (PIN_MAP.md, part B)

## C. Calibrate and measure (25 min) - write the numbers in test_data/bench_log_template.csv
- [ ] DHT11 vs thermometer: ______ C vs ______ C (must be within 2 C); humidity if you have a reference
- [ ] Soil DRY (probe in air): raw = ______      Soil WET (probe in water): raw = ______   (wet must be clearly below dry)
- [ ] In the dashboard: press Capture DRY with the probe in air, then Capture WET with the probe in water
- [ ] Rain: drop water on the plate -> time to rainWet = 1: ______ s; wipe it -> time to 0: ______ s
- [ ] If rain never turns 1: turn the blue potentiometer on the module, or set RAIN_ACTIVE_LOW to 0 in the sketch and upload again

## D. MATLAB live demo (15 min)
- [ ] MATLAB: cd to Review0_Prototype_Demo/matlab, type review0_dashboard
- [ ] Source: Serial (ESP), pick the COM port, baud 115200, Connect, then START live loop
- [ ] Move the sliders: sky (clear -> overcast), solar hour, wind; the pyranometer and PAR values and the angle change
- [ ] Wet the rain plate: mode becomes RAIN HARVEST, angle 3 degrees, cistern level rises
- [ ] Dry soil (probe in air): pump decision ON; probe in water: OFF
- [ ] Set wind to 18: WIND STOW 90 degrees
- [ ] Press Save evidence (PNG + CSV): files go to results/live_logs
- [ ] Screenshot/photo of the laptop with the real board connected (slide 14)

## E. Finish (before the review)
- [ ] Open ppt/Review0_Prototype_Demo.pptx, replace the three dashed frames on slide 14 with the photos/screenshots, fill the table with your numbers
- [ ] Supervisor signs the one-page write-up (documents/Review0_Supervisor_OnePager.docx, print it)
- [ ] Upload the PPT to the seminar-hall PC 10 minutes before the review

## If something fails
- No board / port busy: set Source = Simulate and say so. The dashboard, rules and results are identical.
- No MATLAB serial: use the Arduino Serial Monitor to show the live line, then Simulate for the decision logic.
