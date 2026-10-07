# Coarse-Grained KMC Simulation of Organic Ag/PVA/Pt CBRAM

## 1. Introduction

This report consolidates the frozen coarse-grained KMC mechanism validation, Stage 10A event-window diagnostic, and final voltage, temperature, and thickness studies. The objective is to characterize model outcomes honestly, not to fit literature or force SET.

## 2. Device Structure

Ag / PVA / Pt, nominal PVA thickness 100 nm, 300 K baseline. The baseline lattice is 25 x 15: row 0 Ag, rows 1–23 PVA state sites, row 24 Pt. Cell spacing is 4 nm. The row-count convention includes electrode boundary rows, so literal PVA-state rows span 92 nm; the 100 nm/25-row mapping is a documented coarse numerical convention.

## 3. Literature Context

The project records an Ag/Ag-salt-incorporated PVA/Pt device near 100 nm and experimental SET around +0.27 V, with RESET around -0.13 V. These values are contextual literature references, not calibration targets.

## 4. KMC Model

### 4.1 Lattice

Coarse 4 nm sites, with row 0 Ag and the final row Pt. Baseline active PVA sites occupy rows 1–23.

### 4.2 Ag+ generation

Empty sites immediately below the Ag electrode can receive Ag+.

### 4.3 Ag+ hopping

Ag+ hops to empty 4-neighbor sites. Rate is Arrhenius with a signed field-assisted effective barrier under uniform E=V/d.

### 4.4 Nucleation

An Ag+ on row 1 may stochastically convert to an Ag filament site.

### 4.5 Filament growth

An Ag+ immediately 4-neighbor adjacent to filament may convert into a filament site. Diagonal growth is disabled; disconnected nuclei are permitted; growth multiplier is 1.0.

### 4.6 SET criterion

SET occurs only when a 4-neighbor-connected filament cluster reaches the final PVA row adjacent to Pt. Pt is never overwritten.

### 4.7 RESET mechanism

Not implemented in KMC. Existing KMC has no filament dissolution event or justified dissolution barrier/provenance. Continuous-model RESET was not imported into KMC.

### 4.8 Resistance model

No KMC resistance result is treated as meaningful: tested voltage trajectories did not form a complete bridge, and the engine's fixed state resistance placeholders are not a morphology-calibrated estimate. No experimental resistance was invented.

## 5. Parameter Provenance

- **Materials Project:** Ag and Pt material records/densities; electrode identities follow the project device definition.
- **Literature:** PVA device concept and approximate 100 nm thickness; contextual experimental SET/RESET/resistance references in `data/pva.json` and README.
- **Derived:** E=V/d; 4 nm hop spacing; reported physical depth from lattice rows.
- **Model assumptions:** uniform field, effective 0.25 eV activation barriers, 0.35 field coupling, 4-neighbor transport/growth, local adjacent reduction, nucleation mechanism, deposition bias 1.5, SET connectivity rule.
- **Numerical/KMC:** 1e12 s^-1 attempt frequencies, 25 x 15 baseline geometry, 20,000-event cap, random seeds, diagnostic sampling choices, 4 nm coarse grid.

## 6. Mechanism Validation

Stages 1–5 established the scaffold and baseline engine. Stage 6 growth-rate perturbations (1x/10x/100x) did not reach SET; baseline remains 1x. Stage 7 audited local deposition and found growth requires exact adjacent Ag+; sparse growth candidates compete with many hopping candidates. Stage 8 compared diagnostic spatial rules; neither alternative reached SET, and the original 4-neighbor rule was frozen. Baseline at 0.30 V/300 K/seed 42: 20,000 events; 11 nucleation; 7 growth; 19,962 hopping; 18 filament sites; depth row 2; 8 nm span; max Ag+ row 23; SET=False.

## 7. Event-Window Validation

For the same baseline trajectory at 20k, 50k, 100k, and 200k event caps, growth remained 7, nucleation 11, filament sites 18, maximum depth row 2, and filament length 8 nm. Hopping continued, and simulated time increased. The evidence supports 20,000 events as apparently adequate for observing filament evolution in this one trajectory only; it does not prove SET impossible or general cap adequacy.

## 8. Voltage-Dependent Growth

The study comprises 90 simulations at +0.10–+0.50 V, 300 K, ten seeds per voltage, with the unchanged 20,000-event cap. The enumerated voltage list has nine unique values although the request states “10 voltages x 10 seeds = 100”; the exact list was followed without adding an unrequested voltage. Mean maximum filament depth rows by voltage are [1.9, 1.9, 2, 1.9, 1.9, 2.1, 2.4, 2.1, 2.2]. Mean growth counts are [5.6, 6.1, 6, 6.2, 5.7, 5.7, 5.7, 5.5, 5.2]; mean nucleation counts are [11.1, 11.3, 11.3, 10.9, 11.7, 12.2, 11.9, 11.3, 11.8]. These are descriptive stochastic outputs; inspect the CSVs and plots for spread. No monotonic law is imposed.

