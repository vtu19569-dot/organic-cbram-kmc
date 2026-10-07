"""Run a single coarse-grained KMC SET case for Ag/PVA/Pt."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from kmc_model.kmc_engine import KMCEngine
from kmc_model.parameters import KMCConfig


def main() -> None:
    config = KMCConfig()
    output_dir = Path(config.output_directory)
    output_dir.mkdir(parents=True, exist_ok=True)

    engine = KMCEngine(config)
    result = engine.run()
    engine.save_states_csv(output_dir / "kmc_set_0p30V_states.csv")
    engine.save_process_figure(output_dir / "kmc_set_0p30V_process.png")
    engine.save_diagnostics_csv(output_dir / "kmc_single_set_diagnostics.csv")
    engine.save_diagnostics_figure(output_dir / "kmc_set_0p30V_diagnostics.png")

    csv_path = output_dir / "kmc_single_set.csv"
    with csv_path.open("w", newline="") as handle:
        handle.write(
            "voltage_V,temperature_K,random_seed,set_reached,set_time_s,total_kmc_events,final_filament_length_nm,final_filament_width_nm,ag_ion_count,filament_site_count\n"
        )
        handle.write(
            f"{result.voltage_v},{result.temperature_k},{result.random_seed},{str(result.set_reached).lower()},"
            f"{result.set_time_s},{result.total_events},{result.filament_length_nm},{result.filament_width_nm},"
            f"{result.ag_ion_count},{result.filament_site_count}\n"
        )

    print(f"Single-case KMC SET result saved to {csv_path}")
    print(f"SET reached: {result.set_reached}")
    print(f"SET time (s): {result.set_time_s:.6g}")
    print(f"KMC events: {result.total_events}")
    print(f"Electric field (V/m): {engine.electric_field_v_m:.6g}")
    print(f"Configured activation barrier (eV): {config.activation_energy_ev:.6g}")
    print(f"Effective downward barrier (eV): {engine._effective_barrier_ev(config.activation_energy_ev, 1, 2):.6g}")
    print(f"Base activated rate (Hz): {engine._base_rate_hz():.6g}")
    print(f"Mean KMC time increment (s): {engine.total_time_s / result.total_events:.6g}")
    print(f"Field term used in rate: True (field_factor={config.field_factor})")
    for event_type, rate in engine.rate_contributions.items():
        print(f"Total candidate rate contribution - {event_type}: {rate:.6g} Hz-sum")
    print(f"Total candidate rate contribution: {sum(engine.rate_contributions.values()):.6g} Hz-sum")
    print(f"Maximum Ag+ depth row: {engine.diagnostic_counters['max_ag_ion_depth_row']}")
    print(f"Maximum filament depth row: {engine.diagnostic_counters['max_filament_depth_row']}")


if __name__ == "__main__":
    main()
