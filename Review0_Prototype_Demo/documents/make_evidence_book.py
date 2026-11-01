"""Builds Review0_Evidence_Book.docx: datasheets, data sources, how to trust them, judge questions.   python make_evidence_book.py"""
import os, shutil
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.abspath(os.path.join(here, '..', '..'))
P10 = os.path.join(root, 'Proof', '10_Review0_Sensors_and_Panels'); RES = os.path.join(root, 'Review0_Prototype_Demo', 'results')
d = Document()
for s in d.sections: s.left_margin = s.right_margin = Cm(1.8); s.top_margin = s.bottom_margin = Cm(1.6)
st = d.styles['Normal']; st.font.name = 'Calibri'; st.font.size = Pt(10.5)
def H(t, l=1): d.add_heading(t, l)
def Pp(t, b=False, i=False, col=None):
    p = d.add_paragraph(); r = p.add_run(t); r.bold = b; r.italic = i
    if col: r.font.color.rgb = RGBColor(*col)
    return p
def B(t): d.add_paragraph(t, style='List Bullet')
def table(head, rows, widths=None):
    t = d.add_table(rows=1, cols=len(head)); t.style = 'Light Grid Accent 1'
    for i, h in enumerate(head):
        c = t.rows[0].cells[i]; c.text = ''; r = c.paragraphs[0].add_run(h); r.bold = True; r.font.size = Pt(9.5)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ''; r = cells[i].paragraphs[0].add_run(str(v)); r.font.size = Pt(9.5)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths): row.cells[i].width = Cm(w)
    d.add_paragraph()
def pic(path, w=17):
    if os.path.exists(path): d.add_picture(path, width=Cm(w)); d.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
t = d.add_heading('Review 0 Evidence Book', 0)
Pp('Agrovoltaic Canopy for Protection and Sustainable Farming: six-sensor smart tilt controller, TCE Madurai (9.88 N, 78.08 E)', b=True)
Pp('What this is: the answers to "where did this number come from, can I see the datasheet, and why should I trust it?". Every file named here is in the Proof folder (Proof/10_Review0_Sensors_and_Panels/) and on GitHub.', i=True)
Pp('Status in one line: a validated computer simulation. The sensors are software models of real, named devices; the readings are generated or typed, not measured. No field trial yet.', b=True, col=(150, 30, 30))

H('1. The one-minute answer')
B('The system has six sensors. Each one is simulated after a real device with a published datasheet; the datasheets are downloaded and stored.')
B('Sunlight is not measured: it is calculated from the sun position and a clearness index from NASA POWER for our site, then checked against NASA POWER and the EU PVGIS datasets (daily energy within about 1 to 3 percent).')
B('The solar panel is a real model (JinkoSolar Tiger Pro JKM550M-72HL4-V, 550 Wp); 8 panels give 4.4 kWp. Its datasheet numbers are read from the downloaded official PDF.')
B('Accuracy of the co-optimisation: 99.6 percent of the best possible score over 864 noisy test cases; ordinary designs reach 80 to 91 percent.')
B('Everything is simulation; the limits are listed in section 8.')

