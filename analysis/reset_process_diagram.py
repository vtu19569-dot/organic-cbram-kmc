"""Create a conceptual RESET-process schematic for the Ag/PVA/Pt device."""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle

from particle_layers import draw_particles, filament_particles, particle_cloud


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
RESULTS_DIR = ROOT / "results"


def draw_arrow(axis, start, end, color="#425466", linewidth=1.8, style="-|>"):
    axis.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle=style,
            mutation_scale=13,
            linewidth=linewidth,
            color=color,
        )
    )


def draw_ions(axis, positions, color="#d97706"):
    for x, y in positions:
        axis.scatter(x, y, s=34, color=color, edgecolor="white", linewidth=0.7, zorder=5)
        axis.text(x, y, "+", ha="center", va="center", color="white", fontsize=7, weight="bold", zorder=6)


def draw_stack(axis, filament_segments, ions, stage_label, state_label, number):
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

    for x1, y1, x2, y2, width in filament_segments:
        axis.plot((x1, x2), (y1, y2), color="#8f2d2d", linewidth=3.5, alpha=0.35, solid_capstyle="round", zorder=4)
    particle_length = min(0.99, max(0.0, (max(y2 for _, _, _, y2, _ in filament_segments) - 2.4) / 5.25)) if filament_segments else 0.0
    draw_particles(axis, filament_particles(number + 40, particle_length), size=13)
    ion_positions = particle_cloud(number + 50, 42)
    draw_particles(axis, ion_positions, color="#d97706", size=24, alpha=0.9)
    axis.scatter(ion_positions[:, 0], ion_positions[:, 1], s=24, facecolors="none", edgecolors="white", linewidths=0.6, zorder=6)
    axis.text(5, 0.95, state_label, ha="center", va="center", fontsize=10, color="#23384d", weight="bold")


def make_figure():
    figure, axes = plt.subplots(2, 2, figsize=(16, 12), facecolor="white")
    figure.suptitle("RESET Process - Ag/PVA/Pt CBRAM", fontsize=23, weight="bold", color="#172b3a", y=0.965)
    figure.text(0.5, 0.935, "Negative bias causes Ag filament dissolution and restores the high-resistance state", ha="center", fontsize=12, color="#506273")

    common_ions = [(3.2, 3.0), (4.0, 4.1), (4.7, 5.0), (5.7, 3.4), (6.3, 6.1), (3.4, 6.3)]
    draw_stack(axes[0, 0], [(5.0, 2.4, 5.0, 7.65, 13)], common_ions, "BEFORE RESET", "LRS - conductive filament connected", 1)

    dissolution_ions = [(3.2, 3.0), (3.9, 4.0), (4.4, 5.2), (5.8, 3.5), (6.5, 6.2), (3.5, 6.3)]
    draw_stack(axes[0, 1], [(5.0, 2.4, 5.0, 4.9, 12), (5.0, 5.35, 5.0, 7.65, 8)], dissolution_ions, "FILAMENT DISSOLUTION", "Negative bias: Ag filament begins to dissolve", 2)
    draw_arrow(axes[0, 1], (8.15, 7.1), (8.15, 5.9), color="#7c3aed")
    axes[0, 1].text(8.2, 7.35, "- bias", ha="center", color="#7c3aed", weight="bold")
    draw_arrow(axes[0, 1], (5.0, 5.25), (4.2, 5.25), color="#d97706")
    axes[0, 1].text(3.55, 5.55, "Ag+ leaves path", fontsize=8, color="#a15c00", ha="center")

    rupture_ions = [(3.1, 3.1), (3.8, 4.4), (4.2, 5.8), (5.9, 3.3), (6.6, 4.8), (6.2, 6.3), (4.0, 6.6)]
    draw_stack(axes[1, 0], [(5.0, 2.4, 5.0, 4.45, 10), (5.0, 5.85, 5.0, 7.65, 7)], rupture_ions, "FILAMENT RUPTURE", "Conductive path interrupted - gap formed", 3)
    axes[1, 0].plot((4.75, 5.25), (5.15, 5.15), color="#c2410c", linewidth=1.4, linestyle="--")
    axes[1, 0].text(5, 5.55, "gap", ha="center", color="#c2410c", fontsize=9, weight="bold")

    restored_ions = [(3.2, 3.1), (4.0, 4.5), (4.4, 5.9), (5.8, 3.5), (6.5, 4.8), (6.4, 6.3), (3.8, 6.5)]
    draw_stack(axes[1, 1], [(5.0, 6.1, 5.0, 7.65, 7)], restored_ions, "HRS RESTORED", "HRS - filament dissolved and gap restored", 4)
    draw_arrow(axes[1, 1], (5.0, 4.9), (5.0, 3.3), color="#d97706")
    axes[1, 1].text(5.0, 3.0, "Ag+ redistributed", ha="center", color="#a15c00", fontsize=8)

    figure.text(
        0.5,
        0.025,
        "RESET: Negative bias dissolves the Ag filament, removing the conductive path and restoring the high resistance state.\n"
        "Red dots are conceptual Ag-filament material; orange dots are conceptual Ag+ ions, not individual atoms.",
        ha="center",
        va="center",
        fontsize=12,
        color="#23384d",
        bbox={"boxstyle": "round,pad=0.7", "facecolor": "#eef3f7", "edgecolor": "#9eb1c2", "linewidth": 1.2},
    )
    figure.subplots_adjust(left=0.04, right=0.96, top=0.89, bottom=0.11, wspace=0.08, hspace=0.16)
    return figure


def main():
    RESULTS_DIR.mkdir(exist_ok=True)
    output = RESULTS_DIR / "reset_process_diagram.png"
    figure = make_figure()
    figure.savefig(output, dpi=160, facecolor="white")
    plt.close(figure)
    print(f"Saved RESET process diagram to {output}")


if __name__ == "__main__":
    main()