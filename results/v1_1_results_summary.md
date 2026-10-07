# CBRAM Simulation v1.1 Results Summary

## Frozen configuration

- Device: Ag / PVA / Pt
- PVA thickness: 100 nm baseline
- Temperature: 300 K baseline
- Voltage protocol: triangular sweep from -0.5 V to +0.5 V and back
- Timestep: 1 ms
- Positive-bias operating limit: 0.30 s
- Ag+ inventory: finite normalized inventory

## Baseline simulation

| Quantity | v1.1 result |
| --- | ---: |
| SET voltage | +0.282 V |
| SET sweep time | 0.391 s |
| Positive-bias time to SET | 0.141 s |
| RESET voltage | -0.229 V |
| LRS | approximately 2.04 kOhm |
| HRS | approximately 100 kOhm |

The 0.391 s SET value is absolute time from the beginning of the triangular
sweep. The 0.141 s value is the positive-bias accumulation time and is the
quantity compared with the 0.30 s operating limit.

## Parameter studies

### Thickness

At 300 K and a 0.50 V maximum, SET occurs at 0.099 V, 0.199 V, and 0.299 V
for 50 nm, 100 nm, and 150 nm PVA, respectively. The 200 nm device reaches
113.1 nm and does not SET within 0.30 s.

### Temperature

At 100 nm PVA, 250 K does not SET within the window. SET occurs at 0.282 V,
0.161 V, and 0.107 V at 300 K, 350 K, and 400 K. The model predicts that
higher temperature increases Arrhenius Ag+ mobility and lowers the voltage
needed to reach contact within the finite window.

### Voltage window

At 300 K and 100 nm PVA, 0.10 V, 0.15 V, and 0.20 V do not SET within the
window. SET is reached at 0.25 V and above. Higher voltage also reduces the
positive-bias time required for contact.

## Interpretation and limitations

These are outputs of a physics-informed phenomenological model. The model is
not an atomistic molecular-dynamics or DFT calculation and has not been
experimentally validated.

Literature-backed values include the Ag/PVA/Pt device concept, approximate PVA
thickness, and reference SET, RESET, ON-resistance, and OFF-resistance values.
Materials Project data supplies the Ag and Pt structural records.

Model assumptions include effective Ag+ mobility, activation energy, timestep,
positive-bias limit, finite ion inventory, filament resistivity, filament-radius
bounds, dissolution factor, gap-resistance scaling, and event thresholds.
The approximately linear SET-voltage/thickness trend is model-dependent and
should not be presented as a universal physical law.