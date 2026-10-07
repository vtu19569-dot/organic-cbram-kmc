"""Run controlled KMC parameter explorations without changing frozen kinetics.

Examples:
  .venv/bin/python analysis/kmc_parameter_explorer.py --voltage 0.30 --temperature 300 --seed 42
  .venv/bin/python analysis/kmc_parameter_explorer.py --voltages 0.20,0.30,0.40 --seeds 42,43,44

This is a run-level explorer: each condition starts from a fresh lattice. It does
not claim to model a time-dependent voltage waveform, RESET, current compliance,
or retention, none of which has a defensible event/circuit model in this KMC.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from kmc_model.events import EventType
from kmc_model.experiment_config import ExperimentConfig
from kmc_model.kmc_engine import KMCEngine
from kmc_model.lattice import LatticeState


def parse_values(raw: str, cast):
    try:
        values = [cast(value.strip()) for value in raw.split(",") if value.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid comma-separated values: {raw}") from exc
    if not values:
        raise argparse.ArgumentTypeError("provide at least one value")
    return values


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--voltage", type=float, help="one constant applied voltage (V)")
    parser.add_argument("--temperature", type=float, default=300.0, help="temperature (K), default 300")
    parser.add_argument("--seed", type=int, default=42, help="random seed, default 42")
    parser.add_argument("--voltages", help="comma-separated constant voltages for a sweep")
    parser.add_argument("--temperatures", help="comma-separated temperatures for a sweep")
    parser.add_argument("--seeds", help="comma-separated seeds; reused for each condition")
    parser.add_argument("--max-events", type=int, default=20000, help="numerical event window (default frozen value: 20000)")
    parser.add_argument("--output-dir", type=Path, default=Path("results/kmc/parameter_explorer"))
    return parser


def run_one(voltage: float, temperature: float, seed: int, max_events: int,
            output_dir: Path, run_id: int, experiment: ExperimentConfig) -> dict:
    config = experiment.to_kmc_config(
        voltage_v=voltage, temperature_k=temperature, seed=seed, max_events=max_events,
    )
    engine = KMCEngine(config)
    run_config = replace(experiment, set_bias_v=voltage, temperature_k=temperature, seeds=(seed,))
    run_config = replace(run_config, experiment_id=f"run_{run_id:04d}")
    with (output_dir / f"run_{run_id:04d}_config.json").open("w") as handle:
        json.dump(run_config.to_dict(), handle, indent=2)
    result = engine.run()
    counts = Counter(event["event_type"] for event in result.event_log)
    filament_rows = [r for r in range(config.lattice_rows) for c in range(config.lattice_columns)
                     if engine.lattice.get_state(r, c) == LatticeState.AG_FILAMENT]
    ag_rows = [r for r in range(config.lattice_rows) for c in range(config.lattice_columns)
               if engine.lattice.get_state(r, c) == LatticeState.AG_ION]
    if result.set_reached:
        termination = "SET_REACHED"
    elif result.total_events >= max_events:
        termination = "EVENT_CAP"
    else:
        termination = "NO_ACTIVE_EVENT"
    row = {
        "experiment_id": run_config.experiment_id,
        "run_id": run_id,
        "voltage_V": voltage,
        "effective_voltage_V": voltage,
        "temperature_K": temperature,
        "seed": seed,
        "event_cap": max_events,
        "total_events": result.total_events,
        "termination_reason": termination,
        "simulation_time_s": engine.total_time_s,
        "set_reached": result.set_reached,
        "reset_reached": "NOT_IMPLEMENTED",
        "retention_state": "NOT_IMPLEMENTED",
        "resistance_ohm": "NOT_IMPLEMENTED",
        "current_A": "NOT_IMPLEMENTED",
        "forming_time_s": engine.total_time_s if result.set_reached else "",
        "nucleation_events": counts[EventType.AG_NUCLEATION.value],
        "growth_events": counts[EventType.AG_REDUCTION_DEPOSITION.value],
        "hopping_events": counts[EventType.AG_HOPPING.value],
        "filament_sites": result.filament_site_count,
        "max_filament_depth_row": max(filament_rows, default=0),
        "max_filament_depth_nm": max(filament_rows, default=0) * config.cell_size_nm,
        "filament_length_nm": result.filament_length_nm,
        "max_ag_plus_depth_row": max(ag_rows, default=0),
        "max_ag_plus_depth_nm": max(ag_rows, default=0) * config.cell_size_nm,
        "final_ag_plus_sites": result.ag_ion_count,
        "electric_field_V_m": engine.electric_field_v_m,
    }
    grid_path = output_dir / "morphology" / f"run_{run_id:04d}_V{voltage:g}_T{temperature:g}_s{seed}.csv"
    grid_path.parent.mkdir(parents=True, exist_ok=True)
    with grid_path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["row", *[f"col_{c}" for c in range(config.lattice_columns)]])
        for r, lattice_row in enumerate(result.final_morphology):
            writer.writerow([r, *lattice_row])
    row["morphology_csv"] = str(grid_path)
    return row


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.max_events <= 0:
        parser.error("--max-events must be positive")
    if args.voltage is not None and args.voltages:
        parser.error("choose --voltage or --voltages, not both")
    if args.temperatures and args.temperature != 300.0:
        parser.error("choose --temperature or --temperatures, not both")
    if args.voltages:
        voltages = parse_values(args.voltages, float)
    elif args.voltage is not None:
        voltages = [args.voltage]
    else:
        voltages = [0.30]
    temperatures = parse_values(args.temperatures, float) if args.temperatures else [args.temperature]
    seeds = parse_values(args.seeds, int) if args.seeds else [args.seed]
    if any(v < 0 for v in voltages) or any(t <= 0 for t in temperatures):
        parser.error("voltages must be nonnegative SET biases and temperatures must be positive")

    # Keep the frozen device geometry. Thickness is intentionally not exposed as
    # a numeric override until the project defines an unambiguous row mapping.
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    experiment = ExperimentConfig(
        temperature_k=temperatures[0], set_bias_v=voltages[0], seeds=tuple(seeds),
        max_events=args.max_events, output_dir=str(output_dir),
    )
    with (output_dir / "experiment_plan.json").open("w") as handle:
        json.dump({
            "template": experiment.to_dict(),
            "voltage_values_V": voltages,
            "temperature_values_K": temperatures,
            "seeds": seeds,
        }, handle, indent=2)
    runs = []
    for voltage in voltages:
        for temperature in temperatures:
            for seed in seeds:
                runs.append(run_one(voltage, temperature, seed, args.max_events,
                                    output_dir, len(runs) + 1, experiment))
                print(f"completed {len(runs)}/{len(voltages) * len(temperatures) * len(seeds)}: "
                      f"V={voltage:g} T={temperature:g} seed={seed} "
                      f"events={runs[-1]['total_events']} {runs[-1]['termination_reason']}")
    output_csv = output_dir / "kmc_parameter_explorer_runs.csv"
    with output_csv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(runs[0]))
        writer.writeheader()
        writer.writerows(runs)
    print(f"\nSaved {len(runs)} runs to {output_csv}")
    print("Frozen geometry and kinetic parameters were retained; each row is a fresh constant-condition trajectory.")
    print("RESET bias, compliance current, and retention are not simulated by this SET-only engine.")


if __name__ == "__main__":
    main()
