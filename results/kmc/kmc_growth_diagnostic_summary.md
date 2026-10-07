# Stage 6 controlled KMC growth-rate diagnostic

This is a diagnostic perturbation, not a calibrated model update. Only the growth-rate multiplier was changed. The voltage, temperature, seed, lattice, Ag+ inventory, nucleation mechanism, hopping mechanism, and event cap were held fixed.

## 1. Baseline Stage 5 result

- Conditions: V = 0.30 V, T = 300 K, seed = 42, event cap = 20000
- SET reached: False
- Growth events: 7
- Filament sites: 18
- Filament depth: row 2

## 2. Growth-rate audit

Growth candidates require an Ag+ ion to be exactly 4-neighbor adjacent to an existing AG_FILAMENT site. Growth uses the 0.25 eV growth barrier, the field-assisted barrier term, the existing deposition bias of 1.5, and the diagnostic multiplier. Hopping uses the 0.25 eV transport barrier, the same field coupling, and no deposition bias.

- Baseline growth candidates: 124
- Baseline hopping candidates: 177879
- Mean growth candidate rate: 1.08113e+08 Hz
- Mean hopping candidate rate: 5.79998e+07 Hz
- Mean growth/hopping rate ratio: 1.86402
- Growth fraction of accumulated active candidate rate: 0.00128775
- Mean growth effective barrier: 0.25 eV
- Mean hopping effective barrier: 0.251052 eV
- Final Ag+ ions adjacent to filament: 0
- Final empty growth sites: 15

The rate ratio is a candidate-rate ratio, not a probability of eventual growth. Event selection is additionally controlled by the number of active hopping candidates and their summed rate.

## 3. Controlled cases

| Case | Growth factor | Growth events | Filament sites | Filament depth | SET | Simulation time (s) | Growth/hopping ratio |
|---|---:|---:|---:|---:|---|---:|---:|
| baseline | 1.0x | 7 | 18 | 2 | False | 4.1719161e-05 | 1.864017 |
| 10x growth rate | 10.0x | 12 | 16 | 2 | False | 0.00011559333 | 16.748026 |
| 100x growth rate | 100.0x | 10 | 15 | 1 | False | 2.7391366e-08 | 96.034632 |

## 4. Bottleneck interpretation

The baseline bottleneck is event-selection competition combined with limited local Ag+ adjacency. The mechanism is not blocked by missing logic: nucleation and growth events occur. Growth candidates are rare relative to hopping candidates, and the active hopping population consumes most selected events. The diagnostic multipliers test sensitivity without changing the baseline model.

## 5. Baseline decision

The baseline parameter is unchanged. The 10x and 100x cases are diagnostic perturbations only and are not calibrated physical values. A future baseline change would require separate physical justification for the growth attempt frequency, growth barrier, or local deposition formulation.

## 6. Limitations

- Candidate-rate sums are accumulated over repeated event-list builds, not instantaneous rates.
- The coarse-grained 4 nm lattice does not resolve microscopic Ag+ chemistry.
- The growth multiplier is numerical and diagnostic, not literature-fitted.
- No voltage, temperature, thickness, RESET, or literature calibration study was performed.
