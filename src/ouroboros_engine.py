"""Ouroboros Loop Engine: Periodic Self-Restoring Computation in Malbolge.

Harnesses the exact cycle decomposition of XLAT2 (6 cycles of lengths 68, 9, 6, 5, 4, 2)
to synthesize autonomous periodic loops that return to their exact initial opcode state
without active memory rewrites (* or crazy) from outside.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from baseline.epoch_probe import XLAT1, XLAT2, VALID, MEM_SIZE
from tools.build_candidates import encode, strict_byte


@dataclass(frozen=True)
class XlatCycle:
    cycle_id: int
    length: int
    chars: str
    bytes: Tuple[int, ...]


def compute_xlat2_cycles() -> List[XlatCycle]:
    """Decompose the 94 printable ASCII characters under XLAT2 encryption."""
    visited = set()
    cycles = []
    cycle_id = 0
    for idx in range(94):
        if idx in visited:
            continue
        cycle_chars = []
        cycle_bytes = []
        cur = idx
        while cur not in visited:
            visited.add(cur)
            ch = chr(cur + 33)
            cycle_chars.append(ch)
            cycle_bytes.append(cur + 33)
            nxt_ch = XLAT2[cur]
            cur = ord(nxt_ch) - 33
        cycles.append(
            XlatCycle(
                cycle_id=cycle_id,
                length=len(cycle_chars),
                chars="".join(cycle_chars),
                bytes=tuple(cycle_bytes),
            )
        )
        cycle_id += 1
    cycles.sort(key=lambda c: c.length, reverse=True)
    return cycles


CYCLES = compute_xlat2_cycles()
BYTE_TO_CYCLE: Dict[int, Tuple[XlatCycle, int]] = {}
for c in CYCLES:
    for offset, b in enumerate(c.bytes):
        BYTE_TO_CYCLE[b] = (c, offset)


class OuroborosEngine:
    """Calculates orbital periodicities and generates self-restoring loops."""

    def __init__(self):
        self.cycles = CYCLES
        self.byte_map = BYTE_TO_CYCLE

    def get_orbit(self, initial_byte: int) -> Tuple[XlatCycle, int]:
        """Return the cycle and phase offset for a given byte."""
        if initial_byte not in self.byte_map:
            raise ValueError(f"Byte {initial_byte} outside printable ASCII range 33..126")
        return self.byte_map[initial_byte]

    def opcode_trajectory(self, initial_byte: int, pos: int, count: int) -> List[str]:
        """Compute the sequence of opcodes executed if PC repeatedly visits `pos`."""
        res = []
        cur = initial_byte
        for _ in range(count):
            op = XLAT1[(cur - 33 + pos) % 94]
            res.append(op)
            cur = ord(XLAT2[cur - 33])
        return res

    def find_periodic_nop_sequence(self, length: int = 4) -> List[Tuple[int, int]]:
        """Find (pos, byte) candidates that cycle with length <= 4 and produce only NOPs or valid ops."""
        candidates = []
        for b in range(33, 127):
            cycle, _ = self.get_orbit(b)
            if cycle.length <= length:
                for pos in range(94):
                    if strict_byte(b, pos):
                        candidates.append((pos, b))
        return candidates

    def calculate_loop_restoration_period(self, cell_bytes: List[int]) -> int:
        """Calculate the minimal number of loop passes needed for all cells in `cell_bytes` to restore simultaneously."""
        import math
        lengths = [self.get_orbit(b)[0].length for b in cell_bytes]
        lcm = 1
        for l in lengths:
            lcm = (lcm * l) // math.gcd(lcm, l)
        return lcm
