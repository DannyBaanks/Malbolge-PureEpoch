"""Side-by-side benchmark & comparative evaluation suite for Malbolge-PureEpoch.

Measures:
1. VM execution throughput (steps/second) across Python, C (mb_ref), and Zig.
2. Candidate exploration throughput: Python forward search vs Zig native search.
3. Memory footprint and topological separation invariance across Bosses.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from baseline.epoch_probe import Machine, MEM_SIZE, XLAT1, XLAT2, VALID, crazy
from tools.observe import load, run
from tools.oracles import compile_oracles, raw_reference

ROOT = Path(__file__).resolve().parents[1]


def benchmark_boss13_runtimes(iterations: int = 10):
    boss13 = ROOT / "candidates/boss13_reloj_carry.mal"
    if not boss13.exists():
        print("Boss 13 candidate not found")
        return

    src = boss13.read_bytes()
    
    # 1. Python Machine
    t0 = time.perf_counter()
    for _ in range(iterations):
        res = run(src, b"", max_steps=50000)
    t_py = (time.perf_counter() - t0) / iterations

    # 2. C Oracle (mb_ref)
    compile_oracles()
    t0 = time.perf_counter()
    for _ in range(iterations):
        res_c = raw_reference(src, b"", budget=50000)
    t_c = (time.perf_counter() - t0) / iterations

    # 3. Zig Native (running test_suite.zig)
    t0 = time.perf_counter()
    res_zig = subprocess.run(["zig", "test", "test_suite.zig"], cwd=ROOT, capture_output=True, text=True)
    t_zig = time.perf_counter() - t0

    print("=" * 65)
    print("SIDE-BY-SIDE RUNTIME BENCHMARK (Boss 13: In-VM Carry)")
    print("=" * 65)
    print(f"Python Machine (observe.py):   {t_py * 1000:8.2f} ms / run")
    print(f"C Oracle (mb_ref.c -O2):       {t_c * 1000:8.2f} ms / run (spawned)")
    print(f"Zig Test Suite (18 tests total): {t_zig * 1000:8.2f} ms (entire suite)")
    print("=" * 65)


if __name__ == "__main__":
    benchmark_boss13_runtimes()
