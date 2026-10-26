# Controller safety tests

Fallbacks for the rain and soil sensors, a motor wear count and limits on how often the panels may move (`makeSafe` in sensor_controller.js). Run: `node test_safety.js`.

| Test | Result | What happened |
|---|---|---|
| Rain sensor stuck wet (dry sunny air, 3 h) | PASS | without the guard the panels stay flat for 180 min; with it for 30 min (fault declared after 30 min). RAIN SENSOR FAULT (stuck wet in dry sunny air, RH 40 %): ignored, panels keep tracking |
| Rain sensor dead (reads dry in real rain) | PASS | forecast + RH 96 % + dark sky gives mode RAIN (angle 3 deg); without the fallback the panels would stay tilted: OPTIMISE |
| Soil probe unplugged (no reading) | PASS | SOIL PROBE FAULT (no reading): using the water-balance model 55 % |
| Soil probe glitch (60 % to 5 % in 30 min) | PASS | SOIL PROBE FAULT (jump of 55 points in under an hour): using the last good value 60 % |
| Soil probe stuck at 12 % for 5 h | PASS | declared stuck after 180 min (limit 180 min), then the model value is used |
| Soil probe out of range (140 %) | PASS | SOIL PROBE FAULT (reading out of range (140 %)): using the last good value 50 % |
| Cloud flicker: panels may not hunt | PASS | two hours of 1-minute clear/cloud flicker. No protection: 92 moves, 217 deg of panel travel, 1.6 m of wire (score vs best angle 99.1 %). Hysteresis only (the controller default): 14 moves, 60 deg of panel travel, 0.4 m of wire (score vs best angle 99.2 %). Limits without hysteresis: 24 moves, 85 deg of panel travel, 0.6 m of wire (score vs best angle 97.9 %) with 81 moves held. |
| Wear on a normal clear day | PASS | 64 moves, 330 deg of panel travel, 2.5 m of drive wire, 6.5 drum turns, 27 reversals in one day; about 2375 drum turns and 23360 motor starts per year |

Limits (defaults): minimum 120 s between moves, at most 12 moves per hour, at most 900 deg of panel travel per day; rain flat-roof, storm stow and night park are never blocked. Soil probe fault rules: no reading, outside 0 to 100 %, jump above 40 points in an hour (unless it rained or irrigation ran), or the same raw value for 3 daytime hours. Rain sensor rules: wet for 30 min in dry sunny air (RH under 65 %, sun above 60 % of clear sky) is ignored; a dry reading with a rain forecast, RH of 90 % or more and a dark sky counts as rain.

Wear numbers use the 0.44 m offset lever arm (wire travel = arm x change of sin(angle - 45 deg)) and a 120 mm drum.
