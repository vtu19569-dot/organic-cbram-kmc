"""Generate v1.1 analysis figures without changing the simulation baseline."""

import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from simulation.iv_curve import simulate
from simulation.parameters import (
    DEVICE_THICKNESS,
    LITERATURE_RESET_VOLTAGE,
    LITERATURE_SET_VOLTAGE,
    MAX_SWEEP_VOLTAGE,
    MIN_SWEEP_VOLTAGE,
    TIME_STEP_S,
)

RESULTS_DIR = ROOT / "results"


def read_rows(filename: str) -> list[dict[str, str]]:
    with (RESULTS_DIR / filename).open(newline="") as handle:
        return list(csv.DictReader(handle))


def save_figure(figure: plt.Figure, filename: str) -> None:
    figure.tight_layout()
    figure.savefig(RESULTS_DIR / filename, dpi=160)
    plt.close(figure)


def plot_iv() -> None:
    forward = np.linspace(MIN_SWEEP_VOLTAGE, MAX_SWEEP_VOLTAGE, 500)
    reverse = np.linspace(MAX_SWEEP_VOLTAGE, MIN_SWEEP_VOLTAGE, 500)
    voltage = np.concatenate((forward, reverse[1:]))
    current, resistance, length_nm, _ = simulate(voltage)
    set_indices = np.flatnonzero(length_nm >= 0.99 * DEVICE_THICKNESS * 1e9)
    set_voltage = voltage[set_indices[0]] if set_indices.size else None
    reset_indices = np.flatnonzero(
        (np.arange(voltage.size) > set_indices[0] if set_indices.size else False)
        & (length_nm <= 0.01 * DEVICE_THICKNESS * 1e9)
    )
    reset_voltage = voltage[reset_indices[0]] if reset_indices.size else None

    figure, axis = plt.subplots(figsize=(8, 6))
    axis.plot(voltage, current * 1e6, color="tab:blue", label="I-V sweep")
    axis.axvline(LITERATURE_SET_VOLTAGE, color="tab:orange", linestyle="--")
    axis.axvline(LITERATURE_RESET_VOLTAGE, color="tab:red", linestyle="--")
    if set_voltage is not None:
        axis.axvline(set_voltage, color="tab:green", linestyle=":")
        axis.annotate("SET", (set_voltage, 0), xytext=(8, 24), textcoords="offset points")
    if reset_voltage is not None:
        axis.axvline(reset_voltage, color="tab:purple", linestyle=":")
        axis.annotate("RESET", (reset_voltage, 0), xytext=(8, -32), textcoords="offset points")
    axis.text(0.03, 0.94, f"LRS: {resistance.min() / 1e3:.2f} kOhm", transform=axis.transAxes)
    axis.text(0.03, 0.88, f"HRS: {resistance.max() / 1e3:.0f} kOhm", transform=axis.transAxes)
    axis.set_xlabel("Voltage (V)")
    axis.set_ylabel("Current (uA)")
    axis.set_title("Ag / PVA / Pt CBRAM Hysteresis")
    axis.grid(True)
    save_figure(figure, "iv_hysteresis_v1_1.png")


def plot_set_voltage_vs_thickness(rows: list[dict[str, str]]) -> None:
    selected = [row for row in rows if row["study"] == "thickness"]
    thickness = np.array([float(row["parameter"]) for row in selected])
    set_voltage = np.array(
        [float(row["result"]) if row["result"] else np.nan for row in selected]
    )
    figure, axis = plt.subplots(figsize=(8, 6))
    axis.plot(thickness, set_voltage, "o-", color="tab:blue")
    axis.scatter([200], [0], marker="x", s=90, color="tab:red", label="No SET")
    axis.annotate("No SET", (200, 0), xytext=(-45, 18), textcoords="offset points")
    axis.set_xlabel("PVA thickness (nm)")
    axis.set_ylabel("SET voltage (V)")
    axis.set_title("Simulated SET Voltage vs PVA Thickness")
    axis.grid(True)
    axis.legend()
    save_figure(figure, "set_voltage_vs_thickness.png")


def plot_set_voltage_vs_temperature(rows: list[dict[str, str]]) -> None:
    selected = [row for row in rows if row["study"] == "temperature"]
    reached = [row for row in selected if row["result"]]
    temperature = np.array([float(row["parameter"]) for row in reached])
    set_voltage = np.array([float(row["result"]) for row in reached])
    figure, axis = plt.subplots(figsize=(8, 6))
    axis.plot(temperature, set_voltage, "o-", color="tab:orange")
    axis.annotate("250 K: no SET", (250, 0), xytext=(8, 8), textcoords="offset points")
    axis.set_xlabel("Temperature (K)")
    axis.set_ylabel("SET voltage (V)")
    axis.set_title("Simulated SET Voltage vs Temperature")
    axis.grid(True)
    save_figure(figure, "set_voltage_vs_temperature.png")


def plot_set_time_vs_voltage(rows: list[dict[str, str]]) -> None:
    reached = [row for row in rows if row["set_reached"] == "True"]
    maximum_voltage = np.array([float(row["maximum_voltage_V"]) for row in reached])
    set_time = np.array([float(row["positive_bias_time_s"]) for row in reached])
    figure, axis = plt.subplots(figsize=(8, 6))
    axis.plot(maximum_voltage, set_time, "o-", color="tab:green")
    axis.annotate("No SET at 0.20 V and below", (0.205, set_time[-1]), xytext=(10, -25), textcoords="offset points")
    axis.set_xlabel("Maximum applied voltage (V)")
    axis.set_ylabel("Positive-bias time to SET (s)")
    axis.set_title("Positive-Bias Time to SET vs Maximum Applied Voltage")
    axis.grid(True)
    save_figure(figure, "set_time_vs_voltage.png")


def plot_filament_length_vs_voltage(rows: list[dict[str, str]]) -> None:
    maximum_voltage = np.array([float(row["maximum_voltage_V"]) for row in rows])
    length_nm = np.array([float(row["max_filament_length_nm"]) for row in rows])
    figure, axis = plt.subplots(figsize=(8, 6))
    axis.plot(maximum_voltage, length_nm, "o-", color="tab:purple")
    axis.axhline(DEVICE_THICKNESS * 1e9, color="black", linestyle="--", label="PVA thickness")
    axis.set_xlabel("Maximum applied voltage (V)")
    axis.set_ylabel("Maximum filament length (nm)")
    axis.set_title("Filament Length vs Applied Voltage")
    axis.grid(True)
    axis.legend()
    save_figure(figure, "filament_length_vs_voltage.png")


def main() -> None:
    parameter_rows = read_rows("parameter_study.csv")
    voltage_rows = read_rows("voltage_study.csv")
    plot_iv()
    plot_set_voltage_vs_thickness(parameter_rows)
    plot_set_voltage_vs_temperature(parameter_rows)
    plot_set_time_vs_voltage(voltage_rows)
    plot_filament_length_vs_voltage(voltage_rows)
    print("Saved five v1.1 analysis figures")


if __name__ == "__main__":
    main()