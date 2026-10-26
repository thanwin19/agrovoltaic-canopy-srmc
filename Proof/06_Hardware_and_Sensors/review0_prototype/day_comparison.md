# One-day comparison (day 105, TCE, 6-18 h in 0.5 h steps, simulated sky)

PV in kWh per m2 of panel per day; crop-light score = irradiance-weighted mean of the zone light factors (1 = every zone gets the light its crop needs). "of best" = percentage of the best strategy in that condition.

| condition | strategy | PV kWh/m2/day | crop score | PV | Clear day | Fixed 15 deg (PV-max) | 0.923 | 0.238 | 94.8 | 36.0 | **65.4** |
| Clear day | Fixed 45 deg | 0.717 | 0.536 | 73.6 | 81.0 | **77.3** |
| Clear day | East-west sun tracking | 0.974 | 0.177 | 100.0 | 26.7 | **63.4** |
| Clear day | SRMC controller (50/50) | 0.735 | 0.588 | 75.5 | 88.9 | **82.2** |
| Clear day | Energy-only controller (w=1) | 0.939 | 0.262 | 96.5 | 39.6 | **68.0** |
| Clear day | Crop-only controller (w=0) | 0.625 | 0.661 | 64.2 | 100.0 | **82.1** |
| Partly cloudy day | Fixed 15 deg (PV-max) | 0.565 | 0.263 | 100.0 | 31.5 | **65.7** |
| Partly cloudy day | Fixed 45 deg | 0.479 | 0.704 | 84.6 | 84.3 | **84.5** |
| Partly cloudy day | East-west sun tracking | 0.531 | 0.437 | 93.9 | 52.3 | **73.1** |
| Partly cloudy day | SRMC controller (50/50) | 0.441 | 0.810 | 78.0 | 97.0 | **87.5** |
| Partly cloudy day | Energy-only controller (w=1) | 0.566 | 0.267 | 100.0 | 31.9 | **66.0** |
| Partly cloudy day | Crop-only controller (w=0) | 0.417 | 0.835 | 73.8 | 100.0 | **86.9** |
| Hot clear day (VPD stress) | Fixed 15 deg (PV-max) | 0.887 | 0.285 | 94.8 | 40.2 | **67.5** |
| Hot clear day (VPD stress) | Fixed 45 deg | 0.688 | 0.595 | 73.6 | 83.8 | **78.7** |
| Hot clear day (VPD stress) | East-west sun tracking | 0.935 | 0.228 | 100.0 | 32.0 | **66.0** |
| Hot clear day (VPD stress) | SRMC controller (50/50) | 0.742 | 0.623 | 79.4 | 87.7 | **83.6** |
| Hot clear day (VPD stress) | Energy-only controller (w=1) | 0.902 | 0.316 | 96.5 | 44.5 | **70.5** |
| Hot clear day (VPD stress) | Crop-only controller (w=0) | 0.612 | 0.711 | 65.5 | 100.0 | **82.7** |
