@echo off
rem REAL week: 1) find the port with  python srmc_logger.py --list   2) set PORT below   3) leave it running for a week (Ctrl+C stops)
rem soil calibration: DRY = raw value with the probe in air, WET = raw value with the probe in water (ESP32 defaults 3200 / 1300)
cd /d "%~dp0"
set PORT=COM5
set DRY=3200
set WET=1300
set ANGLE=30
python srmc_logger.py --port %PORT% --out week_real.csv --interval 300 --angle %ANGLE%
node score_week.js week_real.csv --dry %DRY% --wet %WET%
python make_week_report.py score_week_real
start "" score_week_real\week_report.html
