"""Electric-field-driven Ag+ migration and filament resistance model."""

from dataclasses import dataclass

import numpy as np

from .parameters import (
    ACTIVATION_ENERGY_EV,
    AG_ION_MOBILITY_M2_V_S,
    AG_RESISTIVITY_OHM_M,
    BOLTZMANN_EV_K,
    DEVICE_THICKNESS,
    DISSOLUTION_RATE_FACTOR,
    GAP_RESISTANCE_SCALE_OHM,
    INITIAL_FILAMENT_RADIUS_M,
    MAX_SWEEP_VOLTAGE,
    MAX_FILAMENT_RADIUS_M,
    POSITIVE_BIAS_TIME_LIMIT_S,
    REFERENCE_TEMPERATURE_K,
    TEMPERATURE_K,
    TIME_STEP_S,
    AVAILABLE_ION_FRACTION,
)


@dataclass
class FilamentState:
    """Internal state of the Ag filament and mobile Ag+ ions."""

    length_fraction: float = 0.0
    ion_fraction: float = 0.0
    temperature_k: float = TEMPERATURE_K
    voltage_v: float = 0.0
    positive_bias_time_s: float = 0.0

    @property
    def length_nm(self) -> float:
        return self.length_fraction * DEVICE_THICKNESS * 1e9

    @property
    def radius_m(self) -> float:
        return INITIAL_FILAMENT_RADIUS_M + (
            MAX_FILAMENT_RADIUS_M - INITIAL_FILAMENT_RADIUS_M
        ) * self.length_fraction

    @property
    def electric_field_v_m(self) -> float:
        return self.voltage_v / DEVICE_THICKNESS

    @property
    def mobility_m2_v_s(self) -> float:
        """Effective mobility using a relative Arrhenius temperature factor."""
        exponent = -ACTIVATION_ENERGY_EV / BOLTZMANN_EV_K * (
            1 / self.temperature_k - 1 / REFERENCE_TEMPERATURE_K
        )
        return AG_ION_MOBILITY_M2_V_S * np.exp(exponent)

    @property
    def available_ion_fraction(self) -> float:
        return max(0.0, AVAILABLE_ION_FRACTION - self.ion_fraction)

    @property
    def filament_resistance_ohm(self) -> float:
        area = np.pi * self.radius_m**2
        return AG_RESISTIVITY_OHM_M * max(self.length_fraction * DEVICE_THICKNESS, 1e-12) / area

    @property
    def resistance_ohm(self) -> float:
        gap_fraction = 1.0 - self.length_fraction
        gap_resistance = GAP_RESISTANCE_SCALE_OHM * gap_fraction**2
        return self.filament_resistance_ohm + gap_resistance


def update_state(voltage: float, state: FilamentState) -> FilamentState:
    """Advance Ag+ migration and filament geometry for one time step."""
    state.voltage_v = voltage
    if voltage > 0.0:
        if state.positive_bias_time_s < POSITIVE_BIAS_TIME_LIMIT_S:
            state.positive_bias_time_s = min(
                POSITIVE_BIAS_TIME_LIMIT_S,
                state.positive_bias_time_s + TIME_STEP_S,
            )
            electric_field = abs(state.electric_field_v_m)
            drift_distance = state.mobility_m2_v_s * electric_field * TIME_STEP_S
            length_increment = min(
                drift_distance / DEVICE_THICKNESS,
                state.available_ion_fraction,
            )
            state.ion_fraction += length_increment
            state.length_fraction = min(
                1.0, state.length_fraction + length_increment
            )
    elif voltage < 0.0:
        electric_field = abs(state.electric_field_v_m)
        dissolution_distance = (
            state.mobility_m2_v_s
            * electric_field
            * TIME_STEP_S
            * DISSOLUTION_RATE_FACTOR
        )
        rupture_increment = dissolution_distance / DEVICE_THICKNESS
        state.length_fraction = max(0.0, state.length_fraction - rupture_increment)
        state.ion_fraction = max(0.0, state.ion_fraction - rupture_increment)

    return state