# Dimensions, heights, wire lengths and weights (feasible preset, 25 m x 25 m demonstration unit)

| Item | Value | Source |
|---|---|---|
| Panels | 10 pivoting strips, 2.497 m wide, 25 m long, pitch 2.5 m | design.json |
| Pivot-axis height | 5.58 m (= 4.5 m lowest-edge clearance + 1.248 x sin 60 deg) | design.json, derived |
| Lowest panel edge at 60 deg | 4.5 m (harvester 4.1 m high fits) | design.json |
| Tilt range | 15 to 60 deg working, 3 deg rain mode, 90 deg storm stow | design.json |
| Columns | 36 x RHS 200 x 200 x 6 mm, 6.73 m long, 5 m grid | BOM |
| Pivot tube | CHS 114.3 x 4 mm, one per panel, 25 m long | design.json |
| Carrier rope | SS316 16 mm 7x19, span 5 m, sag span/12 = 0.42 m, about 153 m in total, 149 kg | BOM, supplier 0.975 kg/m |
| Stay rope | SS316 20 mm, about 223 m, 340 kg | BOM |
| Drive wire | SS316 6 mm 7x19, about 33 m | design.json, BOM |
| Winch | 10 kN, about 0.25 kW, encoder 0.5 deg | design.json |
| Gutter / cistern | 0.3 x 0.2 m gutter; cistern 100 m3 (4 x 4 m, 3 m deep) | design.json |

SS316 7x19 rope weight (supplier listings, GS Products): 8 mm 0.2438, 10 mm 0.381, 12 mm 0.5486, 16 mm 0.9754 kg/m; rule 0.00381 x d^2 kg/m. Wind check: 39 m/s (IS 875-3), see 02_Geometry_Wire_Heights/structural_report.txt.
