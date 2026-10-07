# KMC model parameter provenance

This provenance table is intentionally conservative. The goal is to distinguish:

- parameters already established from the current project,
- literature-supported values,
- values derived from existing model logic,
- model assumptions that still require justification,
- numerical parameters used for KMC implementation.

| Parameter | Value | Unit | Source | Source type | Notes |
|---|---:|---|---|---|---|
| Top electrode | Ag | - | Project device definition | Materials Project | Ag top electrode for the Ag / PVA / Pt stack |
| Bottom electrode | Pt | - | Project device definition | Materials Project | Pt bottom electrode for the Ag / PVA / Pt stack |
| Switching layer | PVA | - | Project device definition | Literature | Organic switching layer identified in the project literature reference |
| PVA thickness | 100 | nm | Existing project baseline | Literature | Baseline thickness used in the current phenomenological model |
| Ag density | 10.36 | g/cm3 | Materials Project | Materials Project | mp-124, FCC, Fm-3m |
| Pt density | 21.13 | g/cm3 | Materials Project | Materials Project | mp-126, FCC, Fm-3m |
| Ag+ transport mechanism | Ag+ migration in PVA | - | Current project model and literature context | Literature | Mechanism is established at the project level; microscopic details remain to be defined |
| Device geometry | Ag / PVA / Pt | - | Project definition | Materials Project | Device stack designated for KMC extension |
| Temperature range | To be determined | K | Not yet fixed for KMC runs | Model assumption | Temperature sweep values will be justified in Stage 3 |
| Voltage range | 0.05 to 0.50 | V | Planned KMC sweep | Model assumption | Planned SET sweep values require justification and validation |
| Lattice cell size | 4 | nm | Current KMC implementation | Numerical/KMC | Coarse-grained spacing in both row and column directions; not atomistically validated |
| Number of cells through thickness | 25 total rows; 23 PVA-state rows | - | Current KMC implementation | Numerical/KMC | Row 0 is Ag, row 24 is Pt; PVA states occupy rows 1 through 23 |
| Lateral lattice width | 15 columns | - | Current KMC implementation | Numerical/KMC | 60 nm computational lateral span at 4 nm per column |
| Neighborhood | 4-neighbor von Neumann | - | Current KMC implementation | Model assumption | Diagonal hopping and diagonal filament growth are prohibited |
| Exact local deposition | Ag+ must be 4-neighbor adjacent to AG_FILAMENT | - | Current KMC implementation | Model assumption | Coarse-grained spatial kinetics assumption; not atomistically validated |
| 8-neighbor growth diagnostic | Diagonal growth candidates only | - | Stage 8 controlled comparison | Numerical/KMC | Diagnostic alternative; hopping and nucleation remain unchanged; not literature-derived |
| Manhattan-distance-2 growth diagnostic | Growth candidates within Manhattan distance 2 | - | Stage 8 controlled comparison | Numerical/KMC | Diagnostic alternative for spatial reach; not a calibrated physical mechanism |
| Attempt frequency | 1.0e12 | s^-1 | Numerical prototype choice | Numerical/KMC parameter | Hopping attempt frequency; not claimed as a measured PVA microscopic value |
| Activation barrier | 0.25 | eV | Effective prototype barrier | Model assumption | Coarse-grained Ag+ transport barrier |
| Nucleation activation energy | 0.25 | eV | Effective prototype barrier | Model assumption | Used by the stochastic first-nucleus event |
| Nucleation attempt frequency | 1.0e12 | s^-1 | Numerical prototype choice | Numerical/KMC parameter | Attempt frequency for first-nucleus formation |
| Growth activation energy | 0.25 | eV | Effective prototype barrier | Model assumption | Used by adjacent filament growth |
| Growth-rate diagnostic multiplier | 1, 10, 100 | - | Stage 6 controlled perturbation | Numerical/KMC | Diagnostic-only factors; not baseline parameters and not literature-fitted |
| Field-coupling factor alpha | 0.35 | - | Stage 5 coarse-grained formulation | Model assumption | Used in `Ea_eff = max(Emin, Ea - alpha*q*E*a)`; not a measured microscopic value |
| Hop length | 4 | nm | Lattice cell size | Derived | One lattice hop equals one coarse-grained cell |
| Deposition/growth rate | Arrhenius | s^-1 | Stage 5 event rule | Derived | Ag+ adjacent to filament converts with the field-assisted growth rate |
| Deposition probability | Stochastic rate event | - | Stage 5 event rule | Model assumption | No deterministic deposition probability is used |
| Dissolution rate factor | Model assumption — requires justification | - | Not yet established | Model assumption | Required if reverse-bias rupture is included |
| Random seed | 42 | - | Stage 3/5 single-case reproducibility requirement | Numerical/KMC parameter | Fixed seed for the approved single case |
| KMC event rules | Generation, hopping, nucleation, adjacent growth | - | Stage 5 model design | Derived | Minimal event set for the single-case test |
| Filament connection criterion | Final PVA row, row 23 | - | Stage 5 lattice interpretation | Model assumption | 4-neighbor filament cluster reaches the PVA boundary adjacent to Pt |
| Connectivity rule | 4-neighbor | - | Stage 5 model design | Model assumption | Diagonal connections excluded |
| Resistance proxy | To be determined | ohm | Not yet defined | Derived | Future conduction proxy will map morphology to resistance |
