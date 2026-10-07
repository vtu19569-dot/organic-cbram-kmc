"""Stage 7 spatial and field-direction diagnostic for the baseline KMC case."""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from kmc_model.kmc_engine import KMCEngine
from kmc_model.lattice import LatticeState
from kmc_model.parameters import KMCConfig


OUTPUT_DIR = PROJECT_ROOT / "results" / "kmc"
CSV_PATH = OUTPUT_DIR / "kmc_spatial_growth_diagnostic.csv"
SUMMARY_PATH = OUTPUT_DIR / "kmc_spatial_growth_diagnostic_summary.md"
FIGURE_PATH = OUTPUT_DIR / "kmc_spatial_growth_diagnostic.png"


def distance_distribution(engine: KMCEngine) -> dict:
    filament_sites = {
        (row, col)
        for row in range(engine.config.lattice_rows)
        for col in range(engine.config.lattice_columns)
        if engine.lattice.get_state(row, col) == LatticeState.AG_FILAMENT
    }
    if not filament_sites:
        raise AssertionError("Baseline diagnostic requires filament sites.")

    deepest_filament_row = max(row for row, _ in filament_sites)
    pva_sites = [
        (row, col)
        for row in range(1, engine.config.lattice_rows - 1)
        for col in range(engine.config.lattice_columns)
    ]

    def nearest_distance(site: tuple[int, int]) -> int:
        return min(abs(site[0] - filament[0]) + abs(site[1] - filament[1]) for filament in filament_sites)

    distributions: dict[str, dict[int, int]] = {}
    for population, predicate in {
        "ag_ions_all": lambda state: state == LatticeState.AG_ION,
        "ag_ions_below_deepest_filament": lambda state: state == LatticeState.AG_ION,
        "empty_sites_all": lambda state: state == LatticeState.EMPTY,
        "empty_sites_below_deepest_filament": lambda state: state == LatticeState.EMPTY,
    }.items():
        counts = Counter()
        for site in pva_sites:
            row, col = site
            state = engine.lattice.get_state(row, col)
            if not predicate(state):
                continue
            if "below_deepest" in population and row <= deepest_filament_row:
                continue
            distance = nearest_distance(site)
            if distance in (1, 2, 3, 4):
                counts[distance] += 1
        distributions[population] = {distance: counts[distance] for distance in (1, 2, 3, 4)}

    return {
        "deepest_filament_row": deepest_filament_row,
        "filament_site_count": len(filament_sites),
        "distributions": distributions,
    }


def run_baseline() -> tuple[KMCEngine, dict]:
    config = KMCConfig()
    engine = KMCEngine(config)
    result = engine.run()
    distances = distance_distribution(engine)
    growth = engine.growth_diagnostics()
    field_energy_ev = engine.electric_field_v_m * config.cell_size_nm * 1e-9
    audit = {
        "voltage_v": config.applied_voltage_v,
        "temperature_k": config.temperature_k,
        "random_seed": config.random_seed,
        "total_events": result.total_events,
        "set_reached": result.set_reached,
        "growth_events": growth["growth_successes"],
        "filament_sites": result.filament_site_count,
        "filament_depth_row": engine.diagnostic_counters["final_filament_depth_row"],
        "max_ag_ion_depth_row": engine.diagnostic_counters["max_ag_ion_depth_row"],
        "growth_candidates": growth["growth_candidates"],
        "hopping_candidates": growth["hopping_candidates"],
        "growth_successes": growth["growth_successes"],
        "hopping_successes": growth["hopping_successes"],
        "growth_rate_fraction_of_active_rate": growth["growth_rate_fraction_of_active_rate"],
        "growth_to_hopping_rate_ratio": growth["growth_to_hopping_rate_ratio"],
        "final_ag_plus_adjacent_to_filament": growth["number_of_Ag_plus_adjacent_to_filament"],
        "final_empty_growth_sites": growth["number_of_empty_growth_sites"],
        "field_magnitude_v_m": engine.electric_field_v_m,
        "field_energy_per_cell_ev": field_energy_ev,
        "downward_barrier_ev": engine._effective_barrier_ev(config.activation_energy_ev, 1, 2),
        "upward_barrier_ev": engine._effective_barrier_ev(config.activation_energy_ev, 2, 1),
        "downward_growth_barrier_ev": engine._effective_barrier_ev(config.growth_activation_energy_ev, 1, 2),
        "upward_growth_barrier_ev": engine._effective_barrier_ev(config.growth_activation_energy_ev, 2, 1),
        "lattice_rows": config.lattice_rows,
        "lattice_columns": config.lattice_columns,
        "cell_size_nm": config.cell_size_nm,
        "pva_rows": config.lattice_rows - 2,
        "pva_physical_span_nm": (config.lattice_rows - 2) * config.cell_size_nm,
        "computational_span_nm": config.lattice_rows * config.cell_size_nm,
        "lateral_span_nm": config.lattice_columns * config.cell_size_nm,
        "connectivity_rule": config.connectivity_rule,
        "diagonal_movement_allowed": False,
        "diagonal_growth_allowed": False,
        "exact_adjacent_growth": True,
        "first_nucleation_row": engine.nucleation_sites[0][0],
        "first_nucleation_col": engine.nucleation_sites[0][1],
        "distance_data": distances,
    }
    return engine, audit


