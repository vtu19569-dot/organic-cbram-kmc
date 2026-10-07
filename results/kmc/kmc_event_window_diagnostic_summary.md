# KMC Event-Window Adequacy Diagnostic

## 1. Objective

Determine whether the 20,000-event numerical window truncates meaningful evolution for the frozen baseline case, changing only the event cap.

## 2. Current 20,000-event limitation

An event cap is a numerical stopping limit. Reaching it means the configured simulation window ended; it is not evidence of physical non-forming.

## 3. Termination logic

In `KMCEngine.run()`, the loop runs while `total_events < max_kmc_events`. Before each event it exits if `_build_events()` is empty or if summed rate is non-positive. After applying each event it checks the SET condition and exits if reached. Otherwise, reaching the loop bound ends the run. Thus the categories are: `NO_ACTIVE_EVENT` for an empty event list or non-positive total rate before the cap; `SET_REACHED` when the post-event filament connectivity test succeeds; and `EVENT_CAP` when the event bound is reached without SET. The cap is a simulation-window exhaustion, not physical non-forming.

`KMCResult.set_time_s` is assigned the accumulated elapsed KMC time on every exit, including non-SET exits. In the diagnostic CSV it is therefore `simulation_time_s`; `forming_time_s` is blank/NaN unless SET occurs. The event enum also contains `FILAMENT_CONNECTION`, but the engine does not add that event type in `_build_events()`; SET is detected as a post-event condition.

## 4. Controlled event-window cases

V = +0.30 V; T = 300 K; seed = 42. Only `max_kmc_events` varied: 20,000, 50,000, 100,000, and 200,000. Each case starts from the same initial state and seed.

## 5. Results

| Event cap | Events completed | Termination | SET | Forming time (s) | Simulation time (s) | Nucleation | Growth | Hopping | Filament sites | Max filament row | Filament length (nm) | Max Ag+ row | Final Ag+ sites |
|---:|---:|---|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 20000 | 20000 | EVENT_CAP | False | — | 4.1719161e-05 | 11 | 7 | 19962 | 18 | 2 | 8 | 23 | 3 |
| 50000 | 50000 | EVENT_CAP | False | — | 0.00010452967 | 11 | 7 | 49962 | 18 | 2 | 8 | 23 | 3 |
| 100000 | 100000 | EVENT_CAP | False | — | 0.00020905487 | 11 | 7 | 99962 | 18 | 2 | 8 | 23 | 3 |
| 200000 | 200000 | EVENT_CAP | False | — | 0.00041823694 | 11 | 7 | 199962 | 18 | 2 | 8 | 23 | 3 |

## 6. Filament-growth behavior

From 20,000 to 200,000 events, growth events changed from 7 to 7, filament sites from 18 to 18, maximum filament depth from row 2 to row 2, and the model-reported filament vertical span from 8 to 8 nm. Hopping events changed from 19962 to 199962; nucleation events changed from 11 to 11. These counts describe the one fixed-seed trajectory.

Filament length is the vertical bounding span of all filament cells in the engine’s `FilamentState`, not a per-branch connected-path length. The depth counter is a maximum observed row, so it does not decrease.

## 7. Physical simulated-time behavior

Physical KMC time is accumulated as `tau = -ln(U) / total_rate` for each selected event. The rate sum changes with the lattice state, so time is stochastic and need not scale linearly with event count. In this particular trajectory, physical time increased by about 2.505x, 5.011x, and 10.024x at 50k, 100k, and 200k events relative to the 20k case. That near-proportional scaling is an observed result for this trajectory, not a general conversion between events and seconds; see `simulation_time_s` in the table and plot.

## 8. Interpretation

Decision: **C. apparently adequate** for observing filament evolution in this fixed baseline trajectory. Filament growth, site count, depth, and length are identical at all four caps. There is no evidence here that a window beyond 20,000 events is needed to observe this trajectory's filament evolution. Ag+ hopping continues beyond the cap, but does not produce further filament change in this case.

The result addresses filament evolution for this one baseline trajectory only. It does not establish forming probability, a general SET threshold, or behavior across random seeds. Continued hopping events show that state updates still occur after 20,000 events, but nucleation/growth and measured filament morphology are saturated for this trajectory.

## 9. Recommended production event window

Retain 20,000 events as the production window for this fixed case; larger caps showed continued Ag+ hopping but no additional filament growth. Treat this conclusion as case-specific and do not infer general adequacy across other seeds or conditions.

## 10. Limitations

- One voltage, temperature, and seed were tested, as requested.
- Only the numerical event cap changed; all KMC parameters and the frozen 4-neighbor mechanism remained at defaults.
- A continuing trajectory does not guarantee eventual SET.
- No RESET, temperature, thickness, or voltage sweep was performed.

## 11. Conclusion

For the 0.30 V, 300 K, seed 42 trajectory, the evidence supports **C. apparently adequate** for the 20,000-event window when the endpoint is observing filament evolution. Ag+ migration continued at higher event caps, but filament growth and morphology did not change. This does not claim that the KMC cannot form or establish adequacy for other stochastic trajectories. The original production cap remains 20,000 events.
