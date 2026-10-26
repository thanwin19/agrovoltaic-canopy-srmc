
## SRMC expo playbook: what to show, what to say, how to win

Rule for today: show it working, explain it simply, be honest about what is simulated. Judges trust teams that know their own limits.


## 1. Set-up (arrive 30 minutes early)

- Laptop 1: open a terminal in E:\final year project\srmc-twin and run: python -m http.server 8765 . Open http://localhost:8765/SRMC_Digital_Twin.html in Chrome, press F11 for full screen. It works with no internet.
- Laptop or phone 2 (backup, no server needed): the Blender video (out\blender\anim_day_0001-0060.mp4), the three GIFs (out\mechanism_closeup.gif, mechanism_tilt.gif, guide_pulley.gif) and the poster PDF.
- Print: the A3 poster (reviews\SRMC_Poster_A3.pdf) and 10 copies of the one-page handout (this playbook page 1 or the poster at A4).
- Bring: charger, extension board, mouse, a USB copy of the whole folder, your physical prototype and sensors if you have them on the table.
- Test once: twin loads, Play day works, Sensor playground works, the video plays, the MATLAB figures open (out\matlab).

## 2. Your five real sensors and what each one does


| Sensor | What it measures | What the controller does with it |
|---|---|---|
| Pyranometer | Sunlight on a flat surface (W/m2) | Tells day from night and how bright it is. Night (below 20 W/m2): park at 15 deg. It is the reference for the PAR ratio. |
| PAR sensor (under the canopy) | Light plants can use (micromol/m2/s) | The key feedback. PAR divided by sunlight = share of sun reaching the crop. Too little for the crop: tilt up. More than needed: tilt down so the panels make more power. |
| DHT11 | Air temperature and humidity | Gives VPD (air dryness). Hot, dry air (VPD above 2.5 kPa or above 38 C) lowers the light target, so more shade and less crop stress. |
| Soil moisture sensor | Water in the root zone (%) | Below 20 %: dry, drip irrigation ON and a little more shade. Above 35 %: waterlogged, irrigation OFF. |
| Rain sensor | Rain yes / no | Rain: panels go to the flat roof (3 deg) and send water to the gutter and cistern. |

One-sentence rule to say: "Keep just enough light for the crop, and give everything else to the panels."

- Not covered by your sensors (be ready to say so): wind. The spec stows the panels at 90 deg above 15 m/s; that needs an anemometer (cheap), or use a forecast.
- Panel temperature: your list has no IR sensor, so the twin labels panel temperature as modelled.
- DHT11 is a low-cost sensor: about +-2 C and +-5 % RH, slow. Fine for a demo; say a better sensor (SHT40) is the upgrade.

## 3. The 6-minute demo (click by click)

- 0:00 Poster or slide: "One farm, three incomes: crops, rain and solar power." (30 s)
- 0:30 Twin, 3D tab: press Play day. Panels tilt, the drive wire follows, shadows move. Point to the sensor card on the right: "these are our five sensors".
- 1:30 Tick "Use the sensor feedback controller". Slide Cloud cover up: PAR/GHI changes and the panels tilt up. Slide DHT11 temperature to 40 C and humidity to 25 %: target light drops, more shade. Slide soil moisture to 15 %: "dry, drip ON".
- 3:00 Press Rain mode: panels go flat at 3 deg, rain falls, the cistern fills. "Rain sensor wet: panels become a roof."
- 3:45 Open the Mechanism tab: Step A close-up. "The wire slides, the arm swings, the panel tilts." Mention the guide pulley (Step C).
- 4:45 Economics tab: move the farmer-share slider. "Industry pays every month; the farmer earns about 2 lakh per hectare per month in the model."
- 5:30 Blender video or poster proof panel: "We checked the solar model against PVGIS and the shadows against Blender ray tracing." Finish with the honest limits.

## 4. The 30-second and 2-minute pitches

30 seconds: "Farmers depend on crops alone. Our canopy lets the same land earn from crops, rain and solar power. Panels sit 4.5 m up on stainless wire. One motor tilts them to give the crop the light it needs and the panels the rest; in rain they close into a roof that fills a cistern for irrigation. The power is sold to a nearby industry, so the farmer gets a monthly income."

2 minutes: add the five sensors rule, the mechanism (wire, lever arm, pulley), and the three proofs: solar output within 5 % of PVGIS, shadows within 0.010 of a 3-D ray tracer, structure redesigned from 12.5 m to 5 m bays after a wind check failed.


## 5. What makes it stand out (say these)

- It is a complete engineering chain: design, simulation, controller, live twin, drawings, renders, and a proof index.
- We tested our own design and it failed (12.5 m bays): we changed it. That honesty is convincing.
- The controller is explainable in one sentence and driven by real sensors.
- The mechanism is shown step by step: you can see exactly how the motor tilts the panels.

## 6. Likely judge questions about the sensors and controller


| Question | Answer |
|---|---|
| Why PAR and a pyranometer? | The pyranometer measures all sunlight; the PAR sensor measures the part plants use under the canopy. Their ratio tells how much light the crop really gets, which a model cannot know. |
| Why not just track the sun? | A sun tracker maximises electricity and would shade the crop. Our rule gives the crop its light first and gives the rest to the panels. |
| What if the sensors fail? | The twin falls back to the scheduled angles from the optimiser. A real build should also check for stuck or noisy readings and park the panels at a safe angle. |
| Is the DHT11 good enough? | It is a low-cost demo sensor (+-2 C, +-5 % RH). It is enough to show VPD logic; a field system would use an industrial sensor. |
| How fast does the controller act? | Decisions every second in the demo for visibility; in the model hourly (14 per day). Real motion is rate-limited to about 1 deg/s. |
| Is the sensor mode tested on hardware? | The sensor values in the twin are simulated by sliders. The decision rule is what the hardware would run. Say this plainly unless you have run the real sensors. |
| Where is the money? | The industry buys power (assumed INR 3/kWh) and the farmer gets a share (assumed 30 %) plus crops. These two numbers are assumptions; the sensitivity study shows the range. |
| Can it work anywhere? | The twin has 7 climate presets and 9 soils; the landscapes other than TCE are illustrative. |


## 7. If something breaks

- Twin will not open: use the standalone GIFs, the Blender video and the poster; all are plain files.
- Browser blocks the file: make sure you opened it through http://localhost:8765, not by double-clicking.
- A judge asks for a number you do not have: say "that is an assumption; here is how it changes" and open the sensitivity chart (out\matlab\fig12_tornado_farmer_income.png).

## 8. Honesty line (say it once, clearly)

"This is a simulation and design study. The solar model and shadows are validated against PVGIS and a 3-D ray tracer; crop yield, water, controller behaviour and the money are model results with assumed prices, not field measurements."


## Update 2026-10-25: numbers to quote for the six-sensor controller

- Year-long test, noisy sensors: 99.6 % of the best possible combined score; 82 % of the best electricity; 98 % of the best crop light value.
- Monthly plan 98.8 %, fixed 45 deg 91.2 %, PV-only 15 deg 80.0 %.
- MATLAB and the twin: 40 of 40 identical decisions.
- Say once: the sensor values in the twin are simulated, including the anemometer.
