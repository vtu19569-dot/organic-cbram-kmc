# Parameter justification for the first coarse-grained KMC SET model

This document records the parameter choices used in the Stage 3 and Stage 5 coarse-grained KMC implementation for the Ag / PVA / Pt CBRAM system.

The model is explicitly a coarse-grained lattice KMC model for Ag+ migration and filament formation in PVA, not an atomistic model.

## 1. Device and geometry

### PVA physical thickness
- Value: 100 nm
- Classification: A. Literature-supported
- Source: existing project baseline and PVA literature reference in README.md and data/pva.json
- Reason: this is the established switching-layer thickness used in the project baseline and the PVA literature comparison.

### Lattice cell size
- Value: 4 nm per cell
- Classification: D. Model assumption
- Source: chosen for computational feasibility and the coarse-grained interpretation of transport
- Reason: the PVA layer is not represented atom-by-atom; the lattice uses a coarse-grained cell size selected to make the 100 nm layer computationally manageable while preserving a clear physical interpretation.

### Number of lattice cells
- Value: 25 rows, 15 columns
- Classification: E. Numerical/KMC parameter
- Source: chosen for the first working prototype and reproducibility
- Reason: the model is intentionally minimal and computationally lightweight for a first SET test.

### Physical-to-lattice mapping
- Value: 100 nm / 25 cells = 4 nm per cell
- Classification: C. Derived
- Source: derived from the chosen cell size and physical thickness
- Reason: this directly maps the physical PVA thickness to the computational lattice.

## 2. Electrical conditions

### Applied voltage
- Value: 0.30 V
- Classification: A. Literature-supported / project-defined test case
- Source: single-case test value specified for Stage 3
- Reason: this is the first working SET test case chosen for implementation, not a literature fit.

### Electric field approximation
- Value: E = V / d
- Classification: D. Model assumption
- Source: simplified uniform-field approximation used for the first test case
- Reason: the local microscopic field in a polymeric switching layer is not assumed to be spatially uniform; this approximation is used only to generate a simple field-driven migration bias.

## 3. Temperature

### Temperature
- Value: 300 K
- Classification: A. Literature-supported / project baseline
- Source: existing project baseline and v1.1/v1.2 model setup
- Reason: this is the default temperature used by the established phenomenological model and the project baseline.

## 4. Ag+ species and mobility-related parameters

### Attempt frequency
- Value: 1.0e12 s^-1
- Classification: E. Numerical/KMC parameter
- Source: numerical convenience adopted for a first working KMC prototype
- Reason: this is not claimed to be an experimentally measured microscopic hopping attempt frequency for PVA; it is a numerical value used to make the rate model operate in a tractable range.

### Activation energy
- Value: 0.25 eV
- Classification: D. Model assumption
- Source: selected as a first working effective barrier for a coarse-grained model
- Reason: a true microscopic Ag+ transport barrier in PVA is not yet established in this project; this is an effective activation barrier for the prototype KMC event rate.

### Field enhancement factor
- Value: 0.35
- Classification: D. Model assumption
- Source: there is no direct experimental microscopic field coupling in the project data
- Reason: this was inactive in Stage 3. In Stage 5 it is used as a dimensionless coupling in the explicitly documented effective-barrier expression. It remains a model assumption, not a measured microscopic parameter.

### Field-assisted effective barrier
- Equation: $E_{a,eff} = max(10^{-6}, E_a - alpha q E a)$ for downward motion; the sign reverses for upward motion.
- Classification: D. Model assumption
- Parameters: `alpha = field_factor = 0.35`, `E = V/d`, `a = 4 nm`
- Reason: this is a simple coarse-grained field coupling, not a measured microscopic Ag+ barrier. The energy term is evaluated in eV as `E[V/m] * a[m]`, and the barrier is clamped positive.
- Limitation: spatial field variation, image forces, local chemistry, and correlated ion motion are not represented.

### Ag+ initial inventory
- Value: initial ion population created at the Ag electrode neighbor
- Classification: D. Model assumption
- Source: chosen to establish a minimal, reproducible SET prototype
- Reason: the exact Ag+ concentration in the PVA layer is not experimentally established in this project.

## 5. Event rules

### Ag+ hopping rule
- Classification: D. Model assumption
- Source: chosen for the minimal first SET mechanism
- Reason: the model allows Ag+ ions to hop to neighboring PVA sites with a thermally activated rate and a mild directional bias toward the Pt electrode.

