Using only `./inputs/materials/trial_measurements.csv`, create a small biostatistics summary CSV.

Write the final CSV to `./outputs/biomarker_summary.csv`.

The output CSV must have one row per cohort and these columns:

- `cohort`
- `n`
- `mean_baseline_ldl`
- `mean_week12_ldl`
- `mean_change_ldl`
- `responder_count`
- `responder_rate`

A responder is a participant whose LDL changed by `-15.0` mg/dL or lower from baseline to week 12. Round means and responder rates to three decimal places. Do not use external packages.