def assert_reproducible(first: dict) -> None:
    _, repeat = run_baseline()
    keys = [
        "total_events",
        "set_reached",
        "growth_events",
        "filament_sites",
        "filament_depth_row",
        "growth_candidates",
        "hopping_candidates",
        "first_nucleation_row",
        "first_nucleation_col",
        "distance_data",
    ]
    for key in keys:
        if first[key] != repeat[key]:
            raise AssertionError(f"Baseline spatial diagnostic is not reproducible for {key}")


def write_csv(audit: dict) -> None:
    rows = []

    def add(section: str, metric: str, value, units: str, provenance: str, notes: str = "") -> None:
        rows.append(
            {
                "section": section,
                "metric": metric,
                "value": value,
                "units": units,
                "provenance": provenance,
                "notes": notes,
            }
        )

    for metric in (
        "voltage_v", "temperature_k", "random_seed", "total_events", "set_reached",
        "growth_events", "filament_sites", "filament_depth_row", "max_ag_ion_depth_row",
        "growth_candidates", "hopping_candidates", "growth_successes", "hopping_successes",
        "growth_rate_fraction_of_active_rate", "growth_to_hopping_rate_ratio",
        "final_ag_plus_adjacent_to_filament", "final_empty_growth_sites",
    ):
        add("baseline", metric, audit[metric], "", "Derived", "Baseline 0.30 V / 300 K / seed 42 run")

    for metric in (
        "lattice_rows", "lattice_columns", "cell_size_nm", "pva_rows",
        "pva_physical_span_nm", "computational_span_nm", "lateral_span_nm",
        "connectivity_rule", "diagonal_movement_allowed", "diagonal_growth_allowed",
        "exact_adjacent_growth", "first_nucleation_row", "first_nucleation_col",
    ):
        provenance = "Numerical/KMC" if metric in {"lattice_rows", "lattice_columns", "cell_size_nm"} else "Derived"
        add("lattice", metric, audit[metric], "", provenance, "Current implementation mapping")

    for metric in (
        "field_magnitude_v_m", "field_energy_per_cell_ev", "downward_barrier_ev",
        "upward_barrier_ev", "downward_growth_barrier_ev", "upward_growth_barrier_ev",
    ):
        add("field", metric, audit[metric], "", "Derived", "Computed from existing Stage 5 rate formulation")

    for population, values in audit["distance_data"]["distributions"].items():
        for distance, count in values.items():
            add("distance_distribution", f"{population}_manhattan_{distance}", count, "sites", "Derived", "Exact nearest-filament Manhattan distance")

    with CSV_PATH.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["section", "metric", "value", "units", "provenance", "notes"])
        writer.writeheader()
        writer.writerows(rows)


