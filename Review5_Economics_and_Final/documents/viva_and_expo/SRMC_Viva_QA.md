# Viva questions with honest answers

**Q1 (Concept). What problem does your project solve?**

It lets one piece of farmland produce crops, harvest rain and sell solar power at the same time. The farmer gets a monthly income from the industry that buys the electricity, plus his own crop income, instead of relying on crops alone.

**Q2 (Concept). What exactly is new in SRMC-DT?**

The combination: a wire-rope canopy whose panels are moved by one wire-drive motor between a flat rain-harvest position and a tilt position, with an hourly controller that picks the tilt to balance electricity and crop light, plus a farmer-income contract model. Each part exists separately in the literature (agrivoltaics, tilt control, rain-harvesting roofs). We have NOT done a formal prior-art search, so we claim a combination, not absolute novelty.

**Q3 (Concept). Why not just put panels on a normal ground mount?**

A fixed low ground mount shades crops too strongly and blocks machinery. Our canopy is 4.5 m clear, lets a harvester pass, and the panels can open to let light through when crops need it.

**Q4 (Concept). Why is it a computer-only project?**

Scope decision: the work is simulation, digital twin, CAD and rendering. We do not claim measured results. A physical pilot is listed as future work and would be used to calibrate the models.

**Q5 (Physics). How do you compute the sun and the shadows?**

Standard declination and hour-angle formulas for 9.88 N, monthly clearness index from NASA POWER, Erbs diffuse split. Shadows are a 2-D ray cast in the east-west cross-section (panels run north-south) for 40 ground points per row pitch and every hour.

**Q6 (Physics). How do you know the shadow model is right?**

We compared it with Blender Cycles, a 3-D ray tracer: 20 sun and tilt cases x 4 zone strips = 80 comparisons; mean difference in sunlit fraction 0.010, 96 % within 0.10. The comparison also found and fixed a bug (truncated rows at low sun).

**Q7 (Physics). How do you know the PV numbers are right?**

Against PVGIS (ERA5) for a horizontal panel at TCE: annual energy +5.0 %, while the sunshine dataset itself differs by +5.2 % (NASA vs ERA5). So energy per unit of sunshine matches. The module model is the Huld model PVGIS uses plus an incidence-angle loss.

**Q8 (Physics). Why is your annual irradiation 5 % higher than PVGIS?**

We use NASA POWER monthly clearness; PVGIS uses ERA5. The difference is mainly in the monsoon months. It is a data-source difference, not a modelling error, and it is shown explicitly in the validation.

**Q9 (Physics). How is crop yield computed?**

Potential yield x light factor x temperature factor x soil factor x FAO water-stress response (Ky, Doorenbos and Kassam). Water comes from a daily FAO-56 style balance with Hargreaves evapotranspiration. Crop parameters are typical literature-style values, not measured at TCE.

**Q10 (Physics). Why do all climates choose the same four crops?**

Because the canopy leaves about 34 % of sunlight, only shade-tolerant crops (ginger, turmeric, coriander, amaranth) score well. That is a result of the light level, and it shows the design suits shade crops.

**Q11 (Structure). Is your structure safe?**

Not proven. A screening check with IS 875 wind showed the original 12.5 m bays are overloaded many times (rope 16x, tube 30x). A 5 m rope grid with a 114 x 4 mm tube, sag span/12 and 20 mm stays passes at screening level. A certified structural design with real rope data and soil investigation is still required.

**Q12 (Structure). Why did you change from 12.5 m to 5 m spacing?**

Because the structural screening failed at 12.5 m. A 12.5 m rope with 0.32 m sag cannot carry about 300 kN of wind and dead load per bay. The 5 m spacing is also what your own guideline recommends.

**Q13 (Structure). How tall is it and can a harvester pass?**

Pivot axis 5.58 m; lowest panel edge 4.50 m at the maximum 60 deg tilt (a 4.1 m harvester fits). Clear lane between columns is about 4.8 m, below the 6 m in the spec but above a 3 m harvester width.

