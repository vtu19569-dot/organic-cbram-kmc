# Stage 7 local deposition and spatial kinetics validation

This is a diagnostic-only audit of the unchanged Stage 5 baseline. No growth multiplier, rate, barrier, field factor, lattice spacing, event cap, or ion inventory was changed.

## 1. Lattice representation

- Grid: 25 rows x 15 columns.
- One coarse-grained cell: 4.0 nm in the row and column directions.
- Computational span: 100.0 nm using the configured 25-row mapping.
- Electrode rows: row 0 is Ag and row 24 is Pt.
- PVA-state rows: rows 1 through 23, 23 rows and 92.0 nm if each state row is interpreted as 4 nm.
- Lateral computational span: 60.0 nm.
- The 100 nm / 25 cells = 4 nm mapping is a numerical/coarse-grained model assumption. Because boundary electrode rows are included in the 25-row grid, the interior PVA-state rows span 92 nm under the literal row-count interpretation.
- The 4-neighbor von-Neumann neighborhood is explicitly implemented in `LatticeGrid.neighbors`; diagonal motion and diagonal growth are prohibited. This is a model assumption, not an atomistic validation.

## 2. Physical-to-KMC mapping

| Physical process | Current KMC representation | Parameter | Provenance |
|---|---|---|---|
| Ag electrode | Row 0 cells with AG_ELECTRODE state | electrode_top_index = 0 | Materials Project |
| Ag+ generation | Empty PVA cell directly below an Ag electrode cell becomes AG_ION | electrode injection rule | Model assumption |
| Ag+ hopping | AG_ION moves to an empty 4-neighbor cell | activation_energy_ev = 0.25 eV, cell size = 4 nm | Model assumption / Derived |
| Nucleation | AG_ION on row 1 converts stochastically to AG_FILAMENT | nucleation barrier and attempt frequency | Model assumption / Numerical/KMC |
| Local growth | AG_ION exactly adjacent to AG_FILAMENT converts in place | growth barrier, deposition_bias = 1.5 | Model assumption / Numerical/KMC |
| Pt electrode | Row 24 cells with PT_ELECTRODE state | electrode_bottom_index = 24 | Materials Project |
| SET bridge | 4-neighbor filament reaches final PVA row, row 23 | connectivity_rule = 4-neighbor | Model assumption |

## 3. Local Ag+ distance distribution

Distances are nearest-filament Manhattan distances in the final baseline lattice. Distance-2/3/4 ions are diagnostic only and cannot grow the filament under the current event rules.

| Population | d=1 | d=2 | d=3 | d=4 |
|---|---:|---:|---:|---:|
| All Ag+ ions | 0 | 0 | 0 | 0 |
| Ag+ below deepest filament | 0 | 0 | 0 | 0 |
| Empty PVA sites | 15 | 15 | 15 | 15 |
| Empty sites below deepest filament | 3 | 15 | 15 | 15 |

The final lattice has 0 Ag+ ions at distance 1 and 15 empty sites at distance 1 from a filament site. The final Ag+ count is a snapshot after the event cap; it is not the time-integrated availability during the run.

## 4. Field-direction verification

For V = 0.3 V and d = 100 nm, E = V/d = 3e+06 V/m.
One lattice spacing contributes E*a = 0.012 eV for a unit charge.
With alpha = 0.35 and Ea = 0.25 eV, downward migration/growth uses Ea_eff = 0.2458 eV.
Upward migration/growth uses Ea_eff = 0.2542 eV.

The code defines increasing row index as downward motion from Ag toward Pt. Therefore downward motion receives barrier lowering and upward motion receives barrier raising. Growth uses the filament row as the source and the lower Ag+ row as the target, so its field sign is aligned with downward growth.

## 5. Deposition geometry

- Growth requires an Ag+ ion to occupy an immediately adjacent 4-neighbor site.
- The occupied Ag+ site is converted directly into AG_FILAMENT.
- Growth does not deposit into an empty site.
- Diagonal deposition is prohibited.
- Multiple disconnected filaments are possible because nucleation can occur at multiple row-1 sites.
- There is no nonlocal reconnection event. A gap can only be filled if a neighboring Ag+ site creates a normal adjacent growth candidate.
- Exact nearest-neighbor deposition is therefore an explicit coarse-grained model assumption.

## 6. Bottleneck classification

- **A. Spatial-resolution limitation:** selected. The 4 nm cell is a coarse numerical representation, and the literal 25-row mapping includes electrode boundary rows.
- **B. Local-neighbor restriction:** selected. Only exact 4-neighbor Ag+ sites can grow the filament; distance-2/3/4 ions are inactive for growth.
- **C. Event-selection competition:** selected. Baseline hopping candidates = 177879 versus 124 growth candidates, and accumulated growth rate fraction = 0.1288%.
- **D. Kinetic-rate limitation:** partially selected. The growth candidate rate itself is not near zero, but its sparse candidate population limits total growth opportunity.
- **E. Field-direction implementation issue:** not selected. The existing sign convention lowers the barrier for downward motion and raises it for upward motion.
- **F. Insufficient evidence:** not selected for this audit, although local availability is measured only at the terminal lattice state rather than throughout the trajectory.

## 7. Limitations and recommendation

- This diagnostic does not validate the physical 4 nm resolution or the 4-neighbor assumption against atomistic or experimental data.
- Final-state distance counts do not replace a time-resolved local-availability history.
- The model permits multiple nuclei and disconnected branches, while the current connectivity check uses one arbitrary filament cluster when testing the final boundary.
- Baseline parameters should remain unchanged.
- The model is not ready for Stage 8 voltage-dependent forming-time analysis until the spatial coarse-graining and local deposition assumptions are explicitly approved or refined.
