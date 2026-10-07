# KMC RESET mechanism audit

## Decision

RESET was not implemented or simulated. The final voltage-growth study did not provide formed filament states, and the frozen KMC engine has no supported filament dissolution transition.

## Existing implementation

`EventType` defines Ag+ generation, hopping, nucleation, reduction/deposition, and a `FILAMENT_CONNECTION` enum. The engine does not create a filament-connection event; it checks SET as a post-event condition. No event converts `AG_FILAMENT` back into `AG_ION` or `EMPTY`, so reverse voltage alone cannot dissolve a filament in the current mechanism.

## Candidate RESET physics and missing support

| Required item | Current evidence | Decision |
|---|---|---|
| RESET event | No filament detachment/rupture event exists | Do not add an event without a justified state transition |
| Activation barrier | No dissolution barrier is established; provenance calls it unresolved | No value selected |
| Field dependence | Existing signed field barrier applies to mobile Ag+ hopping and deposition, not detachment from `AG_FILAMENT` | Do not reuse it as a dissolution law without support |
| Dissolution rule | No rule for which filament cell detaches, when, or into which state | No rule invented |
| Provenance | Project data contains continuous-model RESET assumptions and literature context, but not a KMC microscopic dissolution rate/barrier | Insufficient to parameterize a KMC event |

The continuous-model RESET threshold/rate is not imported into KMC. The project literature RESET voltage is context only and cannot supply a microscopic event barrier. A future KMC RESET study needs a defensible event and parameter provenance plus formed states; none is available in this frozen model workflow.
