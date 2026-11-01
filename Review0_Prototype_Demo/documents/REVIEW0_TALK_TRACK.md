# Review 0: what to say (about 5 minutes)

1. **Problem.** Crops and solar panels need the same sun. A fixed panel angle either shades the crop too much or wastes electricity.
2. **Idea.** A canopy whose panel angle is chosen by six sensors. The target is the best mix of electricity and crop light.
3. **What I built for Review 0.** Everything on the computer, nothing wired. Each sensor is simulated after a real device (SP-110 pyranometer, SQ-110 PAR, DHT11, SEN0193 soil, YL-83 rain, Adafruit 1733 wind) and I can change any of them by hand. The panels are 8 JinkoSolar Tiger Pro 550 Wp modules (4.4 kWp). Datasheet numbers and sources: `SENSOR_AND_PANEL_PROOF.md`.
4. **Live demo.** (a) Press "Clear noon", show the angle. (b) Drag the PAR or sunlight slider, the angle changes. (c) Hot dry preset: the crop is stressed, more shade. (d) Press RAIN: panels flat at 3 deg. (e) Wind to 20 m/s: panels edge-on at 90 deg. Each time, read the "In simple words" box.
5. **Graphs.** Tab 1 sensors through a day. Tab 2 angle and electricity against a fixed 45 deg panel. Tab 3 accuracy: the controller gets about 99 % of the best possible score even with datasheet-sized sensor errors; fixed 45 deg and plain sun tracking get about 87 % (numbers shown for the chosen day).
6. **Limits (say them first).** Simulation only, no field trial. Sensor readings are generated or typed. Prices are assumptions. Accuracy is measured against the controller's own goal (half electricity, half crop light), not against real crop yield.
7. **Next.** 3D twin, Review 1-5 folders (CAD, solar and shadow, economics) and the paper are prepared.

Likely questions: *Why 50/50?* It is a slider (energy share). *Are the sensors real?* No, they are models of real devices; hardware is a later step. *What is new?* Choosing the angle from sensors to co-optimise crop light and electricity, with a safety layer for rain, wind and faulty sensors.
