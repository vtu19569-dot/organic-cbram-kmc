"""Minimal validation for the isolated coarse-grained KMC model.

This script validates the Stage 3 package structure and confirms that a single
0.30 V, 300 K KMC simulation is deterministic when run twice with the same seed.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def validate_package_structure() -> None:
    project_root = Path(__file__).resolve().parents[1]
    required_files = [
        project_root / "kmc_model" / "__init__.py",
        project_root / "kmc_model" / "README.md",
        project_root / "kmc_model" / "parameters.py",
        project_root / "kmc_model" / "lattice.py",
        project_root / "kmc_model" / "events.py",
        project_root / "kmc_model" / "kmc_engine.py",
        project_root / "kmc_model" / "filament.py",
        project_root / "kmc_model" / "resistance.py",
        project_root / "kmc_model" / "run_single.py",
        project_root / "kmc_model" / "provenance.md",
        project_root / "kmc_model" / "parameter_justification.md",
    ]

    missing = [str(path.relative_to(project_root)) for path in required_files if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required KMC files: " + ", ".join(missing))

    print("Package structure validated.")


def validate_imports() -> None:
    import kmc_model
    from kmc_model.kmc_engine import KMCEngine
    from kmc_model.parameters import KMCConfig
    from kmc_model.lattice import LatticeGrid

    cfg = KMCConfig()
    lattice = LatticeGrid(rows=cfg.lattice_rows, cols=cfg.lattice_columns)
    engine = KMCEngine(cfg)

    assert isinstance(cfg.device_top_electrode, str)
    assert isinstance(lattice.cell_map, dict)
    assert hasattr(engine, "run")
    print("Imports and engine interface validated successfully.")


def validate_determinism() -> None:
    from kmc_model.kmc_engine import KMCEngine
    from kmc_model.parameters import KMCConfig

    cfg1 = KMCConfig()
    cfg2 = KMCConfig()
    result1 = KMCEngine(cfg1).run()
    result2 = KMCEngine(cfg2).run()

    assert result1.set_reached == result2.set_reached
    assert result1.set_time_s == result2.set_time_s
    assert result1.total_events == result2.total_events
    assert result1.final_morphology == result2.final_morphology
    print("Deterministic single-case KMC validation passed.")


def main() -> None:
    validate_package_structure()
    validate_imports()
    validate_determinism()


if __name__ == "__main__":
    main()
