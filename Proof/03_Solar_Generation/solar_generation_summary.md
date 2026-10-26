# Solar generation, how it was calculated

Site: TCE Ground, Madurai (plains, semi-arid tropical), 9.88 N, 78.08 E, elevation 219 m.
Sunshine data: NASA POWER monthly clearness index (file climates.json); PV model: Huld (2010) crystalline-silicon power model with an incidence-angle modifier and row self-shading, 21 % module efficiency, 14 % system loss (same model family as PVGIS).

| Quantity | Value |
|---|---|
| Panel area per hectare (cover 99.9 %) | 9988 m2 |
| Installed power per hectare | 2097 kWp |
| PV output, annual mean | 238.1 kWh per m2 of panel per year |
| Energy per hectare per year | 2378 MWh |
| Specific yield | 1134 kWh per kWp per year |
| Sunshine on flat ground (GHI) | 2033 kWh/m2 per year |
| Demonstration unit (10 panels, 2.497 m x 25 m, 25 m x 25 m field) | 624 m2 of panel, 131 kWp, about 149 MWh per year |
| 8-module set (8 x 550 Wp) | 4.4 kWp, about 4989 kWh per year |

Note on the layout: the specification layout is a sealed flat catchment (panels cover about 100 % of the land), which is why the power per hectare is so large. The twin also offers open agri-PV layouts (about 50 % and 25 % cover) with proportionally less power and more crop light.

Why the yield per kWp (1,134) is below a flat-panel PVGIS value (1,419 kWh/kWp): the controller tilts the panels away from the sun to give the crop light, and neighbouring rows shade each other. A PV-only fixed 15 degree design gives 291 kWh/m2 against 238 kWh/m2 for the co-optimised controller (see 05_Controller_and_Accuracy).

Validation: model versus PVGIS (ERA5, 2005 to 2023) for the same site on a flat plane: +5.0 % per year (sunshine data differ by +5.2 %). Files: 03_Solar_generation/pv_validation.txt and pvgis_PVGIS-ERA5.json.
