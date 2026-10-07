"""Configuration container for the coarse-grained lattice KMC model.

This file contains the first working Stage 3 configuration for a single-case
SET simulation. The values are intentionally labelled as model assumptions
where the exact microscopic quantity is not experimentally established.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class KMCConfig:
    """Configuration for the first working coarse-grained KMC SET simulation."""

    # Device definition
    device_top_electrode: str = "Ag"
    device_bottom_electrode: str = "Pt"
    switching_layer: str = "PVA"
    switching_layer_thickness_nm: float = 100.0
    material_project_top: str = "mp-124"
    material_project_bottom: str = "mp-126"
    silver_density_g_cm3: float = 10.36
    platinum_density_g_cm3: float = 21.13

    # Single-case Stage 3 test conditions
    applied_voltage_v: float = 0.30
    temperature_k: float = 300.0
    random_seed: int = 42
    max_kmc_events: int = 20000

    # Coarse-grained geometry
    lattice_columns: int = 15
    lattice_rows: int = 25
    cell_size_nm: float = 4.0
    physical_thickness_to_cell_mapping: str = "100 nm / 25 cells = 4 nm per cell"

    # Event-rate parameters (model assumptions / numerical KMC values)
    attempt_frequency_hz: float = 1.0e12
    activation_energy_ev: float = 0.25
    nucleation_activation_energy_ev: float = 0.25
    growth_activation_energy_ev: float = 0.25
    nucleation_attempt_frequency_hz: float = 1.0e12
    growth_rate_multiplier: float = 1.0
    field_factor: float = 0.35
    deposition_bias: float = 1.5
    electrode_injection_rate_factor: float = 0.8
    hopping_direction_bias: float = 1.0
    max_hop_distance: int = 1
    connectivity_rule: str = "4-neighbor"
    growth_spatial_rule: str = "4-neighbor"
    growth_reach_distance: int = 1

    # Output settings
    output_directory: str = "results/kmc"
    voltage_label: str = "0p30V"
    random_seed_label: str = "42"

    # Planned validation
    validation_repeats: int = 2
    required_outputs: List[str] = field(
        default_factory=lambda: [
            "kmc_set_0p30V_states.csv",
            "kmc_set_0p30V_process.png",
            "kmc_single_set.csv",
            "kmc_single_set_diagnostics.csv",
            "kmc_set_0p30V_diagnostics.png",
        ]
    )
