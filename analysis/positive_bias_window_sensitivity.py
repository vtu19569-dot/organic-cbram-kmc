"""Run positive-bias operating-window sensitivity for frozen v1.1."""

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
WINDOW_VALUES_S = (0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50)
BASELINE_WINDOW_S = 0.30


def run_case(window_s: float) -> dict[str, object]:
    original_window = filament.POSITIVE_BIAS_TIME_LIMIT_S
    filament.POSITIVE_BIAS_TIME_LIMIT_S = window_s
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

        lengths = np.asarray(lengths)
        resistances = np.asarray(resistances)
        set_reached = set_index is not None
        lrs = float(resistances.min()) if set_reached else ""
        hrs = float(resistances.max())
        return {
            "positive_bias_time_limit_s": window_s,
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
        filament.POSITIVE_BIAS_TIME_LIMIT_S = original_window


def save_csv(rows: list[dict[str, object]]) -> None:
    output = RESULTS_DIR / "positive_bias_window_sensitivity.csv"
    with output.open("w", newline="") as handle:
        fieldnames = list(rows[0].keys()) + ["is_v1_1_baseline"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "is_v1_1_baseline": row["positive_bias_time_limit_s"] == BASELINE_WINDOW_S})


def save_plot(rows: list[dict[str, object]], y_values, ylabel: str, title: str, filename: str) -> None:
    figure, axis = plt.subplots(figsize=(8, 6))
    x_values = [row["positive_bias_time_limit_s"] for row in rows]
    axis.plot(x_values, y_values, "o-", color="tab:green")
    axis.axvline(BASELINE_WINDOW_S, color="tab:orange", linestyle="--", label="v1.1 baseline")
    axis.set_xlabel("Positive-bias time limit (s)")
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.grid(True)
    axis.legend()
    figure.tight_layout()
    figure.savefig(RESULTS_DIR / filename, dpi=160)
    plt.close(figure)


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    rows = [run_case(value) for value in WINDOW_VALUES_S]
    save_csv(rows)
    save_plot(
        rows,
        [1 if row["set_reached"] else 0 for row in rows],
        "SET reached (1 = yes, 0 = no)",
        "SET Reached vs Positive-Bias Window",
        "set_reached_vs_positive_bias_window.png",
    )
    save_plot(
        rows,
        [float(row["set_voltage_V"]) if row["set_voltage_V"] else np.nan for row in rows],
        "SET voltage (V)",
        "SET Voltage vs Positive-Bias Window",
        "set_voltage_vs_positive_bias_window.png",
    )
    save_plot(
        rows,
        [row["max_filament_length_nm"] for row in rows],
        "Maximum filament length (nm)",
        "Maximum Filament Length vs Positive-Bias Window",
        "max_filament_vs_positive_bias_window.png",
    )

    baseline = next(row for row in rows if row["positive_bias_time_limit_s"] == BASELINE_WINDOW_S)
    assert baseline["set_reached"]
    assert abs(float(baseline["set_voltage_V"]) - 0.282) < 0.002
    assert abs(float(baseline["positive_bias_time_s"]) - 0.141) < 0.002
    assert abs(float(baseline["reset_voltage_V"]) + 0.229) < 0.002
    assert abs(float(baseline["lrs_resistance_ohm"]) - 2037.18) < 1
    assert abs(float(baseline["hrs_resistance_ohm"]) - 100000) < 2
    print("Saved positive-bias-window sensitivity CSV and plots")
    for row in rows:
        print(row)
    print("v1.1 positive-bias-window baseline reproduced")


if __name__ == "__main__":
    main()