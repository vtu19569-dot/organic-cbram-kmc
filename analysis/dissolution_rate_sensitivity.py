"""Run RESET-rate sensitivity for the frozen v1.1 CBRAM model."""

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
DISSOLUTION_VALUES = (0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0)
BASELINE_DISSOLUTION = 1.5


def run_case(dissolution_factor: float) -> dict[str, object]:
    original_factor = filament.DISSOLUTION_RATE_FACTOR
    filament.DISSOLUTION_RATE_FACTOR = dissolution_factor
    try:
        forward = np.linspace(MIN_SWEEP_VOLTAGE, MAX_SWEEP_VOLTAGE, 500)
        reverse = np.linspace(MAX_SWEEP_VOLTAGE, MIN_SWEEP_VOLTAGE, 500)
        voltage = np.concatenate((forward, reverse[1:]))
        state = FilamentState(temperature_k=300.0)
        lengths = []
        resistances = []
        set_index = None
        set_positive_bias_time = None
        reset_index = None
        reset_length = None

        for index, sample in enumerate(voltage):
            update_state(float(sample), state)
            lengths.append(state.length_nm)
            resistances.append(state.resistance_ohm)
            if set_index is None and state.length_fraction >= 0.99:
                set_index = index
                set_positive_bias_time = state.positive_bias_time_s
            if (
                set_index is not None
                and index > set_index
                and reset_index is None
                and state.length_fraction <= 0.01
            ):
                reset_index = index
                reset_length = state.length_nm

        lengths = np.asarray(lengths)
        resistances = np.asarray(resistances)
        set_reached = set_index is not None
        reset_reached = reset_index is not None
        lrs = float(resistances.min()) if set_reached else ""
        hrs = float(resistances.max())
        return {
            "dissolution_rate_factor": dissolution_factor,
            "set_reached": set_reached,
            "set_voltage_V": voltage[set_index] if set_reached else "",
            "positive_bias_time_s": set_positive_bias_time if set_reached else "",
            "reset_reached": reset_reached,
            "reset_voltage_V": voltage[reset_index] if reset_reached else "",
            "reset_sweep_time_s": (reset_index + 1) * TIME_STEP_S if reset_reached else "",
            "filament_length_at_reset_nm": reset_length if reset_reached else "",
            "max_filament_length_nm": float(lengths.max()),
            "lrs_resistance_ohm": lrs,
            "hrs_resistance_ohm": hrs,
            "on_off_ratio": hrs / lrs if set_reached else "",
        }
    finally:
        filament.DISSOLUTION_RATE_FACTOR = original_factor


def save_csv(rows: list[dict[str, object]]) -> None:
    output = RESULTS_DIR / "dissolution_rate_sensitivity.csv"
    with output.open("w", newline="") as handle:
        fieldnames = list(rows[0].keys()) + ["is_v1_1_baseline"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "is_v1_1_baseline": row["dissolution_rate_factor"] == BASELINE_DISSOLUTION})


def save_plot(rows: list[dict[str, object]], value_key: str, ylabel: str, title: str, filename: str) -> None:
    figure, axis = plt.subplots(figsize=(8, 6))
    x_values = [row["dissolution_rate_factor"] for row in rows]
    y_values = [row[value_key] for row in rows]
    axis.plot(x_values, y_values, "o-", color="tab:red")
    axis.axvline(BASELINE_DISSOLUTION, color="tab:orange", linestyle="--", label="v1.1 baseline")
    axis.set_xlabel("Dissolution rate factor")
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.grid(True)
    axis.legend()
    figure.tight_layout()
    figure.savefig(RESULTS_DIR / filename, dpi=160)
    plt.close(figure)


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    rows = [run_case(value) for value in DISSOLUTION_VALUES]
    save_csv(rows)
    save_plot(rows, "reset_voltage_V", "RESET voltage (V)", "RESET Voltage vs Dissolution Rate", "reset_voltage_vs_dissolution_rate.png")
    save_plot(rows, "filament_length_at_reset_nm", "Filament length at RESET (nm)", "RESET Filament Behavior vs Dissolution Rate", "reset_behavior_vs_dissolution_rate.png")

    baseline = next(row for row in rows if row["dissolution_rate_factor"] == BASELINE_DISSOLUTION)
    assert baseline["set_reached"] and baseline["reset_reached"]
    assert abs(float(baseline["set_voltage_V"]) - 0.282) < 0.002
    assert abs(float(baseline["positive_bias_time_s"]) - 0.141) < 0.002
    assert abs(float(baseline["reset_voltage_V"]) + 0.229) < 0.002
    assert abs(float(baseline["lrs_resistance_ohm"]) - 2037.18) < 1
    assert abs(float(baseline["hrs_resistance_ohm"]) - 100000) < 2
    print("Saved dissolution-rate sensitivity CSV and plots")
    for row in rows:
        print(row)
    print("v1.1 dissolution-rate baseline reproduced")


if __name__ == "__main__":
    main()