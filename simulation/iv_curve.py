"""Generate a hysteretic I-V response from the filament state model."""

import numpy as np

from .filament import FilamentState, update_state


def simulate(
    voltage: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return current, resistance, filament length, and Ag+ fraction arrays."""
    current = np.zeros_like(voltage)
    resistance = np.zeros_like(voltage)
    filament_length_nm = np.zeros_like(voltage)
    ion_fraction = np.zeros_like(voltage)
    state = FilamentState()

    for index, sample in enumerate(voltage):
        update_state(float(sample), state)
        resistance[index] = state.resistance_ohm
        current[index] = sample / resistance[index]
        filament_length_nm[index] = state.length_nm
        ion_fraction[index] = state.ion_fraction

    return current, resistance, filament_length_nm, ion_fraction