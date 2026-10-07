# KMC Voltage-Dependent Forming Study

## 1. Objective

Measure stochastic forming behavior across 0.15–0.50 V using the frozen Stage 8 KMC mechanism, without calibration or parameter fitting.

## 2. Frozen KMC Mechanism

Ag/PVA/Pt, 100 nm PVA, 25 x 15 lattice, 4 nm spacing, 4-neighbor hopping and growth, no diagonal growth, immediate Ag+ adjacency for growth, growth multiplier 1.0, and SET at the final PVA row adjacent to Pt. Pt cells are never overwritten.

## 3. Simulation Conditions

- Temperature: 300 K.
- Event cap: 20,000 per run.
- All kinetic parameters and the random-number implementation were unchanged.

## 4. Voltage Range

0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, and 0.50 V.

## 5. Random Seeds

Seeds 42 through 51 were used at every voltage: 80 total simulations.

## 6. Forming Probability Results

| Voltage (V) | Runs | SET runs | Non-SET runs | Event-cap runs | Forming probability |
|---:|---:|---:|---:|---:|---:|
| 0.15 | 10 | 0 | 10 | 10 | 0.000 |
| 0.20 | 10 | 0 | 10 | 9 | 0.000 |
| 0.25 | 10 | 0 | 10 | 9 | 0.000 |
| 0.30 | 10 | 0 | 10 | 8 | 0.000 |
| 0.35 | 10 | 0 | 10 | 10 | 0.000 |
| 0.40 | 10 | 0 | 10 | 10 | 0.000 |
| 0.45 | 10 | 0 | 10 | 10 | 0.000 |
| 0.50 | 10 | 0 | 10 | 10 | 0.000 |

Total event-cap terminations: 76 of 80 runs.
More than half of all runs hit the event cap; forming probabilities and non-SET outcomes are therefore window-limited and should not be interpreted as intrinsic failure probabilities. The cap was not increased.

## 7. Forming-Time Results

Only SET runs are included. Blank/NaN entries indicate no SET runs at that voltage. Statistics with fewer than two SET runs are low-sample.

| Voltage (V) | SET count | Mean (s) | Median (s) | Std (s) | Min (s) | Max (s) |
|---:|---:|---:|---:|---:|---:|---:|
| 0.15 | 0 | NaN | NaN | NaN | NaN | NaN | low-sample
| 0.20 | 0 | NaN | NaN | NaN | NaN | NaN | low-sample
| 0.25 | 0 | NaN | NaN | NaN | NaN | NaN | low-sample
| 0.30 | 0 | NaN | NaN | NaN | NaN | NaN | low-sample
| 0.35 | 0 | NaN | NaN | NaN | NaN | NaN | low-sample
| 0.40 | 0 | NaN | NaN | NaN | NaN | NaN | low-sample
| 0.45 | 0 | NaN | NaN | NaN | NaN | NaN | low-sample
| 0.50 | 0 | NaN | NaN | NaN | NaN | NaN | low-sample

## 8. Filament Morphology

Representative selection rule: if SET occurs, choose the SET run closest to the median forming time. Otherwise choose the run with the deepest filament, breaking ties by filament-site count and then lowest seed. The morphology CSVs contain the actual final lattice states.

- 0.15 V: seed 49, depth row 3, SET=False; deepest filament; ties resolved by most filament sites then lowest seed.
- 0.20 V: seed 42, depth row 3, SET=False; deepest filament; ties resolved by most filament sites then lowest seed.
- 0.25 V: seed 46, depth row 2, SET=False; deepest filament; ties resolved by most filament sites then lowest seed.
- 0.30 V: seed 46, depth row 3, SET=False; deepest filament; ties resolved by most filament sites then lowest seed.
- 0.35 V: seed 43, depth row 3, SET=False; deepest filament; ties resolved by most filament sites then lowest seed.
- 0.40 V: seed 48, depth row 4, SET=False; deepest filament; ties resolved by most filament sites then lowest seed.
- 0.45 V: seed 42, depth row 3, SET=False; deepest filament; ties resolved by most filament sites then lowest seed.
- 0.50 V: seed 50, depth row 3, SET=False; deepest filament; ties resolved by most filament sites then lowest seed.

## 9. Event Statistics

Growth and nucleation plots use mean ± standard deviation across the ten seeds. The maximum-depth plot uses the same mean ± standard deviation convention. Individual run data are preserved in the full CSV.

## 10. Comparison With Continuous v1.1/v1.2 Model

The separate continuous phenomenological model reports SET near +0.282 V and a positive-bias SET time near 0.141 s at 300 K and 100 nm PVA. The KMC is stochastic and uses a different coarse-grained mechanism; these values are contextual comparisons, not requirements or validation targets.

## 11. Literature Context

Existing project context reports an Ag/Ag-salt-incorporated PVA/Pt device near 100 nm PVA with experimental SET around +0.27 V. This is reported as literature context only and was not used to fit or tune the KMC model.

## 12. Scientific Interpretation

No SET was observed in any of the 80 runs, so the sampled forming probability was 0/10 at every tested voltage. This does not establish zero physical forming probability: 76/80 runs ended at the 20,000-event cap, making those outcomes finite-window non-SET observations. The other four runs stopped earlier because the engine had no active event; these are distinct from event-cap terminations.

Within this finite window, filament depth does not increase monotonically with voltage. Mean maximum depth by voltage was 1.9, 2.0, 1.9, 1.9, 2.1, 2.4, 2.1, and 2.2 rows from 0.15 through 0.50 V. Growth-event means were 6.1, 6.0, 6.2, 5.7, 5.7, 5.7, 5.5, and 5.2; nucleation-event means were 11.3, 11.3, 10.9, 11.7, 12.2, 11.9, 11.3, and 11.8. These small, non-monotonic changes do not support a clear voltage trend in morphology or event counts. No exponential or power-law fit was applied.

## 13. Limitations

- The 4 nm lattice and local growth rule are coarse-grained assumptions.
- The 20,000-event cap limits interpretation where many runs terminate at the cap.
- Ten seeds per voltage provide an initial stochastic sample, not a precise threshold estimate.
- No temperature, thickness, RESET, or literature-calibration study was performed.

## 14. Reproducibility

Every voltage-seed pair was run twice inside the study runner for deterministic comparison before its first result was recorded. The required exact cases were also checked separately after the sweep.

## 15. Conclusion

The frozen 4-neighbor mechanism was preserved. The requested 80-run sweep and deliverables are complete, but the intended forming-probability and forming-time voltage dependence remains inconclusive: no SET occurred, and 76 runs hit the event cap. These finite-window KMC observations remain separate from the continuous-model result (+0.282 V, 0.141 s) and the literature context (approximately +0.27 V). The study does not validate or contradict either comparison. A suitable Stage 10 recommendation is to investigate event-window adequacy and termination behavior before drawing threshold conclusions; retain the frozen kinetics unless a separately justified study is approved.
