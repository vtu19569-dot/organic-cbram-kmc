# KMC / continuous / literature synthesis

The voltage list specifies nine unique values, although the requested run-count line says ten. The exact listed grid was used (nine voltages x ten seeds = 90 simulations); no extra voltage was introduced.

## Final KMC study outcomes

- **Voltage:** no SET in 90 runs. Mean filament-depth rows across 0.10–0.50 V were 1.9, 1.9, 2.0, 1.9, 1.9, 2.1, 2.4, 2.1, and 2.2; mean growth counts were 5.6, 6.1, 6.0, 6.2, 5.7, 5.7, 5.7, 5.5, and 5.2. Neither measure is monotonic. Maximum Ag+ depth usually reached row 23 in cap-ending runs. Four runs exhausted active events; 86 hit the cap.
- **Temperature:** no SET in 70 runs. Mean filament depth stayed between 1.8 and 2.1 rows; mean growth between 5.7 and 6.1. Mean simulated time across seeds fell from about 2.49e-4 s at 250 K to 3.52e-6 s at 400 K due to existing temperature-dependent rates. Eight early no-active-event exits and 62 event-cap exits.
- **Thickness:** no SET in 70 runs. Mean maximum filament depth stayed between 1.8 and 2.4 rows (about 7.2–9.6 nm); no monotonic thickness response. Ag+ maximum row increases with the modeled layer height. Four early no-active-event exits and 66 event-cap exits.

No voltage, temperature, or thickness condition produced a meaningfully formed KMC state, so RESET and a filament-derived resistance study were not performed. See `kmc_reset_mechanism_audit.md` for the RESET implementation audit.

| Quantity | Literature | Continuous Model | KMC |
|---|---|---|---|
| Device | Ag/Ag-salt-PVA/Pt reference | Ag/PVA/Pt | Ag/PVA/Pt |
| PVA thickness | ~100 nm reference | 100 nm baseline | 100 nm baseline; thickness study uses nearest 4 nm cell mapping |
| Temperature | Not available as a matched sweep | 300 K baseline; existing separate parametric results | New 250–400 K sub-threshold KMC study |
| Voltage | SET ~+0.27 V | SET ~+0.282 V; positive-bias time ~0.141 s | 0.10–0.50 V stochastic growth study; no SET observed |
| SET mechanism | Ag filament formation | Phenomenological continuous growth threshold | 4-neighbor Ag+ nucleation/growth; final PVA row connectivity |
| RESET | ~-0.13 V reference | ~-0.229 V result | Not available; no supported KMC dissolution process or formed voltage-study states |
| Resistance | ON ~1 kOhm; OFF ~100 kOhm project reference | ~2.04 kOhm LRS; ~100 kOhm HRS model result | Not meaningfully estimated for unformed sub-threshold structures |

## KMC mechanism

Discrete 25 x 15 baseline lattice; row 0 Ag electrode, rows 1–23 PVA states, row 24 Pt; 4 nm cells; 4-neighbor hopping and growth. Nucleation occurs stochastically on row 1. Growth converts an Ag+ adjacent to existing filament into filament. SET is a 4-neighbor-connected filament reaching the final PVA row. Pt is never overwritten.

## Voltage, temperature, thickness, and morphology

- Voltage: 90 runs across +0.10 to +0.50 V, ten seeds per listed voltage, at 300 K and 20,000 events per run. Mean depth by voltage: [1.9, 1.9, 2, 1.9, 1.9, 2.1, 2.4, 2.1, 2.2]. Mean growth counts: [5.6, 6.1, 6, 6.2, 5.7, 5.7, 5.7, 5.5, 5.2]; mean nucleation counts: [11.1, 11.3, 11.3, 10.9, 11.7, 12.2, 11.9, 11.3, 11.8]; mean maximum Ag+ depth rows: [23, 23, 20.8, 20.8, 18.6, 23, 23, 23, 23]. Depth peaks at 0.40 V then falls; event counts are non-monotonic. See `kmc_voltage_growth_statistics.csv` for exact values.
- Temperature: 250–400 K at +0.30 V, ten seeds per temperature. No SET; mean depth 1.8–2.1 rows and mean growth 5.7–6.1. Mean simulation time falls from ~2.49e-4 s at 250 K to ~3.52e-6 s at 400 K under the existing temperature-dependent rates.
- Thickness: 50–200 nm at +0.30 V/300 K, ten seeds per thickness. No SET; mean depth 1.8–2.4 rows without a monotonic trend. PVA rows use the nearest 4 nm cell count (ties upward) plus two electrode rows; requested and represented thicknesses are both recorded.
- Morphology: saved representative voltage states use the specified deterministic selection rule. Four-neighbor lattice morphologies are not atomistic filament structures.

## SET and RESET

No SET events were observed under the frozen KMC mechanism and tested voltage-study conditions. This is a model outcome, not proof that experimental SET is impossible. Across voltage, temperature, and thickness studies, observed SET counts were 0/90, 0/70, and 0/70 respectively. A zero count in these finite stochastic samples does not prove SET impossible.

RESET was not evaluated because the voltage study produced no SET states, and no justified filament-dissolution event/barrier exists in the frozen KMC implementation. No RESET event was fabricated.

## Model and numerical assumptions

Rates use the existing Arrhenius effective-barrier equations, uniform E=V/d field, 0.35 field factor, 0.25 eV effective barriers, 1e12 s^-1 attempt frequencies, baseline deposition bias 1.5, growth multiplier 1.0, and 20,000-event cap. These are a mixture of model assumptions and numerical KMC choices, not measured microscopic parameters. The 4 nm cell and nearest-neighbor rules are coarse-grained assumptions.

## Limitations

The KMC is stochastic, samples ten seeds per condition, uses a finite event window, and has not been calibrated directly to experiments. The voltage study reaches only +0.50 V. Temperature and thickness outputs are sub-threshold growth results if SET is absent. No KMC RESET or meaningful resistance study is available. Literature and continuous-model values are contextual comparisons, not validation targets.