def write_summary(audit: dict) -> None:
    distance = audit["distance_data"]["distributions"]
    lines = [
        "# Stage 7 local deposition and spatial kinetics validation",
        "",
        "This is a diagnostic-only audit of the unchanged Stage 5 baseline. No growth multiplier, rate, barrier, field factor, lattice spacing, event cap, or ion inventory was changed.",
        "",
        "## 1. Lattice representation",
        "",
        f"- Grid: {audit['lattice_rows']} rows x {audit['lattice_columns']} columns.",
        f"- One coarse-grained cell: {audit['cell_size_nm']} nm in the row and column directions.",
        f"- Computational span: {audit['computational_span_nm']} nm using the configured 25-row mapping.",
        f"- Electrode rows: row 0 is Ag and row 24 is Pt.",
        f"- PVA-state rows: rows 1 through 23, {audit['pva_rows']} rows and {audit['pva_physical_span_nm']} nm if each state row is interpreted as 4 nm.",
        f"- Lateral computational span: {audit['lateral_span_nm']} nm.",
        "- The 100 nm / 25 cells = 4 nm mapping is a numerical/coarse-grained model assumption. Because boundary electrode rows are included in the 25-row grid, the interior PVA-state rows span 92 nm under the literal row-count interpretation.",
        "- The 4-neighbor von-Neumann neighborhood is explicitly implemented in `LatticeGrid.neighbors`; diagonal motion and diagonal growth are prohibited. This is a model assumption, not an atomistic validation.",
        "",
        "## 2. Physical-to-KMC mapping",
        "",
        "| Physical process | Current KMC representation | Parameter | Provenance |",
        "|---|---|---|---|",
        "| Ag electrode | Row 0 cells with AG_ELECTRODE state | electrode_top_index = 0 | Materials Project |",
        "| Ag+ generation | Empty PVA cell directly below an Ag electrode cell becomes AG_ION | electrode injection rule | Model assumption |",
        "| Ag+ hopping | AG_ION moves to an empty 4-neighbor cell | activation_energy_ev = 0.25 eV, cell size = 4 nm | Model assumption / Derived |",
        "| Nucleation | AG_ION on row 1 converts stochastically to AG_FILAMENT | nucleation barrier and attempt frequency | Model assumption / Numerical/KMC |",
        "| Local growth | AG_ION exactly adjacent to AG_FILAMENT converts in place | growth barrier, deposition_bias = 1.5 | Model assumption / Numerical/KMC |",
        "| Pt electrode | Row 24 cells with PT_ELECTRODE state | electrode_bottom_index = 24 | Materials Project |",
        "| SET bridge | 4-neighbor filament reaches final PVA row, row 23 | connectivity_rule = 4-neighbor | Model assumption |",
        "",
        "## 3. Local Ag+ distance distribution",
        "",
        "Distances are nearest-filament Manhattan distances in the final baseline lattice. Distance-2/3/4 ions are diagnostic only and cannot grow the filament under the current event rules.",
        "",
        "| Population | d=1 | d=2 | d=3 | d=4 |",
        "|---|---:|---:|---:|---:|",
        f"| All Ag+ ions | {distance['ag_ions_all'][1]} | {distance['ag_ions_all'][2]} | {distance['ag_ions_all'][3]} | {distance['ag_ions_all'][4]} |",
        f"| Ag+ below deepest filament | {distance['ag_ions_below_deepest_filament'][1]} | {distance['ag_ions_below_deepest_filament'][2]} | {distance['ag_ions_below_deepest_filament'][3]} | {distance['ag_ions_below_deepest_filament'][4]} |",
        f"| Empty PVA sites | {distance['empty_sites_all'][1]} | {distance['empty_sites_all'][2]} | {distance['empty_sites_all'][3]} | {distance['empty_sites_all'][4]} |",
        f"| Empty sites below deepest filament | {distance['empty_sites_below_deepest_filament'][1]} | {distance['empty_sites_below_deepest_filament'][2]} | {distance['empty_sites_below_deepest_filament'][3]} | {distance['empty_sites_below_deepest_filament'][4]} |",
        "",
        f"The final lattice has {audit['final_ag_plus_adjacent_to_filament']} Ag+ ions at distance 1 and {audit['final_empty_growth_sites']} empty sites at distance 1 from a filament site. The final Ag+ count is a snapshot after the event cap; it is not the time-integrated availability during the run.",
        "",
        "## 4. Field-direction verification",
        "",
        f"For V = {audit['voltage_v']} V and d = 100 nm, E = V/d = {audit['field_magnitude_v_m']:.6g} V/m.",
        f"One lattice spacing contributes E*a = {audit['field_energy_per_cell_ev']:.6g} eV for a unit charge.",
        f"With alpha = 0.35 and Ea = 0.25 eV, downward migration/growth uses Ea_eff = {audit['downward_barrier_ev']:.6g} eV.",
        f"Upward migration/growth uses Ea_eff = {audit['upward_barrier_ev']:.6g} eV.",
        "",
        "The code defines increasing row index as downward motion from Ag toward Pt. Therefore downward motion receives barrier lowering and upward motion receives barrier raising. Growth uses the filament row as the source and the lower Ag+ row as the target, so its field sign is aligned with downward growth.",
        "",
        "## 5. Deposition geometry",
        "",
        "- Growth requires an Ag+ ion to occupy an immediately adjacent 4-neighbor site.",
        "- The occupied Ag+ site is converted directly into AG_FILAMENT.",
        "- Growth does not deposit into an empty site.",
        "- Diagonal deposition is prohibited.",
        "- Multiple disconnected filaments are possible because nucleation can occur at multiple row-1 sites.",
        "- There is no nonlocal reconnection event. A gap can only be filled if a neighboring Ag+ site creates a normal adjacent growth candidate.",
        "- Exact nearest-neighbor deposition is therefore an explicit coarse-grained model assumption.",
        "",
        "## 6. Bottleneck classification",
        "",
        "- **A. Spatial-resolution limitation:** selected. The 4 nm cell is a coarse numerical representation, and the literal 25-row mapping includes electrode boundary rows.",
        "- **B. Local-neighbor restriction:** selected. Only exact 4-neighbor Ag+ sites can grow the filament; distance-2/3/4 ions are inactive for growth.",
        "- **C. Event-selection competition:** selected. Baseline hopping candidates = 177879 versus 124 growth candidates, and accumulated growth rate fraction = 0.1288%.",
        "- **D. Kinetic-rate limitation:** partially selected. The growth candidate rate itself is not near zero, but its sparse candidate population limits total growth opportunity.",
        "- **E. Field-direction implementation issue:** not selected. The existing sign convention lowers the barrier for downward motion and raises it for upward motion.",
        "- **F. Insufficient evidence:** not selected for this audit, although local availability is measured only at the terminal lattice state rather than throughout the trajectory.",
        "",
        "## 7. Limitations and recommendation",
        "",
        "- This diagnostic does not validate the physical 4 nm resolution or the 4-neighbor assumption against atomistic or experimental data.",
        "- Final-state distance counts do not replace a time-resolved local-availability history.",
        "- The model permits multiple nuclei and disconnected branches, while the current connectivity check uses one arbitrary filament cluster when testing the final boundary.",
        "- Baseline parameters should remain unchanged.",
        "- The model is not ready for Stage 8 voltage-dependent forming-time analysis until the spatial coarse-graining and local deposition assumptions are explicitly approved or refined.",
    ]
    SUMMARY_PATH.write_text("\n".join(lines) + "\n")


