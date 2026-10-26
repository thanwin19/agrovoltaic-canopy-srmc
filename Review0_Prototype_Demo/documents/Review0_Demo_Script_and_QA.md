# Review 0 - demo script and likely questions

## Marks to aim at (rubric)
Prototype demonstration 20 | Testing and validation evidence 10 | Feasibility and constraints 5 | SDG and cost mapping 5 | Time management 5 | Response to questions 5.

## 5-minute demo script
1. (30 s) "The goal is one decision: the panel angle that gives the most energy and still lets the crop receive its light."
2. (45 s) Slide 3 / dashboard: "These three are real sensors on the prototype: DHT11, soil moisture and rain. These three are simulated, shown as SIM: pyranometer, PAR and wind, because we do not have those sensors yet."
3. (60 s) Live: change sky from Clear to Overcast; GHI and PAR fall; the controller changes the angle. Move the solar hour; the angle follows.
4. (45 s) Wet the rain plate: "Rain sensor wet -> the panels go to a 3 degree slope, the cistern fills."
5. (30 s) Probe in air: soil % falls, pump ON from the harvested water. Probe in water: pump OFF.
6. (30 s) Wind slider to 18: stow at 90 degrees. "Safety overrides everything."
7. (60 s) Slides 9 to 12: "16 of 16 logic tests pass; on a clear day the controller keeps about 75 % of the best energy and 89 % of the best crop light, while pure sun tracking keeps 100 % energy and 27 % crop light."

## Likely questions and honest answers
1. **Is the pyranometer real?** No. It is computed from the sun model and a sky setting and is labelled SIM. The control code only reads a number, so a real pyranometer replaces that input without code changes.
2. **How do you know the virtual numbers are right?** The same equations were checked against PVGIS (annual PV within +5.0 %, of which +5.2 % is the sunshine dataset) and against Blender ray tracing (shading difference 0.010). They were not checked against a field instrument.
3. **What is "co-optimising"?** An objective J = w x energy + (1 - w) x crop light, each normalised to its best value at that moment; w is a slider. The optimiser tests every angle from 15 to 60 degrees in 0.5 degree steps.
4. **Why not just track the sun?** Tracking gives the most energy but leaves the crop about 27 % of its light target on a clear day, and the wire-drive design has two positions, not continuous tracking. It is shown only as a reference.
5. **Does the controller beat tracking?** Not on energy; it trades about a quarter of the energy for most of the crop light. It beats a fixed 45 degree angle on both. Which trade is right depends on w, which Review 4 prices.
6. **How accurate are the sensors?** DHT11: +-2 C and +-5 % RH (datasheet); our bench comparison is on slide 14. The resistive soil probe drifts and needs two-point recalibration each session.
7. **Why USB serial and not WiFi?** It needs no network and is reliable for a demo; the same protocol can go over WiFi/MQTT later.
8. **Why two boards?** The ESP8266 has one analog pin; the ESP32 is a backup with more ADC pins. Same serial lines, same MATLAB code.
9. **What does VPD do here?** It is computed from the DHT11 temperature and humidity. High VPD (> 2.5 kPa) or dry soil raises a stress index that lowers the light the crops need by up to 30 %, so the controller can accept more shade and more energy.
10. **What if the sensor fails?** A failed DHT11 read (-999) is ignored and the last good value is kept; a lost serial link is reported on the dashboard and Simulate mode takes over.
11. **Is the tilt real?** No actuator yet. The angle is shown on the MATLAB drawing; a motor driver with an encoder is the next step (Reviews 1 and 4 contain the full-scale wire-drive design).
12. **SDGs?** 7 (clean energy), 2 (food), 6 (rain harvest and efficient irrigation), 13 (climate action), 1/8 (monthly farmer income). Indicators are on slide 16.
13. **Cost?** Kit of a few hundred to about one thousand rupees at hobby prices (indicative, replace with the bill); a calibrated pyranometer is far more expensive, which is why it is simulated now.
14. **What has been validated and what not?** Validated against PVGIS and Blender; logic tested in software; sensors bench-tested today. Not validated against field data or a real pyranometer.
15. **What is next?** Real pyranometer and PAR sensor, a dead-band and motor driver, a week of logged data, comparison with local weather data.
