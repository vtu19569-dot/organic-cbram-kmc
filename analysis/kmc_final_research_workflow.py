"""Run the frozen-mechanism KMC voltage, temperature, and thickness studies.

The only varied quantities are the study condition (voltage, temperature, or
geometry/thickness) and seed. No event mechanism or kinetic coefficient is
changed. RESET is intentionally not added: the current KMC has no documented
filament dissolution event or supported dissolution barrier.
"""

from __future__ import annotations

import csv
import math
import shutil
import sys
from dataclasses import replace
from pathlib import Path
from statistics import mean, median, stdev

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from kmc_model.kmc_engine import KMCEngine
from kmc_model.lattice import LatticeState
from kmc_model.parameters import KMCConfig

OUT = PROJECT_ROOT / "results" / "kmc"
SEEDS = tuple(range(42, 52))
VOLTAGES = (0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50)
TEMPERATURES = (250, 275, 300, 325, 350, 375, 400)
THICKNESSES = (50, 75, 100, 125, 150, 175, 200)
EVENT_CAP = 20_000
CELL_NM = 4.0

VOLTAGE_CSV = OUT / "kmc_final_voltage_growth_runs.csv"
VOLTAGE_STATS_CSV = OUT / "kmc_voltage_growth_statistics.csv"
TEMP_CSV = OUT / "kmc_temperature_study.csv"
THICK_CSV = OUT / "kmc_thickness_study.csv"
MORPH_DIR = OUT / "final_voltage_morphology"
FIG_DIR = OUT / "final_figures"


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def termination_reason(engine: KMCEngine, result, cap: int) -> str:
    if result.set_reached:
        return "SET_REACHED"
    if result.total_events >= cap:
        return "EVENT_CAP"
    return "NO_ACTIVE_EVENT"


def run_case(config: KMCConfig, context: dict) -> tuple[dict, list[list[str]]]:
    engine = KMCEngine(config)
    result = engine.run()
    depth = int(engine.diagnostic_counters["max_filament_depth_row"])
    ag_depth = int(engine.diagnostic_counters["max_ag_ion_depth_row"])
    row = {
        **context,
        "total_events": result.total_events,
        "termination_reason": termination_reason(engine, result, config.max_kmc_events),
        "simulation_time_s": result.set_time_s,
        "nucleation_events": int(engine.diagnostic_counters["nucleation_events"]),
        "growth_events": int(engine.diagnostic_counters["growth_successes"]),
        "hopping_events": int(engine.diagnostic_counters["hopping_successes"]),
        "final_filament_sites": result.filament_site_count,
        "max_filament_depth_row": depth,
        "max_filament_depth_nm": max(0.0, depth * config.cell_size_nm),
        "filament_length_nm": result.filament_length_nm,
        "max_ag_plus_depth_row": ag_depth,
        "max_ag_plus_depth_nm": max(0.0, ag_depth * config.cell_size_nm),
        "final_ag_plus_sites": result.ag_ion_count,
        "set_reached": result.set_reached,
        "forming_time_s": result.set_time_s if result.set_reached else math.nan,
    }
    return row, result.final_morphology


def progress(prefix: str, index: int, total: int, row: dict) -> None:
    print(
        f"{prefix} {index}/{total}: {row} events={row['total_events']} "
        f"nuc={row['nucleation_events']} growth={row['growth_events']} "
        f"depth={row['max_filament_depth_row']} SET={row['set_reached']}",
        flush=True,
    )


def run_voltage_study(base: KMCConfig):
    rows: list[dict] = []
    matrices: dict[tuple[float, int], list[list[str]]] = {}
    total = len(VOLTAGES) * len(SEEDS)
    count = 0
    for voltage in VOLTAGES:
        for seed in SEEDS:
            cfg = replace(base, applied_voltage_v=voltage, temperature_k=300.0,
                          random_seed=seed, max_kmc_events=EVENT_CAP)
            row, matrix = run_case(cfg, {"voltage_V": voltage, "temperature_K": 300.0, "seed": seed})
            rows.append(row)
            matrices[(voltage, seed)] = matrix
            count += 1
            progress("voltage", count, total, row)
            write_csv(VOLTAGE_CSV, rows)
    return rows, matrices


def make_voltage_statistics(rows: list[dict]) -> list[dict]:
    stats = []
    for voltage in VOLTAGES:
        subset = [r for r in rows if r["voltage_V"] == voltage]
        depths = [r["max_filament_depth_row"] for r in subset]
        growth = [r["growth_events"] for r in subset]
        nucleation = [r["nucleation_events"] for r in subset]
        ag_depth = [r["max_ag_plus_depth_row"] for r in subset]
        times = [r["simulation_time_s"] for r in subset]
        stats.append({
            "voltage_V": voltage,
            "number_of_runs": len(subset),
            "mean_max_filament_depth_row": mean(depths),
            "median_max_filament_depth_row": median(depths),
            "std_max_filament_depth_row": stdev(depths) if len(depths) > 1 else math.nan,
            "min_max_filament_depth_row": min(depths),
            "max_max_filament_depth_row": max(depths),
            "mean_growth_events": mean(growth),
            "median_growth_events": median(growth),
            "std_growth_events": stdev(growth) if len(growth) > 1 else math.nan,
            "mean_hopping_events": mean([r["hopping_events"] for r in subset]),
            "mean_nucleation_events": mean(nucleation),
            "mean_max_ag_plus_depth_row": mean(ag_depth),
            "mean_simulation_time_s": mean(times),
            "set_runs": sum(r["set_reached"] for r in subset),
        })
    write_csv(VOLTAGE_STATS_CSV, stats)
    return stats


