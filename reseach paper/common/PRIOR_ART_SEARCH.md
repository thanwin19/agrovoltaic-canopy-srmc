# Prior-art search: sensor-driven tilt control for agrovoltaics

Date: 26 October 2026. Method: web search of the scholarly literature and of patent records (Google Patents and USPTO pages found through the search engine). This is **not a professional patent search**. Before filing a patent or claiming novelty in a thesis, repeat it on Google Patents, Espacenet and the Indian patent database (InPASS) with the CPC classes H02S 20/32 (tilting PV arrays) and A01G 9/24 or A01G 7/04 (crop light control), and read the full texts listed below.

Queries used: agrivoltaic tracking or tilt control and crop light; PAR or crop sensor under panels and tilt; soil moisture or water stress and tilt; model predictive control and agrivoltaic; Sun'Agri steering; cable or lever drive single-axis trackers.

## What already exists (so we must NOT claim it as new)

| Prior work | What it does | Overlap with our project | Status of the reference |
|---|---|---|---|
| Elamri et al., Agric. Water Manag. 208 (2018) 440-453, doi 10.1016/j.agwat.2018.07.001 (Sun'Agri, France) | Water budget and crop model under orientable panels, a first step toward piloting panels and irrigation together | Model-based steering of panels for the crop; links to irrigation | Verified (title, journal, pages, DOI) - cited [6] |
| Stuhlmacher, Srisuthankul, Mathieu, Seiler, "A model predictive control approach to dual-axis agrivoltaic panel tracking," Renew. Energy 274 (2026) 126155 | MPC that optimizes crop yield plus PV revenue over a season from forecasts | Co-optimization of crop and electricity by tilt control | Verified via Michigan Tech repository and arXiv 2603.22554 - cited [7] |
| Cornell (K. Max Zhang and co-authors), "An integrated control framework for optimal sunlight sharing in agrivoltaic systems," Solar Energy (2026) | Proactive forecast-based tilt control plus reactive correction of crop light deficits; reported maximum light deficit cut from 43 % to 8 % | Tilt control for crop light targets | Full author list and volume NOT verified - not cited; add after checking |
| Mälardalen University (Sweden), DLIT and KPT tracking strategies (2026, thesis / news) | Track until the crop daily light integral is met, or maximize photosynthesis from the light-response curve | Crop-aware tracking | Only news and thesis text seen - not cited |
| Purdue (Bermel group), "Optimized agrivoltaic tracking for nearly-full commodity crop and energy production," Renew. Sustain. Energy Rev. (2024) | Anti-tracking at critical times keeps corn yield near control with about 87 % of tracker power | Crop-aware tracking | Authors not verified - not cited |
| Yano and Li, Adv. Sustain. Syst. (2025), doi 10.1002/adsu.202500603 | Dynamic semitransparent panel allocating sunlight to cells and crops | Dynamic light sharing | Verified (partly) - cited [8] |
| Riaz et al., IEEE J. Photovolt. 12(2) (2022) 572-580 | Light productivity factor for crop-specific array design | Metric of light sharing | Verified through a citing paper - cited [9] |
| A 2026 review of intelligent equipment control for agrivoltaics (MDPI, title "Synergistic Optimization of Agrivoltaic Systems ...") | Lists "crop-state feedback" control using canopy PAR, temperature, soil moisture and plant stress | **Our sensor set as a control idea is already described** | Bibliographic details not verified - not cited |
| J. Shingleton, US 6 058 930 (2000) | One linear actuator drives the torque arms of several rows through linked members | Single drive for many rows through lever (torque) arms | Verified - cited [11] |
| R. B. Dally, US 12 355 392 B2 (2025), Sun and Steel Solar | Lever arms on torque tubes pulled by cables driven by one mechanical drive | **Very close to our drive wire + lever arm mechanism** | Verified on Google Patents / IPQwery (dates not checked at USPTO) - cited [12] |
| US 11 646 694, "Winch-pulley drive system for solar tracker" | Winch and pulleys drive a tracker | Winch drive | Title only seen - not cited |

## What we did NOT find (the contributions we claim)

1. A measure of how close a sensor-driven tilt controller gets to the **best possible angle** for the same crop-plus-electricity objective, tested with sensor noise, faulty sensors and an error in the crop light model.
2. An **ablation** that shows which sensors that accuracy depends on (the PAR sensor matters only when the light model is wrong; the stress sensors add 0.4 to 0.8 point).
3. The specific **online correction of the crop light model** from the ratio of under-panel PAR to sky irradiance, with a fault guard, evaluated across seven climates.

The paper words these as "we did not find", not "this is the first". The 45 degree offset lever arm, the closed-loop drive wire, the flat rain-harvest mode on a wire-rope canopy and the storm stow are design details built on known principles; we do not claim them as inventions.

## Patent advice

Because US 12 355 392 B2 (lever arms pulled by cables from one drive) and the linked-row trackers already exist, a patent on the mechanism is unlikely to succeed without a professional search. A claim on the control method would also need a search of the crop-state feedback literature listed in the 2026 review.
