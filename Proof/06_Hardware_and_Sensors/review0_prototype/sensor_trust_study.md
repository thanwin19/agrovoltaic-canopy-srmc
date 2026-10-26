# Can the simulated pyranometer and PAR sensor be trusted? (day-wide sensitivity)

For every half hour from 7 to 17 h on day 105 (TCE) the controller decides with a sensor reading that is wrong by the stated percentage (either sensor, either sign); the decision is then judged under the true conditions. Loss = what the farm gives up compared with the decision from a perfect reading (energy: PV per m2 of panel; crop: crop-light score). Mean, 90th percentile and maximum over the 21 half-hours.

| sky | mode | sensor error | energy loss mean | p90 | max | crop loss mean | p90 | mean angle shift |
|---|---|---|---|---|---|---|---|---|
| Clear day | plain | +-5 % | 2.5 % | 11.2 % | 19.7 % | 2.7 % | 7.2 % | 2.2 deg |
| Clear day | plain | +-10 % | 5.1 % | 22.0 % | 35.4 % | 5.8 % | 26.8 % | 3.2 deg |
| Clear day | plain | +-20 % | 9.7 % | 37.4 % | 43.7 % | 7.0 % | 27.6 % | 4.9 deg |
| Clear day | robust (+-10 % worst case) | +-5 % | 4.0 % | 15.2 % | 27.8 % | 3.6 % | 21.4 % | 3.0 deg |
| Clear day | robust (+-10 % worst case) | +-10 % | 5.7 % | 17.4 % | 27.8 % | 3.8 % | 21.4 % | 3.1 deg |
| Clear day | robust (+-10 % worst case) | +-20 % | 12.5 % | 34.2 % | 39.3 % | 4.9 % | 23.1 % | 5.7 deg |
| Partly cloudy day | plain | +-5 % | 1.2 % | 3.7 % | 4.0 % | 0.6 % | 3.1 % | 1.8 deg |
| Partly cloudy day | plain | +-10 % | 2.0 % | 4.1 % | 18.4 % | 2.5 % | 4.2 % | 4.7 deg |
| Partly cloudy day | plain | +-20 % | 3.2 % | 8.1 % | 18.4 % | 2.6 % | 4.2 % | 6.1 deg |
| Partly cloudy day | robust (+-10 % worst case) | +-5 % | 1.5 % | 5.1 % | 16.2 % | 0.5 % | 2.4 % | 2.4 deg |
| Partly cloudy day | robust (+-10 % worst case) | +-10 % | 2.0 % | 6.6 % | 16.2 % | 0.9 % | 3.6 % | 3.2 deg |
| Partly cloudy day | robust (+-10 % worst case) | +-20 % | 2.6 % | 9.1 % | 16.2 % | 3.0 % | 4.9 % | 5.9 deg |
