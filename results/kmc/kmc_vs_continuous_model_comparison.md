# KMC vs continuous v1.1/v1.2 model comparison

| Quantity | Continuous model | Frozen KMC | Comparable interpretation |
|---|---|---|---|
| Device | Ag/PVA/Pt | Ag/PVA/Pt | Same nominal stack |
| Baseline thickness / temperature | 100 nm / 300 K | 100 nm / 300 K | Nominal conditions |
| SET voltage | +0.282 V | Not observed in tested voltage study | The KMC has no observed SET point to compare numerically |
| SET time | +bias accumulation 0.141 s | Not available | Different model timing definitions; KMC event time is accumulated stochastic waiting time |
| Voltage behavior | Deterministic finite-window phenomenological result; SET at ~0.282 V | Stochastic, 10 seeds per voltage, finite 20,000-event window | KMC sub-threshold depth/growth vary by seed; no threshold inferred |
| Filament representation | Continuous phenomenological filament length/radius | Discrete 4-neighbor lattice sites, 4 nm spacing | Morphologies and physical scales are not directly equivalent |
| RESET | Continuous-model result around -0.229 V | Not implemented/evaluated | KMC has no supported dissolution event/rate |

The continuous-model values come from the existing v1.1/v1.2 project results and were not changed by this workflow. Its +0.282 V and 0.141 s values are not targets for KMC calibration. The continuous model is itself phenomenological and is not experimental validation. KMC time is obtained by summing stochastic `-ln(U)/total_rate` increments and must not be equated to the continuous model's positive-bias accumulated time without a validated mapping.
