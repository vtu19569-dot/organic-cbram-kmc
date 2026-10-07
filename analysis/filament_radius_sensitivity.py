"""Run filament-radius sensitivity for the frozen v1.1 CBRAM model."""

import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

import simulation.filament as filament
from simulation.filament import FilamentState, update_state
from simulation.parameters import (
    DEVICE_THICKNESS,
    MAX_SWEEP_VOLTAGE,
    MIN_SWEEP_VOLTAGE,
)


RESULTS_DIR = ROOT / "results"
RADIUS_VALUES_M = tuple(value * 1e-9 for value in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0))
BASELINE_RADIUS_M = 0.5e-9


def run_case(max_radius_m: float) -> dict[str, object]:
    original_radius = filament.MAX_FILAMENT_RADIUS_M
    filament.MAX_FILAMENT_RADIUS_M = max_radius_m
    try:
        forward = np.linspace(MIN_SWEEP_VOLTAGE, MAX_SWEEP_VOLTAGE, 500)
        reverse = np.linspace(MAX_SWEEP_VOLTAGE, MIN_SWEEP_VOLTAGE, 500)
        voltage = np.concatenate((forward, reverse[1:]))
        state = FilamentState(temperature_k=300.0)
        lengths = []
        resistances = []
        set_index = None
        set_positive_bias_time = None

        for index, sample in enumerate(voltage):
            update_state(float(sample), state)
            lengths.append(state.length_nm)
            resistances.append(state.resistance_ohm)
            if set_index is None and state.length_fraction >= 0.99:
                set_index = index
                set_positive_bias_time = state.positive_bias_time_s

        lengths = np.asarray(lengths)
        resistances = np.asarray(resistances)
        reset_indices = np.flatnonzero(
            (np.arange(voltage.size) > set_index if set_index is not None else False)
            & (lengths <= 0.01 * DEVICE_THICKNESS * 1e9)
        )
        reset_index = reset_indices[0] if reset_indices.size else None
        set_reached = set_index is not None
        lrs = float(resistances.min()) if set_reached else ""
        hrs = float(resistances.max())
        return {
            "max_filament_radius_nm": max_radius_m * 1e9,
            "max_filament_length_nm": float(lengths.max()),
            "set_reached": set_reached,
            "set_voltage_V": voltage[set_index] if set_reached else "",
            "positive_bias_time_s": set_positive_bias_time if set_reached else "",
            "reset_voltage_V": voltage[reset_index] if reset_index is not None else "",
            "lrs_resistance_ohm": lrs,
            "hrs_resistance_ohm": hrs,
            "on_off_ratio": hrs / lrs if set_reached else "",
        }
    finally:
        filament.MAX_FILAMENT_RADIUS_M = original_radius


def save_csv(rows: list[dict[str, object]]) -> None:
    output = RESULTS_DIR / "filament_radius_sensitivity.csv"
    with output.open("w", newline="") as handle:
        fieldnames = list(rows[0].keys()) + ["is_v1_1_baseline"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "is_v1_1_baseline": row["max_filament_radius_nm"] == 0.5})


def save_plot(rows: list[dict[str, object]], value_key: str, ylabel: str, title: str, filename: str) -> None:
    figure, axis = plt.subplots(figsize=(8, 6))
    x_values = [row["max_filament_radius_nm"] for row in rows]
    y_values = [row[value_key] for row in rows]
    axis.plot(x_values, y_values, "o-", color="tab:blue")
    axis.axvline(0.5, color="tab:orange", linestyle="--", label="v1.1 baseline")
    axis.set_xlabel("Maximum filament radius (nm)")
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.grid(True)
    axis.legend()
    figure.tight_layout()
    figure.savefig(RESULTS_DIR / filename, dpi=160)
    plt.close(figure)


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    rows = [run_case(value) for value in RADIUS_VALUES_M]
    save_csv(rows)
    save_plot(rows, "lrs_resistance_ohm", "LRS resistance (Ohm)", "LRS Resistance vs Filament Radius", "lrs_resistance_vs_filament_radius.png")
    save_plot(rows, "on_off_ratio", "ON/OFF ratio", "ON/OFF Ratio vs Filament Radius", "on_off_ratio_vs_filament_radius.png")

    baseline = next(row for row in rows if row["max_filament_radius_nm"] == 0.5)
    assert baseline["set_reached"]
    assert abs(float(baseline["set_voltage_V"]) - 0.282) < 0.002
    assert abs(float(baseline["positive_bias_time_s"]) - 0.141) < 0.002
    assert abs(float(baseline["reset_voltage_V"]) + 0.229) < 0.002
    assert abs(float(baseline["lrs_resistance_ohm"]) - 2037.18) < 1
    assert abs(float(baseline["hrs_resistance_ohm"]) - 100000) < 2
    print("Saved filament-radius sensitivity CSV and plots")
    for row in rows:
        print(row)
    print("v1.1 filament-radius baseline reproduced")


if __name__ == "__main__":
    main()