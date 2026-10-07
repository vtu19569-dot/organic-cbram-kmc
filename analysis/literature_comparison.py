"""Compare the 100 nm, 300 K simulation with literature reference values."""

import csv
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"


def load_temperature_result() -> dict[str, str]:
    with (RESULTS_DIR / "temperature_study_v1_1.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    return next(row for row in rows if row["temperature_K"] == "300")


def main() -> None:
    with (DATA_DIR / "pva.json").open() as handle:
        pva = json.load(handle)

    reference = pva["experimental_reference_parameters"]
    simulation = load_temperature_result()
    comparison = [
        {
            "parameter": "PVA thickness",
            "literature_value": pva["device_layer"]["thickness_nm"],
            "literature_unit": "nm",
            "simulation_value": 100,
            "simulation_unit": "nm",
            "literature_source": "PVA device reference",
            "simulation_source": "v1.1 finite-window study",
        },
        {
            "parameter": "SET voltage",
            "literature_value": reference["set_voltage_V"],
            "literature_unit": "V",
            "simulation_value": simulation["set_voltage_V"],
            "simulation_unit": "V",
            "literature_source": "PVA device reference",
            "simulation_source": "v1.1 finite-window study at 300 K",
        },
        {
            "parameter": "RESET voltage",
            "literature_value": reference["reset_voltage_V"],
            "literature_unit": "V",
            "simulation_value": simulation["reset_voltage_V"],
            "simulation_unit": "V",
            "literature_source": "PVA device reference",
            "simulation_source": "v1.1 finite-window study at 300 K",
        },
        {
            "parameter": "ON resistance",
            "literature_value": reference["on_resistance_ohm"],
            "literature_unit": "Ohm",
            "simulation_value": simulation["min_resistance_ohm"],
            "simulation_unit": "Ohm",
            "literature_source": "PVA device reference",
            "simulation_source": "v1.1 geometric filament model",
        },
        {
            "parameter": "OFF resistance",
            "literature_value": reference["off_resistance_ohm"],
            "literature_unit": "Ohm",
            "simulation_value": simulation["hrs_resistance_ohm"],
            "simulation_unit": "Ohm",
            "literature_source": "PVA device reference",
            "simulation_source": "v1.1 gap-resistance model",
        },
    ]

    output = RESULTS_DIR / "literature_comparison.csv"
    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=comparison[0].keys())
        writer.writeheader()
        writer.writerows(comparison)
    print(f"Saved literature comparison to {output}")


if __name__ == "__main__":
    main()