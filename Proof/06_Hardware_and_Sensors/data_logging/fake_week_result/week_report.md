# Week score: week_fake.csv

2016 readings over 7 days (every 300 s), 935 daytime readings scored.

## How close to the best possible (100 % = best angle for each reading)

| Strategy | Electricity % | Crop light % | Combined score % | Tilt error (deg) | Week electricity (kWh/m2 panel) |
|---|---|---|---|---|---|
| controller | 73.7 | 97.4 | 99 | 8.9 | 2.65 |
| logged angle | 73.4 | 96.9 | 98.6 | 9.3 | 2.64 |
| fixed 45 deg | 82 | 79.7 | 92.9 | 13.4 | 2.91 |
| fixed 15 deg | 99.9 | 32.5 | 75.9 | 39.1 | 3.52 |
| monthly plan | 76.6 | 92.3 | 97.5 | 9.8 | 2.74 |
| best possible | 100 | 100 | 100 | 0 | 2.69 |

The controller scored 99 % of the best combined score (fixed 45 deg: 92.9 %, fixed 15 deg: 75.9 %, monthly plan: 97.5 %).
The angle that was actually logged scored 98.6 %.

## Data quality

- complete pct: 100
- dht11 failures: 24
- dht11 failure pct: 1.2
- par guard triggers: 36
- pyranometer above clearsky: 0
- data gaps: 0
- stuck soil events: 1
- rain rows: 12
- storm rows wind ge 15: 5

## Flagged days

- 2026-10-26: DHT11 read failures
- 2026-10-27: DHT11 read failures
- 2026-10-28: DHT11 read failures
- 2026-10-29: DHT11 read failures; PAR/pyranometer ratio implausible; PAR sensor implausible
- 2026-10-30: DHT11 read failures
- 2026-10-31: DHT11 read failures; soil probe stuck for 3 h
- 2026-11-01: DHT11 read failures

Files: week_scores.csv (every reading), week_summary.json. Scores use the logged sensor values as truth, so a faulty sensor lowers confidence in them; check the flagged days first.