def write_figure(audit: dict) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    distance = audit["distance_data"]["distributions"]
    labels = ["d=1", "d=2", "d=3", "d=4"]
    positions = range(4)
    figure, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].bar([p - 0.2 for p in positions], [distance["ag_ions_all"][d] for d in (1, 2, 3, 4)], width=0.4, label="Ag+ ions")
    axes[0].bar([p + 0.2 for p in positions], [distance["empty_sites_all"][d] for d in (1, 2, 3, 4)], width=0.4, label="empty PVA sites")
    axes[0].set_xticks(list(positions), labels)
    axes[0].set_ylabel("final site count")
    axes[0].set_title("Distance to nearest filament")
    axes[0].legend()
    axes[1].bar(["downward", "upward"], [audit["downward_barrier_ev"], audit["upward_barrier_ev"]], color=["#2f80ed", "#d94841"])
    axes[1].set_ylabel("effective barrier (eV)")
    axes[1].set_title("Field-direction barrier check")
    figure.suptitle("Stage 7 baseline spatial diagnostic: 0.30 V / 300 K / seed 42")
    figure.tight_layout()
    figure.savefig(FIGURE_PATH, dpi=180, facecolor="white")
    plt.close(figure)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _, audit = run_baseline()
    assert_reproducible(audit)
    write_csv(audit)
    write_summary(audit)
    write_figure(audit)
    print("Baseline spatial diagnostic reproducibility passed.")
    print(f"Growth events: {audit['growth_events']}")
    print(f"Filament sites: {audit['filament_sites']}")
    print(f"Filament depth row: {audit['filament_depth_row']}")
    print(f"SET: {audit['set_reached']}")
    print(f"Wrote {CSV_PATH}")
    print(f"Wrote {SUMMARY_PATH}")
    print(f"Wrote {FIGURE_PATH}")


if __name__ == "__main__":
    main()
