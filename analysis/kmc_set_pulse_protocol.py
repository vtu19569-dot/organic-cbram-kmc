"""Run a voltage-pulse SET protocol on one persistent frozen KMC lattice.

Example:
  .venv/bin/python analysis/kmc_set_pulse_protocol.py \
      --pulse 0.30:0.0001 --pulse 0.00:0.001 --pulse 0.35:0.0001 \
      --temperature 300 --seed 42

Each pulse is ``voltage_V:duration_s``. Voltage is held constant during a pulse.
At a boundary the same lattice and RNG state continue into the next pulse. This
is SET-only: zero/negative voltage does not dissolve existing filament sites.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from kmc_model.experiment_config import ExperimentConfig, WaveformSegment
from kmc_model.kmc_engine import KMCEngine
from kmc_model.lattice import LatticeState


def parse_pulse(raw: str) -> tuple[float, float]:
    try:
        voltage_text, duration_text = raw.split(":", 1)
        voltage, duration = float(voltage_text), float(duration_text)
    except (ValueError, TypeError) as exc:
        raise argparse.ArgumentTypeError("pulse must be VOLTAGE_V:DURATION_S") from exc
    if not math.isfinite(voltage) or not math.isfinite(duration) or duration <= 0:
        raise argparse.ArgumentTypeError("pulse voltage must be finite and duration must be finite and positive")
    return voltage, duration


def count_states(engine: KMCEngine) -> tuple[list[int], list[int]]:
    filament_rows = [r for r in range(engine.config.lattice_rows)
                     if any(engine.lattice.get_state(r, c) == LatticeState.AG_FILAMENT
                            for c in range(engine.config.lattice_columns))]
    ion_rows = [r for r in range(engine.config.lattice_rows)
                if any(engine.lattice.get_state(r, c) == LatticeState.AG_ION
                       for c in range(engine.config.lattice_columns))]
    return filament_rows, ion_rows


def run_protocol(pulses: list[tuple[float, float]], temperature: float, seed: int,
                 max_events: int, output_dir: Path) -> tuple[list[dict], dict]:
    experiment = ExperimentConfig(
        temperature_k=temperature,
        set_bias_v=pulses[0][0],
        waveform=tuple(WaveformSegment(voltage, duration, f"pulse_{i}")
                       for i, (voltage, duration) in enumerate(pulses, start=1)),
        seeds=(seed,), max_events=max_events, output_dir=str(output_dir),
        experiment_id=f"pulse_protocol_seed_{seed}",
    )
    config = experiment.to_kmc_config(voltage_v=pulses[0][0], seed=seed, max_events=max_events)
    engine = KMCEngine(config)
    engine.initialize()
    engine._record_snapshot("initial")
    pulse_rows: list[dict] = []
    event_rows: list[dict] = []
    elapsed_s = 0.0
    termination = "PROTOCOL_COMPLETE"

    for pulse_index, (voltage, duration_s) in enumerate(pulses, start=1):
        start_s = elapsed_s
        end_s = start_s + duration_s
        start_events = engine.total_events
        counts_before = Counter(engine.diagnostic_counters)
        engine.config.applied_voltage_v = voltage
        engine.electric_field_v_m = voltage / (engine.config.switching_layer_thickness_nm * 1e-9)

        while engine.total_events < max_events and engine.total_time_s < end_s:
            events = engine._build_events()
            total_rate = sum(event.rate for event in events)
            if not events or total_rate <= 0.0:
                termination = "NO_ACTIVE_EVENT"
                break

            tau = -math.log(engine.rng.random()) / total_rate
            # At a known protocol boundary, discard an event whose waiting time
            # crosses the edge and resample under the next segment's rates.
            if engine.total_time_s + tau >= end_s:
                engine.total_time_s = end_s
                break

            chosen = engine._select_event(events)
            engine.total_time_s += tau
            engine._apply_event(chosen)
            engine.total_events += 1
            event_rows.append({
                "event_number": engine.total_events,
                "pulse_index": pulse_index,
                "voltage_V": voltage,
                "time_s": engine.total_time_s,
                "event_type": chosen.event_type.value,
                "source_site": chosen.source_site,
                "target_site": chosen.target_site,
                "rate_Hz": chosen.rate,
            })
            engine.event_log.append({
                "event_number": engine.total_events,
                "time_s": engine.total_time_s,
                "event_type": chosen.event_type.value,
                "source_site": chosen.source_site,
                "target_site": chosen.target_site,
                "rate": chosen.rate,
                "ag_ion_count": engine.lattice.count_state(LatticeState.AG_ION),
                "filament_site_count": engine.lattice.count_state(LatticeState.AG_FILAMENT),
            })
            if engine._check_set_condition():
                engine.set_reached = True
                termination = "SET_REACHED"
                break

        elapsed_s = engine.total_time_s
        filament_rows, ion_rows = count_states(engine)
        counts_after = Counter(engine.diagnostic_counters)
        pulse_rows.append({
            "pulse_index": pulse_index,
            "voltage_V": voltage,
            "pulse_duration_s": duration_s,
            "pulse_start_time_s": start_s,
            "pulse_end_time_s": elapsed_s,
            "events_this_pulse": engine.total_events - start_events,
            "total_events": engine.total_events,
            "nucleation_events_this_pulse": int(counts_after["nucleation_events"] - counts_before["nucleation_events"]),
            "growth_events_this_pulse": int(counts_after["filament_growth_events"] - counts_before["filament_growth_events"]),
            "hopping_events_this_pulse": int(counts_after["ag_hopping_events"] - counts_before["ag_hopping_events"]),
            "filament_sites": engine.lattice.count_state(LatticeState.AG_FILAMENT),
            "max_filament_depth_row": max(filament_rows, default=0),
            "max_filament_depth_nm": max(filament_rows, default=0) * config.cell_size_nm,
            "max_ag_plus_depth_row": max(ion_rows, default=0),
            "final_ag_plus_sites": engine.lattice.count_state(LatticeState.AG_ION),
            "set_reached": engine.set_reached,
        })
        engine._record_snapshot(f"after pulse {pulse_index}")
        if termination in {"NO_ACTIVE_EVENT", "SET_REACHED"}:
            break
        if engine.total_events >= max_events:
            termination = "EVENT_CAP"
            break

    final_filament_rows, final_ion_rows = count_states(engine)
    summary = {
        "experiment_id": experiment.experiment_id,
        "temperature_K": temperature,
        "seed": seed,
        "event_cap": max_events,
        "total_events": engine.total_events,
        "simulation_time_s": engine.total_time_s,
        "termination_reason": termination,
        "set_reached": engine.set_reached,
        "reset_reached": "NOT_IMPLEMENTED",
        "retention_state": "NOT_IMPLEMENTED",
        "resistance_ohm": "NOT_IMPLEMENTED",
        "current_A": "NOT_IMPLEMENTED",
        "forming_time_s": engine.total_time_s if engine.set_reached else "",
        "nucleation_events": engine.diagnostic_counters["nucleation_events"],
        "growth_events": engine.diagnostic_counters["filament_growth_events"],
        "hopping_events": engine.diagnostic_counters["ag_hopping_events"],
        "filament_sites": engine.lattice.count_state(LatticeState.AG_FILAMENT),
        "max_filament_depth_row": max(final_filament_rows, default=0),
        "max_filament_depth_nm": max(final_filament_rows, default=0) * config.cell_size_nm,
        "max_ag_plus_depth_row": max(final_ion_rows, default=0),
        "final_ag_plus_sites": engine.lattice.count_state(LatticeState.AG_ION),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "experiment_config.json").open("w") as handle:
        json.dump(experiment.to_dict(), handle, indent=2)
    with (output_dir / "kmc_set_pulse_protocol_summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary))
        writer.writeheader()
        writer.writerow(summary)
    with (output_dir / "kmc_set_pulse_protocol_by_pulse.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(pulse_rows[0]))
        writer.writeheader()
        writer.writerows(pulse_rows)
    with (output_dir / "kmc_set_pulse_protocol_events.csv").open("w", newline="") as handle:
        columns = ["event_number", "pulse_index", "voltage_V", "time_s", "event_type", "source_site", "target_site", "rate_Hz"]
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(event_rows)
    with (output_dir / "kmc_set_pulse_protocol_final_lattice.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["row", *[f"col_{c}" for c in range(config.lattice_columns)]])
        for row_index, lattice_row in enumerate(engine.lattice.snapshot_matrix()):
            writer.writerow([row_index, *lattice_row])
    return pulse_rows, summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pulse", action="append", type=parse_pulse, required=True,
                        help="voltage_V:duration_s; repeat to define an ordered waveform")
    parser.add_argument("--temperature", type=float, default=300.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-events", type=int, default=20000)
    parser.add_argument("--output-dir", type=Path, default=Path("results/kmc/pulse_protocol"))
    args = parser.parse_args()
    if args.temperature <= 0 or args.max_events <= 0:
        parser.error("temperature and max-events must be positive")
    pulse_rows, summary = run_protocol(args.pulse, args.temperature, args.seed, args.max_events, args.output_dir)
    print(f"Termination: {summary['termination_reason']}; events={summary['total_events']}; "
          f"simulated_time_s={summary['simulation_time_s']:.8g}; SET={summary['set_reached']}")
    print(f"Saved {len(pulse_rows)} pulse records and final morphology under {args.output_dir}")
    print("This protocol has no RESET dissolution, compliance circuit, or calibrated retention model.")


if __name__ == "__main__":
    main()
