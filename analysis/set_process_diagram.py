"""Create a conceptual spatial SET schematic for the Ag/PVA/Pt device."""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle

from particle_layers import draw_particles, filament_particles, particle_cloud


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
RESULTS_DIR = ROOT / "results"


def draw_arrow(axis, start, end, color="#425466"):
    axis.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=13,
            linewidth=1.8,
            color=color,
        )
    )


def draw_ions(axis, positions):
    for x, y in positions:
        axis.scatter(x, y, s=34, color="#d97706", edgecolor="white", linewidth=0.7, zorder=5)
        axis.text(x, y, "+", ha="center", va="center", color="white", fontsize=7, weight="bold", zorder=6)


def draw_stack(axis, length_fraction, ions, stage_label, state_label, number, show_migration=False):
    axis.set_xlim(0, 10)
    axis.set_ylim(0, 10)
    axis.axis("off")

    axis.add_patch(Circle((0.8, 9.15), 0.36, color="#23384d", zorder=8))
    axis.text(0.8, 9.15, str(number), ha="center", va="center", color="white", fontsize=12, weight="bold", zorder=9)
    axis.text(1.35, 9.15, stage_label, fontsize=12, weight="bold", color="#23384d", va="center")

    axis.add_patch(Rectangle((2.2, 7.65), 5.6, 0.65, facecolor="#a7b4c2", edgecolor="#23384d", linewidth=1.2))
    axis.text(5, 7.97, "Ag top electrode", ha="center", va="center", fontsize=9, weight="bold")
    axis.add_patch(Rectangle((2.2, 1.75), 5.6, 0.65, facecolor="#a7b4c2", edgecolor="#23384d", linewidth=1.2))
    axis.text(5, 2.07, "Pt bottom electrode", ha="center", va="center", fontsize=9, weight="bold")
    axis.add_patch(Rectangle((2.2, 2.4), 5.6, 5.25, facecolor="#f5e9d3", edgecolor="#b08b57", linewidth=1.2))
    axis.text(7.45, 5.05, "PVA\n~100 nm", ha="center", va="center", fontsize=9, color="#795548", weight="bold")

    bottom = 2.4
    top = bottom + 5.25 * length_fraction
    if length_fraction > 0:
        axis.plot((5, 5), (bottom, top), color="#8f2d2d", linewidth=3.5, alpha=0.35, zorder=4)
        draw_particles(axis, filament_particles(number + 20, length_fraction), size=13)

    ion_positions = particle_cloud(number, 42)
    draw_particles(axis, ion_positions, color="#d97706", size=24, alpha=0.9)
    axis.scatter(ion_positions[:, 0], ion_positions[:, 1], s=24, facecolors="none", edgecolors="white", linewidths=0.6, zorder=6)
    if show_migration:
        draw_arrow(axis, (4.0, 3.25), (4.7, 5.0), color="#d97706")
        draw_arrow(axis, (4.2, 4.0), (4.85, 5.8), color="#d97706")
        axis.text(3.35, 3.0, "Ag+ migration", fontsize=8, color="#a15c00", ha="center")
    axis.text(5, 0.95, state_label, ha="center", va="center", fontsize=10, color="#23384d", weight="bold")


def make_figure():
    figure, axes = plt.subplots(2, 2, figsize=(16, 12), facecolor="white")
    figure.suptitle("SET Process - Ag/PVA/Pt CBRAM", fontsize=23, weight="bold", color="#172b3a", y=0.965)
    figure.text(0.5, 0.935, "Conceptual spatial visualization based on the phenomenological filament model", ha="center", fontsize=12, color="#506273")

    draw_stack(
        axes[0, 0], 0.0,
        [(3.2, 3.2), (4.0, 4.3), (4.8, 5.4), (5.9, 3.5), (6.5, 6.2), (3.5, 6.4)],
        "INITIAL HRS", "HRS - no connected filament", 1,
    )
    draw_stack(
        axes[0, 1], 0.22,
        [(3.1, 3.1), (3.8, 4.1), (4.4, 5.0), (5.9, 3.6), (6.5, 6.1), (3.5, 6.3)],
        "Ag+ MIGRATION", "Initial Ag filament formation", 2, show_migration=True,
    )
    draw_stack(
        axes[1, 0], 0.68,
        [(3.2, 3.2), (3.9, 4.4), (4.4, 5.8), (5.9, 3.6), (6.5, 6.3)],
        "FILAMENT GROWTH", "Conductive path approaches contact", 3, show_migration=True,
    )
    draw_stack(
        axes[1, 1], 0.99,
        [(3.4, 3.2), (4.0, 4.5), (5.9, 3.7), (6.4, 6.1)],
        "SET / LRS", "LRS - filament reaches the electrodes", 4,
    )

    figure.text(
        0.5, 0.025,
        "SET: Positive bias drives modeled Ag+ migration and filament growth until a conductive path forms.\n"
        "Red dots represent conceptual Ag-filament material; orange dots represent conceptual Ag+ ions.\n"
        "The dots are not individual atoms or atomistic molecular-dynamics coordinates.",
        ha="center", va="center", fontsize=12, color="#23384d",
        bbox={"boxstyle": "round,pad=0.7", "facecolor": "#eef3f7", "edgecolor": "#9eb1c2", "linewidth": 1.2},
    )
    figure.subplots_adjust(left=0.04, right=0.96, top=0.89, bottom=0.11, wspace=0.08, hspace=0.16)
    return figure


def main():
    RESULTS_DIR.mkdir(exist_ok=True)
    output = RESULTS_DIR / "set_process_diagram.png"
    figure = make_figure()
    figure.savefig(output, dpi=160, facecolor="white")
    plt.close(figure)
    print(f"Saved SET process diagram to {output}")


if __name__ == "__main__":
    main()