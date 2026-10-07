# Organic CBRAM Simulation v1.0

A phenomenological Ag/PVA/Pt conductive-bridge random-access memory (CBRAM) model.
The simulation represents Ag+ migration, filament growth during SET, and
field-driven filament dissolution during RESET.

## Device

- Top electrode: Ag
- Switching layer: PVA (polyvinyl alcohol)
- Bottom electrode: Pt
- PVA thickness: 100 nm
- Simulation temperature: 300 K

## Version 1.0 results

These values are produced by the default simulation run:

- Simulated SET voltage: 0.282 V
- Simulated RESET voltage: -0.229 V
- LRS: approximately 2.04 kOhm
- HRS: approximately 100 kOhm
- Maximum filament length: 100 nm

SET is detected when the filament reaches 99% of the PVA thickness. RESET is
detected when the filament falls below 1% of the PVA thickness.

## Data provenance

### Materials Project data

- Ag: `mp-124`, cubic Fm-3m structure, density 10.36 g/cm3
- Pt: `mp-126`, cubic Fm-3m structure, density 21.13 g/cm3

The normalized records are stored in `data/ag.json` and `data/pt.json`.
The original exports are retained as `mp-124.json` and `mp-126.json`.

### Literature reference values

The PVA device reference values are stored in `data/pva.json`:

- PVA film thickness: approximately 100 nm
- Reference SET voltage: approximately +0.27 V
- Reference RESET voltage: approximately -0.13 V
- Reference ON resistance: approximately 1 kOhm
- Reference OFF resistance: approximately 100 kOhm
- Mechanism: Ag filament formation and dissolution

Reference: Royal Society of Chemistry, *J. Mater. Chem. C* (2018),
https://pubs.rsc.org/en/content/articlehtml/2018/tc/c8tc01809j

These values are comparison targets, not proof of experimental validation.

## Version 1.1 analysis timing

The v1.1 analysis distinguishes two timing quantities:

1. `set_sweep_time_s` is the absolute elapsed time from the beginning of the
	triangular voltage sweep.
2. `positive_bias_time_s` is the time accumulated under positive bias before
	SET.

Because the triangular sweep begins at negative voltage, these quantities are
different. Positive-bias time is used when comparing SET operation with the
configured positive-bias operating window of `0.30 s`.

For the 100 nm, 300 K case:

- SET voltage: `0.282 V`
- Absolute sweep time: `0.391 s`
- Positive-bias time: `0.141 s`
- Positive-bias limit: `0.300 s`

### Model assumptions

The following values are simulation assumptions or calibration parameters. They
are not claimed to be measured PVA properties:

- Effective Ag+ mobility: `5e-13 m2/(V s)`
- Activation energy: `0.20 eV`
- Temperature: `300 K`
- Time step: `1e-3 s`
- Ag filament resistivity: `1.6e-8 Ohm m`
- Initial filament radius: `0.1 nm`
- Maximum filament radius: `0.5 nm`
- Dissolution rate factor: `1.5`
- Device area: `5 um x 5 um`
- SET/RESET detection thresholds: 99% and 1% of PVA thickness

The resistance combines the geometric filament term,
`R = rho * L / (pi * r^2)`, with a gap-resistance contribution while the
filament is incomplete.

## Run

```bash
.venv/bin/python main.py
```

Outputs are written to `results/iv_curve.csv` and `results/iv_curve.png`.
The CSV contains voltage, current, resistance, filament length, and Ag+ ion
fraction for every sweep sample.