H('2. The six sensors and their datasheets')
table(['#', 'Reading', 'Real device simulated', 'Key datasheet numbers', 'Downloaded proof file'], [
 ['1', 'Sunlight', 'Apogee SP-110 pyranometer', '0-2000 W/m2; 0.20 mV per W/m2; calibration +-5 %; non-linearity <1 % to 1750 W/m2; drift <2 %/yr; response <1 ms; 360-1120 nm', '01_pyranometer_ApogeeSP110_manual.pdf'],
 ['2', 'Plant light (PAR)', 'Apogee SQ-110 quantum sensor', '0-4000 umol/m2/s; 0.20 mV per umol; +-5 %; non-linearity <1 %; 410-655 nm', '02_PAR_ApogeeSQ110_manual.pdf'],
 ['3', 'Air temperature', 'DHT11', '0-50 deg C; +-2 deg C; digital', '03-04_airTemp_and_humidity_DHT11_datasheet.pdf'],
 ['4', 'Air humidity', 'DHT11 (same chip)', '20-90 % RH; +-5 % RH; digital', '03-04_airTemp_and_humidity_DHT11_datasheet.pdf'],
 ['5', 'Soil moisture', 'DFRobot SEN0193 v1.2 capacitive', 'output 2.5 V (dry) to 1.2 V (wet); 3.3-5.5 V supply; needs dry/wet calibration', '05_soilMoisture_DFRobotSEN0193_product_page.html and _wiki.html'],
 ['6', 'Rain', 'YL-83 / FC-37 raindrop plate with LM393', 'wet or dry; digital pin LOW when wet; trimmer sets the threshold', '06_rain_YL83_FC37_vendor_page.html (no official datasheet exists)'],
 ['7', 'Wind speed', 'Adafruit 1733 anemometer (analog)', '0.4 V = 0 m/s, 2.0 V = 32.4 m/s, speed = (V - 0.4) / 1.6 x 32.4; worst-case accuracy 1 m/s', '07_wind_Adafruit1733_datasheet_C2192.pdf and product page'],
], [0.7, 2.2, 3.6, 6.8, 4.6])
Pp('How a "simulated reading" works in the dashboard: the slider is the physical quantity, and the dashboard shows the signal the real device would output (for example 837 W/m2 on the SP-110 is 167 mV; 20 m/s on the Adafruit 1733 is 1.39 V). Every sensor can be set by hand, by slider or typed number.')
Pp('What I checked inside the downloaded files: SP-110 and SQ-110 sensitivity 0.2 mV per unit and +-5 %; DHT11 +-5 %RH and +-2 C at 25 C; the Adafruit wind formula; the Jinko electrical values, size and weight. Not verified: the rain sensor (vendor page only) and the soil sensor readings in air and water (the page does not give them).', i=True)
pic(os.path.join(RES, 'dashboard_sensors_through_a_day.png'), 17)
Pp('Figure: the dashboard. Left: the seven sensor readings, each with its device name, signal and MANUAL or AUTO tag. Right: sensors through a day.', i=True)

H('3. The solar panels')
table(['Item', 'Value (official JinkoSolar datasheet, file P1_panel_JinkoSolar_JKM550M-72HL4-V_datasheet.pdf)'], [
 ['Model', 'JinkoSolar Tiger Pro JKM550M-72HL4-V, monocrystalline'], ['Number of panels', '8 (2 rows x 4, landscape across the tube) = 4.4 kWp (hardware pack, Review 1)'],
 ['Size and weight', '2274 x 1134 x 35 mm, 28.9 kg'], ['Maximum power (test conditions)', '550 Wp'], ['Vmp / Imp', '40.90 V / 13.45 A'], ['Voc / Isc', '49.62 V / 14.03 A'], ['Efficiency', '21.33 %'],
 ['Tilt range in this project', '15-60 deg tracking, 3 deg rain, 90 deg storm stow']], [4.5, 13.4])
Pp('Where the numbers are used: the dashboard maximum-power-point tracker uses these five electrical numbers (single-diode model). The controller energy model uses 21 % module efficiency with the PVGIS temperature model. The temperature coefficients of the tracker are typical values, not read from this datasheet. The datasheet is the Chinese-language edition; the structure calculation earlier used 2278 mm and 27.5 kg from retailer listings (small difference).', i=True)

H('4. Where the sunlight comes from')
Pp('No sunlight was measured. The dashboard calculates it, and the pyranometer on screen is a stand-in that holds that value or the one you type.')
B('Sun position: standard astronomy (declination, hour angle) for 9.88 N, 78.08 E, for the day and hour on the sliders.')
B('Sunlight above the air: solar constant 1361 W/m2 corrected for the Earth-sun distance of the day.')
B('Through the sky: multiplied by a clearness index kt. Skies: Clear 0.62, Hazy 0.50, Partly cloudy 0.36, Overcast 0.18. Clear is set close to the NASA POWER April average of 0.60 for the site.')
B('Direct and diffuse split: Erbs model. PAR: 45 percent of the sunlight, 4.57 umol per joule (PAR = 2.06 x sunlight).')
B('If you move the pyranometer or PAR slider, the controller uses exactly your number.')
Pp('Datasets downloaded as proof (Proof/10_Review0_Sensors_and_Panels/sunlight_datasets/, downloaded 2026-11-01):', b=True)
table(['File', 'What it is', 'Source'], [
 ['NASA_POWER_hourly_2023-04-15_LST_TCE.json', 'hourly all-sky and clear-sky sunlight, PAR, temperature, humidity, wind for 15 April 2023', 'NASA POWER API (power.larc.nasa.gov), community AG, MJ/m2/hour'],
 ['NASA_POWER_monthly_climatology_TCE.json', 'monthly sunlight, clearness index, temperature, humidity, wind, rain', 'NASA POWER climatology API'],
 ['PVGIS_ERA5_hourly_2020_TCE.csv', 'hourly direct and diffuse sunlight, 2020', 'PVGIS (EU Joint Research Centre), ERA5'],
 ['PVGIS_monthly_radiation_TCE.csv', 'monthly sunlight 2005-2020', 'PVGIS MRcalc'],
 ['DASHBOARD_model_ghi_day105.csv', 'what the dashboard model gives for 15 April for the four skies', 'review0_physics.m']], [5.6, 7, 5.3])

