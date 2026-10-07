"""Simple conduction proxy for the first KMC SET case."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ResistanceModel:
    """Minimal resistance proxy using the filament geometry as a crude estimate."""

    filament_length_nm: float = 0.0
    filament_width_nm: float = 0.0
    conductivity_proxy: Optional[float] = None
    resistance_ohm: Optional[float] = None
    notes: str = "single-case coarse-grained KMC conduction proxy"

    def update_from_filament(self) -> None:
        """Estimate a crude conduction proxy using a geometrical scaling argument."""
        if self.filament_length_nm <= 0.0 or self.filament_width_nm <= 0.0:
            self.resistance_ohm = 1e9
            self.conductivity_proxy = 0.0
            return
        cross_section = self.filament_width_nm * self.filament_width_nm
        self.conductivity_proxy = cross_section / self.filament_length_nm
        self.resistance_ohm = 1.0 / max(self.conductivity_proxy, 1e-12)
