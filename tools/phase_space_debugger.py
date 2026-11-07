"""Phase Space Tracer & Memory Heatmap Profiler for Malbolge-PureEpoch.

Visualizes and audits:
1. Toroidal pointer separation delta(t) = min(|C - D|, 59049 - |C - D|).
2. Segmented activity heatmap across the 59,049-cell memory space.
3. Classification of cells: Code, Read-Data, Written-Data, and Collisions.
4. Exportable audit reports for Boss battles and new candidates.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
from pathlib import Path
import sys
from typing import Dict, List, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from baseline.epoch_probe import Machine, MEM_SIZE, XLAT1, XLAT2, VALID, crazy
from tools.observe import load, run

MIN_SAFE_DELTA = 42


@dataclass
class PhaseSpaceProfile:
    source_path: str
    total_steps: int
    terminal: str
    min_toroidal_delta: int
    max_toroidal_delta: int
    avg_toroidal_delta: float
    violations_count: int
    code_cells_count: int
    data_read_cells_count: int
    data_written_cells_count: int
    collision_cells_count: int
    heatmap_bins: List[int] = field(default_factory=list)


class PhaseSpaceDebugger:
    """Executes and profiles the geometric trajectory of a Malbolge program."""

    def __init__(self, min_delta: int = MIN_SAFE_DELTA, num_bins: int = 64):
        self.min_delta = min_delta
        self.num_bins = num_bins

    def profile_execution(self, source_bytes: bytes, payload: bytes = b"", max_steps: int = 50000) -> PhaseSpaceProfile:
        cells = load(source_bytes)
        vm = Machine(cells, payload)

        deltas: List[int] = []
        code_cells: Set[int] = set()
        data_read_cells: Set[int] = set()
        data_written_cells: Set[int] = set()
        violations: int = 0

        # Memory activity counter for bins
        bin_size = (MEM_SIZE + self.num_bins - 1) // self.num_bins
        activity_bins = [0] * self.num_bins

        for step in range(max_steps):
            if vm.terminal != "RUNNING":
                break
            
            c_pos = vm.c
            d_pos = vm.d
            
            # Record distance
            diff = abs(c_pos - d_pos)
            torus_dist = min(diff, MEM_SIZE - diff)
            deltas.append(torus_dist)
            if torus_dist < self.min_delta:
                violations += 1

            # Mark code cell
            code_cells.add(c_pos)
            activity_bins[c_pos // bin_size] += 1

            # Read before state
            v = vm.mem[c_pos]
            if not 33 <= v <= 126:
                vm.terminal = "STALL"
                break
            instr = XLAT1[(v - 33 + c_pos) % 94]

            if instr in ('*', 'p'):
                data_read_cells.add(d_pos)
                data_written_cells.add(d_pos)
                activity_bins[d_pos // bin_size] += 1
            elif instr in ('j', 'i'):
                data_read_cells.add(d_pos)
                activity_bins[d_pos // bin_size] += 1

            vm.tick()

        min_d = min(deltas) if deltas else 0
        max_d = max(deltas) if deltas else 0
        avg_d = sum(deltas) / len(deltas) if deltas else 0.0
        collisions = len(code_cells.intersection(data_written_cells))

        return PhaseSpaceProfile(
            source_path="<memory>",
            total_steps=vm.steps,
            terminal=vm.terminal,
            min_toroidal_delta=min_d,
            max_toroidal_delta=max_d,
            avg_toroidal_delta=round(avg_d, 2),
            violations_count=violations,
            code_cells_count=len(code_cells),
            data_read_cells_count=len(data_read_cells),
            data_written_cells_count=len(data_written_cells),
            collision_cells_count=collisions,
            heatmap_bins=activity_bins,
        )

    def render_ascii_heatmap(self, profile: PhaseSpaceProfile) -> str:
        """Render a 64-character ASCII intensity bar graph."""
        chars = " .:-=+*#%@"
        max_val = max(profile.heatmap_bins) if profile.heatmap_bins else 1
        if max_val == 0:
            max_val = 1
        bar = []
        for val in profile.heatmap_bins:
            idx = int((val / max_val) * (len(chars) - 1))
            bar.append(chars[idx])
        return "[" + "".join(bar) + "]"


def main():
    parser = argparse.ArgumentParser(description="Phase Space Debugger & Profiler")
    parser.add_argument("program", help="Path to .mal source file")
    parser.add_argument("-p", "--payload", default="", help="Input payload string")
    parser.add_argument("-b", "--budget", type=int, default=50000, help="Max step budget")
    parser.add_argument("--json", action="store_true", help="Output raw JSON profile")
    args = parser.parse_args()

    prog_path = Path(args.program)
    if not prog_path.exists():
        print(f"Error: file not found {args.program}", file=sys.stderr)
        sys.exit(1)

    src = prog_path.read_bytes()
    debugger = PhaseSpaceDebugger()
    profile = debugger.profile_execution(src, args.payload.encode("utf-8"), args.budget)
    profile.source_path = str(prog_path)

    if args.json:
        data = {
            "source": profile.source_path,
            "steps": profile.total_steps,
            "terminal": profile.terminal,
            "min_delta": profile.min_toroidal_delta,
            "max_delta": profile.max_toroidal_delta,
            "avg_delta": profile.avg_toroidal_delta,
            "violations": profile.violations_count,
            "code_cells": profile.code_cells_count,
            "data_read": profile.data_read_cells_count,
            "data_written": profile.data_written_cells_count,
            "collisions": profile.collision_cells_count,
            "heatmap": debugger.render_ascii_heatmap(profile),
        }
        print(json.dumps(data, indent=2))
    else:
        print("=" * 60)
        print(f"Phase Space Profile: {prog_path.name}")
        print("=" * 60)
        print(f"Terminal:              {profile.terminal} ({profile.total_steps} steps)")
        print(f"Toroidal Delta min/avg: {profile.min_toroidal_delta} / {profile.avg_toroidal_delta:.1f}")
        print(f"Code cells executed:   {profile.code_cells_count}")
        print(f"Data cells read:       {profile.data_read_cells_count}")
        print(f"Data cells written:    {profile.data_written_cells_count}")
        print(f"C/D Collisions:        {profile.collision_cells_count}")
        print(f"Heatmap (59k mem):     {debugger.render_ascii_heatmap(profile)}")
        print("=" * 60)


if __name__ == "__main__":
    main()
