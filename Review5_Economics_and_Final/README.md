# Review 5 - Economics, farmer income and final conclusions: Agrovoltaic Canopy for Protection and Sustainable Farming

**Goal.** Show the business case (industry buys the power, the farmer earns a monthly income), how uncertain it is, and give the final report.

## What was done

- Business model: the industry pays a tariff for the electricity; the farmer receives a share every month plus crop income at harvest.
- Farmer monthly income chart; one-at-a-time sensitivity (farmer share and tariff dominate); Monte Carlo with 20,000 draws: farmer income P5/P50/P95 = 1.41 / 2.12 / 2.99 lakh per month per hectare.
- Investor payback is the weak link: about 15 years needs roughly INR 6.2/kWh at a 30 % farmer share.
- Final report, A3 poster, viva Q&A, expo playbook, proof index (every claim -> evidence -> command) and references.

## Where the results are

- Figures: `results/figures/`
- Tables: `results/tables/`
- Final report, poster, viva, proof index: `documents/`

## What to say honestly

- Every price (tariff INR 3/kWh, farmer share 30 %, capex, crop prices) is an ASSUMPTION; replace them with a real PPA or lease figure before presenting numbers as results.
- The study is simulation-only; no field data, no patent search.

## How to reproduce

MATLAB: the scripts in `matlab/` run directly from this folder (open MATLAB, `cd` into `matlab`). They read data and the design file from `../_project_core` and write their outputs to `../_project_core/out/`. Other files in `code_reference/` are read-only copies; the master versions are in `../_project_core`.

- `MATLAB (cd into matlab in this review folder): srmc_master(); srmc_sensitivity()`

## Documents still needed to turn assumptions into evidence

- PPA term sheet or industrial open-access tariff
- PM-KUSUM / state scheme guidelines
- Mandi price series
- CEA grid emission factor
- Prior-art / patent search record

## Everything in this folder

| File |
|---|
| `documents/final_report/SRMC_Final_Report.docx` |
| `documents/one_page_summaries/SRMC_Judge_Summary.html` |
| `documents/one_page_summaries/SRMC_Results_Sheet.html` |
| `documents/poster/SRMC_Poster_A3.pdf` |
| `documents/poster/SRMC_Poster_A3.png` |
| `documents/poster/SRMC_Poster_A3.pptx` |
| `documents/proof_and_references/NEEDED_DOCUMENTS.md` |
| `documents/proof_and_references/PROOF_INDEX.csv` |
| `documents/proof_and_references/PROOF_INDEX.md` |
| `documents/proof_and_references/README_PACK.md` |
| `documents/proof_and_references/REFERENCES.md` |
| `documents/proof_and_references/SHA256_manifest.csv` |
| `documents/viva_and_expo/SRMC_Expo_Playbook.docx` |
| `documents/viva_and_expo/SRMC_Expo_Playbook.md` |
| `documents/viva_and_expo/SRMC_Viva_QA.docx` |
| `documents/viva_and_expo/SRMC_Viva_QA.md` |
| `matlab/build_simulink_controller.m` |
| `matlab/srmc_master.m` |
| `matlab/srmc_plots.m` |
| `matlab/srmc_run.m` |
| `matlab/srmc_sensitivity.m` |
| `matlab/structural_check.m` |
| `ppt/Review5_Economics_and_Final.pptx` |
| `results/figures/fig12_tornado_farmer_income.png` |
| `results/figures/fig13_tornado_payback.png` |
| `results/figures/fig14_montecarlo.png` |
| `results/figures/fig9_farmer_income.png` |
| `results/figures/lcoe_vs_tariff.png` |
| `results/tables/T5_tornado.csv` |
| `results/tables/T7_montecarlo_rank_correlation.csv` |
| `results/tables/T8_breakeven_tariff.csv` |
| `results/tables/lcoe_table.csv` |
| `results/tables/sensitivity_summary.md` |


## Update 2026-10-25

- Title and wording changed to **Agrovoltaic Canopy for Protection and Sustainable Farming**; the report has a new section 6A (six-sensor controller and accuracy); viva Q&A and expo playbook have new questions and numbers; poster, judge summary, results sheet and accuracy scorecard are updated and self-contained.
- Electricity cost: about INR 6 to 7 per kWh with interest (`results/figures/lcoe_vs_tariff.png`), near the Tamil Nadu industrial grid charge (INR 7.50, Mercom India), above utility solar auctions (INR 2 to 2.6).
- Year-long test with noisy sensors (864 cases): 99.6 % of the best possible combined score (50 % electricity + 50 % crop light value); electricity 82 % and crop light 98 % of the best. Monthly plan 98.8 %, fixed 45 deg 91.2 %. MATLAB and the web twin make identical decisions (40 of 40).