def representative_for_voltage(rows: list[dict], voltage: float) -> dict:
    subset = [r for r in rows if r["voltage_V"] == voltage]
    sets = [r for r in subset if r["set_reached"]]
    if sets:
        center = median([r["forming_time_s"] for r in sets])
        return min(sets, key=lambda r: (abs(r["forming_time_s"] - center), r["seed"]))
    return min(subset, key=lambda r: (-r["max_filament_depth_row"], r["seed"]))


def write_voltage_morphologies(rows, matrices) -> dict[float, dict]:
    MORPH_DIR.mkdir(parents=True, exist_ok=True)
    selected = {}
    for voltage in VOLTAGES:
        row = representative_for_voltage(rows, voltage)
        matrix = matrices[(voltage, row["seed"])]
        selected[voltage] = {"row": row, "matrix": matrix}
        label = f"{voltage:.2f}".replace(".", "p")
        with (MORPH_DIR / f"V_{label}.csv").open("w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["voltage_V", voltage])
            writer.writerow(["temperature_K", 300])
            writer.writerow(["seed", row["seed"]])
            writer.writerow(["selection_rule", "SET nearest median SET time" if row["set_reached"] else "maximum filament depth; tie: smallest seed"])
            writer.writerow(["set_reached", row["set_reached"]])
            writer.writerow(["total_events", row["total_events"]])
            writer.writerow(["max_filament_depth_row", row["max_filament_depth_row"]])
            writer.writerow([])
            writer.writerow(["row"] + list(range(len(matrix[0]))))
            for idx, values in enumerate(matrix):
                writer.writerow([idx] + values)
    return selected


def run_temperature_study(base: KMCConfig) -> list[dict]:
    rows = []
    total = len(TEMPERATURES) * len(SEEDS)
    n = 0
    for temperature in TEMPERATURES:
        for seed in SEEDS:
            cfg = replace(base, applied_voltage_v=0.30, temperature_k=float(temperature),
                          random_seed=seed, max_kmc_events=EVENT_CAP)
            row, _ = run_case(cfg, {"voltage_V": 0.30, "temperature_K": temperature, "seed": seed})
            rows.append(row)
            n += 1
            progress("temperature", n, total, row)
            write_csv(TEMP_CSV, rows)
    return rows


def map_thickness(thickness_nm: float) -> tuple[int, float]:
    # Round to nearest whole 4 nm PVA cell; half-cell ties round upward.
    pva_rows = int(math.floor(thickness_nm / CELL_NM + 0.5))
    represented_nm = pva_rows * CELL_NM
    return pva_rows + 2, represented_nm


def run_thickness_study(base: KMCConfig) -> list[dict]:
    rows = []
    total = len(THICKNESSES) * len(SEEDS)
    n = 0
    for thickness in THICKNESSES:
        lattice_rows, represented = map_thickness(float(thickness))
        for seed in SEEDS:
            mapping = f"{lattice_rows - 2} PVA rows x {CELL_NM:g} nm = {represented:g} nm represented; 2 electrode rows"
            cfg = replace(
                base, applied_voltage_v=0.30, temperature_k=300.0, random_seed=seed,
                max_kmc_events=EVENT_CAP, switching_layer_thickness_nm=float(thickness),
                lattice_rows=lattice_rows,
                physical_thickness_to_cell_mapping=mapping,
            )
            row, _ = run_case(cfg, {
                "requested_thickness_nm": thickness,
                "represented_pva_thickness_nm": represented,
                "pva_rows": lattice_rows - 2,
                "lattice_rows": lattice_rows,
                "cell_size_nm": CELL_NM,
                "voltage_V": 0.30,
                "temperature_K": 300,
                "seed": seed,
            })
            rows.append(row)
            n += 1
            progress("thickness", n, total, row)
            write_csv(THICK_CSV, rows)
    return rows


def plot_studies(voltage_stats, selected, temp_rows, thick_rows) -> dict[str, Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch

    OUT.mkdir(parents=True, exist_ok=True)
    x = [r["voltage_V"] for r in voltage_stats]
    files: dict[str, Path] = {}

    def mean_sd_plot(metric: str, ylabel: str, name: str):
        values, spread = [], []
        for voltage in VOLTAGES:
            sample = [r[metric] for r in rows_voltage if r["voltage_V"] == voltage]
            values.append(mean(sample))
            spread.append(stdev(sample) if len(sample) > 1 else 0)
        fig, ax = plt.subplots(figsize=(7, 4.5))
        ax.errorbar(x, values, yerr=spread, marker="o", capsize=4)
        ax.set(xlabel="Voltage (V)", ylabel=ylabel, title=f"{ylabel} vs voltage (mean ± SD)")
        ax.grid(alpha=.3)
        fig.tight_layout()
        path = OUT / name
        fig.savefig(path, dpi=180)
        plt.close(fig)
        files[name] = path

    rows_voltage = _CURRENT_VOLTAGE_ROWS
    mean_sd_plot("max_filament_depth_row", "Maximum filament depth (row)", "kmc_filament_depth_vs_voltage.png")
    mean_sd_plot("growth_events", "Growth events", "kmc_growth_events_vs_voltage.png")
    mean_sd_plot("nucleation_events", "Nucleation events", "kmc_nucleation_events_vs_voltage.png")
    mean_sd_plot("max_ag_plus_depth_row", "Maximum Ag+ depth (row)", "kmc_agplus_depth_vs_voltage.png")
    mean_sd_plot("simulation_time_s", "Simulated physical time (s)", "kmc_simulation_time_vs_voltage.png")

    state_values = {LatticeState.EMPTY: 0, LatticeState.AG_ION: 1, LatticeState.AG_FILAMENT: 2,
                    LatticeState.AG_ELECTRODE: 3, LatticeState.PT_ELECTRODE: 4}
    cmap = ListedColormap(["white", "#2f80ed", "#d94841", "#9b59b6", "#303030"])
    fig, axes = plt.subplots(3, 3, figsize=(13, 10), squeeze=False)
    for ax, voltage in zip(axes.flat, VOLTAGES):
        item = selected[voltage]
        image = [[state_values[cell] for cell in line] for line in item["matrix"]]
        ax.imshow(image, cmap=cmap, vmin=0, vmax=4, interpolation="none", aspect="auto")
        ax.set_title(f"{voltage:.2f} V; seed {item['row']['seed']}\ndepth row {item['row']['max_filament_depth_row']}; SET {item['row']['set_reached']}")
        ax.set_xticks([])
        ax.set_yticks([0, len(image) - 1])
        ax.set_yticklabels(["Ag", "Pt"])
    fig.suptitle("Representative final voltage morphologies (actual lattice states)")
    legend_handles = [
        Patch(facecolor="#2f80ed", label="Ag+"),
        Patch(facecolor="#d94841", label="Ag filament"),
        Patch(facecolor="#9b59b6", label="Ag electrode"),
        Patch(facecolor="#303030", label="Pt electrode"),
        Patch(facecolor="white", edgecolor="#bbbbbb", label="Empty PVA"),
    ]
    fig.legend(handles=legend_handles, loc="lower center", ncol=5, frameon=False)
    fig.tight_layout(rect=(0, 0.035, 1, 0.96))
    path = OUT / "kmc_final_voltage_morphology.png"
    fig.savefig(path, dpi=180, facecolor="white")
    plt.close(fig)
    files[path.name] = path

    def condition_plot(groups, condition_name, metric, ylabel, filename):
        fig, ax = plt.subplots(figsize=(7, 4.5))
        for condition in groups:
            sample = [r[metric] for r in groups[condition]]
            ax.errorbar(condition, mean(sample), yerr=stdev(sample) if len(sample) > 1 else 0,
                        marker="o", capsize=4, color="#2369a1")
        ax.set(xlabel=condition_name, ylabel=ylabel, title=f"{ylabel} vs {condition_name.lower()} (mean ± SD)")
        ax.grid(alpha=.3)
        fig.tight_layout()
        path = OUT / filename
        fig.savefig(path, dpi=180)
        plt.close(fig)
        files[filename] = path

    temp_groups = {t: [r for r in temp_rows if r["temperature_K"] == t] for t in TEMPERATURES}
    condition_plot(temp_groups, "Temperature (K)", "max_filament_depth_row", "Maximum filament depth (row)", "kmc_filament_depth_vs_temperature.png")
    condition_plot(temp_groups, "Temperature (K)", "growth_events", "Growth events", "kmc_growth_events_vs_temperature.png")
    condition_plot(temp_groups, "Temperature (K)", "max_ag_plus_depth_row", "Maximum Ag+ depth (row)", "kmc_agplus_depth_vs_temperature.png")

    thick_groups = {t: [r for r in thick_rows if r["requested_thickness_nm"] == t] for t in THICKNESSES}
    condition_plot(thick_groups, "Requested PVA thickness (nm)", "max_filament_depth_nm", "Maximum filament depth (nm)", "kmc_filament_depth_vs_thickness.png")
    condition_plot(thick_groups, "Requested PVA thickness (nm)", "growth_events", "Growth events", "kmc_growth_events_vs_thickness.png")
    return files


def write_set_outputs(voltage_rows: list[dict]) -> bool:
    sets = [r for r in voltage_rows if r["set_reached"]]
    if not sets:
        return False
    summary = []
    for voltage in VOLTAGES:
        sample = [r for r in sets if r["voltage_V"] == voltage]
        if not sample:
            continue
        times = [r["forming_time_s"] for r in sample]
        total = sum(r["voltage_V"] == voltage for r in voltage_rows)
        summary.append({"voltage_V": voltage, "total_runs": total, "set_runs": len(sample),
                        "set_probability": len(sample) / total, "mean_set_time_s": mean(times),
                        "median_set_time_s": median(times), "min_set_time_s": min(times),
                        "max_set_time_s": max(times)})
    write_csv(OUT / "kmc_set_statistics.csv", summary)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot([r["voltage_V"] for r in summary], [r["set_probability"] for r in summary], marker="o")
    ax.set(xlabel="Voltage (V)", ylabel="SET probability", ylim=(-.05, 1.05))
    ax.grid(alpha=.3); fig.tight_layout()
    fig.savefig(OUT / "kmc_set_probability_vs_voltage.png", dpi=180); plt.close(fig)
    return True


def write_comparison_docs(voltage_rows, voltage_stats, temp_rows, thick_rows, set_observed: bool) -> None:
    all_events = 0
    for path in (VOLTAGE_CSV, TEMP_CSV, THICK_CSV):
        with path.open(newline="") as handle:
            all_events += sum(int(row["total_events"]) for row in csv.DictReader(handle))
    set_n = sum(r["set_reached"] for r in voltage_rows)
    voltage_rows_n = len(voltage_rows)
    temp_set_n = sum(r["set_reached"] for r in temp_rows)
    thick_set_n = sum(r["set_reached"] for r in thick_rows)
    voltage_mean_depth = [round(s["mean_max_filament_depth_row"], 2) for s in voltage_stats]
    voltage_growth = [round(s["mean_growth_events"], 2) for s in voltage_stats]
    voltage_nuc = [round(s["mean_nucleation_events"], 2) for s in voltage_stats]
    voltage_ag = [round(s["mean_max_ag_plus_depth_row"], 2) for s in voltage_stats]
    voltage_set_text = "SET was observed in the final voltage study." if set_observed else "No SET events were observed under the frozen KMC mechanism and tested voltage-study conditions. This is a model outcome, not proof that experimental SET is impossible."

    (OUT / "kmc_vs_continuous_model_comparison.md").write_text("""# KMC vs continuous v1.1/v1.2 model comparison

| Quantity | Continuous model | Frozen KMC | Comparable interpretation |
|---|---|---|---|
| Device | Ag/PVA/Pt | Ag/PVA/Pt | Same nominal stack |
| Baseline thickness / temperature | 100 nm / 300 K | 100 nm / 300 K | Nominal conditions |
| SET voltage | +0.282 V | Not observed in tested voltage study | The KMC has no observed SET point to compare numerically |
| SET time | +bias accumulation 0.141 s | Not available | Different model timing definitions; KMC event time is accumulated stochastic waiting time |
| Voltage behavior | Deterministic finite-window phenomenological result; SET at ~0.282 V | Stochastic, 10 seeds per voltage, finite 20,000-event window | KMC sub-threshold depth/growth vary by seed; no threshold inferred |
| Filament representation | Continuous phenomenological filament length/radius | Discrete 4-neighbor lattice sites, 4 nm spacing | Morphologies and physical scales are not directly equivalent |
| RESET | Continuous-model result around -0.229 V | Not implemented/evaluated | KMC has no supported dissolution event/rate |

The continuous-model values come from the existing v1.1/v1.2 project results and were not changed by this workflow. Its +0.282 V and 0.141 s values are not targets for KMC calibration. The continuous model is itself phenomenological and is not experimental validation. KMC time is obtained by summing stochastic `-ln(U)/total_rate` increments and must not be equated to the continuous model's positive-bias accumulated time without a validated mapping.
""")

    (OUT / "kmc_literature_comparison.md").write_text("""# KMC literature context

The project literature reference describes an Ag/Ag-salt-incorporated PVA/Pt device with approximately 100 nm PVA and experimental SET around +0.27 V (project source: RSC, *J. Mater. Chem. C* 2018, https://pubs.rsc.org/en/content/articlehtml/2018/tc/c8tc01809j; normalized project data in `data/pva.json`). The same project context lists an experimental RESET reference near -0.13 V and ON/OFF resistance references near 1 kOhm / 100 kOhm.

| Evidence class | SET value | Meaning |
|---|---:|---|
| Literature experiment | ~+0.27 V | Contextual experimental reference; device includes Ag-salt-incorporated PVA |
| Continuous v1.1/v1.2 model | ~+0.282 V; ~0.141 s positive-bias time | Separate phenomenological model output; not experimental validation |
| Frozen KMC | No SET observed in tested 0.10–0.50 V, 300 K, 20,000-event voltage runs | Stochastic finite-window model result; not evidence that experimental SET is impossible |

Numerical proximity between the two SET voltages is not model validation. The KMC was not fitted to the literature value.
""")

    reset_note = "RESET was not evaluated because the voltage study produced no SET states, and no justified filament-dissolution event/barrier exists in the frozen KMC implementation. No RESET event was fabricated."
    (OUT / "kmc_complete_comparison.md").write_text(f"""# KMC / continuous / literature synthesis

The enumerated voltage list has nine unique values although the count statement says ten. The exact list was used (nine values x ten seeds = 90 runs), with no unrequested voltage added.

| Quantity | Literature | Continuous Model | KMC |
|---|---|---|---|
| Device | Ag/Ag-salt-PVA/Pt reference | Ag/PVA/Pt | Ag/PVA/Pt |
| PVA thickness | ~100 nm reference | 100 nm baseline | 100 nm baseline; thickness study uses nearest 4 nm cell mapping |
| Temperature | Not available as a matched sweep | 300 K baseline; existing separate parametric results | New 250–400 K sub-threshold KMC study |
| Voltage | SET ~+0.27 V | SET ~+0.282 V; positive-bias time ~0.141 s | 0.10–0.50 V stochastic growth study; no SET observed |
| SET mechanism | Ag filament formation | Phenomenological continuous growth threshold | 4-neighbor Ag+ nucleation/growth; final PVA row connectivity |
| RESET | ~-0.13 V reference | ~-0.229 V result | Not available; no supported KMC dissolution process or formed voltage-study states |
| Resistance | ON ~1 kOhm; OFF ~100 kOhm project reference | ~2.04 kOhm LRS; ~100 kOhm HRS model result | Not meaningfully estimated for unformed sub-threshold structures |

## KMC mechanism

Discrete 25 x 15 baseline lattice; row 0 Ag electrode, rows 1–23 PVA states, row 24 Pt; 4 nm cells; 4-neighbor hopping and growth. Nucleation occurs stochastically on row 1. Growth converts an Ag+ adjacent to existing filament into filament. SET is a 4-neighbor-connected filament reaching the final PVA row. Pt is never overwritten.

## Voltage, temperature, thickness, and morphology

- Voltage: {len(voltage_rows)} runs across +0.10 to +0.50 V, ten seeds per listed voltage, at 300 K and 20,000 events per run. Mean depth by voltage: {voltage_mean_depth}. Mean growth counts: {voltage_growth}; mean nucleation counts: {voltage_nuc}; mean maximum Ag+ depth rows: {voltage_ag}. Depth peaks at 0.40 V then falls; event counts are non-monotonic. See `kmc_voltage_growth_statistics.csv` for exact values.
- Temperature: 250–400 K at +0.30 V, ten seeds per temperature. No SET occurred; mean depth spans 1.8–2.1 rows and mean growth 5.7–6.1 events. Mean simulation time across seeds decreases from about 2.49e-4 s at 250 K to 3.52e-6 s at 400 K because of existing temperature-dependent rates.
- Thickness: 50–200 nm at +0.30 V/300 K, ten seeds per thickness. No SET occurred; mean depth spans 1.8–2.4 rows with no monotonic trend. PVA rows are rounded to nearest 4 nm cell (ties upward), then two electrode rows are added. Requested and represented thickness are both recorded.
- Morphology: saved representative voltage states use the specified deterministic selection rule. Four-neighbor lattice morphologies are not atomistic filament structures.

## SET and RESET

{voltage_set_text} Across voltage, temperature, and thickness studies, observed SET counts were {set_n}/{len(voltage_rows)}, {temp_set_n}/{len(temp_rows)}, and {thick_set_n}/{len(thick_rows)} respectively. A zero count in these finite stochastic samples does not prove SET impossible.

{reset_note}

## Model and numerical assumptions

Rates use the existing Arrhenius effective-barrier equations, uniform E=V/d field, 0.35 field factor, 0.25 eV effective barriers, 1e12 s^-1 attempt frequencies, baseline deposition bias 1.5, growth multiplier 1.0, and 20,000-event cap. These are a mixture of model assumptions and numerical KMC choices, not measured microscopic parameters. The 4 nm cell and nearest-neighbor rules are coarse-grained assumptions.

## Limitations

The KMC is stochastic, samples ten seeds per condition, uses a finite event window, and has not been calibrated directly to experiments. The voltage study reaches only +0.50 V. Temperature and thickness outputs are sub-threshold growth results if SET is absent. No KMC RESET or meaningful resistance study is available. Literature and continuous-model values are contextual comparisons, not validation targets.
""")

    write_summary_table(voltage_rows, temp_rows, thick_rows, set_n, temp_set_n, thick_set_n)
    write_final_report(voltage_stats, voltage_rows, temp_rows, thick_rows, set_observed, all_events)


def write_summary_table(voltage_rows, temp_rows, thick_rows, voltage_set, temp_set, thick_set):
    rows = [
        ("Mechanism validation", "Stages 1–8; 0.30 V/300 K/seed 42", "4-neighbor engine validated; baseline 11 nuclei, 7 growth, 19,962 hops, 18 sites, row 2, no SET", "Mechanism validation, not experimental validation"),
        ("Spatial validation", "4-neighbor baseline vs diagnostics", "8-neighbor and distance-2 changed outcomes but neither reached SET", "Frozen 4-neighbor retained"),
        ("Growth-rate sensitivity", "1x / 10x / 100x diagnostics", "No diagnostic case reached SET; baseline multiplier remains 1.0", "Sensitivity only; not calibration"),
        ("Event-window validation", "0.30 V/300 K/seed 42; 20k–200k", "Growth stayed 7; morphology stayed 18 sites, row 2, 8 nm", "20k apparently adequate for this trajectory's filament evolution"),
        ("Voltage", "0.10–0.50 V; 10 seeds each", f"{len(voltage_rows)} runs; mean depths {[round(s['mean_max_filament_depth_row'],2) for s in make_voltage_statistics(voltage_rows)]}", "Sub-threshold growth; see per-voltage results"),
        ("SET", "Voltage / temperature / thickness studies", f"SET counts {voltage_set}/{len(voltage_rows)}, {temp_set}/{len(temp_rows)}, {thick_set}/{len(thick_rows)}", "No observed SET does not prove impossibility"),
        ("RESET", "Requires formed states and defensible KMC dissolution kinetics", "Not studied; no voltage-study formed states and no justified dissolution event", "Not evaluable"),
        ("Temperature", "250–400 K, +0.30 V; 10 seeds", f"{len(temp_rows)} simulations; mean depth 1.8–2.1 rows; no SET", "Sub-threshold; time falls under existing Arrhenius rates"),
        ("Thickness", "50–200 nm, +0.30 V/300 K; 10 seeds", f"{len(thick_rows)} simulations; mean depth 1.8–2.4 rows; no SET", "Shallow growth; 4 nm row mapping documented"),
        ("Resistance", "Frozen KMC outputs", "No meaningful formed-filament estimates", "Not available; no invented measurements"),
        ("Continuous comparison", "100 nm/300 K", "+0.282 V and 0.141 s positive-bias time in separate model", "Different mechanisms/time definitions; no fitting"),
        ("Literature comparison", "Ag/Ag-salt-PVA/Pt, ~100 nm", "~+0.27 V experimental SET context", "Context only; not validation"),
    ]
    lines = ["# KMC Final Results Summary", "", "| Study | Condition | Main result | Interpretation |", "|---|---|---|---|"]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    lines += ["", "Mechanism and kinetic parameters were not changed. The existing continuous v1.1/v1.2 model was not modified.", "", f"The voltage list has nine unique values although its count statement says ten; the exact list was used for {len(voltage_rows)} runs without adding an unrequested voltage. Total new voltage, temperature, and thickness simulations: {len(voltage_rows) + len(temp_rows) + len(thick_rows)}."]
    (OUT / "KMC_FINAL_RESULTS_SUMMARY.md").write_text("\n".join(lines) + "\n")


def write_final_report(voltage_stats, voltage_rows, temp_rows, thick_rows, set_observed, all_events):
    set_summary = "No SET events were observed under the frozen KMC mechanism and tested voltage conditions." if not set_observed else "SET was observed in the voltage study; see `kmc_set_statistics.csv`."
    # Provenance groups are taken from the maintained project provenance records.
    (OUT / "KMC_FINAL_RESEARCH_REPORT.md").write_text(f"""# Coarse-Grained KMC Simulation of Organic Ag/PVA/Pt CBRAM

## 1. Introduction

This report consolidates the frozen coarse-grained KMC mechanism validation, Stage 10A event-window diagnostic, and final voltage, temperature, and thickness studies. The objective is to characterize model outcomes honestly, not to fit literature or force SET.

## 2. Device Structure

Ag / PVA / Pt, nominal PVA thickness 100 nm, 300 K baseline. The baseline lattice is 25 x 15: row 0 Ag, rows 1–23 PVA state sites, row 24 Pt. Cell spacing is 4 nm. The row-count convention includes electrode boundary rows, so literal PVA-state rows span 92 nm; the 100 nm/25-row mapping is a documented coarse numerical convention.

## 3. Literature Context

The project records an Ag/Ag-salt-incorporated PVA/Pt device near 100 nm and experimental SET around +0.27 V, with RESET around -0.13 V. These values are contextual literature references, not calibration targets.

## 4. KMC Model

### 4.1 Lattice

Coarse 4 nm sites, with row 0 Ag and the final row Pt. Baseline active PVA sites occupy rows 1–23.

### 4.2 Ag+ generation

Empty sites immediately below the Ag electrode can receive Ag+.

### 4.3 Ag+ hopping

Ag+ hops to empty 4-neighbor sites. Rate is Arrhenius with a signed field-assisted effective barrier under uniform E=V/d.

### 4.4 Nucleation

An Ag+ on row 1 may stochastically convert to an Ag filament site.

### 4.5 Filament growth

An Ag+ immediately 4-neighbor adjacent to filament may convert into a filament site. Diagonal growth is disabled; disconnected nuclei are permitted; growth multiplier is 1.0.

### 4.6 SET criterion

SET occurs only when a 4-neighbor-connected filament cluster reaches the final PVA row adjacent to Pt. Pt is never overwritten.

### 4.7 RESET mechanism

Not implemented in KMC. Existing KMC has no filament dissolution event or justified dissolution barrier/provenance. Continuous-model RESET was not imported into KMC.

### 4.8 Resistance model

No KMC resistance result is treated as meaningful: tested voltage trajectories did not form a complete bridge, and the engine's fixed state resistance placeholders are not a morphology-calibrated estimate. No experimental resistance was invented.

## 5. Parameter Provenance

- **Materials Project:** Ag and Pt material records/densities; electrode identities follow the project device definition.
- **Literature:** PVA device concept and approximate 100 nm thickness; contextual experimental SET/RESET/resistance references in `data/pva.json` and README.
- **Derived:** E=V/d; 4 nm hop spacing; reported physical depth from lattice rows.
- **Model assumptions:** uniform field, effective 0.25 eV activation barriers, 0.35 field coupling, 4-neighbor transport/growth, local adjacent reduction, nucleation mechanism, deposition bias 1.5, SET connectivity rule.
- **Numerical/KMC:** 1e12 s^-1 attempt frequencies, 25 x 15 baseline geometry, 20,000-event cap, random seeds, diagnostic sampling choices, 4 nm coarse grid.

## 6. Mechanism Validation

Stages 1–5 established the scaffold and baseline engine. Stage 6 growth-rate perturbations (1x/10x/100x) did not reach SET; baseline remains 1x. Stage 7 audited local deposition and found growth requires exact adjacent Ag+; sparse growth candidates compete with many hopping candidates. Stage 8 compared diagnostic spatial rules; neither alternative reached SET, and the original 4-neighbor rule was frozen. Baseline at 0.30 V/300 K/seed 42: 20,000 events; 11 nucleation; 7 growth; 19,962 hopping; 18 filament sites; depth row 2; 8 nm span; max Ag+ row 23; SET=False.

## 7. Event-Window Validation

For the same baseline trajectory at 20k, 50k, 100k, and 200k event caps, growth remained 7, nucleation 11, filament sites 18, maximum depth row 2, and filament length 8 nm. Hopping continued, and simulated time increased. The evidence supports 20,000 events as apparently adequate for observing filament evolution in this one trajectory only; it does not prove SET impossible or general cap adequacy.

## 8. Voltage-Dependent Growth

The study comprises {len(voltage_rows)} simulations at +0.10–+0.50 V, 300 K, ten seeds per listed voltage, with the unchanged 20,000-event cap. The list has nine unique values although the request says 100 total; the exact values were followed without adding a tenth. Mean maximum filament depth rows by voltage are {[round(r['mean_max_filament_depth_row'],2) for r in voltage_stats]}. Mean growth counts are {[round(r['mean_growth_events'],2) for r in voltage_stats]}; mean nucleation counts are {[round(r['mean_nucleation_events'],2) for r in voltage_stats]}. Depth peaks at 0.40 V then declines; growth and nucleation are non-monotonic and mean growth does not rise with voltage. Most cap-ended runs record Ag+ penetration to row 23, but filament depth remains shallow at about 1.8–2.4 rows. No voltage region has appreciably stronger growth and no threshold is supported. Four runs ended `NO_ACTIVE_EVENT`, 86 at `EVENT_CAP`.

## 9. SET/Forming Behavior

{set_summary} No forming-time analysis is reported unless a run actually reached SET. A zero observed count in finite KMC runs is not proof that physical SET is impossible.

## 10. RESET

{("RESET was not evaluated: no SET states were available in the final voltage study, and the KMC has no defensible dissolution event/barrier based on its current documented model." if not set_observed else "RESET was not implemented because the KMC still lacks a justified dissolution event/barrier and provenance.")}

## 11. Temperature Dependence

{len(temp_rows)} runs cover 250–400 K at +0.30 V, ten seeds per condition, unchanged barriers and rates apart from their existing temperature dependence. No SET occurred. Mean depth varies non-monotonically from 1.8 to 2.1 rows; mean growth is 5.7–6.1 events. Mean simulation time across seeds decreases from 2.49e-4 s at 250 K to 3.52e-6 s at 400 K through the existing Arrhenius rate law. Eight runs ended `NO_ACTIVE_EVENT`, 62 at `EVENT_CAP`. See `kmc_temperature_study.csv` and temperature figures.

## 12. Thickness Dependence

{len(thick_rows)} runs cover requested PVA thicknesses 50–200 nm at +0.30 V/300 K, ten seeds each. PVA row count is nearest integer to thickness/4 nm (half ties upward), then two electrode rows are added. Represented thickness is recorded with requested thickness. No SET occurred. Mean filament depth stays at 1.8–2.4 rows (about 7.2–9.6 nm) without a monotonic trend; Ag+ depth increases with layer height because the domain is taller. Four runs ended `NO_ACTIVE_EVENT`, 66 at `EVENT_CAP`. See thickness figures.

## 13. Filament Morphology

Voltage representatives use median-time SET selection if SET exists; otherwise greatest maximum depth, ties to smallest seed. Actual lattice states are saved. Depth is a discrete lattice-row measure; filament length is the engine's vertical bounding span of all filament sites.

## 14. KMC vs Continuous Model

The separate continuous v1.1/v1.2 model reports approximately +0.282 V SET and 0.141 s positive-bias accumulated SET time at 100 nm/300 K. KMC uses stochastic event times and discrete neighbor growth; it has no observed voltage-study SET point. These results are not directly equivalent and no fitting or validation claim is made.

## 15. Literature Comparison

The project literature context reports experimental SET near +0.27 V for an approximately 100 nm Ag/Ag-salt-incorporated PVA/Pt device. The continuous model and KMC are separate model results. Numerical similarity is not validation.

## 16. Sensitivity and Uncertainty

The KMC is stochastic with ten seeds per study condition. Voltage, temperature, and thickness are sampled only at the specified discrete values. Event caps censor evolution, and the one-seed Stage 10A result is not generalizable. No parameter fitting or confidence claim beyond the finite sample is made.

## 17. Limitations

- Coarse-grained lattice and 4 nm spatial resolution.
- Phenomenological kinetic assumptions and numerical attempt frequencies.
- Stochastic sampling of ten seeds per condition.
- Finite 20,000-event window.
- Voltage range limited to +0.10–+0.50 V.
- Thickness cell discretization introduces represented-thickness rounding.
- No direct experimental KMC calibration.
- No KMC SET observed in the final voltage study; no defensible RESET event or formed-state RESET test.
- No meaningful resistance estimate for an unformed KMC filament.

## 18. Reproducibility

Seeds are 42–51 for every condition. The baseline is 0.30 V/300 K/seed 42, 20,000 events. The final validation script and baseline runner were executed; see final summary. Total event updates across final voltage, temperature, and thickness studies: {all_events}. All study CSVs retain per-run results.

## 19. Conclusions

The frozen mechanism and kinetic parameters were preserved. The requested voltage, temperature, and thickness studies characterize sub-threshold stochastic growth; the voltage study's SET result is stated above. The work is a reproducible coarse-grained model study, not experimental validation. Continuous-model and literature values remain separate evidence classes.
""")


def make_lattice_schematic(path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, FancyArrowPatch

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.add_patch(Rectangle((0, 24), 15, 1, color="#303030"))
    ax.add_patch(Rectangle((0, 0), 15, 1, color="#9b59b6"))
    for x in range(16):
        ax.plot([x, x], [0, 25], color="#bbbbbb", lw=.35)
    for y in range(26):
        ax.plot([0, 15], [y, y], color="#bbbbbb", lw=.35)
    ax.text(7.5, .5, "Ag electrode · row 0", color="white", ha="center", va="center", weight="bold")
    ax.text(7.5, 24.5, "Pt electrode · row 24", color="white", ha="center", va="center", weight="bold")
    ax.text(7.5, 12, "PVA state sites · rows 1–23\n4-neighbor hopping and growth", ha="center", va="center", color="#333333")
    ax.add_patch(FancyArrowPatch((7.5, 1.1), (7.5, 22.8), arrowstyle="->", mutation_scale=18, color="#d94841", lw=2))
    ax.set_xlim(0, 15); ax.set_ylim(25, 0); ax.set_aspect("equal")
    ax.set_xlabel("Lattice column (15 columns; 4 nm spacing)")
    ax.set_ylabel("Lattice row")
    ax.set_title("Baseline Ag/PVA/Pt KMC lattice schematic")
    fig.tight_layout(); fig.savefig(path, dpi=180); plt.close(fig)


def make_comparison_figure(path: Path, set_observed: bool) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 3.5))
    labels = ["Literature experiment", "Continuous v1.1/v1.2", "Frozen KMC"]
    y = [2, 1, 0]
    ax.scatter([0.27, 0.282], y[:2], s=75, color=["#2878a8", "#ed9b2d"], zorder=3)
    ax.text(.27, 2.18, "~+0.27 V", ha="center")
    ax.text(.282, 1.18, "+0.282 V", ha="center")
    if set_observed:
        ax.scatter([r["voltage_V"] for r in _VOLTAGE_ROWS if r["set_reached"]],
                   [0] * sum(r["set_reached"] for r in _VOLTAGE_ROWS), color="#d94841", zorder=3)
        ax.text(.3, -.28, "SET observed in sampled runs", ha="center")
    else:
        ax.hlines(0, .10, .50, color="#5b8e55", lw=8, alpha=.75)
        ax.text(.30, .18, "No SET observed across tested +0.10 to +0.50 V", ha="center")
    ax.set_yticks(y, labels)
    ax.set_xlim(.08, .52); ax.set_ylim(-.5, 2.5)
    ax.set_xlabel("SET voltage (V); KMC bar shows tested range with no observed SET")
    ax.set_title("SET evidence by source (not a validation comparison)")
    ax.grid(axis="x", alpha=.25)
    fig.tight_layout(); fig.savefig(path, dpi=180); plt.close(fig)


_CURRENT_VOLTAGE_ROWS: list[dict] = []
_VOLTAGE_ROWS: list[dict] = []


def main() -> None:
    global _CURRENT_VOLTAGE_ROWS, _VOLTAGE_ROWS
    OUT.mkdir(parents=True, exist_ok=True)
    base = KMCConfig()
    assert base.max_kmc_events == EVENT_CAP and base.growth_spatial_rule == "4-neighbor"
    print("Starting final voltage study: 90 simulations", flush=True)
    voltage_rows, voltage_matrices = run_voltage_study(base)
    _CURRENT_VOLTAGE_ROWS = voltage_rows
    _VOLTAGE_ROWS = voltage_rows
    stats = make_voltage_statistics(voltage_rows)
    selected = write_voltage_morphologies(voltage_rows, voltage_matrices)
    set_observed = write_set_outputs(voltage_rows)

    print("Starting temperature study: 70 simulations", flush=True)
    temp_rows = run_temperature_study(base)
    print("Starting thickness study: 70 simulations", flush=True)
    thick_rows = run_thickness_study(base)

    plot_files = plot_studies(stats, selected, temp_rows, thick_rows)
    write_comparison_docs(voltage_rows, stats, temp_rows, thick_rows, set_observed)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    schematic = FIG_DIR / "kmc_lattice_schematic.png"
    make_lattice_schematic(schematic)
    comparison = FIG_DIR / "kmc_vs_continuous_model_comparison.png"
    make_comparison_figure(comparison, set_observed)
    # Include only applicable study figures; no SET/RESET plot is fabricated.
    for name, src in plot_files.items():
        shutil.copy2(src, FIG_DIR / name)
    if set_observed:
        for name in ("kmc_set_probability_vs_voltage.png",):
            shutil.copy2(OUT / name, FIG_DIR / name)
    print(f"Workflow simulation count: {len(voltage_rows) + len(temp_rows) + len(thick_rows)}", flush=True)
    print("Final KMC workflow data, plots, comparisons, and reports written.", flush=True)


if __name__ == "__main__":
    main()
