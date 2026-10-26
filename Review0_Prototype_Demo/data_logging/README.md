# Real-data logging and weekly self-scoring

Goal: log the sensors for a week and let the six-sensor controller score the week by itself (how close it gets to the best electricity and crop light, which sensors misbehaved).
Today it runs on a FAKE week (same columns as a real log). When the ESP32 is connected, only the data source changes.

## 1. Rehearse now (no hardware)
Double-click `run_fake_week.bat` (or run the three commands in it). It writes `week_fake.csv`, scores it and opens `score_week_fake/week_report.html`.
The fake week contains deliberate problems so you can see the checks work: DHT11 read failures every day, a dirty PAR sensor (26 Oct + 3 days = 29 Oct, 10:00 to 13:00), rain on 28 Oct 14:00 to 15:00, a wind gust on 30 Oct 17:00, a stuck soil probe on 31 Oct 08:00 to 14:00.

## 2. Connect the ESP32
1. Upload `firmware/SRMC_ESP32_six_sensors/SRMC_ESP32_six_sensors.ino` (DHT11 GPIO32, soil GPIO35, rain AO GPIO34 / DO GPIO27 as in Review 0; new: pyranometer GPIO36, PAR GPIO39, anemometer pulse GPIO25). It was written without the board: set the calibration constants at the top first. If you only have the first four sensors, upload the Review 0 sketch; the logger accepts 7-field lines and leaves the sun and wind columns empty.
2. Close the Arduino Serial Monitor. `python srmc_logger.py --list` shows the COM port.
3. Edit PORT, DRY, WET and ANGLE in `run_real_week.bat` and run it (or run `srmc_logger.py` yourself). One row every 5 minutes (median of the readings). Ctrl+C stops it; running it again with the same file name continues the log.
4. Scoring: `node score_week.js week_real.csv --dry 3200 --wet 1300` then `python make_week_report.py score_week_real`.

## Columns of the log
timestamp (local, with UTC offset), ms, tempC, rh, soilRaw, rain, rainRaw, ghi (W/m2), par (umol/m2/s), wind (m/s), angleDeg (panel angle in use when the reading was taken; blank if unknown, then the scorer assumes the panels followed the controller). tempC and rh are -999 when the DHT11 failed.

## What the score means
For every daytime reading the controller picks an angle from the median of the last 5 readings; that angle is compared with the best angle for the same reading (same 50 % electricity + 50 % crop light score as the accuracy study; 100 % = the best). The same is done for the angle that was logged, a fixed 45 deg panel, a fixed 15 deg panel and the monthly plan, plus the week's electricity in kWh per m2 of panel. The sensor values are treated as truth, so a faulty sensor lowers the trust in them: check the flagged days (DHT11 failures, PAR/pyranometer ratio implausible, pyranometer above clear sky, stuck soil probe, data gaps).

## Honest limits
- The fake week is made by the same model the controller uses, so its scores are optimistic; a real week will be lower and noisier.
- The firmware, the logger on a real port, the analogue calibration of pyranometer and PAR, and the anemometer count have not been tested on hardware.
- Crop parameters are the project's typical values; the week score is not a yield measurement.

## Files
`common.js`, `make_fake_week.js`, `score_week.js`, `make_week_report.py`, `srmc_logger.py`, `run_fake_week.bat`, `run_real_week.bat`, `firmware/SRMC_ESP32_six_sensors/`.
