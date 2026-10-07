"""Controlled event-window diagnostic for the frozen Stage 8 KMC model."""

from __future__ import annotations

import csv
import math
import sys
from dataclasses import replace
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from kmc_model.kmc_engine import KMCEngine
from kmc_model.parameters import KMCConfig

OUTPUT_DIR = PROJECT_ROOT / "results" / "kmc"
CAPS = (20_000, 50_000, 100_000, 200_000)
CSV_PATH = OUTPUT_DIR / "kmc_event_window_diagnostic.csv"
PLOT_PATH = OUTPUT_DIR / "kmc_event_window_diagnostic.png"
SUMMARY_PATH = OUTPUT_DIR / "kmc_event_window_diagnostic_summary.md"


def run_case(base: KMCConfig, event_cap: int) -> tuple[dict, KMCEngine]:
    config = replace(base, max_kmc_events=event_cap)
    engine = KMCEngine(config)
    result = engine.run()

    if result.set_reached:
        termination_reason = "SET_REACHED"
    elif result.total_events >= event_cap:
        termination_reason = "EVENT_CAP"
    else:
        # run() exits before the cap only when _build_events() is empty or
        # the summed event rate is non-positive.
        termination_reason = "NO_ACTIVE_EVENT"

    row = {
        "event_cap": event_cap,
        "total_events": result.total_events,
        "set_reached": result.set_reached,
        "forming_time_s": result.set_time_s if result.set_reached else math.nan,
        "simulation_time_s": result.set_time_s,
        "nucleation_events": engine.diagnostic_counters["nucleation_events"],
        "growth_events": engine.diagnostic_counters["growth_successes"],
        "hopping_events": engine.diagnostic_counters["hopping_successes"],
        "filament_sites": result.filament_site_count,
        "maximum_filament_depth_row": engine.diagnostic_counters["max_filament_depth_row"],
        "filament_length_nm": result.filament_length_nm,
        "maximum_ag_plus_depth_row": engine.diagnostic_counters["max_ag_ion_depth_row"],
        "final_ag_plus_sites": result.ag_ion_count,
        "termination_reason": termination_reason,
    }
    return row, engine


