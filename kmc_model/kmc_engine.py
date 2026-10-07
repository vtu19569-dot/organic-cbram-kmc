"""First working coarse-grained KMC engine for a single Ag/PVA/Pt SET case."""

from __future__ import annotations

import csv
import math
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .events import EventType, KMCEvent
from .filament import FilamentState
from .lattice import LatticeGrid, LatticeState
from .parameters import KMCConfig
from .resistance import ResistanceModel


@dataclass
class KMCResult:
    """Result container for the single-case KMC SET simulation."""

    voltage_v: float
    temperature_k: float
    random_seed: int
    set_reached: bool
    set_time_s: float
    total_events: int
    filament_length_nm: float
    filament_width_nm: float
    ag_ion_count: int
    filament_site_count: int
    final_morphology: List[List[str]]
    event_log: List[dict]
    filament_state: Optional[FilamentState] = None
    conduction_proxy_ohm: Optional[float] = None


class KMCEngine:
    """Coarse-grained lattice KMC engine for a single SET test case."""

    def __init__(self, config: Optional[KMCConfig] = None):
        self.config = config or KMCConfig()
        self.rng = random.Random(self.config.random_seed)
        self.lattice = LatticeGrid(
            rows=self.config.lattice_rows,
            cols=self.config.lattice_columns,
            thickness_nm=self.config.switching_layer_thickness_nm,
            cell_size_nm=self.config.cell_size_nm,
        )
        self.event_log: List[dict] = []
        self.state_snapshots: List[dict] = []
        self.total_time_s = 0.0
        self.total_events = 0
        self.set_reached = False
        self.electric_field_v_m = self.config.applied_voltage_v / (self.config.switching_layer_thickness_nm * 1e-9)
        self.diagnostic_counters: Dict[str, float] = {}
        self.rate_contributions: Dict[str, float] = {}
        self.rate_candidate_counts: Dict[str, int] = {}
        self.diagnostic_history: List[dict] = []
        self.nucleation_sites: List[tuple[int, int]] = []
        self.nucleation_snapshot_recorded = False
        self.growth_snapshot_recorded = False
        self.near_set_snapshot_recorded = False
        self._reset_diagnostics()

    def _reset_diagnostics(self) -> None:
        self.diagnostic_counters = {
            "ag_generation_events": 0,
            "ag_hopping_events": 0,
            "nucleation_events": 0,
            "successful_ag_deposition_events": 0,
            "failed_deposition_attempts": 0,
            "filament_site_creation_events": 0,
            "filament_growth_events": 0,
            "final_filament_depth_row": 0,
            "deposition_candidates": 0,
            "deposition_blocked_no_nucleus": 0,
            "max_ag_ion_depth_row": 1,
            "max_filament_depth_row": 0,
            "growth_candidates": 0,
            "growth_successes": 0,
            "growth_candidate_rate_sum": 0.0,
            "growth_success_rate_sum": 0.0,
            "hopping_candidates": 0,
            "hopping_successes": 0,
            "hopping_candidate_rate_sum": 0.0,
            "hopping_success_rate_sum": 0.0,
            "growth_barrier_sum_ev": 0.0,
            "hopping_barrier_sum_ev": 0.0,
        }
        self.rate_contributions = {event_type.value: 0.0 for event_type in EventType}
        self.rate_candidate_counts = {event_type.value: 0 for event_type in EventType}
        self.diagnostic_history = []
        self.nucleation_sites = []
        self.nucleation_snapshot_recorded = False
        self.growth_snapshot_recorded = False
        self.near_set_snapshot_recorded = False

    def initialize(self) -> None:
        self.lattice = LatticeGrid(
            rows=self.config.lattice_rows,
            cols=self.config.lattice_columns,
            thickness_nm=self.config.switching_layer_thickness_nm,
            cell_size_nm=self.config.cell_size_nm,
        )
        self.event_log = []
        self.state_snapshots = []
        self.total_time_s = 0.0
        self.total_events = 0
        self.set_reached = False
        self._reset_diagnostics()

        for col in range(self.config.lattice_columns):
            self.lattice.set_state(0, col, LatticeState.AG_ELECTRODE)
            self.lattice.set_state(self.config.lattice_rows - 1, col, LatticeState.PT_ELECTRODE)

        for row in range(1, self.config.lattice_rows - 1):
            for col in range(self.config.lattice_columns):
                self.lattice.set_state(row, col, LatticeState.EMPTY)

        center_col = self.config.lattice_columns // 2
        self.lattice.set_state(0, center_col, LatticeState.AG_ELECTRODE)
        self.lattice.set_state(1, center_col, LatticeState.AG_ION)

    def _effective_barrier_ev(self, activation_energy_ev: float, source_row: int, target_row: int) -> float:
        """Apply the symmetric field term required by detailed balance."""
        if source_row == target_row:
            return max(1e-6, activation_energy_ev)

        field_energy_ev = abs(self.electric_field_v_m) * self.config.cell_size_nm * 1e-9
        direction = 1.0 if target_row > source_row else -1.0
        # A field lowers the barrier for motion in the direction of the applied
        # electric force and raises it for the opposite direction. The reduction is
        # limited to half the electrostatic work over the hop to keep the forward
        # and reverse rates consistent with detailed balance.
        barrier = activation_energy_ev - self.config.field_factor * direction * 0.5 * field_energy_ev
        return max(1e-6, barrier)

    def _rate_factor(
        self,
        target_state: str,
        source_row: int,
        target_row: int,
        activation_energy_ev: Optional[float] = None,
        attempt_frequency_hz: Optional[float] = None,
    ) -> float:
        activation_energy_ev = activation_energy_ev or self.config.activation_energy_ev
        attempt_frequency_hz = attempt_frequency_hz or self.config.attempt_frequency_hz
        effective_barrier_ev = self._effective_barrier_ev(activation_energy_ev, source_row, target_row)
        base = attempt_frequency_hz * math.exp(
            -(effective_barrier_ev * 1.602176634e-19)
            / (1.380649e-23 * self.config.temperature_k)
        )
        if target_state == LatticeState.AG_FILAMENT:
            return base * self.config.deposition_bias
        return base

    def _base_rate_hz(self) -> float:
        return self.config.attempt_frequency_hz * math.exp(
            -(self._effective_barrier_ev(self.config.activation_energy_ev, 1, 2) * 1.602176634e-19)
            / (1.380649e-23 * self.config.temperature_k)
        )

    def _nucleation_rate(self, row: int) -> float:
        return self._rate_factor(
            LatticeState.AG_FILAMENT,
            row,
            row + 1,
            activation_energy_ev=self.config.nucleation_activation_energy_ev,
            attempt_frequency_hz=self.config.nucleation_attempt_frequency_hz,
        )

    def _growth_candidates_for_ion(self, row: int, col: int) -> List[tuple[int, int]]:
        """Return filament sites eligible to support this ion under the configured diagnostic rule."""
        if self.config.growth_spatial_rule == "4-neighbor":
            candidate_sites = self.lattice.neighbors(row, col)
        elif self.config.growth_spatial_rule == "8-neighbor":
            candidate_sites = [
                (r2, c2)
                for r2 in range(max(0, row - 1), min(self.config.lattice_rows, row + 2))
                for c2 in range(max(0, col - 1), min(self.config.lattice_columns, col + 2))
                if (r2, c2) != (row, col)
            ]
        elif self.config.growth_spatial_rule == "manhattan-2":
            candidate_sites = [
                (r2, c2)
                for r2 in range(self.config.lattice_rows)
                for c2 in range(self.config.lattice_columns)
                if (r2, c2) != (row, col) and abs(r2 - row) + abs(c2 - col) <= self.config.growth_reach_distance
            ]
        else:
            raise ValueError(f"Unknown growth spatial rule: {self.config.growth_spatial_rule}")
        return [
            site
            for site in candidate_sites
            if self.lattice.get_state(*site) == LatticeState.AG_FILAMENT
        ]

    def _build_events(self) -> List[KMCEvent]:
        events: List[KMCEvent] = []

        for row in range(self.config.lattice_rows):
            for col in range(self.config.lattice_columns):
                state = self.lattice.get_state(row, col)
                if state == LatticeState.AG_ELECTRODE:
                    for neighbor in self.lattice.neighbors(row, col):
                        r2, c2 = neighbor
                        if r2 == row + 1 and self.lattice.get_state(r2, c2) == LatticeState.EMPTY:
                            rate = self._rate_factor(LatticeState.AG_ION, row, r2)
                            events.append(
                                KMCEvent(
                                    event_type=EventType.AG_GENERATION,
                                    source_site=(row, col),
                                    target_site=(r2, c2),
                                    rate=rate,
                                    notes="Ag+ injection from Ag electrode",
                                )
                            )
                        elif r2 == row + 1 and self.lattice.get_state(r2, c2) == LatticeState.AG_ION:
                            self.diagnostic_counters["deposition_blocked_no_nucleus"] += 1

                if state == LatticeState.AG_ION:
                    if row == 1:
                        events.append(
                            KMCEvent(
                                event_type=EventType.AG_NUCLEATION,
                                source_site=(row, col),
                                target_site=(row, col),
                                rate=self._nucleation_rate(row),
                                notes="field-assisted Ag+ reduction at the Ag/PVA interface",
                            )
                        )
                    for neighbor in self.lattice.neighbors(row, col):
                        r2, c2 = neighbor
                        neighbor_state = self.lattice.get_state(r2, c2)
                        if neighbor_state == LatticeState.EMPTY:
                            rate = self._rate_factor(LatticeState.AG_ION, row, r2)
                            events.append(
                                KMCEvent(
                                    event_type=EventType.AG_HOPPING,
                                    source_site=(row, col),
                                    target_site=(r2, c2),
                                    rate=rate,
                                    notes="Ag+ hopping in PVA",
                                )
                            )
                        elif neighbor_state == LatticeState.AG_FILAMENT and self.config.growth_spatial_rule == "4-neighbor":
                            rate = self._rate_factor(
                                LatticeState.AG_FILAMENT,
                                r2,
                                row,
                                activation_energy_ev=self.config.growth_activation_energy_ev,
                            )
                            events.append(
                                KMCEvent(
                                    event_type=EventType.AG_REDUCTION_DEPOSITION,
                                    source_site=(row, col),
                                    target_site=(row, col),
                                    rate=rate,
                                    notes="Ag+ deposition onto filament",
                                )
                            )

                    if self.config.growth_spatial_rule != "4-neighbor":
                        for filament_row, filament_col in self._growth_candidates_for_ion(row, col):
                            rate = self._rate_factor(
                                LatticeState.AG_FILAMENT,
                                filament_row,
                                row,
                                activation_energy_ev=self.config.growth_activation_energy_ev,
                            )
                            events.append(
                                KMCEvent(
                                    event_type=EventType.AG_REDUCTION_DEPOSITION,
                                    source_site=(row, col),
                                    target_site=(filament_row, filament_col),
                                    rate=rate,
                                    notes=f"diagnostic {self.config.growth_spatial_rule} filament deposition",
                                )
                            )

        for event in events:
            if event.event_type == EventType.AG_HOPPING:
                event.effective_barrier_ev = self._effective_barrier_ev(
                    self.config.activation_energy_ev,
                    event.source_site[0],
                    event.target_site[0],
                )
            elif event.event_type == EventType.AG_NUCLEATION:
                event.effective_barrier_ev = self._effective_barrier_ev(
                    self.config.nucleation_activation_energy_ev,
                    event.source_site[0],
                    event.source_site[0] + 1,
                )
            elif event.event_type == EventType.AG_REDUCTION_DEPOSITION:
                event.rate *= self.config.growth_rate_multiplier
                event.effective_barrier_ev = self._effective_barrier_ev(
                    self.config.growth_activation_energy_ev,
                    event.target_site[0],
                    event.source_site[0],
                )
            event_name = event.event_type.value
            self.rate_contributions[event_name] += event.rate
            self.rate_candidate_counts[event_name] += 1
            if event.event_type == EventType.AG_HOPPING:
                self.diagnostic_counters["hopping_candidates"] += 1
                self.diagnostic_counters["hopping_candidate_rate_sum"] += event.rate
                self.diagnostic_counters["hopping_barrier_sum_ev"] += event.effective_barrier_ev
            elif event.event_type == EventType.AG_REDUCTION_DEPOSITION:
                self.diagnostic_counters["growth_candidates"] += 1
                self.diagnostic_counters["growth_candidate_rate_sum"] += event.rate
                self.diagnostic_counters["growth_barrier_sum_ev"] += event.effective_barrier_ev
            if event.event_type == EventType.AG_REDUCTION_DEPOSITION:
                self.diagnostic_counters["deposition_candidates"] += 1

        return events

    def _select_event(self, events: List[KMCEvent]) -> KMCEvent:
        total_rate = sum(event.rate for event in events)
        if total_rate <= 0.0:
            raise ValueError("No valid KMC events available.")
        threshold = self.rng.random() * total_rate
        cumulative = 0.0
        for event in events:
            cumulative += event.rate
            if cumulative >= threshold:
                return event
        return events[-1]

    def _apply_event(self, event: KMCEvent) -> None:
        if event.event_type == EventType.AG_GENERATION and event.target_site is not None:
            r, c = event.target_site
            self.lattice.set_state(r, c, LatticeState.AG_ION)
            self.diagnostic_counters["ag_generation_events"] += 1
            return

        if event.event_type == EventType.AG_HOPPING and event.source_site and event.target_site:
            r1, c1 = event.source_site
            r2, c2 = event.target_site
            if self.lattice.get_state(r1, c1) == LatticeState.AG_ION and self.lattice.get_state(r2, c2) == LatticeState.EMPTY:
                self.lattice.set_state(r1, c1, LatticeState.EMPTY)
                self.lattice.set_state(r2, c2, LatticeState.AG_ION)
                self.diagnostic_counters["ag_hopping_events"] += 1
                self.diagnostic_counters["hopping_successes"] += 1
                self.diagnostic_counters["hopping_success_rate_sum"] += event.rate
            return

        if event.event_type == EventType.AG_NUCLEATION and event.source_site:
            r, c = event.source_site
            if self.lattice.get_state(r, c) == LatticeState.AG_ION and r == 1:
                self.lattice.set_state(r, c, LatticeState.AG_FILAMENT)
                self.diagnostic_counters["nucleation_events"] += 1
                self.diagnostic_counters["filament_site_creation_events"] += 1
                self.nucleation_sites.append((r, c))
                if not self.nucleation_snapshot_recorded:
                    self._record_snapshot("nucleation")
                    self.nucleation_snapshot_recorded = True
            else:
                self.diagnostic_counters["failed_deposition_attempts"] += 1
            return

        if event.event_type == EventType.AG_REDUCTION_DEPOSITION and event.source_site:
            r, c = event.source_site
            if self.lattice.get_state(r, c) == LatticeState.AG_ION:
                had_filament_neighbor = bool(self._growth_candidates_for_ion(r, c))
                self.lattice.set_state(r, c, LatticeState.AG_FILAMENT)
                self.diagnostic_counters["successful_ag_deposition_events"] += 1
                self.diagnostic_counters["filament_site_creation_events"] += 1
                self.diagnostic_counters["filament_growth_events"] += 1
                self.diagnostic_counters["growth_successes"] += 1
                self.diagnostic_counters["growth_success_rate_sum"] += event.rate
                if had_filament_neighbor and not self.growth_snapshot_recorded:
                    self.growth_snapshot_recorded = True
            else:
                self.diagnostic_counters["failed_deposition_attempts"] += 1
            return

    def _update_depth_diagnostics(self) -> None:
        ion_rows = [
            row
            for row in range(self.config.lattice_rows)
            for col in range(self.config.lattice_columns)
            if self.lattice.get_state(row, col) == LatticeState.AG_ION
        ]
        filament_rows = [
            row
            for row in range(self.config.lattice_rows)
            for col in range(self.config.lattice_columns)
            if self.lattice.get_state(row, col) == LatticeState.AG_FILAMENT
        ]
        if ion_rows:
            self.diagnostic_counters["max_ag_ion_depth_row"] = max(
                self.diagnostic_counters["max_ag_ion_depth_row"], max(ion_rows)
            )
        if filament_rows:
            self.diagnostic_counters["max_filament_depth_row"] = max(
                self.diagnostic_counters["max_filament_depth_row"], max(filament_rows)
            )
            self.diagnostic_counters["final_filament_depth_row"] = max(filament_rows)

    def _record_diagnostic_history(self) -> None:
        self._update_depth_diagnostics()
        self.diagnostic_history.append(
            {
                "event_count": self.total_events,
                "time_s": self.total_time_s,
                "matrix": self.lattice.snapshot_matrix(),
            }
        )

    def _check_set_condition(self) -> bool:
        return self._connected_filament_cluster()

    def _connected_filament_cluster(self) -> bool:
        """Return True only if a single filament cluster spans from the Ag electrode to the Pt electrode."""
        start_sites = [
            (1, col)
            for col in range(self.config.lattice_columns)
            if self.lattice.get_state(1, col) == LatticeState.AG_FILAMENT
            and self.lattice.get_state(0, col) == LatticeState.AG_ELECTRODE
        ]
        if not start_sites:
            return False

        stack = list(start_sites)
        visited: set[tuple[int, int]] = set()
        while stack:
            cell = stack.pop()
            if cell in visited:
                continue
            visited.add(cell)
            for neighbor in self.lattice.neighbors(cell[0], cell[1]):
                if self.lattice.get_state(*neighbor) == LatticeState.AG_FILAMENT and neighbor not in visited:
                    stack.append(neighbor)

        bottom_row = self.config.lattice_rows - 2
        return any((bottom_row, col) in visited for col in range(self.config.lattice_columns))

    def _extract_filament_state(self) -> FilamentState:
        filament_positions = [
            (row, col)
            for row in range(self.config.lattice_rows)
            for col in range(self.config.lattice_columns)
            if self.lattice.get_state(row, col) == LatticeState.AG_FILAMENT
        ]
        if not filament_positions:
            return FilamentState(length_nm=0.0, width_nm=0.0, connection_status="not connected")

        row_values = [row for row, _ in filament_positions]
        col_values = [col for _, col in filament_positions]
        length_nm = (max(row_values) - min(row_values) + 1) * self.config.cell_size_nm
        width_nm = (max(col_values) - min(col_values) + 1) * self.config.cell_size_nm
        connected = self._check_set_condition()
        return FilamentState(
            start_site=(min(row_values), min(col_values)),
            end_site=(max(row_values), max(col_values)),
            occupied_sites=filament_positions,
            length_nm=length_nm,
            width_nm=width_nm,
            connection_status="connected" if connected else "partial",
            connectivity="top-to-bottom" if connected else "incomplete",
            metal_fraction=len(filament_positions) / (self.config.lattice_rows * self.config.lattice_columns),
        )

    def _record_snapshot(self, label: str) -> None:
        self.state_snapshots.append(
            {
                "label": label,
                "event_count": self.total_events,
                "time_s": self.total_time_s,
                "matrix": self.lattice.snapshot_matrix(),
            }
        )

    def run(self) -> KMCResult:
        self.initialize()
        self._record_snapshot("initial")
        self._record_diagnostic_history()
        max_events = self.config.max_kmc_events
        snapshot_targets = {
            0: "initial",
            int(max_events * 0.25): "25pct",
            int(max_events * 0.50): "50pct",
            int(max_events * 0.75): "75pct",
        }

        while self.total_events < max_events:
            events = self._build_events()
            if not events:
                break
            total_rate = sum(event.rate for event in events)
            if total_rate <= 0:
                break
            chosen_event = self._select_event(events)
            tau = -math.log(self.rng.random()) / total_rate
            self.total_time_s += tau
            self._apply_event(chosen_event)
            self.total_events += 1
            if self.total_events % 100 == 0:
                self._record_diagnostic_history()

            self.event_log.append(
                {
                    "event_number": self.total_events,
                    "time_s": self.total_time_s,
                    "event_type": chosen_event.event_type.value,
                    "source_site": chosen_event.source_site,
                    "target_site": chosen_event.target_site,
                    "rate": chosen_event.rate,
                    "ag_ion_count": self.lattice.count_state(LatticeState.AG_ION),
                    "filament_site_count": self.lattice.count_state(LatticeState.AG_FILAMENT),
                }
            )

            if self.growth_snapshot_recorded and not any(
                snapshot["label"] == "early growth" for snapshot in self.state_snapshots
            ):
                self._record_snapshot("early growth")
            if (
                self.diagnostic_counters["filament_growth_events"] > 0
                and self.total_events >= int(max_events * 0.50)
                and not any(snapshot["label"] == "mid growth" for snapshot in self.state_snapshots)
            ):
                self._record_snapshot("mid growth")
            if (
                self.diagnostic_counters["max_filament_depth_row"] >= self.config.lattice_rows - 3
                and not self.near_set_snapshot_recorded
            ):
                self._record_snapshot("near SET")
                self.near_set_snapshot_recorded = True

            event_target = snapshot_targets.get(self.total_events)
            if event_target is not None:
                self._record_snapshot(event_target)

            if self._check_set_condition():
                self.set_reached = True
                self._record_snapshot("SET")
                self._record_snapshot("set")
                break

        self._record_snapshot("final")
        filament_state = self._extract_filament_state()
        self._record_diagnostic_history()
        conduction_model = ResistanceModel(
            filament_length_nm=filament_state.length_nm,
            filament_width_nm=filament_state.width_nm,
        )
        conduction_model.resistance_ohm = 1e3 if self.set_reached else 1e6
        conduction_model.conductivity_proxy = 1.0 / conduction_model.resistance_ohm if conduction_model.resistance_ohm else None

        return KMCResult(
            voltage_v=self.config.applied_voltage_v,
            temperature_k=self.config.temperature_k,
            random_seed=self.config.random_seed,
            set_reached=self.set_reached,
            set_time_s=self.total_time_s,
            total_events=self.total_events,
            filament_length_nm=filament_state.length_nm,
            filament_width_nm=filament_state.width_nm,
            ag_ion_count=self.lattice.count_state(LatticeState.AG_ION),
            filament_site_count=self.lattice.count_state(LatticeState.AG_FILAMENT),
            final_morphology=self.lattice.snapshot_matrix(),
            event_log=self.event_log,
            filament_state=filament_state,
            conduction_proxy_ohm=conduction_model.resistance_ohm,
        )

    def save_diagnostics_csv(self, output_path: Path) -> None:
        """Write event counts, rate magnitudes, field terms, and final state metrics."""
        fieldnames = ["record_type", "name", "value", "units", "notes"]
        with output_path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()

            for event_type in EventType:
                name = event_type.value
                candidate_count = self.rate_candidate_counts[name]
                writer.writerow(
                    {
                        "record_type": "event_rate",
                        "name": name,
                        "value": self.rate_contributions[name],
                        "units": "Hz summed over event-list builds",
                        "notes": f"candidate_count={candidate_count}; mean_candidate_rate_hz={self.rate_contributions[name] / candidate_count if candidate_count else 0.0}; selected_count={self._selected_event_count(event_type)}",
                    }
                )

            diagnostic_values = {
                **self.diagnostic_counters,
                **self.growth_diagnostics(),
                "total_events": self.total_events,
                "total_time_s": self.total_time_s,
                "final_ag_ion_sites": self.lattice.count_state(LatticeState.AG_ION),
                "final_filament_sites": self.lattice.count_state(LatticeState.AG_FILAMENT),
                "electric_field_v_m": self.electric_field_v_m,
                "effective_activation_energy_ev": self.config.activation_energy_ev,
                "effective_hop_barrier_ev": self._effective_barrier_ev(self.config.activation_energy_ev, 1, 2),
                "effective_nucleation_barrier_ev": self._effective_barrier_ev(self.config.nucleation_activation_energy_ev, 1, 2),
                "effective_growth_barrier_ev": self._effective_barrier_ev(self.config.growth_activation_energy_ev, 1, 2),
                "base_activated_rate_hz": self._base_rate_hz(),
                "total_candidate_rate_contribution_hz_sum": sum(self.rate_contributions.values()),
                "field_factor_configured": self.config.field_factor,
                "field_term_used_in_rate": 1,
                "mean_kmc_time_increment_s": self.total_time_s / self.total_events if self.total_events else 0.0,
                "cell_size_m": self.config.cell_size_nm * 1e-9,
                "physical_thickness_m": self.config.switching_layer_thickness_nm * 1e-9,
                "voltage_v": self.config.applied_voltage_v,
                "temperature_k": self.config.temperature_k,
                "random_seed": self.config.random_seed,
                "first_nucleation_row": self.nucleation_sites[0][0] if self.nucleation_sites else -1,
                "first_nucleation_col": self.nucleation_sites[0][1] if self.nucleation_sites else -1,
            }
            for name, value in diagnostic_values.items():
                notes = ""
                if name == "electric_field_v_m":
                    notes = "E = V / d; uniform-field approximation"
                elif name == "field_term_used_in_rate":
                    notes = "field-assisted barrier term is applied and clamped positive"
                elif name == "max_ag_ion_depth_row":
                    notes = "row 0 is Ag electrode; row 24 is Pt electrode"
                elif name == "max_filament_depth_row":
                    notes = "filament remains in PVA; SET boundary is row 23"
                writer.writerow(
                    {
                        "record_type": "summary",
                        "name": name,
                        "value": value,
                        "units": "",
                        "notes": notes,
                    }
                )

    def growth_diagnostics(self) -> dict:
        """Return growth-versus-hopping diagnostics for the completed run."""
        final_adjacent_ions = 0
        final_empty_growth_sites = 0
        final_growth_rates: List[float] = []
        for row in range(self.config.lattice_rows):
            for col in range(self.config.lattice_columns):
                state = self.lattice.get_state(row, col)
                if state != LatticeState.AG_ION:
                    continue
                neighbors = self.lattice.neighbors(row, col)
                if any(self.lattice.get_state(*neighbor) == LatticeState.AG_FILAMENT for neighbor in neighbors):
                    final_adjacent_ions += 1
                    final_growth_rates.append(
                        self._rate_factor(
                            LatticeState.AG_FILAMENT,
                            next(neighbor[0] for neighbor in neighbors if self.lattice.get_state(*neighbor) == LatticeState.AG_FILAMENT),
                            row,
                            activation_energy_ev=self.config.growth_activation_energy_ev,
                        ) * self.config.growth_rate_multiplier
                    )
        for row in range(self.config.lattice_rows):
            for col in range(self.config.lattice_columns):
                if self.lattice.get_state(row, col) == LatticeState.EMPTY and any(
                    self.lattice.get_state(*neighbor) == LatticeState.AG_FILAMENT
                    for neighbor in self.lattice.neighbors(row, col)
                ):
                    final_empty_growth_sites += 1
        growth_candidates = self.diagnostic_counters["growth_candidates"]
        hopping_candidates = self.diagnostic_counters["hopping_candidates"]
        mean_growth_rate = self.diagnostic_counters["growth_candidate_rate_sum"] / growth_candidates if growth_candidates else 0.0
        mean_hopping_rate = self.diagnostic_counters["hopping_candidate_rate_sum"] / hopping_candidates if hopping_candidates else 0.0
        return {
            "growth_candidates": growth_candidates,
            "growth_successes": self.diagnostic_counters["growth_successes"],
            "growth_candidate_rate_sum": self.diagnostic_counters["growth_candidate_rate_sum"],
            "growth_success_rate_sum": self.diagnostic_counters["growth_success_rate_sum"],
            "hopping_candidates": hopping_candidates,
            "hopping_successes": self.diagnostic_counters["hopping_successes"],
            "hopping_candidate_rate_sum": self.diagnostic_counters["hopping_candidate_rate_sum"],
            "mean_growth_rate": mean_growth_rate,
            "mean_hopping_rate": mean_hopping_rate,
            "growth_to_hopping_rate_ratio": mean_growth_rate / mean_hopping_rate if mean_hopping_rate else 0.0,
            "growth_rate_fraction_of_active_rate": self.diagnostic_counters["growth_candidate_rate_sum"] / sum(self.rate_contributions.values()) if sum(self.rate_contributions.values()) else 0.0,
            "mean_growth_effective_barrier_ev": self.diagnostic_counters["growth_barrier_sum_ev"] / growth_candidates if growth_candidates else 0.0,
            "mean_hopping_effective_barrier_ev": self.diagnostic_counters["hopping_barrier_sum_ev"] / hopping_candidates if hopping_candidates else 0.0,
            "number_of_Ag_plus_adjacent_to_filament": final_adjacent_ions,
            "number_of_empty_growth_sites": final_empty_growth_sites,
            "final_growth_candidate_rates": ";".join(f"{rate:.8g}" for rate in final_growth_rates),
            "number_of_filament_sites": self.lattice.count_state(LatticeState.AG_FILAMENT),
            "growth_rate_multiplier": self.config.growth_rate_multiplier,
        }

    def _selected_event_count(self, event_type: EventType) -> int:
        return sum(1 for event in self.event_log if event["event_type"] == event_type.value)

    def save_diagnostics_figure(self, output_path: Path) -> None:
        """Plot actual lattice states nearest 10%, 25%, 50%, 75%, and 100%."""
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.colors import ListedColormap

        if not self.diagnostic_history:
            return
        final_events = self.total_events
        targets = [("10%", 0.10), ("25%", 0.25), ("50%", 0.50), ("75%", 0.75), ("100%", 1.00)]
        selected = []
        for label, fraction in targets:
            target = final_events * fraction
            snapshot = min(self.diagnostic_history, key=lambda item: abs(item["event_count"] - target))
            selected.append((label, snapshot))

        state_values = {
            LatticeState.EMPTY: 0,
            LatticeState.AG_ION: 1,
            LatticeState.AG_FILAMENT: 2,
            LatticeState.AG_ELECTRODE: 3,
            LatticeState.PT_ELECTRODE: 4,
        }
        colors = ["white", "#2f80ed", "#d94841", "#9b59b6", "#303030"]
        figure, axes = plt.subplots(1, len(selected), figsize=(16, 5), squeeze=False)
        for axis, (label, snapshot) in zip(axes[0], selected):
            image = [[state_values[cell] for cell in row] for row in snapshot["matrix"]]
            axis.imshow(image, cmap=ListedColormap(colors), vmin=0, vmax=4, interpolation="none", aspect="auto")
            axis.set_title(f"{label}\n{snapshot['event_count']} events")
            axis.set_xlabel("lateral cell")
            axis.set_xticks([])
            axis.set_yticks([0, self.config.lattice_rows - 1])
            axis.set_yticklabels(["Ag", "Pt"])
        figure.suptitle("0.30 V / 300 K / seed 42: actual KMC lattice states")
        figure.tight_layout()
        figure.savefig(output_path, dpi=180, facecolor="white")
        plt.close(figure)

    def save_states_csv(self, output_path: Path) -> None:
        fieldnames = ["stage", "event_count", "time_s", "ag_ion_count", "filament_site_count", "grid"]
        with output_path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for snapshot in self.state_snapshots:
                grid_str = "|".join(
                    ";".join(row) for row in snapshot["matrix"]
                )
                writer.writerow(
                    {
                        "stage": snapshot["label"],
                        "event_count": snapshot["event_count"],
                        "time_s": snapshot["time_s"],
                        "ag_ion_count": sum(cell == LatticeState.AG_ION for row in snapshot["matrix"] for cell in row),
                        "filament_site_count": sum(cell == LatticeState.AG_FILAMENT for row in snapshot["matrix"] for cell in row),
                        "grid": grid_str,
                    }
                )

    def save_process_figure(self, output_path: Path) -> None:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from matplotlib.colors import ListedColormap

        state_values = {
            LatticeState.EMPTY: 0,
            LatticeState.AG_ION: 1,
            LatticeState.AG_FILAMENT: 2,
            LatticeState.AG_ELECTRODE: 3,
            LatticeState.PT_ELECTRODE: 4,
        }
        colors = ["white", "#2f80ed", "#d94841", "#9b59b6", "#303030"]
        figure, axes = plt.subplots(1, len(self.state_snapshots), figsize=(20, 4), squeeze=False)
        for axis, snapshot in zip(axes[0], self.state_snapshots):
            matrix = snapshot["matrix"]
            image = [[state_values[cell] for cell in row] for row in matrix]
            axis.imshow(image, cmap=ListedColormap(colors), vmin=0, vmax=4, interpolation="none", aspect="auto")
            axis.set_title(f"{snapshot['label']}\n{snapshot['event_count']} events")
            axis.set_xticks([])
            axis.set_yticks([0, self.config.lattice_rows - 2, self.config.lattice_rows - 1])
            axis.set_yticklabels(["Ag", "PVA/Pt", "Pt"])
        figure.suptitle("0.30 V / 300 K / seed 42: KMC nucleation and filament growth")
        figure.tight_layout()
        figure.savefig(output_path, dpi=180, facecolor="white")
        plt.close(figure)
