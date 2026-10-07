"""Controlled Stage 6 growth-rate diagnostic for the single KMC SET case.

Only the growth-rate multiplier is perturbed. Voltage, temperature, seed,
lattice, inventory, hopping, nucleation, and event cap remain unchanged.
"""

from __future__ import annotations

import csv
import sys
from dataclasses import replace
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from kmc_model.kmc_engine import KMCEngine
from kmc_model.parameters import KMCConfig


OUTPUT_DIR = PROJECT_ROOT / "results" / "kmc"
CSV_PATH = OUTPUT_DIR / "kmc_growth_diagnostic.csv"
SUMMARY_PATH = OUTPUT_DIR / "kmc_growth_diagnostic_summary.md"
FIGURE_PATH = OUTPUT_DIR / "kmc_growth_diagnostic.png"


def run_case(base_config: KMCConfig, factor: float) -> tuple[dict, dict]:
    config = replace(base_config, growth_rate_multiplier=factor)
    engine = KMCEngine(config)
    result = engine.run()
    diagnostics = engine.growth_diagnostics()
    row = {
        "case": "baseline" if factor == 1.0 else f"{int(factor)}x growth rate",
        "growth_factor": factor,
        "growth_events": diagnostics["growth_successes"],
        "filament_sites": result.filament_site_count,
        "filament_depth_row": engine.diagnostic_counters["final_filament_depth_row"],
        "set_reached": result.set_reached,
        "simulation_time_s": result.set_time_s,
        "growth_candidates": diagnostics["growth_candidates"],
        "growth_candidate_rate_sum_hz": diagnostics["growth_candidate_rate_sum"],
        "growth_success_rate_sum_hz": diagnostics["growth_success_rate_sum"],
        "hopping_candidates": diagnostics["hopping_candidates"],
        "hopping_successes": diagnostics["hopping_successes"],
        "hopping_candidate_rate_sum_hz": diagnostics["hopping_candidate_rate_sum"],
        "mean_growth_rate_hz": diagnostics["mean_growth_rate"],
        "mean_hopping_rate_hz": diagnostics["mean_hopping_rate"],
        "growth_to_hopping_rate_ratio": diagnostics["growth_to_hopping_rate_ratio"],
        "growth_rate_fraction_of_active_rate": diagnostics["growth_rate_fraction_of_active_rate"],
        "mean_growth_effective_barrier_ev": diagnostics["mean_growth_effective_barrier_ev"],
        "mean_hopping_effective_barrier_ev": diagnostics["mean_hopping_effective_barrier_ev"],
        "ag_plus_adjacent_to_filament": diagnostics["number_of_Ag_plus_adjacent_to_filament"],
        "empty_growth_sites": diagnostics["number_of_empty_growth_sites"],
        "final_ag_ion_sites": result.ag_ion_count,
        "total_events": result.total_events,
        "first_nucleation_row": engine.nucleation_sites[0][0] if engine.nucleation_sites else -1,
        "first_nucleation_col": engine.nucleation_sites[0][1] if engine.nucleation_sites else -1,
    }
    return row, diagnostics


def assert_reproducible(base_config: KMCConfig, factor: float, first_row: dict) -> None:
    repeat_row, _ = run_case(base_config, factor)
    keys = [
        "growth_events",
        "filament_sites",
        "filament_depth_row",
        "set_reached",
        "simulation_time_s",
        "total_events",
        "first_nucleation_row",
        "first_nucleation_col",
    ]
    for key in keys:
        if repeat_row[key] != first_row[key]:
            raise AssertionError(f"Non-deterministic {factor}x diagnostic for {key}")