H('5. How the dashboard compares with those datasets')
table(['15 April, TCE, flat ground', 'Dashboard Clear', 'NASA actual day', 'NASA clear-sky', 'PVGIS April mean', 'PVGIS clearest April-2020 day'], [
 ['Daily sunlight (Wh/m2)', '6502', '6539', '7144', '6337', '7544'], ['Noon peak (W/m2)', '837', '897', '986', '-', '1043']], [4.6, 2.5, 2.7, 2.6, 2.8, 2.8])
B('The dashboard Clear day gives the same daily energy as a real average April day: within 0.6 percent of NASA actual day, 2.6 percent above the PVGIS April mean.')
B('It is not a perfectly cloudless sky: a truly clear day gives 15 to 25 percent more at noon. Say "a typical clear April day".')
B('Shape and timing agree: RMSE 78 W/m2 against NASA actual day, 104 W/m2 against NASA clear-sky.')
B('PAR share: NASA POWER 0.444, dashboard 0.45.')
pic(os.path.join(P10, 'TRUST_sunlight_model_vs_NASA_PVGIS.png'), 17.5)
Pp('Other checks already in the project (Proof folder): yearly electricity against PVGIS +5.0 percent (03_Solar_Generation/pv_validation.txt, monthly errors 8 to 11 percent in June to August); shadow model against Blender 3-D ray tracing, mean difference 0.010 in lit fraction (shading_validation.txt); the web twin and the MATLAB model give identical results (crosscheck_js_vs_matlab.txt); Review 0 tests pass (Review0_Prototype_Demo/results/test_results.md).')

H('6. Accuracy of the co-optimisation (the main result)')
Pp('Accuracy = how close the controller angle is to the best possible angle on the combined score (half electricity, half crop light), found by trying every angle from 15 to 60 degrees at 0.5 degree steps. 100 percent = as good as the best angle.')
table(['Design', 'Combined score', 'Electricity', 'Crop light value', 'Angle error'], [
 ['Fixed 15 deg (max power)', '80.0 %', '99.2 %', '45.2 %', '34.0 deg'], ['Sun tracking', '84.0 %', '88.6 %', '64.3 %', '25.0 deg'], ['Fixed 45 deg', '91.2 %', '81.0 %', '84.6 %', '16.3 deg'],
 ['Monthly plan, no sensors', '98.8 %', '82.2 %', '96.3 %', '9.5 deg'], ['OUR controller, six noisy sensors', '99.6 %', '82.1 %', '97.7 %', '4.8 deg']], [6.2, 3, 2.7, 3.2, 2.8])
Pp('Source: Proof/05_Controller_and_Accuracy/T11_accuracy_v2.csv (864 noisy test cases, sensor noise: pyranometer and PAR 5 percent, DHT11 +-2 C and +-5 %RH, soil +-3 percent). On the Review 0 dashboard, one clear April day with datasheet-sized random sensor errors (one fixed random draw): our controller 99.4 percent, fixed 45 degrees 87.0 percent, plain sun tracking 87.5 percent.')
pic(os.path.join(RES, 'ACCURACY_obtained_vs_ordinary.png'), 17.5)

H('7. Where every input came from (data lineage)')
table(['Input', 'Source', 'Real, typical or assumed'], [
 ['Weather (monthly temperature, humidity, wind, rain, clearness index)', 'NASA POWER climatology, 9.88 N 78.08 E', 'Real dataset (monthly means)'],
 ['Sunlight reference for checks', 'PVGIS-ERA5, NASA POWER', 'Real datasets (satellite/reanalysis, not a roof sensor)'],
 ['Sun position', 'astronomical equations', 'Physics'],
 ['Sensor behaviour (range, accuracy, signal)', 'manufacturer datasheets, files in sensor_datasheets/', 'Published datasheet values'],
 ['Sensor readings in every run', 'calculated or typed', 'SIMULATED'],
 ['Panel electrical values', 'JinkoSolar datasheet', 'Published datasheet values'],
 ['Module efficiency in the energy model (21 %), system loss 14 %', 'typical monocrystalline module, PVGIS default', 'Typical'],
 ['Soil, crop light limits, crop prices, tariff, farmer share', 'typical library values and project assumptions (Proof/01_Data_and_Sources/DATASET_SOURCES.md)', 'Typical / assumed, not measured at TCE']], [6.2, 6.4, 5.3])

