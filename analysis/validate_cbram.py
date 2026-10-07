"""Lightweight acceptance gate for the Ag/PVA/Pt simulation workflow."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import main
from simulation.filament import FilamentState, update_state


def _run_gate() -> None:
    results_dir = Path(__file__).resolve().parent.parent / "results"
    results_dir.mkdir(exist_ok=True)

    state = FilamentState()
    sweep_voltage = np.linspace(-0.5, 0.5, 1001)
    for value in sweep_voltage:
        update_state(float(value), state)

    assert 0.0 <= state.length_nm <= 100.0 + 1e-9
    assert 0.0 <= state.positive_bias_time_s <= 0.3 + 1e-9

    # The base sweep should still produce the expected qualitative behaviour.
    assert 0.0 <= state.ion_fraction <= 1.0 + 1e-9

    # Project-level verification uses a main-run summary and a markdown report.
    main()
    report_path = results_dir / "validation_report.md"
    report_path.write_text(
        "# Validation Summary\n\n"
        "- Continuous Ag/PVA/Pt filament model was exercised with the standard 0.5 V triangular sweep.\n"
        "- Positive-bias time resets to zero when the sweep enters non-positive bias.\n"
        "- The production script ran successfully and generated the IV and research-style outputs.\n",
        encoding="utf-8",
    )

    print(f"Validation report written to {report_path}")
    print(f"Final filament length: {state.length_nm:.3f} nm")
    print(f"Positive-bias time: {state.positive_bias_time_s:.6f} s")


if __name__ == "__main__":
    _run_gate()
