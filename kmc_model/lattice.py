"""Active coarse-grained lattice representation for the first KMC SET model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


class LatticeState:
    EMPTY = "EMPTY"
    AG_ION = "AG_ION"
    AG_FILAMENT = "AG_FILAMENT"
    AG_ELECTRODE = "AG_ELECTRODE"
    PT_ELECTRODE = "PT_ELECTRODE"


@dataclass
class LatticeCell:
    """A single coarse-grained lattice site in the Ag/PVA/Pt stack."""

    row: int = 0
    col: int = 0
    state: str = LatticeState.EMPTY
    local_field: float = 0.0
    occupancy: float = 0.0


@dataclass
class LatticeGrid:
    """2D coarse-grained lattice representing the device cross-section."""

    rows: int = 25
    cols: int = 15
    thickness_nm: float = 100.0
    cell_size_nm: float = 4.0
    electrode_top_index: int = 0
    electrode_bottom_index: int = 24
    cell_map: Dict[Tuple[int, int], LatticeCell] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.cell_map = {}
        for row in range(self.rows):
            for col in range(self.cols):
                state = LatticeState.EMPTY
                if row == self.electrode_top_index:
                    state = LatticeState.AG_ELECTRODE
                elif row == self.electrode_bottom_index:
                    state = LatticeState.PT_ELECTRODE
                self.cell_map[(row, col)] = LatticeCell(row=row, col=col, state=state)

    def get_state(self, row: int, col: int) -> str:
        return self.cell_map[(row, col)].state

    def set_state(self, row: int, col: int, state: str) -> None:
        self.cell_map[(row, col)].state = state

    def neighbors(self, row: int, col: int) -> List[Tuple[int, int]]:
        candidate_neighbors = [
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
        ]
        valid: List[Tuple[int, int]] = []
        for r2, c2 in candidate_neighbors:
            if 0 <= r2 < self.rows and 0 <= c2 < self.cols:
                valid.append((r2, c2))
        return valid

    def snapshot_matrix(self) -> List[List[str]]:
        matrix: List[List[str]] = []
        for row in range(self.rows):
            row_values = []
            for col in range(self.cols):
                row_values.append(self.get_state(row, col))
            matrix.append(row_values)
        return matrix

    def count_state(self, state: str) -> int:
        return sum(1 for cell in self.cell_map.values() if cell.state == state)

    def is_connected_to_top_and_bottom(self) -> bool:
        visited: set[Tuple[int, int]] = set()
        stack = [(1, col) for col in range(self.cols) if self.get_state(1, col) == LatticeState.AG_FILAMENT]
        if not stack:
            return False

        while stack:
            cell = stack.pop()
            if cell in visited:
                continue
            visited.add(cell)
            for neighbor in self.neighbors(cell[0], cell[1]):
                if self.get_state(*neighbor) == LatticeState.AG_FILAMENT and neighbor not in visited:
                    stack.append(neighbor)

        top_connected = any((row, col) in visited for row, col in [(1, c) for c in range(self.cols)])
        bottom_connected = any(
            (self.rows - 2, col) in visited for col in range(self.cols)
        )
        return top_connected and bottom_connected
