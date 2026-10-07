"""Run activation-energy sensitivity at the frozen 300 K baseline."""

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
ACTIVATION_ENERGIES = (0.10, 0.15, 0.20, 0.25, 0.30)
BASELINE_ACTIVATION_ENERGY = 0.20


def run_case(activation_energy: float) -> dict[str, object]:
    original_value = filament.ACTIVATION_ENERGY_EV
    filament.ACTIVATION_ENERGY_EV = activation_energy
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
        lrs = float(resistances.min())
        hrs = float(resistances.max())
        return {
            "activation_energy_eV": activation_energy,
            "max_filament_length_nm": float(lengths.max()),
            "set_reached": set_reached,
            "set_voltage_V": voltage[set_index] if set_reached else "",
            "positive_bias_time_s": set_positive_bias_time if set_reached else "",
            "reset_voltage_V": voltage[reset_index] if reset_index is not None else "",
            "min_resistance_ohm": lrs,
            "hrs_resistance_ohm": hrs,
            "on_off_ratio": hrs / lrs,
        }
    finally:
        filament.ACTIVATION_ENERGY_EV = original_value


def save_csv(rows: list[dict[str, object]]) -> None:
    output = RESULTS_DIR / "activation_energy_sensitivity.csv"
    with output.open("w", newline="") as handle:
        fieldnames = list(rows[0].keys()) + ["is_v1_1_baseline"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "is_v1_1_baseline": row["activation_energy_eV"] == BASELINE_ACTIVATION_ENERGY})


def save_plot(rows: list[dict[str, object]], value_key: str, ylabel: str, title: str, filename: str) -> None:
    figure, axis = plt.subplots(figsize=(8, 6))
    reached = [row for row in rows if row["set_reached"]]
    x_values = [row["activation_energy_eV"] for row in reached]
    y_values = [row[value_key] for row in reached]
    axis.plot(x_values, y_values, "o-", color="tab:blue")
    axis.axvline(BASELINE_ACTIVATION_ENERGY, color="tab:orange", linestyle="--", label="v1.1 baseline")
    axis.set_xlabel("Activation energy (eV)")
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.grid(True)
    axis.legend()
    figure.tight_layout()
    figure.savefig(RESULTS_DIR / filename, dpi=160)
    plt.close(figure)


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    rows = [run_case(value) for value in ACTIVATION_ENERGIES]
    save_csv(rows)
    save_plot(rows, "set_voltage_V", "SET voltage (V)", "SET Voltage vs Activation Energy", "set_voltage_vs_activation_energy.png")
    save_plot(rows, "positive_bias_time_s", "Positive-bias time to SET (s)", "SET Time vs Activation Energy", "set_time_vs_activation_energy.png")

    baseline = next(row for row in rows if row["activation_energy_eV"] == BASELINE_ACTIVATION_ENERGY)
    assert baseline["set_reached"]
    assert abs(float(baseline["set_voltage_V"]) - 0.282) < 0.002
    assert abs(float(baseline["positive_bias_time_s"]) - 0.141) < 0.002
    assert abs(float(baseline["reset_voltage_V"]) + 0.229) < 0.002
    print("Saved activation-energy sensitivity CSV and plots")
    for row in rows:
        print(row)
    print("v1.1 activation-energy baseline reproduced")


if __name__ == "__main__":
    main()