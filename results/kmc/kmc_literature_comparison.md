# KMC literature context

The project literature reference describes an Ag/Ag-salt-incorporated PVA/Pt device with approximately 100 nm PVA and experimental SET around +0.27 V (project source: RSC, *J. Mater. Chem. C* 2018, https://pubs.rsc.org/en/content/articlehtml/2018/tc/c8tc01809j; normalized project data in `data/pva.json`). The same project context lists an experimental RESET reference near -0.13 V and ON/OFF resistance references near 1 kOhm / 100 kOhm.

| Evidence class | SET value | Meaning |
|---|---:|---|
| Literature experiment | ~+0.27 V | Contextual experimental reference; device includes Ag-salt-incorporated PVA |
| Continuous v1.1/v1.2 model | ~+0.282 V; ~0.141 s positive-bias time | Separate phenomenological model output; not experimental validation |
| Frozen KMC | No SET observed in tested 0.10–0.50 V, 300 K, 20,000-event voltage runs | Stochastic finite-window model result; not evidence that experimental SET is impossible |

Numerical proximity between the two SET voltages is not model validation. The KMC was not fitted to the literature value.
