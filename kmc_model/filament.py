"""Filament summary representation for the first working KMC SET simulation."""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class FilamentState:
    """Summary of the filament morphology in the coarse-grained KMC model."""

    start_site: Optional[Tuple[int, int]] = None
    end_site: Optional[Tuple[int, int]] = None
    occupied_sites: List[Tuple[int, int]] = field(default_factory=list)
    length_nm: float = 0.0
    width_nm: float = 0.0
    connection_status: str = "not connected"
    connectivity: str = "incomplete"
    metal_fraction: float = 0.0
    notes: str = "single-case KMC SET prototype"


@dataclass
class FilamentMorphology:
    """Container for morphology snapshots and summary data."""

    voltage_v: float = 0.0
    temperature_k: Optional[float] = None
    filament: Optional[FilamentState] = None
    snapshot_label: str = "initial"
    morphology_summary: str = "single-case KMC SET prototype"
