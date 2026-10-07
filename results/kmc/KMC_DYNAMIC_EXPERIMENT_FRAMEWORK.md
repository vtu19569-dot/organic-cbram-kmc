# KMC Dynamic Experiment Framework

## 1. Objective

Provide one explicit experiment-input schema for operating conditions while
keeping the Ag/PVA/Pt KMC kinetic mechanism and parameters frozen. The first
engineering milestone is the chain from evolving filament morphology to device
resistance, current, and then compliance feedback.

## 2. Configuration system

`kmc_model/experiment_config.py` defines `ExperimentConfig` and
`WaveformSegment`. It records the stack, geometry, temperature, SET/RESET bias,
compliance, waveform, seeds, event cap, hold condition, and output requests.
Both the constant-condition explorer and pulse runner now construct their engine
configuration through this schema and save JSON configuration records.

Unsupported requests fail explicitly when converted for the current engine:
nonbaseline geometry, RESET bias, compliance, and enabled retention. The fields
are present to make the intended experiment auditable; their presence does not
mean those physical features have been implemented.

## 3. Voltage waveform

`analysis/kmc_set_pulse_protocol.py` executes ordered constant-voltage segments
on one persistent lattice. It updates voltage and `E=V/d` at each segment edge,
rebuilds event rates, and records event-level and per-segment outputs. If a
sampled Gillespie waiting time crosses a known edge, the simulator advances to
the edge and resamples under the new rates. The existing SET event rule remains
the only filament-connection criterion. Negative or zero voltage does not
remove filament sites.

## 4. Morphology-to-resistance model

**Stopped at audit.** The current resistance code cannot calculate a meaningful
state-dependent device resistance. `ResistanceModel.update_from_filament()`
uses `width_nm² / length_nm` as a conductivity-like proxy, then takes its
reciprocal. That expression has dimensions of inverse length, not ohms, and no
material transport coefficient converts it to resistance. Also, the engine does
not use that method for its result: it assigns fixed values of 1 kΩ after SET
and 1 MΩ otherwise.

## 5. Resistance provenance

| Quantity | Current representation | Classification | Audit |
|---|---|---|---|
| Filament length | Occupied lattice span × cell spacing | Derived from model state | A geometric measure, not enough for resistance. |
| Filament width | Lattice span × cell spacing | Derived from model state | A 2D span does not determine the out-of-plane conducting cross-section. |
| Cross-section = width² | Geometric proxy in `ResistanceModel` | Model assumption | Unjustified for a branching 2D lattice and lacks a calibrated shape interpretation. |
| `conductivity_proxy = area/length` | `nm²/nm` | Numerical/model proxy | Not conductivity; it lacks S/m units and material transport information. |
| `1/conductivity_proxy` | Fixed reciprocal geometry expression | Numerical/model proxy | Not resistance in ohms. |
| 1 kΩ SET / 1 MΩ non-SET | Hard-coded in engine | Model assumption / placeholder | Not morphology-dependent or literature-calibrated; must not drive current. |

The current project lacks a justified filament resistivity/conductivity, a
validated conversion from 2D occupancy to 3D conducting cross-section, contact
resistance, and a gap/access resistance law for nonconnected states. The circuit
topology and source impedance are also unspecified. These are required before
calculating a defensible device current.

## 6. Current calculation

Not implemented. `I=V/R` would produce a number, but the available `R` is a
placeholder and has no valid ohm units. No current values are reported.

## 7. Compliance model

Not implemented. Applying a compliance clamp before obtaining a defensible
morphology-dependent resistance would turn an unsupported resistance proxy into
feedback on the KMC field. Therefore the proposed 10 µA–1 mA diagnostic sweep was
not run, and no compliance CSV or plot was created.

## 8. Temperature

Temperature remains an experiment input and is passed to the existing Arrhenius
rate implementation. Activation energies and prefactors remain unchanged.

## 9. Thickness

Thickness is represented in the configuration, but the current engine accepts
only the frozen 100 nm, 4 nm-spacing, 25×15 geometry. The existing baseline has
23 PVA rows; a new mapping must reconcile this baseline with physical thickness
before a dynamic thickness study is supported. Nonbaseline thickness requests
are rejected rather than silently changing row count or electric field.

## 10. Retention status

Not implemented. A zero-voltage waveform segment can continue existing KMC
events, including Ag+ hopping, but there is no justified metal-filament
dissolution/decay law. Such a segment is a zero-bias hold condition, not a
validated retention simulation.

## 11. RESET status

Not implemented. Reverse bias can alter field-assisted Ag+ hopping direction,
but the event set contains no filament dissolution or rupture transition. No
RESET result is claimed.

## 12. Limitations and stopping decision

The configuration and waveform infrastructure is ready for controlled SET-only
experiments. The model is **not ready for compliance experiments**, because the
resistance/current link fails dimensional and provenance checks. It is also not
ready for RESET or retention studies. No kinetic parameters or the continuous
v1.1/v1.2 model were changed. The 2D model is not ready to freeze for a 3D
extension because the electrical output and several state-transition mechanisms
remain unresolved.

Before resuming Parts 4–7, establish project-supported values or explicit
model-derived assumptions for: Ag filament resistivity/conductivity, effective
cross-section mapping (including out-of-plane depth), PVA gap/access transport,
electrode contact resistance, and the applied source/circuit topology. Keep each
provenance category explicit; do not relabel assumed values as literature data.

## 13. Reproducibility and validation

- `.venv/bin/python -m compileall kmc_model analysis`: passed (cache directed to
  a writable temporary directory).
- `.venv/bin/python analysis/kmc_validation.py`: passed deterministic
  single-case validation.
- `.venv/bin/python kmc_model/run_single.py`: baseline remained +0.30 V, 300 K,
  seed 42, 20,000 events, 11 nucleations, 7 growth events, 19,962 hops, 18
  filament sites, maximum filament row 2, SET false.
- Unified explorer repeated seed 42 twice and seed 43 twice at +0.30 V / 300 K;
  each same-seed pair had identical output. Seed 42 reached the event cap at
  20,000; seed 43 terminated with no active events at 33.
- A short pulse-runner smoke case completed and wrote its outputs. This only
  checks protocol execution; it is not a scientific pulse result.
- A compliance-config request and a nonbaseline-thickness request both failed
  explicitly with `NotImplementedError`, rather than running with ignored inputs.
