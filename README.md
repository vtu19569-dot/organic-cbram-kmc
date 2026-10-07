# Ag/PVA/Pt CBRAM model

This project contains a coarse-grained Ag/PVA/Pt conductive-bridge memory model that combines a phenomenological filament-growth state model with a lattice-KMC prototype for Ag+ migration and filament linkage.

The current codebase is intended as a research-oriented simulation and analysis workflow rather than a validated atomistic device model. It documents the assumptions, maintains data provenance, and generates the relevant IV and morphology outputs for a 100 nm Ag/PVA/Pt stack at 300 K.

## Device stack

- Top electrode: Ag
- Switching layer: PVA
- Bottom electrode: Pt
- Nominal thickness: 100 nm
- Base temperature: 300 K

## What is implemented

- A continuous filament state model used for voltage sweeps and IV generation.
- A coarse-grained lattice KMC engine for Ag+ hopping, nucleation, and filament cluster formation.
- Sensitivity-analysis tooling for positive-bias timing, activation energy, temperature, and filament radius.
- Output CSVs and plots written under the results directory.

## Core assumptions

The model uses explicit assumptions for coarse-grained kinetics rather than claiming measured microscopic material properties. These values are documented in the model parameter files and are treated as calibration parameters for the current workflow.

## Run the project

```bash
. .venv/bin/activate
python main.py
```

This writes the main IV data and summary figures under the results directory.

## Validation workflow

```bash
. .venv/bin/activate
pytest -q
python analysis/validate_cbram.py
```

The validation script checks the sweep timing consistency and the baseline SET/RESET behavior for the current model assumptions.