def write_csv(rows: list[dict]) -> None:
    with CSV_PATH.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_summary(rows: list[dict]) -> None:
    baseline = rows[0]
    lines = [
        "# Stage 6 controlled KMC growth-rate diagnostic",
        "",
        "This is a diagnostic perturbation, not a calibrated model update. Only the growth-rate multiplier was changed. The voltage, temperature, seed, lattice, Ag+ inventory, nucleation mechanism, hopping mechanism, and event cap were held fixed.",
        "",
        "## 1. Baseline Stage 5 result",
        "",
        f"- Conditions: V = 0.30 V, T = 300 K, seed = 42, event cap = {baseline['total_events']}",
        f"- SET reached: {baseline['set_reached']}",
        f"- Growth events: {baseline['growth_events']}",
        f"- Filament sites: {baseline['filament_sites']}",
        f"- Filament depth: row {baseline['filament_depth_row']}",
        "",
        "## 2. Growth-rate audit",
        "",
        "Growth candidates require an Ag+ ion to be exactly 4-neighbor adjacent to an existing AG_FILAMENT site. Growth uses the 0.25 eV growth barrier, the field-assisted barrier term, the existing deposition bias of 1.5, and the diagnostic multiplier. Hopping uses the 0.25 eV transport barrier, the same field coupling, and no deposition bias.",
        "",
        f"- Baseline growth candidates: {baseline['growth_candidates']}",
        f"- Baseline hopping candidates: {baseline['hopping_candidates']}",
        f"- Mean growth candidate rate: {baseline['mean_growth_rate_hz']:.6g} Hz",
        f"- Mean hopping candidate rate: {baseline['mean_hopping_rate_hz']:.6g} Hz",
        f"- Mean growth/hopping rate ratio: {baseline['growth_to_hopping_rate_ratio']:.6g}",
        f"- Growth fraction of accumulated active candidate rate: {baseline['growth_rate_fraction_of_active_rate']:.6g}",
        f"- Mean growth effective barrier: {baseline['mean_growth_effective_barrier_ev']:.6g} eV",
        f"- Mean hopping effective barrier: {baseline['mean_hopping_effective_barrier_ev']:.6g} eV",
        f"- Final Ag+ ions adjacent to filament: {baseline['ag_plus_adjacent_to_filament']}",
        f"- Final empty growth sites: {baseline['empty_growth_sites']}",
        "",
        "The rate ratio is a candidate-rate ratio, not a probability of eventual growth. Event selection is additionally controlled by the number of active hopping candidates and their summed rate.",
        "",
        "## 3. Controlled cases",
        "",
        "| Case | Growth factor | Growth events | Filament sites | Filament depth | SET | Simulation time (s) | Growth/hopping ratio |",
        "|---|---:|---:|---:|---:|---|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['case']} | {row['growth_factor']}x | {row['growth_events']} | {row['filament_sites']} | {row['filament_depth_row']} | {row['set_reached']} | {row['simulation_time_s']:.8g} | {row['growth_to_hopping_rate_ratio']:.8g} |"
        )
    lines.extend(
        [
            "",
            "## 4. Bottleneck interpretation",
            "",
            "The baseline bottleneck is event-selection competition combined with limited local Ag+ adjacency. The mechanism is not blocked by missing logic: nucleation and growth events occur. Growth candidates are rare relative to hopping candidates, and the active hopping population consumes most selected events. The diagnostic multipliers test sensitivity without changing the baseline model.",
            "",
            "## 5. Baseline decision",
            "",
            "The baseline parameter is unchanged. The 10x and 100x cases are diagnostic perturbations only and are not calibrated physical values. A future baseline change would require separate physical justification for the growth attempt frequency, growth barrier, or local deposition formulation.",
            "",
            "## 6. Limitations",
            "",
            "- Candidate-rate sums are accumulated over repeated event-list builds, not instantaneous rates.",
            "- The coarse-grained 4 nm lattice does not resolve microscopic Ag+ chemistry.",
            "- The growth multiplier is numerical and diagnostic, not literature-fitted.",
            "- No voltage, temperature, thickness, RESET, or literature calibration study was performed.",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines) + "\n")


def write_figure(rows: list[dict]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = [row["case"] for row in rows]
    factors = [row["growth_factor"] for row in rows]
    growth_events = [row["growth_events"] for row in rows]
    depths = [row["filament_depth_row"] for row in rows]
    figure, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].bar(labels, growth_events, color=["#4c78a8", "#f58518", "#e45756"])
    axes[0].set_ylabel("successful growth events")
    axes[0].set_title("Controlled growth diagnostic")
    axes[1].plot(factors, depths, marker="o", color="#2f4b7c")
    axes[1].set_xscale("log")
    axes[1].set_xlabel("growth-rate multiplier")
    axes[1].set_ylabel("final filament depth row")
    axes[1].set_xticks(factors, ["1x", "10x", "100x"])
    axes[1].grid(True, alpha=0.3)
    figure.tight_layout()
    figure.savefig(FIGURE_PATH, dpi=180, facecolor="white")
    plt.close(figure)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    base_config = KMCConfig()
    rows = []
    for factor in (1.0, 10.0, 100.0):
        row, _ = run_case(base_config, factor)
        assert_reproducible(base_config, factor, row)
        rows.append(row)
    write_csv(rows)
    write_summary(rows)
    write_figure(rows)
    for row in rows:
        print(
            f"{row['case']}: growth_events={row['growth_events']}, "
            f"filament_sites={row['filament_sites']}, depth_row={row['filament_depth_row']}, "
            f"SET={row['set_reached']}, time_s={row['simulation_time_s']:.8g}, "
            f"growth_hopping_ratio={row['growth_to_hopping_rate_ratio']:.8g}"
        )
    print(f"Wrote {CSV_PATH}")
    print(f"Wrote {SUMMARY_PATH}")
    print(f"Wrote {FIGURE_PATH}")


if __name__ == "__main__":
    main()
