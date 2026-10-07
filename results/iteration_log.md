# Iteration log

## Iteration 1
- Reproduced the project validation workflow and confirmed the active environment issue.
- Installed pytest into the project environment to enable reproducible regression checks.
- Added regression tests covering the nonphysical directional bias, disconnected filament connectivity, and positive-bias sweep reset behavior.

## Iteration 2
- Removed the artificial `hopping_direction_bias` contribution from the KMC rate law.
- Replaced the asymmetric barrier term with a symmetric detailed-balance field term that lowers the forward barrier and raises the reverse barrier.
- Fixed the connected-filament check so a valid SET path must span the Ag electrode to the Pt electrode instead of relying on an arbitrary cluster start.
- Reset `positive_bias_time_s` when the sweep returns to zero or negative bias so the time-to-SET metric is not carried across sweep segments.

## Iteration 3
- Added the project-level validation script and task scaffolding.
- Documented the current honest model scope in the project README and added the MIT license.
