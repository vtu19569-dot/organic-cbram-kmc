"""Deterministic conceptual particle layers for SET and RESET figures."""

import numpy as np


def particle_cloud(seed: int, count: int, x_low: float = 3.0, x_high: float = 7.0):
    generator = np.random.default_rng(seed)
    return np.column_stack((generator.uniform(x_low, x_high, count), generator.uniform(2.65, 7.4, count)))


def filament_particles(seed: int, length_fraction: float, count: int = 170):
    if length_fraction <= 0:
        return np.empty((0, 2))
    generator = np.random.default_rng(seed)
    y_low = 2.45
    y_high = y_low + 5.05 * length_fraction
    y = generator.uniform(y_low, y_high, count)
    x = generator.normal(5.0, 0.08 + 0.22 * length_fraction, count)
    return np.column_stack((x, y))


def draw_particles(axis, positions, color="#bd3939", size=12, alpha=0.82):
    if len(positions):
        axis.scatter(positions[:, 0], positions[:, 1], s=size, c=color, alpha=alpha, edgecolors="none", zorder=5)
