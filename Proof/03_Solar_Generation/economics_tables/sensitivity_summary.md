# Sensitivity and uncertainty study (TCE ground, per hectare)

Base case: farmer income 198943 INR/month, investor payback 40.9 years (industry pays INR 3.0/kWh, farmer share 30 %, capex INR 60000/kWp).

## Monte Carlo (20000 draws, triangular inputs, ranges in T5)

| outcome | P5 | P50 | P95 |
|---|---|---|---|
| Farmer income (INR/month/ha) | 140924 | 211562 | 299123 |
| Investor payback (years) | 21.3 | 37.1 | 78.3 |
| Total annual value (INR lakh/ha) | 41.1 | 57.4 | 78.3 |

- Probability farmer income >= INR 1.0 / 1.5 / 2.0 lakh per month: **100 % / 92 % / 60 %**
- Probability investor payback <= 15 / 20 / 25 years: **0 % / 3 % / 13 %**

## Weather scenarios (full model re-run)

| scenario | pv_kWh_m2 | rain_harvested_m3 | irrigation_demand_m3 | borewell_topup_m3 | rain_fed_pct | crop_net_lakh | farmer_inr_month |
|---|---|---|---|---|---|---|---|
| Base year | 237.55 | 4635.00 | 4933.69 | 298.69 | 93.95 | 2.52 | 198942.90 |
| Drier year (rain -30 %) | 237.55 | 4072.48 | 4508.86 | 436.38 | 90.32 | 2.27 | 196847.23 |
| Wetter year (rain +20 %) | 237.55 | 4926.85 | 5220.89 | 294.04 | 94.37 | 2.63 | 199848.38 |
| Cloudier (sunshine -5 %) | 226.61 | 4636.96 | 4935.03 | 298.07 | 93.96 | 2.58 | 191269.65 |
| Clearer (sunshine +5 %) | 248.57 | 4591.50 | 4907.36 | 315.86 | 93.56 | 2.40 | 206194.83 |

## Strongest drivers of farmer income (rank correlation)

| input | rank_corr_farmer_income | rank_corr_payback |
|---|---|---|
| Farmer share of payment | 0.84 | 0.38 |
| Industry tariff (INR/kWh) | 0.49 | -0.56 |
| PV energy model error (x) | 0.10 | -0.11 |
| Crop price (x) | 0.07 | 0.00 |
| Crop yield (x) | 0.07 | 0.00 |
| Capex (INR/kWp) | -0.01 | 0.57 |
| Capital subsidy | -0.00 | -0.22 |
| O&M (% of capex/yr) | 0.00 | 0.33 |

## Break-even: tariff the industry must pay for a given investor payback (base capex, base physics)

| target_investor_payback_yr | farmer_share | tariff_needed_inr_per_kwh | farmer_income_inr_month |
|---|---|---|---|
| 10.00 | 0.10 | 6.81 | 155648.93 |
| 10.00 | 0.30 | 8.76 | 540374.12 |
| 10.00 | 0.50 | 12.26 | 1232879.45 |
| 15.00 | 0.10 | 4.83 | 116590.66 |
| 15.00 | 0.30 | 6.22 | 389720.78 |
| 15.00 | 0.50 | 8.70 | 881355.01 |
| 20.00 | 0.10 | 3.85 | 97061.53 |
| 20.00 | 0.30 | 4.95 | 314394.12 |
| 20.00 | 0.50 | 6.92 | 705592.78 |

Input ranges are judgement-based (no market survey). Physics-model error is represented by a +-% band around PVGIS agreement (-8 % to +5 %). Prices, tariff and farmer share are assumptions to be replaced with real quotes.
