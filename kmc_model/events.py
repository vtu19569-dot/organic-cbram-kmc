"""Event definitions for the first working KMC SET simulation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple


class EventType(str, Enum):
    """Minimal event set used in the first coarse-grained KMC SET model."""

    AG_GENERATION = "Ag+ generation"
    AG_HOPPING = "Ag+ hopping"
    AG_NUCLEATION = "Ag+ nucleation"
    AG_REDUCTION_DEPOSITION = "Ag+ reduction/deposition"
    FILAMENT_CONNECTION = "filament connection"


@dataclass
class KMCEvent:
    """A single event candidate in the KMC model."""

    event_type: EventType
    source_site: Optional[Tuple[int, int]] = None
    target_site: Optional[Tuple[int, int]] = None
    rate: float = 0.0
    effective_barrier_ev: float = 0.0
    time_increment: float = 0.0
    notes: str = ""


@dataclass
class EventQueue:
    """Simple event container for the first KMC engine."""

    events: list[KMCEvent] = field(default_factory=list)
