"""Run v1.2 sensitivity studies without changing the frozen simulation model."""

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
    TIME_STEP_S,
)


RESULTS_DIR = ROOT / "results"
MOBILITY_VALUES = (1e-13, 2.5e-13, 5e-13, 7.5e-13, 1e-12)
BASELINE_MOBILITY = 5e-13


def run_mobility_case(mobility: float) -> dict[str, object]:
    """Run one complete triangular sweep with a temporary mobility override."""
    original_mobility = filament.AG_ION_MOBILITY_M2_V_S
    filament.AG_ION_MOBILITY_M2_V_S = mobility
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
        set_voltage = voltage[set_index] if set_reached else ""
        set_time = set_positive_bias_time if set_reached else ""
        reset_voltage = voltage[reset_index] if reset_index is not None else ""
        lrs = float(resistances.min())
        hrs = float(resistances.max())

        return {
            "mobility_m2_V_s": mobility,
            "max_filament_length_nm": float(lengths.max()),
            "set_reached": set_reached,
            "set_voltage_V": set_voltage,
            "positive_bias_time_s": set_time,
            "reset_voltage_V": reset_voltage,
            "min_resistance_ohm": lrs,
            "hrs_resistance_ohm": hrs,
            "on_off_ratio": hrs / lrs,
        }
    finally:
        filament.AG_ION_MOBILITY_M2_V_S = original_mobility


def save_results(rows: list[dict[str, object]]) -> None:
    output = RESULTS_DIR / "mobility_sensitivity.csv"
    with output.open("w", newline="") as handle:
        fieldnames = list(rows[0].keys()) + ["is_v1_1_baseline"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "is_v1_1_baseline": row["mobility_m2_V_s"] == BASELINE_MOBILITY})


def save_plot(rows: list[dict[str, object]], x_values, y_values, ylabel: str, title: str, filename: str) -> None:
    figure, axis = plt.subplots(figsize=(8, 6))
    axis.plot(x_values, y_values, "o-", color="tab:blue")
    axis.axvline(BASELINE_MOBILITY, color="tab:orange", linestyle="--", label="v1.1 baseline")
    axis.set_xlabel("Ag+ mobility (m2/(V s))")
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.grid(True)
    axis.legend()
    figure.tight_layout()
    figure.savefig(RESULTS_DIR / filename, dpi=160)
    plt.close(figure)


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    rows = [run_mobility_case(mobility) for mobility in MOBILITY_VALUES]
    save_results(rows)

    reached_rows = [row for row in rows if row["set_reached"]]
    save_plot(
        rows,
        [row["mobility_m2_V_s"] for row in reached_rows],
        [row["set_voltage_V"] for row in reached_rows],
        "SET voltage (V)",
        "SET Voltage vs Ag+ Mobility",
        "set_voltage_vs_mobility.png",
    )
    save_plot(
        rows,
        [row["mobility_m2_V_s"] for row in reached_rows],
        [row["positive_bias_time_s"] for row in reached_rows],
        "Positive-bias time to SET (s)",
        "SET Time vs Ag+ Mobility",
        "set_time_vs_mobility.png",
    )

    baseline = next(row for row in rows if row["mobility_m2_V_s"] == BASELINE_MOBILITY)
    assert baseline["set_reached"]
    assert abs(float(baseline["set_voltage_V"]) - 0.282) < 0.002
    assert abs(float(baseline["positive_bias_time_s"]) - 0.141) < 0.002
    assert abs(float(baseline["reset_voltage_V"]) + 0.229) < 0.002
    print("Saved mobility sensitivity CSV and plots")
    for row in rows:
        print(row)
    print("v1.1 mobility baseline reproduced")


if __name__ == "__main__":
    main()