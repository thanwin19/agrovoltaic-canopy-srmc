# Crop-light measurement protocol (to replace the calculated light with real readings)

Goal: compare the measured daily light integral (DLI, mol/m2/day) under the panels with the calculated one (`par_under_ctrl_umol` and `par_under_fixed45_umol` in the simulated file).

Equipment: one quantum (PAR) sensor or a calibrated PAR/lux meter (a lux meter needs a conversion factor for sunlight, about 0.0185 umol/m2/s per lux; a PAR sensor is better), a data logger or a phone camera to record readings, a tripod at crop height.

Method:
1. Choose 4 points under the panels (one in each crop zone) and 1 point in the open at the same height.
2. Read the PAR (umol/m2/s) at all 5 points every hour from 07:00 to 17:00 on at least 5 clear and 5 cloudy days; write the panel tilt shown by the controller.
3. DLI of a point = sum of hourly PAR x 3600 / 1,000,000 (mol/m2/day), using the mean of the readings at the start and end of each hour if you can.
4. Compare: measured under-canopy / open-field light against the calculated ratio (calculated: about 27 % in October 2023).

Record in `crop_light_readings_template.csv` (date, hour, tilt_deg, point, PAR_umol_m2_s, sky_note). Report the mean difference between measured and calculated light in percent, and say how many days were measured.
