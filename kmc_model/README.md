# Coarse-grained lattice KMC model for Ag+ migration and filament formation in PVA

This package defines the isolated next-stage model for the Ag / PVA / Pt CBRAM system. The model is intentionally described as a coarse-grained lattice KMC model and is not an atomistic simulation.

For controlled constant-bias voltage and temperature runs, see
[`analysis/kmc_parameter_explorer.py`](../analysis/kmc_parameter_explorer.py)
and the [parameter explorer guide](../results/kmc/KMC_PARAMETER_EXPLORER_GUIDE.md).
For sequential piecewise-constant SET voltage pulses on one persistent lattice,
see [`analysis/kmc_set_pulse_protocol.py`](../analysis/kmc_set_pulse_protocol.py).
The explorer preserves the frozen mechanism and kinetic defaults. It does not
model RESET dissolution, compliance current, thickness variation, or filament
retention.

## 1. Device

- Top electrode: Ag
- Switching layer: PVA (polyvinyl alcohol)
- Bottom electrode: Pt
- Baseline switching-layer thickness: 100 nm

## 2. Physical layer

- Physical switching layer: PVA
- Baseline thickness: 100 nm
- Mobile species: Ag+
- Primary mechanism: filament formation and dissolution in the polymer matrix

## 3. Computational representation

The simulation will use a coarse-grained lattice representation of the device. The goal is to represent a physically interpretable network of occupied sites, electrode interfaces, and filament growth without requiring atomistic PVA structure or unverified microscopic parameters.

The computational representation will document:

- physical thickness
- lattice cell size
- number of lattice cells across the PVA layer
- mapping from physical length to computational length
- electrode boundaries
- site classes

## 4. Electrode boundaries

- Ag top electrode: source of Ag+ and metallic contact region
- Pt bottom electrode: sink/collecting electrode for filament connection
- PVA region: active switching layer between electrodes

## 5. Planned states

The planned state space includes:

- empty
- Ag+
- Ag filament
- electrode

Additional state labels may be added later only if they are required for a physically justified event rule and are documented in the provenance table.

## 6. Planned KMC events

The model will be built around a limited set of event types:

1. Ag+ generation
2. Ag+ hopping
3. Field-assisted migration
4. Ag+ reduction/deposition
5. Filament growth
6. Filament connection
7. Reverse-bias dissolution/rupture if justified

These events are planned but not yet implemented.

## 7. Planned outputs

The future KMC model will report:

- filament morphology
- forming time
- KMC event count
- filament length
- filament width
- SET success/failure
- resistance/conduction proxy

## 8. Scope of this Stage 2 structure

This stage creates the isolated package structure and documentation only. It deliberately does not implement the KMC event physics or run a voltage sweep.

The goal is to establish a clean, reviewable framework that can be expanded in Stage 3.
