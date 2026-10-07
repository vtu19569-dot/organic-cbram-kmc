import pytest

from kmc_model.kmc_engine import KMCEngine
from kmc_model.lattice import LatticeGrid, LatticeState
from kmc_model.parameters import KMCConfig
from simulation.filament import FilamentState, update_state


def test_direction_bias_is_zero_and_field_is_not_artificially_asymmetric():
    config = KMCConfig()
    assert config.hopping_direction_bias == 0.0

    engine = KMCEngine(config)
    down_barrier = engine._effective_barrier_ev(0.25, 1, 2)
    up_barrier = engine._effective_barrier_ev(0.25, 2, 1)

    assert down_barrier < up_barrier
    assert engine._rate_factor(LatticeState.AG_ION, 1, 2) > 0.0
    assert engine._rate_factor(LatticeState.AG_ION, 2, 1) > 0.0


def test_connected_filament_cluster_requires_top_to_bottom_path():
    engine = KMCEngine(KMCConfig())
    lattice = engine.lattice

    for row in range(engine.config.lattice_rows):
        for col in range(engine.config.lattice_columns):
            lattice.set_state(row, col, LatticeState.EMPTY)

    for col in range(engine.config.lattice_columns):
        lattice.set_state(0, col, LatticeState.AG_ELECTRODE)
        lattice.set_state(engine.config.lattice_rows - 1, col, LatticeState.PT_ELECTRODE)

    # Two disconnected filament islands: one at the top and one at the bottom.
    lattice.set_state(1, 1, LatticeState.AG_FILAMENT)
    lattice.set_state(2, 1, LatticeState.AG_FILAMENT)
    lattice.set_state(23, 7, LatticeState.AG_FILAMENT)
    lattice.set_state(24, 7, LatticeState.PT_ELECTRODE)

    assert not engine._connected_filament_cluster()

    lattice.set_state(3, 1, LatticeState.AG_FILAMENT)
    lattice.set_state(4, 1, LatticeState.AG_FILAMENT)
    lattice.set_state(5, 1, LatticeState.AG_FILAMENT)
    lattice.set_state(6, 1, LatticeState.AG_FILAMENT)
    lattice.set_state(7, 1, LatticeState.AG_FILAMENT)
    lattice.set_state(8, 1, LatticeState.AG_FILAMENT)
    lattice.set_state(9, 1, LatticeState.AG_FILAMENT)
    lattice.set_state(10, 1, LatticeState.AG_FILAMENT)
    lattice.set_state(11, 1, LatticeState.AG_FILAMENT)
    lattice.set_state(12, 1, LatticeState.AG_FILAMENT)
    lattice.set_state(13, 1, LatticeState.AG_FILAMENT)
    lattice.set_state(14, 1, LatticeState.AG_FILAMENT)
    lattice.set_state(15, 1, LatticeState.AG_FILAMENT)
    lattice.set_state(16, 1, LatticeState.AG_FILAMENT)
    lattice.set_state(17, 1, LatticeState.AG_FILAMENT)
    lattice.set_state(18, 1, LatticeState.AG_FILAMENT)
    lattice.set_state(19, 1, LatticeState.AG_FILAMENT)
    lattice.set_state(20, 1, LatticeState.AG_FILAMENT)
    lattice.set_state(21, 1, LatticeState.AG_FILAMENT)
    lattice.set_state(22, 1, LatticeState.AG_FILAMENT)
    lattice.set_state(23, 1, LatticeState.AG_FILAMENT)

    assert engine._connected_filament_cluster()


def test_positive_bias_time_resets_between_sweeps():
    state = FilamentState()

    update_state(0.3, state)
    assert state.positive_bias_time_s > 0.0

    update_state(0.0, state)
    assert state.positive_bias_time_s == 0.0

    update_state(0.3, state)
    assert 0.0 < state.positive_bias_time_s <= 0.30
