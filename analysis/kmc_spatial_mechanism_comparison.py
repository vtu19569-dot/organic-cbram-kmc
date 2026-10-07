"""Stage 8 comparison of spatial filament-growth rules.

Only growth candidate geometry changes. The default baseline remains 4-neighbor.
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
from kmc_model.lattice import LatticeState
from kmc_model.parameters import KMCConfig

OUTPUT_DIR = PROJECT_ROOT / "results" / "kmc"
CSV_PATH = OUTPUT_DIR / "kmc_spatial_mechanism_comparison.csv"
SUMMARY_PATH = OUTPUT_DIR / "kmc_spatial_mechanism_comparison.md"
FIGURE_PATH = OUTPUT_DIR / "kmc_spatial_mechanism_comparison.png"

CASES = [
    ("4-neighbor baseline", "4-neighbor", 1),
    ("8-neighbor diagnostic", "8-neighbor", 1),
    ("Manhattan-distance-2 diagnostic", "manhattan-2", 2),
]


def run_case(base_config: KMCConfig, label: str, rule: str, reach: int) -> tuple[dict, KMCEngine]:
    config = replace(
        base_config,
        growth_spatial_rule=rule,
        growth_reach_distance=reach,
        growth_rate_multiplier=1.0,
    )
    engine = KMCEngine(config)
    result = engine.run()
    growth = engine.growth_diagnostics()
    row = {
        "case": label,
        "growth_rule": rule,
        "growth_candidates": growth["growth_candidates"],
        "growth_events": growth["growth_successes"],
        "hopping_candidates": growth["hopping_candidates"],
        "hopping_events": growth["hopping_successes"],
        "filament_sites": result.filament_site_count,
        "filament_depth_row": engine.diagnostic_counters["final_filament_depth_row"],
        "max_ag_depth_row": engine.diagnostic_counters["max_ag_ion_depth_row"],
        "simulation_time_s": result.set_time_s,
        "total_events": result.total_events,
        "set_reached": result.set_reached,
        "final_ag_plus_sites": result.ag_ion_count,
        "final_adjacent_ag_plus": growth["number_of_Ag_plus_adjacent_to_filament"],
        "growth_hopping_rate_ratio": growth["growth_to_hopping_rate_ratio"],
    }
    return row, engine


def assert_same_result(first: dict, repeat: dict) -> None:
    for key in first:
        if first[key] != repeat[key]:
            raise AssertionError(f"Non-reproducible spatial comparison for {first['case']}: {key}")


def write_csv(rows: list[dict]) -> None:
    fields = [
        "case", "growth_rule", "growth_candidates", "growth_events",
        "hopping_candidates", "hopping_events", "filament_sites",
        "filament_depth_row", "max_ag_depth_row", "simulation_time_s",
        "total_events", "set_reached", "final_ag_plus_sites",
        "final_adjacent_ag_plus", "growth_hopping_rate_ratio",
    ]
    with CSV_PATH.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_figure(engines: list[KMCEngine]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap

    values = {
        LatticeState.EMPTY: 0,
        LatticeState.AG_ION: 1,
        LatticeState.AG_FILAMENT: 2,
        LatticeState.AG_ELECTRODE: 3,
        LatticeState.PT_ELECTRODE: 4,
    }
    cmap = ListedColormap(["white", "#2f80ed", "#d94841", "#9b59b6", "#303030"])
    figure, axes = plt.subplots(1, 3, figsize=(12, 5), squeeze=False)
    for axis, (label, _, _), engine in zip(axes[0], CASES, engines):
        matrix = engine.lattice.snapshot_matrix()
        image = [[values[cell] for cell in row] for row in matrix]
        axis.imshow(image, cmap=cmap, vmin=0, vmax=4, interpolation="none", aspect="auto")
        axis.set_title(label)
        axis.set_xticks([])
        axis.set_yticks([0, engine.config.lattice_rows - 2, engine.config.lattice_rows - 1])
        axis.set_yticklabels(["Ag", "PVA/Pt", "Pt"])
    figure.suptitle("Stage 8 spatial growth comparison: actual final KMC lattices")
    figure.tight_layout()
    figure.savefig(FIGURE_PATH, dpi=180, facecolor="white")
    plt.close(figure)


def write_summary(rows: list[dict]) -> None:
    baseline, diagonal, reach2 = rows
    lines = [
        "# Stage 8 final KMC mechanism validation",
        "",
        "This comparison changes only the spatial rule used to construct filament-growth candidates. Voltage, temperature, seed, lattice dimensions, cell spacing, event cap, Ag+ inventory, nucleation, hopping, field factor, activation energies, attempt frequencies, and growth multiplier remain unchanged.",
        "",
        "## 1. Baseline mechanism",
        "",
        "The default model uses exact 4-neighbor filament-growth candidates. An Ag+ ion must occupy an immediately adjacent lattice site; it is then converted in place into AG_FILAMENT. Hopping and nucleation remain unchanged. SET remains defined by a 4-neighbor filament cluster reaching the final PVA row.",
        "",
        "## 2. Diagnostic alternatives",
        "",
        "- 8-neighbor diagnostic: diagonal neighbors are allowed only when constructing filament-growth candidates. Hopping remains 4-neighbor.",
        "- Manhattan-distance-2 diagnostic: Ag+ ions within Manhattan distance 2 of an existing filament can become growth candidates. This is a deliberately nonlocal diagnostic rule, not a calibrated mechanism.",
        "",
        "## 3. Conditions",
        "",
        "- Device: Ag / PVA / Pt; PVA thickness 100 nm.",
        "- V = +0.30 V, T = 300 K, random seed = 42.",
        "- Lattice = 25 x 15, cell spacing = 4 nm, event cap = 20,000.",
        "- Baseline growth multiplier = 1.0 for all cases.",
        "",
        "## 4. Results",
        "",
        "| Case | Growth rule | Growth candidates | Growth events | Hopping candidates | Hopping events | Filament sites | Depth | Max Ag+ depth | Time (s) | Events | SET | Final Ag+ | Adjacent Ag+ | Growth/hopping ratio |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['case']} | {row['growth_rule']} | {row['growth_candidates']} | {row['growth_events']} | {row['hopping_candidates']} | {row['hopping_events']} | {row['filament_sites']} | {row['filament_depth_row']} | {row['max_ag_depth_row']} | {row['simulation_time_s']:.8g} | {row['total_events']} | {row['set_reached']} | {row['final_ag_plus_sites']} | {row['final_adjacent_ag_plus']} | {row['growth_hopping_rate_ratio']:.8g} |"
        )
    lines.extend(
        [
            "",
            "## 5. Morphology comparison",
            "",
            "The accompanying PNG uses the actual final lattice states. It does not draw or infer a filament between sites. The 8-neighbor and Manhattan-distance-2 panels are diagnostic morphology outcomes only.",
            "",
            "## 6. Interpretation",
            "",
            f"- 8-neighbor growth changes successful growth from {baseline['growth_events']} to {diagonal['growth_events']} events and filament sites from {baseline['filament_sites']} to {diagonal['filament_sites']}.",
            f"- Manhattan-distance-2 growth changes successful growth from {baseline['growth_events']} to {reach2['growth_events']} events and filament sites from {baseline['filament_sites']} to {reach2['filament_sites']}.",
            f"- SET is reached in none of the three cases: baseline={baseline['set_reached']}, 8-neighbor={diagonal['set_reached']}, distance-2={reach2['set_reached']}.",
            "- The diagnostic alternatives do not create a complete bridge in this single case, but they relax the spatial interpretation. The Manhattan-distance-2 rule can create disconnected or nonlocal filament additions and is therefore less physically conservative.",
            "- No implementation error was found in the original 4-neighbor baseline. Its behavior is consistent with its stated coarse-grained nearest-neighbor assumption.",
            "",
            "## 7. Provenance",
            "",
            "| Quantity | Classification |",
            "|---|---|",
            "| 4 nm lattice spacing | Numerical/KMC; coarse-grained model assumption |",
            "| 4-neighbor connectivity | Model assumption |",
            "| 8-neighbor diagnostic | Numerical/KMC diagnostic; model assumption, not literature-derived |",
            "| Manhattan-distance-2 diagnostic | Numerical/KMC diagnostic; model assumption, not literature-derived |",
            "| Local growth rule | Model assumption |",
            "| Field-assisted barrier | Model assumption |",
            "| Activation energy | Model assumption |",
            "| Attempt frequency | Numerical/KMC |",
            "",
            "## 8. Limitations",
            "",
            "- This is one fixed voltage, temperature, seed, lattice, and event cap.",
            "- The 4 nm resolution is not atomistically validated.",
            "- The comparison changes candidate geometry but retains the original 4-neighbor SET connectivity test.",
            "- The Manhattan-distance-2 diagnostic is intentionally not a physical calibration.",
            "",
            "## 9. Final mechanism decision",
            "",
            "Freeze the original 4-neighbor growth mechanism for the upcoming voltage study. It is the most conservative and internally consistent coarse-grained rule, no coding defect was identified, and the diagnostic alternatives do not provide a scientifically justified replacement. Baseline parameters remain unchanged.",
            "",
            "The model is ready for Stage 9 only as a documented mechanism-validation baseline. The voltage-dependent forming analysis should remain explicitly conditional on the limitations above and must not treat the diagnostic alternatives as validated physics.",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines) + "\n")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    base_config = KMCConfig()
    rows = []
    engines = []
    for label, rule, reach in CASES:
        row, engine = run_case(base_config, label, rule, reach)
        repeat_row, _ = run_case(base_config, label, rule, reach)
        assert_same_result(row, repeat_row)
        rows.append(row)
        engines.append(engine)
    write_csv(rows)
    write_summary(rows)
    write_figure(engines)
    for row in rows:
        print(
            f"{row['case']}: growth={row['growth_events']}, filaments={row['filament_sites']}, "
            f"depth={row['filament_depth_row']}, SET={row['set_reached']}, events={row['total_events']}"
        )
    print(f"Wrote {CSV_PATH}")
    print(f"Wrote {SUMMARY_PATH}")
    print(f"Wrote {FIGURE_PATH}")


if __name__ == "__main__":
    main()