def write_csv(rows: list[dict]) -> None:
    fields = [
        "event_cap", "total_events", "set_reached", "forming_time_s",
        "simulation_time_s", "nucleation_events", "growth_events",
        "hopping_events", "filament_sites", "maximum_filament_depth_row",
        "filament_length_nm", "maximum_ag_plus_depth_row",
        "final_ag_plus_sites", "termination_reason",
    ]
    with CSV_PATH.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_plot(rows: list[dict]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    caps = [row["event_cap"] for row in rows]
    figure, axes = plt.subplots(3, 1, figsize=(7, 10), sharex=True)
    axes[0].plot(caps, [row["maximum_filament_depth_row"] for row in rows], marker="o")
    axes[0].set_ylabel("Maximum filament depth (row)")
    axes[1].plot(caps, [row["growth_events"] for row in rows], marker="o")
    axes[1].set_ylabel("Cumulative growth events")
    axes[2].plot(caps, [row["simulation_time_s"] for row in rows], marker="o")
    axes[2].set_ylabel("Simulated physical time (s)")
    axes[2].set_xlabel("Event cap")
    for axis, row in zip(axes, rows):
        if row["set_reached"]:
            axis.axvline(row["total_events"], color="crimson", linestyle="--", label="SET reached")
            axis.legend()
        axis.grid(alpha=0.3)
    axes[2].set_xscale("log")
    figure.suptitle("KMC event-window diagnostic: 0.30 V, 300 K, seed 42")
    figure.tight_layout()
    figure.savefig(PLOT_PATH, dpi=180)
    plt.close(figure)


def write_summary(rows: list[dict]) -> None:
    first, last = rows[0], rows[-1]
    filament_changed = any(
        row[metric] != first[metric]
        for row in rows[1:]
        for metric in ("growth_events", "filament_sites", "maximum_filament_depth_row", "filament_length_nm")
    )
    if filament_changed:
        decision = "A. clearly inadequate"
        rationale = (
            "The same seeded trajectory changes its filament growth count, site count, depth, "
            "or length after 20,000 events, so the production window cuts off ongoing "
            "filament evolution. This does not imply that SET must eventually occur."
        )
        recommendation = "For a future production run, use at least 200,000 events as a provisional observation window and verify convergence there before further increasing it. Do not change the production default in this diagnostic."
    else:
        decision = "C. apparently adequate"
        rationale = (
            "Filament growth, site count, depth, and length are identical at all four caps. "
            "This trajectory therefore shows no evidence that a window beyond 20,000 events "
            "is needed to observe its filament evolution. Ag+ hopping continues beyond the "
            "cap, but does not produce further filament change in this case."
        )
        recommendation = "Retain 20,000 events as the production window for this fixed case; the larger caps showed continued Ag+ hopping but no additional filament growth. Treat the conclusion as case-specific and do not infer general adequacy across other seeds or conditions."

    lines = [
        "# KMC Event-Window Adequacy Diagnostic", "",
        "## 1. Objective", "",
        "Determine whether the 20,000-event numerical window truncates meaningful evolution for the frozen baseline case, changing only the event cap.", "",
        "## 2. Current 20,000-event limitation", "",
        "An event cap is a numerical stopping limit. Reaching it means the configured simulation window ended; it is not evidence of physical non-forming.", "",
        "## 3. Termination logic", "",
        "In `KMCEngine.run()`, the loop runs while `total_events < max_kmc_events`. Before each event it exits if `_build_events()` is empty or if summed rate is non-positive. After applying each event it checks the SET condition and exits if reached. Otherwise, reaching the loop bound ends the run. Thus the categories are: `NO_ACTIVE_EVENT` for an empty event list or non-positive total rate before the cap; `SET_REACHED` when the post-event filament connectivity test succeeds; and `EVENT_CAP` when the event bound is reached without SET. The cap is a simulation-window exhaustion, not physical non-forming.", "",
        "`KMCResult.set_time_s` is assigned the accumulated elapsed KMC time on every exit, including non-SET exits. In the diagnostic CSV it is therefore `simulation_time_s`; `forming_time_s` is blank/NaN unless SET occurs. The event enum also contains `FILAMENT_CONNECTION`, but the engine does not add that event type in `_build_events()`; SET is detected as a post-event condition.", "",
        "## 4. Controlled event-window cases", "",
        "V = +0.30 V; T = 300 K; seed = 42. Only `max_kmc_events` varied: 20,000, 50,000, 100,000, and 200,000. Each case starts from the same initial state and seed.", "",
        "## 5. Results", "",
        "| Event cap | Events completed | Termination | SET | Forming time (s) | Simulation time (s) | Nucleation | Growth | Hopping | Filament sites | Max filament row | Filament length (nm) | Max Ag+ row | Final Ag+ sites |",
        "|---:|---:|---|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        forming = "—" if math.isnan(row["forming_time_s"]) else f"{row['forming_time_s']:.8g}"
        lines.append(
            f"| {row['event_cap']} | {row['total_events']} | {row['termination_reason']} | "
            f"{row['set_reached']} | {forming} | {row['simulation_time_s']:.8g} | "
            f"{row['nucleation_events']} | {row['growth_events']} | {row['hopping_events']} | "
            f"{row['filament_sites']} | {row['maximum_filament_depth_row']} | "
            f"{row['filament_length_nm']:.4g} | {row['maximum_ag_plus_depth_row']} | "
            f"{row['final_ag_plus_sites']} |"
        )
    lines += [
        "", "## 6. Filament-growth behavior", "",
        f"From 20,000 to 200,000 events, growth events changed from {first['growth_events']} to {last['growth_events']}, filament sites from {first['filament_sites']} to {last['filament_sites']}, maximum filament depth from row {first['maximum_filament_depth_row']} to row {last['maximum_filament_depth_row']}, and the model-reported filament vertical span from {first['filament_length_nm']:.4g} to {last['filament_length_nm']:.4g} nm. Hopping events changed from {first['hopping_events']} to {last['hopping_events']}; nucleation events changed from {first['nucleation_events']} to {last['nucleation_events']}. These counts describe the one fixed-seed trajectory.", "",
        "Filament length is the vertical bounding span of all filament cells in the engine’s `FilamentState`, not a per-branch connected-path length. The depth counter is a maximum observed row, so it does not decrease.", "",
        "## 7. Physical simulated-time behavior", "",
        "Physical KMC time is accumulated as `tau = -ln(U) / total_rate` for each selected event. The rate sum changes with the lattice state, so time is stochastic and non-linear in event count. The four event caps are not fixed multiples of physical time; see `simulation_time_s` in the table and plot.", "",
        "## 8. Interpretation", "",
        f"Decision: **{decision}**. {rationale}", "",
        "The result addresses filament evolution for this one baseline trajectory only. It does not establish forming probability, a general SET threshold, or behavior across random seeds. Continued hopping events show that microscopic state updates still occur after 20,000 events, but nucleation/growth and the measured filament morphology are saturated for this trajectory.", "",
        "## 9. Recommended production event window", "",
        recommendation, "",
        "## 10. Limitations", "",
        "- One voltage, temperature, and seed were tested, as requested.",
        "- Only the numerical event cap changed; all KMC parameters and the frozen 4-neighbor mechanism remained at defaults.",
        "- A continuing trajectory does not guarantee eventual SET.",
        "- No RESET, temperature, thickness, or voltage sweep was performed.", "",
        "## 11. Conclusion", "",
        f"For the 0.30 V, 300 K, seed 42 trajectory, the evidence supports **{decision}** for the 20,000-event window. The classification is about observing meaningful filament evolution, not claiming that the KMC cannot form. The original production cap remains 20,000 events.",
    ]
    SUMMARY_PATH.write_text("\n".join(lines) + "\n")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    base = KMCConfig()
    assert base.applied_voltage_v == 0.30 and base.temperature_k == 300.0 and base.random_seed == 42
    rows = []
    for event_cap in CAPS:
        row, _engine = run_case(base, event_cap)
        rows.append(row)
        print(
            f"cap={event_cap} events={row['total_events']} stop={row['termination_reason']} "
            f"SET={row['set_reached']} growth={row['growth_events']} "
            f"depth={row['maximum_filament_depth_row']} filament_sites={row['filament_sites']} "
            f"time_s={row['simulation_time_s']:.8g}"
        )
    write_csv(rows)
    write_plot(rows)
    write_summary(rows)
    print(f"Wrote {CSV_PATH}")
    print(f"Wrote {PLOT_PATH}")
    print(f"Wrote {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
