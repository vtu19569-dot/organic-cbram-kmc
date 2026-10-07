"""Study activation energy and temperature together without changing the model."""

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
ACTIVATION_ENERGIES = (0.10, 0.20, 0.30)
TEMPERATURES_K = (250.0, 300.0, 350.0, 400.0)
BASELINE_ACTIVATION_ENERGY = 0.20


def run_case(activation_energy: float, temperature: float) -> dict[str, object]:
    original_energy = filament.ACTIVATION_ENERGY_EV
    filament.ACTIVATION_ENERGY_EV = activation_energy
    try:
        forward = np.linspace(MIN_SWEEP_VOLTAGE, MAX_SWEEP_VOLTAGE, 500)
        reverse = np.linspace(MAX_SWEEP_VOLTAGE, MIN_SWEEP_VOLTAGE, 500)
        voltage = np.concatenate((forward, reverse[1:]))
        state = FilamentState(temperature_k=temperature)
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
            "activation_energy_eV": activation_energy,
            "temperature_K": temperature,
            "mobility_m2_V_s": state.mobility_m2_v_s,
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
        filament.ACTIVATION_ENERGY_EV = original_energy


def save_csv(rows: list[dict[str, object]]) -> None:
    output = RESULTS_DIR / "activation_energy_temperature_study.csv"
    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def save_temperature_plot(rows, value_key: str, ylabel: str, title: str, filename: str) -> None:
    figure, axis = plt.subplots(figsize=(8, 6))
    for energy in ACTIVATION_ENERGIES:
        selected = [row for row in rows if row["activation_energy_eV"] == energy]
        reached = [row for row in selected if row["set_reached"] and row[value_key] != ""]
        axis.plot(
            [row["temperature_K"] for row in reached],
            [row[value_key] for row in reached],
            "o-",
            label=f"Ea = {energy:.2f} eV",
            linewidth=2 if energy == BASELINE_ACTIVATION_ENERGY else 1.5,
        )
    axis.set_xlabel("Temperature (K)")
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.grid(True)
    axis.legend()
    figure.tight_layout()
    figure.savefig(RESULTS_DIR / filename, dpi=160)
    plt.close(figure)


def save_mobility_plot(rows) -> None:
    figure, axis = plt.subplots(figsize=(8, 6))
    for energy in ACTIVATION_ENERGIES:
        selected = [row for row in rows if row["activation_energy_eV"] == energy]
        axis.plot(
            [row["temperature_K"] for row in selected],
            [row["mobility_m2_V_s"] for row in selected],
            "o-",
            label=f"Ea = {energy:.2f} eV",
            linewidth=2 if energy == BASELINE_ACTIVATION_ENERGY else 1.5,
        )
    axis.set_xlabel("Temperature (K)")
    axis.set_ylabel("Ag+ mobility (m2/(V s))")
    axis.set_title("Ag+ Mobility vs Temperature by Activation Energy")
    axis.grid(True)
    axis.legend()
    figure.tight_layout()
    figure.savefig(RESULTS_DIR / "mobility_vs_temperature_by_activation_energy.png", dpi=160)
    plt.close(figure)


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    rows = [run_case(energy, temperature) for energy in ACTIVATION_ENERGIES for temperature in TEMPERATURES_K]
    save_csv(rows)
    save_temperature_plot(rows, "set_voltage_V", "SET voltage (V)", "SET Voltage vs Temperature by Activation Energy", "set_voltage_vs_temperature_by_activation_energy.png")
    save_temperature_plot(rows, "positive_bias_time_s", "Positive-bias time to SET (s)", "SET Time vs Temperature by Activation Energy", "set_time_vs_temperature_by_activation_energy.png")
    save_mobility_plot(rows)

    baseline = next(row for row in rows if row["activation_energy_eV"] == 0.20 and row["temperature_K"] == 300.0)
    assert baseline["set_reached"]
    assert abs(float(baseline["set_voltage_V"]) - 0.282) < 0.002
    assert abs(float(baseline["positive_bias_time_s"]) - 0.141) < 0.002
    assert abs(float(baseline["reset_voltage_V"]) + 0.229) < 0.002
    print("Saved activation-energy x temperature study and plots")
    for row in rows:
        print(row)
    print("v1.1 activation-energy/temperature baseline reproduced")


if __name__ == "__main__":
    main()