**Q14 (Structure). How strong is the rope?**

We used an indicative 0.6 d2 kN breaking load (154 kN for 16 mm) and limited ULS load to half of it. This must be replaced with a supplier datasheet. Our own guideline lists 250 kN working load, which looks about five times too high.

**Q15 (Controller). How does the controller decide the tilt?**

Every hour it evaluates tilt angles from 15 to 60 deg (5 deg steps, then 0.5 deg refinement) and picks the one maximising 0.5 x PV/PVmax + 0.5 x crop-value/cropmax. Priority overrides: wind stow above 15 m/s, flat rain mode above 1 mm/h, night park.

**Q16 (Controller). Does it beat a fixed tilt?**

Against a fixed 45 deg stop: +2 % electricity, +3.5 % crop light, +55 % crop income, +5 % total value. Against a PV-only design it earns less money (55.0 vs 68.2 INR lakh per ha) because crop income is small at assumed prices. We state this openly.

**Q17 (Controller). Is this really sensor-based?**

In the model the sensor signals are simulated from the same physics (pyranometer, zone light, panel temperature, VPD, soil moisture, rain). The decision logic is exactly what a physical controller would run; the simulated sensors would be replaced by real ones.

**Q18 (Controller). Is the Simulink model the same as the MATLAB controller?**

The Simulink model implements the supervisory logic (priorities, motor rate limit, encoder resolution) around the hourly schedule produced by the MATLAB optimiser. It is a block-diagram verification of the behaviour on a test day, not a second optimiser.

**Q19 (Controller). What about wind and failure modes?**

Wind above 15 m/s commands a 90 deg stow in the Simulink model (spec). Power-failure brake behaviour, communication loss and sensor faults are not modelled.

**Q20 (Water). How much rain can you harvest?**

About 4,640 m3 per hectare per year from 959 mm of rain; irrigation demand is about 4,930 m3 so roughly 94 % is met from rain; in a 30 % drier year about 90 %.

**Q21 (Water). Why a cistern of 100 m3?**

It is the value in the design file for the per-hectare model; the cistern-sizing curve in the twin shows demand not met falls below 5 % at about 100-150 m3. The CAD demonstration unit (25 x 25 m) needs only a small fraction of that.

**Q22 (Economics). How much does the farmer earn?**

About INR 2.0 lakh per hectare per month in the model, almost all from the solar share. This rests on two assumptions: the industry pays INR 3.0/kWh and the farmer receives 30 %. With the full uncertainty ranges (Monte Carlo) the P5-P95 range is INR 1.4-3.0 lakh per month.

**Q23 (Economics). Where do the tariff and the 30 % come from?**

They are assumptions; no contract exists. They must be replaced by a PPA term sheet or lease. The sensitivity study shows the farmer share and tariff dominate the farmer income.

**Q24 (Economics). Is it a good investment?**

Not at these assumptions. The investor payback is about 41 years in the base case (37 at the median). A 15-year payback would need roughly INR 6.2/kWh at a 30 % farmer share. Lower capex, subsidy or a lower farmer share are needed.

**Q25 (Economics). Did you include subsidies?**

The model has a subsidy parameter (0-30 % in the sweep). Actual eligibility under PM-KUSUM or state schemes has not been checked.

**Q26 (Economics). Why is crop income so small?**

At 34 % of full sunlight the shade crops give a modest net margin per hectare compared with solar sales of about INR 70 lakh per hectare. The crop benefit is in resilience, water and soil, which we do not price.

**Q27 (Validity). What is validated and what is not?**

Validated: PV module model (PVGIS), shading geometry (Blender), JS vs MATLAB implementation. NOT validated: crop yields, water balance, controller behaviour and economics against any measurement. There is no field data.

**Q28 (Validity). What are the biggest uncertainties?**