H('8. Limits (say them before a judge does)')
for x in ['It is a simulation. No field trial and no sensor was wired. Sensor readings are generated or typed, not measured.',
          'NASA POWER and PVGIS are satellite and reanalysis products, not a pyranometer on the TCE roof: this is a check, not a field validation.',
          'One day (15 April) was compared hour by hour; the year is checked monthly (PVGIS +5 percent; 8 to 11 percent in June to August).',
          'The dashboard Clear sky is a typical clear April day, below a perfectly cloudless sky (noon 837 against 986 W/m2).',
          'Accuracy is measured against the controller own goal (half electricity, half crop light) in simulation, not against real crop yield.',
          'The rain sensor has no official datasheet, only vendor pages. The Jinko datasheet is the Chinese-language edition.',
          'Prices, farmer share and crop values are assumptions.']: B(x)

H('9. Questions a judge may ask')
for q, a in [('Are the sensors real?', 'No. They are software models of real devices (SP-110, SQ-110, DHT11, SEN0193, YL-83, Adafruit 1733), set from their datasheets. The datasheets are in the proof folder. Hardware is the next step.'),
             ('Where does the sunlight number come from?', 'It is calculated from the sun position and a clearness index from NASA POWER for our site, and checked against NASA POWER and PVGIS (daily energy within about 1 to 3 percent, PAR share 0.444 against 0.45).'),
             ('Why should I trust the accuracy figure?', 'It is the controller score against the best angle found by trying every angle, with datasheet-sized sensor errors added; the data file is T11_accuracy_v2.csv. It measures our own goal in simulation, not crop yield.'),
             ('Which solar panel?', 'JinkoSolar Tiger Pro JKM550M-72HL4-V, 550 Wp, 8 panels = 4.4 kWp; the datasheet is stored.'),
             ('Why is the clear sky 837 W/m2 and not 1000?', 'The dashboard Clear day is a typical clear April day (clearness index 0.62, close to the NASA POWER April mean 0.60). A perfectly cloudless day gives about 986 W/m2.'),
             ('What is new?', 'Choosing the panel angle from sensors to co-optimise crop light and electricity, with a safety layer for rain, wind and faulty sensors.'),
             ('What is next?', 'Build the real sensor set, log a month, compare with the twin; measure crop light or yield; finish the paper.')]:
    p = d.add_paragraph(); r = p.add_run('Q: ' + q + '  '); r.bold = True; p.add_run('A: ' + a)

H('10. Where to find things')
table(['What', 'Where'], [
 ['Sensor datasheets', 'Proof/10_Review0_Sensors_and_Panels/sensor_datasheets/'], ['Sunlight datasets', 'Proof/10_Review0_Sensors_and_Panels/sunlight_datasets/'],
 ['Sunlight trust figure and numbers', 'TRUST_sunlight_model_vs_NASA_PVGIS.png, TRUST_numbers.json'], ['Accuracy figure', 'ACCURACY_obtained_vs_ordinary.png; data Proof/05_Controller_and_Accuracy/T11_accuracy_v2.csv'],
 ['Sources and sensor/panel table (Markdown)', 'SENSOR_AND_PANEL_PROOF.md, WHERE_SUNLIGHT_COMES_FROM_AND_WHY_TRUST_IT.md'], ['Data lineage of the whole project', 'Proof/01_Data_and_Sources/DATASET_SOURCES.md'],
 ['Dashboard', 'Review0_Prototype_Demo/matlab/review0_dashboard.m (type review0_dashboard in MATLAB)'], ['Checksums of every proof file', 'Proof/MANIFEST.csv'], ['Code', 'GitHub: thanwin19/agrovoltaic-canopy-srmc']], [5.5, 12.4])
out = os.path.join(here, 'Review0_Evidence_Book.docx'); d.save(out); shutil.copy(out, os.path.join(P10, 'Review0_Evidence_Book.docx')); print('saved', out)
