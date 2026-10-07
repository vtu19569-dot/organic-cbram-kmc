"""Run the Ag/PVA/Pt CBRAM filament-growth simulation."""

from pathlib import Path
from typing import Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from simulation.filament import FilamentState, update_state
from simulation.iv_curve import simulate
from simulation.parameters import (
    DEVICE_THICKNESS,
    LITERATURE_SET_VOLTAGE,
    LITERATURE_RESET_VOLTAGE,
    MAX_SWEEP_VOLTAGE,
    MIN_SWEEP_VOLTAGE,
)


ROOT = Path(__file__).parent
RESULTS_DIR = ROOT / "results"


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    forward_sweep = np.linspace(MIN_SWEEP_VOLTAGE, MAX_SWEEP_VOLTAGE, 500)
    reverse_sweep = np.linspace(MAX_SWEEP_VOLTAGE, MIN_SWEEP_VOLTAGE, 500)
    voltage = np.concatenate((forward_sweep, reverse_sweep[1:]))
    current, resistance, filament_length_nm, ion_fraction = simulate(voltage)
    set_threshold_nm = 0.99 * DEVICE_THICKNESS * 1e9
    set_indices = np.flatnonzero(filament_length_nm >= set_threshold_nm)
    set_voltage = voltage[set_indices[0]] if set_indices.size else None
    reset_threshold_nm = 0.01 * DEVICE_THICKNESS * 1e9
    reset_indices = np.flatnonzero(
        (np.arange(voltage.size) > set_indices[0] if set_indices.size else False)
        & (filament_length_nm <= reset_threshold_nm)
    )
    reset_voltage = voltage[reset_indices[0]] if reset_indices.size else None

    output = np.column_stack(
        (voltage, current, resistance, filament_length_nm, ion_fraction)
    )
    np.savetxt(
        RESULTS_DIR / "iv_curve.csv",
        output,
        delimiter=",",
        header="voltage_V,current_A,resistance_ohm,filament_length_nm,ag_ion_fraction",
        comments="",
    )

    figure, axes = plt.subplots(2, 2, figsize=(12, 9))
    axes[0, 0].plot(voltage, current)
    axes[0, 0].set_xlabel("Voltage (V)")
    axes[0, 0].set_ylabel("Current (A)")
    axes[0, 0].set_title("Hysteresis I-V")
    axes[0, 0].axvline(
        LITERATURE_SET_VOLTAGE,
        color="tab:orange",
        linestyle="--",
        label="Literature SET reference",
    )
    if set_voltage is not None:
        axes[0, 0].axvline(
            set_voltage,
            color="tab:green",
            linestyle=":",
            label=f"Simulated SET ({set_voltage:.3f} V)",
        )
    axes[0, 0].legend()
    axes[0, 0].axvline(
        LITERATURE_RESET_VOLTAGE,
        color="tab:red",
        linestyle="--",
        label="Literature RESET reference",
    )
    if reset_voltage is not None:
        axes[0, 0].axvline(
            reset_voltage,
            color="tab:purple",
            linestyle=":",
            label=f"Simulated RESET ({reset_voltage:.3f} V)",
        )
    axes[0, 0].legend()

    axes[0, 1].plot(voltage, filament_length_nm)
    axes[0, 1].set_xlabel("Voltage (V)")
    axes[0, 1].set_ylabel("Filament length (nm)")
    axes[0, 1].set_title("Ag filament growth and rupture")

    axes[1, 0].semilogy(voltage, resistance)
    axes[1, 0].set_xlabel("Voltage (V)")
    axes[1, 0].set_ylabel("Resistance (Ohm)")
    axes[1, 0].set_title("HRS to LRS transition")

    axes[1, 1].plot(voltage, ion_fraction)
    axes[1, 1].set_xlabel("Voltage (V)")
    axes[1, 1].set_ylabel("Ag+ migration fraction")
    axes[1, 1].set_title("Ag+ migration")

    for axis in axes.flat:
        axis.grid(True)

    figure.suptitle("Ag / PVA / Pt CBRAM Filament Simulation")
    figure.tight_layout()
    plt.savefig(RESULTS_DIR / "iv_curve.png", dpi=150)
    plt.close()

    print(f"Saved {len(voltage)} samples to {RESULTS_DIR / 'iv_curve.csv'}")
    print(f"Saved plot to {RESULTS_DIR / 'iv_curve.png'}")
    print(
        "Simulated SET voltage: "
        + (f"{set_voltage:.3f} V" if set_voltage is not None else "not reached")
    )
    print(
        "Simulated RESET voltage: "
        + (f"{reset_voltage:.3f} V" if reset_voltage is not None else "not reached")
    )
    print(f"Filament length range: {filament_length_nm.min():.1f}-{filament_length_nm.max():.1f} nm")
    print(f"Resistance range: {resistance.min():.0f}-{resistance.max():.0f} Ohm")

    save_research_style_temperature_figure()
    save_iv_graph_reference()


def save_iv_graph_reference() -> None:
    """Generate a dedicated IV graph matching the paper's current-voltage plot style."""
    forward = np.linspace(MIN_SWEEP_VOLTAGE, MAX_SWEEP_VOLTAGE, 500)
    reverse = np.linspace(MAX_SWEEP_VOLTAGE, MIN_SWEEP_VOLTAGE, 500)
    voltage = np.concatenate((forward, reverse[1:]))
    current, _, _, _ = simulate(voltage)

    figure, axis = plt.subplots(figsize=(7.5, 5.8), facecolor="white")
    axis.plot(
        voltage,
        np.abs(current) * 1e3,
        color="black",
        linewidth=1.8,
    )
    axis.set_xmargin(0.02)
    axis.set_yscale("log")
    axis.set_xlim(-0.6, 0.6)
    axis.set_ylim(1e-9, 1e1)
    axis.set_xlabel("Bias Voltage (V)")
    axis.set_ylabel("Current (mA)")
    axis.grid(True, which="both", linestyle="-", alpha=0.15)
    axis.tick_params(direction="in", top=True, right=True, which="both")
    axis.set_title("Resistive switching I-V curve", pad=10)
    figure.tight_layout()

    output_path = RESULTS_DIR / "paper_iv_graph.png"
    figure.savefig(output_path, dpi=220, facecolor="white")
    plt.close(figure)
    print(f"Saved IV graph to {output_path}")


