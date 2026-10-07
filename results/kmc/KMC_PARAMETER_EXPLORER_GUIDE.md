# KMC Parameter Explorer: Current Scope and Research Plan

## Purpose

`analysis/kmc_parameter_explorer.py` provides repeatable constant-condition KMC
runs for voltage and temperature questions. Each combination starts with a fresh
Ag/PVA/Pt lattice and uses the same frozen event mechanism and kinetic defaults.
It writes one full run table and one final-lattice CSV per trajectory.
Both experiment runners use `kmc_model/experiment_config.py`; the saved JSON
captures the operating conditions and marks unsupported requests by rejecting
them during conversion to the current engine configuration.
`analysis/kmc_set_pulse_protocol.py` applies an ordered piecewise-constant SET
voltage schedule to one persistent lattice and writes event-level and per-pulse
records.

Examples:

```bash
.venv/bin/python analysis/kmc_parameter_explorer.py --voltage 0.30 --temperature 300 --seed 42
.venv/bin/python analysis/kmc_parameter_explorer.py --voltages 0.15,0.25,0.35,0.45 --seeds 42,43,44
.venv/bin/python analysis/kmc_parameter_explorer.py --temperatures 275,300,325 --voltages 0.30 --seeds 42,43
.venv/bin/python analysis/kmc_set_pulse_protocol.py --pulse 0.30:0.0001 --pulse 0.00:0.001 --pulse 0.35:0.0001 --temperature 300 --seed 42
```

The output goes to `results/kmc/parameter_explorer/` unless `--output-dir` is
specified. `--max-events` changes the numerical observation window only; its
default is the frozen 20,000 events. A changed cap must be reported in any
analysis using those outputs.

## Parameter capability and interpretation

| Research input | Current status | Safe interpretation |
|---|---|---|
| SET bias / constant applied voltage | Supported | Changes the existing uniform field `E=V/d` and existing field-assisted hopping and deposition rates. It is not a compliance-controlled pulse. |
| Temperature | Supported | Changes the existing Arrhenius rates. Activation energies and prefactors remain frozen. |
| PVA thickness | Not exposed by this runner | Geometry has a frozen 25×15 lattice and 4 nm spacing; changing thickness alone would make row count and field geometry inconsistent. Define and document a thickness-to-row mapping before comparing thicknesses. |
| RESET bias | Not supported | There is no reverse-bias dissolution event in the frozen engine. A voltage sign change alone cannot reset filament sites. |
| Compliance current | Not supported | There is no voltage/current circuit solution or calibrated conductance law coupled to evolving morphology. Existing resistance output is only a placeholder. |
| Filament retention | Not supported | There is no zero-bias detachment, dissolution, diffusion, or aging event law. The current simulator stops after a finite event window. |
| Piecewise SET voltage waveform | Supported by `kmc_set_pulse_protocol.py` | One lattice persists across voltage segments; rates are rebuilt at each edge. At an edge, an event whose sampled waiting time crosses the edge is discarded and resampled under the new rates. A zero-voltage segment allows existing Ag+ hopping, but it does not dissolve metal filament sites or establish retention. |

The runner deliberately does not accept arbitrary overrides for activation
energy, hopping/nucleation/growth prefactors, field factor, growth multiplier,
cell spacing, or ion inventory. That prevents an exploratory sweep from silently
becoming a kinetic recalibration.

## Recommended order for a real-time device study

1. **SET pulse / voltage dependence:** use the piecewise protocol with explicit
   pulse amplitudes, durations, and inter-pulse intervals. Record event counts
   and physical KMC time per pulse. Before interpreting pulse data, compare a
   single constant segment against the existing fixed-bias engine using the same
   seed and event cap.
2. **Temperature:** run controlled ensembles at fixed waveform and geometry,
   with the existing Arrhenius model. Report stochastic spread, not only a
   representative path.
3. **Thickness:** choose a documented lattice mapping that preserves the intended
   spatial resolution, then recompute `E=V/d`; do not change kinetic parameters.
4. **Compliance:** couple the KMC morphology to a device/circuit relation so
   current determines the instantaneous voltage actually dropped across PVA.
   Establish a conductance model and units before introducing a compliance
   threshold. A hard-coded current cutoff is not a physical compliance model.
5. **RESET:** only after formed filaments can be generated, define a reverse-bias
   dissolution/rupture event and document its barrier, field term, and provenance
   or model-assumption status.
6. **Retention:** after RESET and state transitions are represented, define
   zero-bias evolution and an operational retention criterion (for example,
   persistence of a connectivity/resistance state over a stated elapsed time).
   This needs a physically justified spontaneous migration/dissolution law.
7. **3D morphology:** extend the lattice only after the 2D event rules and
   observables are stable; otherwise the added degrees of freedom obscure which
   mechanism changed the result.

The images supplied as research context include other materials and device
geometries (including Cu/H2O/Cu and Ag/Ag2S/W). Their voltages and morphologies
are not quantitative calibration targets for Ag/PVA/Pt.
