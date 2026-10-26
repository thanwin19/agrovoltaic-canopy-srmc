# Review 2 - Solar resource, shadow and light model

**Goal.** Model the sun, the electricity from the panels and the light that reaches the crops, and validate against independent references.

## What was done

- Solar geometry for TCE (9.88 N); monthly clearness index from NASA POWER; Erbs diffuse split.
- PV module model: Huld (2010) as used by PVGIS plus an incidence-angle modifier.
- 2-D ray casting of the canopy shadow and sky-view factor at 40 ground points for every hour of a representative day per month.
- Light vs electricity trade-off: fixed tilt sweep, zone light by month (about 12-41 %, mean 34 %).
- PV validated against PVGIS (ERA5, horizontal, 14 % loss): annual energy +5.0 %, of which +5.2 % is the sunshine dataset (NASA vs ERA5).
- Shadow model validated against Blender Cycles 3-D ray tracing: mean absolute difference 0.010 in lit fraction; 96 % of 80 comparisons within 0.10.

## Where the results are

- Figures: `results/figures/` (sun path, zone light, tilt trade-off, PV vs PVGIS, shading scatter)
- Validation logs: `results/validation_logs/`

## What to say honestly

- Monthly-mean sky (no day-to-day cloud), isotropic diffuse.
- Validated against PVGIS and Blender, NOT against field measurements.
- The earlier version over-predicted energy by 11 %; the fix and its reason are documented.

## How to reproduce

MATLAB: the scripts in `matlab/` run directly from this folder (open MATLAB, `cd` into `matlab`). They read data and the design file from `../_project_core` and write their outputs to `../_project_core/out/`. Other files in `code_reference/` are read-only copies; the master versions are in `../_project_core`.

- `MATLAB (cd into matlab in this review folder): srmc_run()`
- `node tools/validate_pv.js` (from `_project_core`)
- `node tools/shade_ref.js` then `D:/blender.exe -b -P blender/validate_shading.py`

## Documents still needed to turn assumptions into evidence

- Local radiation data (IMD / TNAU station) to compare with NASA/ERA5
- PV module datasheet

## Everything in this folder

| File |
|---|
| `code_reference/shade_ref.js` |
| `code_reference/validate_pv.js` |
| `code_reference/validate_shading.py` |
| `matlab/build_simulink_controller.m` |
| `matlab/srmc_master.m` |
| `matlab/srmc_plots.m` |
| `matlab/srmc_run.m` |
| `matlab/srmc_sensitivity.m` |
| `matlab/structural_check.m` |
| `ppt/Review2_Solar_and_Shadow.pptx` |
| `results/figures/fig1_sunpath.png` |
| `results/figures/fig2_zone_light.png` |
| `results/figures/fig3_tilt_tradeoff.png` |
| `results/figures/val_pv_vs_pvgis.png` |
| `results/figures/val_shading_scatter.png` |
| `results/validation_logs/pv_validation.csv` |
| `results/validation_logs/pv_validation.txt` |
| `results/validation_logs/pvgis_PVGIS-ERA5.json` |
| `results/validation_logs/shade_results.json` |
| `results/validation_logs/shading_validation.txt` |


Project title: **Agrovoltaic Canopy for Protection and Sustainable Farming**.