def save_research_style_temperature_figure(output_path: Optional[Path] = None) -> None:
    """Generate a two-panel figure closely matching the paper's switching-cycle plot."""
    plt.rcParams.update(
        {
            "font.family": "serif",
            "axes.titlesize": 18,
            "axes.labelsize": 18,
            "xtick.labelsize": 14,
            "ytick.labelsize": 14,
            "legend.fontsize": 14,
            "axes.linewidth": 1.5,
        }
    )

    cycle_count = 100
    sweep_points = 500
    voltage = np.concatenate(
        (
            np.linspace(MIN_SWEEP_VOLTAGE, MAX_SWEEP_VOLTAGE, sweep_points),
            np.linspace(MAX_SWEEP_VOLTAGE, MIN_SWEEP_VOLTAGE, sweep_points - 1),
        )
    )

    figure, axes = plt.subplots(2, 1, figsize=(8.5, 9.2), facecolor="0.92")
    for axis in axes:
        axis.set_facecolor("0.94")
        axis.tick_params(direction="in", top=True, right=True, which="both")
        axis.spines["top"].set_linewidth(1.5)
        axis.spines["right"].set_linewidth(1.5)
        axis.spines["left"].set_linewidth(1.5)
        axis.spines["bottom"].set_linewidth(1.5)

    figure.subplots_adjust(left=0.14, right=0.94, bottom=0.11, top=0.9, hspace=0.35)

    for axis, (temperature_c, panel_label) in zip(
        axes,
        [(25.0, "(a)"), (70.0, "(b)")],
    ):
        state = FilamentState(temperature_k=temperature_c + 273.15)
        cycle_currents: list[np.ndarray] = []
        for _ in range(cycle_count):
            current_cycle = np.zeros_like(voltage)
            for index, bias_voltage in enumerate(voltage):
                update_state(float(bias_voltage), state)
                resistance = state.resistance_ohm
                current_cycle[index] = bias_voltage / resistance if resistance > 0 else 0.0
            cycle_currents.append(np.abs(current_cycle) * 1e3)

        for cycle_index in range(1, cycle_count):
            axis.plot(
                voltage,
                cycle_currents[cycle_index],
                color="0.6",
                linewidth=0.8,
                alpha=0.9,
            )

        axis.plot(
            voltage,
            cycle_currents[0],
            color="black",
            linewidth=1.4,
            label="1st sweep",
        )

        if temperature_c == 25.0:
            axis.plot(
                voltage,
                cycle_currents[-1],
                color="#ef3b2c",
                linewidth=1.8,
                label="100th sweep",
            )
            axis.set_xlim(-0.6, 0.6)
            axis.set_ylim(1e-9, 1e1)
            axis.set_yticks([1e-9, 1e-7, 1e-5, 1e-3, 1e-1, 1e1])
        else:
            axis.plot(
                voltage,
                cycle_currents[52],
                color="#1f77b4",
                linewidth=1.5,
                label="53rd sweep",
            )
            axis.plot(
                voltage,
                cycle_currents[53],
                color="#2ca02c",
                linewidth=1.5,
                label="54th sweep",
            )
            axis.plot(
                voltage,
                cycle_currents[-1],
                color="#ef3b2c",
                linewidth=1.8,
                label="100th sweep",
            )
            axis.set_xlim(-0.5, 1.0)
            axis.set_ylim(1e-12, 1e1)
            axis.set_yticks([1e-12, 1e-9, 1e-6, 1e-3, 1e0])

        axis.set_yscale("log")
        axis.set_ylabel("Current (mA)")
        axis.set_xlabel("Bias Voltage (V)")
        axis.set_title(f"{panel_label} {temperature_c} °C", pad=8)
        axis.grid(True, which="both", linestyle="-", linewidth=0.6, alpha=0.2)
        axis.axvline(0.0, color="black", linewidth=1.0)

        legend = axis.legend(
            loc="center left",
            bbox_to_anchor=(0.55, 0.22),
            frameon=True,
            facecolor="white",
            edgecolor="black",
            framealpha=1.0,
            fancybox=False,
            borderpad=0.6,
            handlelength=2.0,
            handletextpad=0.5,
        )
        legend.get_frame().set_linewidth(1.2)

    axes[0].set_xticks([-0.6, -0.3, 0.0, 0.3, 0.6])
    axes[1].set_xticks([-0.5, 0.0, 0.5, 1.0])

    figure.text(
        0.06,
        0.02,
        "Fig. 2  Resistive switching characteristics of a Ag/Ag-PVA/Pt device, measured\nat 25 (a) and 70 °C (b) with a constant sweep rate of 7.2 mV s$^{-1}$ and Icc of\n100 \u00b5A for 10$^2$ continuous sweep cycles.",
        fontsize=18,
        ha="left",
        va="bottom",
    )

    output_path = output_path or RESULTS_DIR / "research_style_temperature_sweeps.png"
    figure.savefig(output_path, dpi=220, facecolor="0.92")
    plt.close(figure)
    print(f"Saved publication-style plot to {output_path}")


if __name__ == "__main__":
    main()