@echo off
rem Rehearsal with a FAKE week: no hardware needed. Needs Node and Python (matplotlib).
cd /d "%~dp0"
node make_fake_week.js week_fake.csv
node score_week.js week_fake.csv
python make_week_report.py score_week_fake
start "" score_week_fake\week_report.html
