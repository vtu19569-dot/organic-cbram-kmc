# Stage 8 final KMC mechanism validation

This comparison changes only the spatial rule used to construct filament-growth candidates. Voltage, temperature, seed, lattice dimensions, cell spacing, event cap, Ag+ inventory, nucleation, hopping, field factor, activation energies, attempt frequencies, and growth multiplier remain unchanged.

## 1. Baseline mechanism

The default model uses exact 4-neighbor filament-growth candidates. An Ag+ ion must occupy an immediately adjacent lattice site; it is then converted in place into AG_FILAMENT. Hopping and nucleation remain unchanged. SET remains defined by a 4-neighbor filament cluster reaching the final PVA row.

## 2. Diagnostic alternatives

- 8-neighbor diagnostic: diagonal neighbors are allowed only when constructing filament-growth candidates. Hopping remains 4-neighbor.
- Manhattan-distance-2 diagnostic: Ag+ ions within Manhattan distance 2 of an existing filament can become growth candidates. This is a deliberately nonlocal diagnostic rule, not a calibrated mechanism.

## 3. Conditions

- Device: Ag / PVA / Pt; PVA thickness 100 nm.
- V = +0.30 V, T = 300 K, random seed = 42.
- Lattice = 25 x 15, cell spacing = 4 nm, event cap = 20,000.
- Baseline growth multiplier = 1.0 for all cases.

## 4. Results

| Case | Growth rule | Growth candidates | Growth events | Hopping candidates | Hopping events | Filament sites | Depth | Max Ag+ depth | Time (s) | Events | SET | Final Ag+ | Adjacent Ag+ | Growth/hopping ratio |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| 4-neighbor baseline | 4-neighbor | 124 | 7 | 177879 | 19962 | 18 | 2 | 23 | 4.1719161e-05 | 20000 | False | 3 | 0 | 1.864017 |
| 8-neighbor diagnostic | 8-neighbor | 266 | 10 | 123686 | 19957 | 21 | 4 | 23 | 6.0268351e-05 | 20000 | False | 2 | 0 | 2.3589181 |
| Manhattan-distance-2 diagnostic | manhattan-2 | 199 | 4 | 64553 | 19966 | 17 | 2 | 23 | 0.00011556144 | 20000 | False | 1 | 0 | 1.5530851 |

## 5. Morphology comparison

The accompanying PNG uses the actual final lattice states. It does not draw or infer a filament between sites. The 8-neighbor and Manhattan-distance-2 panels are diagnostic morphology outcomes only.

## 6. Interpretation

- 8-neighbor growth changes successful growth from 7 to 10 events and filament sites from 18 to 21.
- Manhattan-distance-2 growth changes successful growth from 7 to 4 events and filament sites from 18 to 17.
- SET is reached in none of the three cases: baseline=False, 8-neighbor=False, distance-2=False.
- The diagnostic alternatives do not create a complete bridge in this single case, but they relax the spatial interpretation. The Manhattan-distance-2 rule can create disconnected or nonlocal filament additions and is therefore less physically conservative.
- No implementation error was found in the original 4-neighbor baseline. Its behavior is consistent with its stated coarse-grained nearest-neighbor assumption.

## 7. Provenance

| Quantity | Classification |
|---|---|
| 4 nm lattice spacing | Numerical/KMC; coarse-grained model assumption |
| 4-neighbor connectivity | Model assumption |
| 8-neighbor diagnostic | Numerical/KMC diagnostic; model assumption, not literature-derived |
| Manhattan-distance-2 diagnostic | Numerical/KMC diagnostic; model assumption, not literature-derived |
| Local growth rule | Model assumption |
| Field-assisted barrier | Model assumption |
| Activation energy | Model assumption |
| Attempt frequency | Numerical/KMC |

## 8. Limitations

- This is one fixed voltage, temperature, seed, lattice, and event cap.
- The 4 nm resolution is not atomistically validated.
- The comparison changes candidate geometry but retains the original 4-neighbor SET connectivity test.
- The Manhattan-distance-2 diagnostic is intentionally not a physical calibration.

## 9. Final mechanism decision

Freeze the original 4-neighbor growth mechanism for the upcoming voltage study. It is the most conservative and internally consistent coarse-grained rule, no coding defect was identified, and the diagnostic alternatives do not provide a scientifically justified replacement. Baseline parameters remain unchanged.

The model is ready for Stage 9 only as a documented mechanism-validation baseline. The voltage-dependent forming analysis should remain explicitly conditional on the limitations above and must not treat the diagnostic alternatives as validated physics.
