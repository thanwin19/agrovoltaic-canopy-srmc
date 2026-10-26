# Review 1 - Design, structure and CAD of the agrovoltaic canopy

**Goal.** Fix the geometry of the wire-driven agrivoltaic canopy, show that it can stand, and give drawings and a parts list.

## What was done

- Put every dimension in ONE design file (`design.json`) with four presets; the pivot height is derived from the required lowest-edge clearance (4.5 m + 1.25 m x sin 60 deg = 5.58 m).
- Resolved the conflict between the wire-driven specification (12.5 m bays, 3.1 m panels) and the SRMC guidelines (5 m column spacing, 4.5 m clearance).
- Structural screening with IS 875 wind (Vb = 39 m/s): the 12.5 m-bay presets FAIL (carrier rope about 16x, stays about 40x, 60 mm pivot tube about 30x over capacity).
- A checked preset passes at screening level: 5 m rope grid, 114.3x4 mm pivot tube, sag span/12, 20 mm stays (utilisation tube 0.94, rope 0.82, stay 0.71, column 0.05).
- AutoCAD drawings generated from the design file: plan, elevation (with clearance check), panel section and wire-drive layout; bill of materials (22 items).
- Mechanism animations: motor -> drum -> drive wire -> lever arm -> pivot tube -> panel tilt, and the guide-pulley (capstan friction 2.6x vs 1.02x).
- Ray-traced Blender renders of the design (hero, under-canopy, aerial, top, rain mode).

## Where the results are

- Structure: `results/structure/` (report, summary, utilisation chart, wind sweep)
- Drawings + BOM: `results/cad_drawings/` (open the .dxf in AutoCAD)
- Renders: `results/renders/`; mechanism GIFs: `results/mechanism/`
- Design file: `results/design/design.json`

## What to say honestly

- Everything is computer-only; the structure is a screening check, not a certified design.
- The rope breaking loads are indicative (0.60 x d^2 kN) and must be replaced with supplier datasheets.
- The 5 m column spacing leaves a 4.8 m lane between columns (the spec asked for 6 m; a 3 m harvester still fits).

## How to reproduce

MATLAB: the scripts in `matlab/` run directly from this folder (open MATLAB, `cd` into `matlab`). They read data and the design file from `../_project_core` and write their outputs to `../_project_core/out/`. Other files in `code_reference/` are read-only copies; the master versions are in `../_project_core`.

- `MATLAB (cd into matlab in this review folder): structural_check()`
- `node tools/export_blender.js feasible 105 9.5 0` then `python tools/make_dxf.py` (from `_project_core`)
- `bash tools/render_all.sh feasible` (Blender at D:/blender.exe)

## Documents still needed to turn assumptions into evidence

- Rope datasheets (SS316 7x19 16/20 mm, 7x7 4 mm)
- PV module datasheet and certificates
- IS 875 Part 3 (2015) map check
- Geotechnical report for anchors

## Everything in this folder

| File |
|---|
| `code_reference/design.json` |
| `code_reference/make_dxf.py` |
| `documents/SRMC_8Panel_Guide_and_Cost.docx` |
| `documents/SRMC_8Panel_Installation_Spec.html` |
| `documents/SRMC_Component_Strength_Table.docx` |
| `matlab/build_simulink_controller.m` |
| `matlab/srmc_master.m` |
| `matlab/srmc_plots.m` |
| `matlab/srmc_run.m` |
| `matlab/srmc_sensitivity.m` |
| `matlab/structural_check.m` |
| `ppt/Review1_Design_and_CAD.pptx` |
| `results/cad_drawings/SRMC_feasible_BOM.csv` |
| `results/cad_drawings/SRMC_feasible_elevation.dxf` |
| `results/cad_drawings/SRMC_feasible_elevation.png` |
| `results/cad_drawings/SRMC_feasible_plan.dxf` |
| `results/cad_drawings/SRMC_feasible_plan.png` |
| `results/cad_drawings/SRMC_feasible_section.dxf` |
| `results/cad_drawings/SRMC_feasible_section.png` |
| `results/cad_drawings/SRMC_feasible_wire_drive.dxf` |
| `results/cad_drawings/SRMC_feasible_wire_drive.png` |
| `results/design/climates.json` |
| `results/design/crops.json` |
| `results/design/design.json` |
| `results/design/soils.json` |
| `results/mechanism/guide_pulley.gif` |
| `results/mechanism/mechanism_closeup.gif` |
| `results/mechanism/mechanism_tilt.gif` |
| `results/renders/aerial.png` |
| `results/renders/hero.png` |
| `results/renders/rain.png` |
| `results/renders/top.png` |
| `results/renders/under.png` |
| `results/structure/T4_structural.csv` |
| `results/structure/structural_report.txt` |
| `results/structure/structural_summary.csv` |
| `results/structure/val_structural_utilisation.png` |
| `results/structure/wind_sweep_feasible.png` |


## Update 2026-10-25: hardware after the strength check

- Wire, joints, poles and motor were checked (`documents/SRMC_Component_Strength_Table.docx`). Carrier rope 0.37, stay 0.30, tube 0.76, bearings 0.37, column 0.05 at 140 km/h: good.
- Four weak items were changed in `design.json` (feasible preset), the parts list and the DXF notes: drive wire 4 mm -> 6 mm SS316 7x19, winch 3 kN -> 10 kN (about 0.25 kW), turnbuckle M16 -> M24 (>= 72 kN), anchors -> screw/rock or 1.6 m3 buried concrete (the old block resisted 6.6 kN of 26 kN).
- 8-panel set (4.4 kWp): weights, installation steps and cost in `documents/SRMC_8Panel_Guide_and_Cost.docx`, `SRMC_8Panel_Installation_Spec.html`, `8panel_BOM.csv`; generator `code_reference/build_hardware_docs.py`. Cost mid about INR 7.2 lakh, indicative.
- Wind stow: anemometer plus a 45 deg offset lever arm (the plain arm has no lever at 90 deg).
- Drawings and animations are regenerated for the final design: `results/cad_drawings/` (plan, elevation with anemometer mast and 90 deg stow, section and wire drive with the offset arm, parts list), `results/mechanism/mechanism_closeup.gif` and `mechanism_tilt.gif` (generators: `code_reference/derive_final_dxf.py` then `make_dxf_final.py`, and `make_mech_gifs.py`). The guide-pulley GIF and the Blender renders are from the first design.