Depth peaks at 0.40 V and then falls; growth counts do not rise with voltage, and nucleation counts vary only modestly without a monotonic pattern. Mean maximum Ag+ depth is mostly row 23, with reductions at 0.20–0.30 V caused by early no-active-event runs. This indicates Ag+ can penetrate deeply in cap-ended runs, while filament growth remains shallow (mean maximum depth about 1.8–2.4 rows). There is no distinct voltage region with appreciably stronger forming, and no threshold is supported. Four runs ended `NO_ACTIVE_EVENT`; 86 reached `EVENT_CAP`.

## 9. SET/Forming Behavior

No SET events were observed under the frozen KMC mechanism and tested voltage conditions. No forming-time analysis is reported unless a run actually reached SET. A zero observed count in finite KMC runs is not proof that physical SET is impossible.

## 10. RESET

RESET was not evaluated: no SET states were available in the final voltage study, and the KMC has no defensible dissolution event/barrier based on its current documented model.

## 11. Temperature Dependence

70 runs cover 250–400 K at +0.30 V, ten seeds per condition, unchanged barriers and rates apart from their existing temperature dependence. No run SET. Mean maximum filament depth varies non-monotonically from 1.8 to 2.1 rows and mean growth from 5.7 to 6.1 events. Mean simulation time across the ten runs decreases from about 2.49e-4 s at 250 K to 3.52e-6 s at 400 K, consistent with the existing Arrhenius rate change; time is not an event-count-independent forming-time measure. Eight runs ended `NO_ACTIVE_EVENT`, 62 at `EVENT_CAP`. See `kmc_temperature_study.csv` and temperature figures.

## 12. Thickness Dependence

70 runs cover requested PVA thicknesses 50–200 nm at +0.30 V/300 K, ten seeds each. To represent thickness consistently, PVA row count is nearest integer to thickness/4 nm (half ties upward), with two electrode rows added. Represented PVA thicknesses are 52, 76, 100, 124, 152, 176, and 200 nm. Both requested and represented thickness are in the CSV; kinetic parameters remain fixed. No run SET. Mean filament depth stays shallow at 1.8–2.4 rows (roughly 7.2–9.6 nm using row x 4 nm), with no monotonic thickness trend. Mean Ag+ maximum row increases with layer height as expected from the larger domain and should not be read as a thickness-normalized transport improvement. Four runs ended `NO_ACTIVE_EVENT`, 66 at `EVENT_CAP`. See thickness figures.

## 13. Filament Morphology

Voltage representatives use median-time SET selection if SET exists; otherwise greatest maximum depth, ties to smallest seed. Actual lattice states are saved. Depth is a discrete lattice-row measure; filament length is the engine's vertical bounding span of all filament sites.

## 14. KMC vs Continuous Model

The separate continuous v1.1/v1.2 model reports approximately +0.282 V SET and 0.141 s positive-bias accumulated SET time at 100 nm/300 K. KMC uses stochastic event times and discrete neighbor growth; it has no observed voltage-study SET point. These results are not directly equivalent and no fitting or validation claim is made.

## 15. Literature Comparison

The project literature context reports experimental SET near +0.27 V for an approximately 100 nm Ag/Ag-salt-incorporated PVA/Pt device. The continuous model and KMC are separate model results. Numerical similarity is not validation.

## 16. Sensitivity and Uncertainty

The KMC is stochastic with ten seeds per study condition. Voltage, temperature, and thickness are sampled only at the specified discrete values. Event caps censor evolution, and the one-seed Stage 10A result is not generalizable. No parameter fitting or confidence claim beyond the finite sample is made.

## 17. Limitations

- Coarse-grained lattice and 4 nm spatial resolution.
- Phenomenological kinetic assumptions and numerical attempt frequencies.
- Stochastic sampling of ten seeds per condition.
- Finite 20,000-event window.
- Voltage range limited to +0.10–+0.50 V.
- Thickness cell discretization introduces represented-thickness rounding.
- No direct experimental KMC calibration.
- No KMC SET observed in the final voltage study; no defensible RESET event or formed-state RESET test.
- No meaningful resistance estimate for an unformed KMC filament.

## 18. Reproducibility

Seeds are 42–51 for every condition. The baseline is 0.30 V/300 K/seed 42, 20,000 events. The final validation script and baseline runner were executed; see final summary. Total event updates across final voltage, temperature, and thickness studies: 4280598. All study CSVs retain per-run results.

## 19. Conclusions

The frozen mechanism and kinetic parameters were preserved. The requested voltage, temperature, and thickness studies characterize sub-threshold stochastic growth; the voltage study's SET result is stated above. The work is a reproducible coarse-grained model study, not experimental validation. Continuous-model and literature values remain separate evidence classes.