1) tariff and farmer share; 2) rope and structural data; 3) crop light-response parameters; 4) monthly-mean sky instead of hourly weather.

**Q29 (Validity). Why are two MATLAB and JavaScript codes the same? Is that a proof?**

It proves the twin and MATLAB implement the same equations (0.0000 % difference on 22 outputs). It does not prove the equations are physically right; that is what the PVGIS and Blender comparisons address.

**Q30 (Validity). Did you use any measured data?**

Only public data sets: NASA POWER climate, PVGIS for validation, OpenStreetMap for the campus layout. No sensor measurements.

**Q31 (Tools). Why MATLAB, Blender, AutoCAD and a web twin?**

MATLAB/Simulink is the engineering model and controller; the web twin is the live demonstration; DXF drawings and the BOM are the design deliverable; Blender gives independent ray-traced validation and the visuals. All read the same design file.

**Q32 (Tools). How can I rerun your results?**

Every claim is listed in PROOF_INDEX.md with the command that reproduces it; a SHA-256 manifest of all files is in evidence/logs.

**Q33 (Future). What would you do next?**

Replace assumptions with quotes and datasheets; get a soil and geotechnical report; run a one-row pilot with the sensor stack to calibrate the twin; add hourly weather; price water and soil benefits; do a formal prior-art search.


## Six-sensor controller (added 2026-10-25)

**Q. How do the six sensors decide the tilt?**

A. Rain wet: flat roof 3 deg. Pyranometer below 20 W/m2: night park. Otherwise the controller tries every angle from 15 to 60 deg and picks the best combined score of 50 % electricity and 50 % crop light. The PAR sensor corrects the model; DHT11 and soil moisture lower the light the crop needs when it is stressed.

**Q. How accurate is it?**

A. In a year-long test with noisy sensors the controller reaches 99.6 % of the best possible combined score, with 82 % of the best electricity and 98 % of the best crop light value. The monthly plan reaches 98.8 %, a fixed 45 deg panel 91.2 %. The score is measured against the controller's own objective, not against field crop yield.

**Q. Are the sensor readings real?**

A. In the twin and the Simulink model they are simulated (sliders and climate data). Review 0 uses real DHT11, soil and rain readings on an ESP board. No pyranometer or PAR data has been measured yet.

**Q. Why is the PAR sensor needed if there is a pyranometer?**

A. The pyranometer measures total sun above the canopy. The PAR sensor measures what reaches the crop. Their ratio tells whether the model matches reality (dirt, clouds, shading error) and corrects it.

**Q. What protects the crop?**

A. Rain: flat roof. Hot dry air (VPD above 1.6 kPa rising to 2.5) or dry soil (below 20 %): the controller accepts more shade. Wind: the anemometer stows the panels at 90 deg at 15 m/s (54 km/h).

**Q. Why does the controller keep the angle sometimes?**

A. A hysteresis of 2 % of the score stops it moving for tiny gains, which protects the motor. A bigger value gives a calmer motor at a small cost in score.

**Q. What does the soil probe change?**

A. It decides when the drip irrigation runs: 5,372 m3 per hectare a year against 5,641 m3 for a timer (4.8 % saved) and no water-stress days instead of 20. A stuck or dead probe falls back to the timer schedule.

**Q. What if the rain or soil sensor fails?**

A. A soil probe that is missing, out of range, jumping or stuck is replaced by the water-balance model value; a rain sensor stuck wet in dry sunny air is ignored for 30 minutes onwards; panel moves are limited to 12 an hour and the motor wear is counted. Tested in 8 simulation tests.

**Q. Is the motor strong enough?**

A. The first parts list (3 kN winch, 4 mm drive wire) was not: its 3 kN winch is 1.4 times overloaded at 54 km/h wind and the 4 mm wire is at 0.9 of its limit. The final design uses a 10 kN winch, a 6 mm wire and a 45 degree offset lever arm, good to 54 km/h with panels held. Capacities are screening estimates.

