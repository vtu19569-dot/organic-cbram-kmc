"""Central, serializable inputs for KMC device experiments.

This schema separates operating conditions from the frozen KMC kinetics. Fields
that the current engine cannot honor are retained for complete experiment
specification, but conversion rejects unsupported geometry/physics rather than
silently ignoring them.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import Optional

from .parameters import KMCConfig


@dataclass(frozen=True)
class WaveformSegment:
    voltage_v: float
    duration_s: float
    label: str = "segment"

    def __post_init__(self) -> None:
        if self.duration_s <= 0:
            raise ValueError("waveform segment duration must be positive")


@dataclass(frozen=True)
class ExperimentConfig:
    experiment_id: str = "kmc_experiment"
    # Device stack
    top_electrode: str = "Ag"
    switching_material: str = "PVA"
    bottom_electrode: str = "Pt"

    # Geometry (current engine only supports the frozen baseline)
    thickness_nm: float = 100.0
    lattice_spacing_nm: float = 4.0
    lattice_rows: int = 25
    lattice_columns: int = 15

    # Operating inputs
    temperature_k: float = 300.0
    set_bias_v: float = 0.30
    reset_bias_v: Optional[float] = None
    compliance_current_a: Optional[float] = None
    waveform: tuple[WaveformSegment, ...] = field(default_factory=tuple)

    # Stochastic controls
    seeds: tuple[int, ...] = (42,)
    max_events: int = 20000

    # Hold/retention inputs (condition only; evolution law is not implemented)
    retention_enabled: bool = False
    hold_voltage_v: float = 0.0
    hold_time_s: float = 0.0

    # Output controls
    output_dir: str = "results/kmc"
    save_event_log: bool = True
    save_morphology: bool = True
    save_lattice: bool = True
    save_current: bool = False
    save_resistance: bool = False

    def __post_init__(self) -> None:
        if self.temperature_k <= 0 or self.thickness_nm <= 0 or self.lattice_spacing_nm <= 0:
            raise ValueError("temperature, thickness, and lattice spacing must be positive")
        if self.max_events <= 0:
            raise ValueError("max_events must be positive")
        if not self.seeds:
            raise ValueError("at least one random seed is required")
        if self.compliance_current_a is not None and self.compliance_current_a <= 0:
            raise ValueError("compliance current must be positive when specified")
        if self.hold_time_s < 0:
            raise ValueError("hold_time_s cannot be negative")

    def to_kmc_config(
        self,
        *,
        voltage_v: Optional[float] = None,
        temperature_k: Optional[float] = None,
        seed: Optional[int] = None,
        max_events: Optional[int] = None,
    ) -> KMCConfig:
        """Build the frozen engine config, rejecting unsupported geometry edits."""
        baseline = KMCConfig()
        geometry = (self.thickness_nm, self.lattice_spacing_nm,
                    self.lattice_rows, self.lattice_columns)
        frozen_geometry = (baseline.switching_layer_thickness_nm, baseline.cell_size_nm,
                           baseline.lattice_rows, baseline.lattice_columns)
        if geometry != frozen_geometry:
            raise NotImplementedError(
                "the current KMC engine cannot map changed thickness/spacing to a validated lattice; "
                "only the frozen 100 nm, 4 nm, 25x15 geometry is supported"
            )
        if self.top_electrode != "Ag" or self.switching_material != "PVA" or self.bottom_electrode != "Pt":
            raise NotImplementedError("the current KMC engine supports only the Ag/PVA/Pt stack")
        if self.reset_bias_v is not None:
            raise NotImplementedError("RESET bias is an experiment input only; no dissolution event is implemented")
        if self.compliance_current_a is not None:
            raise NotImplementedError("compliance is specified but cannot be applied without a validated current model")
        if self.retention_enabled:
            raise NotImplementedError("retention evolution is not implemented in the current KMC event set")
        return replace(
            baseline,
            applied_voltage_v=self.set_bias_v if voltage_v is None else voltage_v,
            temperature_k=self.temperature_k if temperature_k is None else temperature_k,
            random_seed=self.seeds[0] if seed is None else seed,
            max_kmc_events=self.max_events if max_events is None else max_events,
        )

    def to_dict(self) -> dict:
        return asdict(self)