### Ag+ reduction/deposition rule
- Classification: D. Model assumption
- Source: required to convert mobile Ag+ into a filament site and enable growth
- Reason: this is the minimum rule needed to form a conductive filament in the coarse-grained KMC description.

### Ag+ nucleation event
- Event: an Ag+ ion on the first PVA row can stochastically reduce into an `AG_FILAMENT` site.
- Rate: `r_nuc = nu_nuc * exp(-Ea_nuc_eff / (kB*T))`
- Classification: D. Model assumption for the mechanism; E. Numerical/KMC parameter for the selected attempt frequency and barrier values
- Values: `Ea_nuc = 0.25 eV`, `nu_nuc = 1.0e12 s^-1`
- Reason: this supplies an explicit stochastic first-nucleus transition near the Ag/PVA interface without using a deterministic row threshold.

### Filament growth event
- Event: an Ag+ ion adjacent by 4-neighbor contact to an existing filament site converts into a new `AG_FILAMENT` site.
- Rate: Arrhenius rate with `Ea_growth = 0.25 eV`, field-assisted barrier, and the existing directional factor.
- Classification: D. Model assumption for reduction/growth physics; E. Numerical/KMC parameter for the selected effective barrier and attempt frequency
- Reason: this is the smallest local growth rule consistent with Ag+ presence, filament proximity, temperature, and field direction.

### Filament connection criterion
- Classification: D. Model assumption
- Source: Stage 5 lattice interpretation
- Reason: SET is reached when a 4-neighbor-connected filament cluster reaches the final PVA row (`row = lattice_rows - 2`) adjacent to the Pt electrode. The Pt electrode cell is not overwritten.

### Connectivity rule
- Value: 4-neighbor connectivity
- Classification: D. Model assumption
- Reason: diagonal contact is excluded for a conservative first lattice model.

### Hop length
- Value: 4 nm
- Classification: C. Derived
- Source: lattice cell size
- Reason: one lattice hop corresponds to one coarse-grained cell, so `a = cell_size_nm = 4 nm` in the field barrier term.

## 6. Randomness and reproducibility

### Random seed
- Value: 42
- Classification: E. Numerical/KMC parameter
- Source: fixed for reproducibility in the first test case
- Reason: this ensures that repeated runs with the same seed produce identical results.

### Maximum KMC events
- Value: 20000
- Classification: E. Numerical/KMC parameter
- Source: numerical safeguard for the prototype simulation
- Reason: prevents runaway event loops while allowing the first SET case to reach a terminating condition.

## 7. Resistance/conduction proxy

### Conduction proxy
- Value: crude geometry-based estimate in ResistanceModel
- Classification: D. Model assumption
- Source: chosen for the minimal KMC prototype only
- Reason: no calibrated transport model is available for this first coarse-grained KMC implementation. This is an approximation used only to report a rough proxy, not a validated experimental resistance.

## 8. Summary of what remains unresolved

The following items remain intentionally unresolved in the first KMC prototype and must be justified later if the model is extended:

- microscopic Ag+ diffusion barrier in PVA
- actual local field coupling inside the polymer
- realistic Ag+ concentration and inventory in the film
- realistic deposition probability at filament sites
- realistic branching and lateral growth rules
- reverse-bias dissolution/rupture kinetics
- actual filament cross-section dependence on conduction
- any experimentally calibrated activation-energy or attempt-frequency value

These are not hidden; they are explicitly labelled as model assumptions or numerical KMC parameters.

## 9. Stage 6 controlled growth diagnostic

- Diagnostic multiplier: 1x, 10x, and 100x applied only to the growth event rate.
- Classification: E. Numerical/KMC parameter
- Purpose: sensitivity diagnosis only; these factors are not calibrated physical values and the 1x baseline remains unchanged.
- Baseline finding: 124 growth candidates and 177879 hopping candidates were accumulated over event-list builds. The mean candidate growth rate was 1.08113e8 Hz and the mean hopping rate was 5.79998e7 Hz, but growth contributed only 0.1288% of the accumulated active candidate rate because hopping candidates were far more numerous.
- Controlled finding: 10x increased successful growth events from 7 to 12, while 100x produced 10 growth events and exhausted the active event population after 29 total events. Neither diagnostic case reached SET.
- Interpretation: the baseline limitation combines sparse local Ag+ adjacency with event-selection competition. The response is not monotonic because changing growth kinetics changes the morphology and the remaining active event population.
