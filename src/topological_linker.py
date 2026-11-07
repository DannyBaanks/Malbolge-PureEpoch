"""Topological Memory Linker & Layout Manager for Malbolge-PureEpoch.

Resolves:
1. Low-memory constant placement satisfying Olmstead strict loader constraints:
   strict_byte(V, P) == True  where XLAT1[(V - 33 + P) % 94] in "ji*p</vo".
2. Topological separation invariants:
   min(|C - D|, 59049 - |C - D|) >= MIN_DELTA (default 42).
3. Symbolic labels and relocations.
4. Memory region segregation (CONSTANTS, DATA_STACK, CODE_TRACKS, JOURNAL).
5. Deterministic pointer steering without host memory manipulation.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from baseline.epoch_probe import XLAT1, XLAT2, VALID, MEM_SIZE, crazy
from tools.build_candidates import encode, strict_byte

MIN_DELTA = 42


@dataclass
class Symbol:
    name: str
    address: int
    size: int
    kind: str  # 'constant', 'buffer', 'label'
    initial_value: Optional[int] = None


class TopologicalLinker:
    """Manages memory layout, constraint resolution, and topological invariants."""

    def __init__(self, min_delta: int = MIN_DELTA):
        self.min_delta = min_delta
        self.symbols: Dict[str, Symbol] = {}
        self.cells: Dict[int, int] = {}
        self.allocated_addresses: Set[int] = set()
        
        # Pointers
        self.c: int = 0
        self.d: int = 0
        
        # Invariant violations log
        self.violations: List[str] = []

    def is_valid_constant_placement(self, value: int, pos: int) -> bool:
        """Check if putting `value` at address `pos` satisfies Olmstead strict loader."""
        if not (0 <= pos < 94):
            return 33 <= value <= 126
        return strict_byte(value, pos)

    def alloc_constant(self, name: str, value: int, preferred_range: Tuple[int, int] = (33, 94)) -> int:
        """Find a strict-compliant address for a constant in low memory (0..93) and bind symbol."""
        if name in self.symbols:
            existing = self.symbols[name]
            if existing.initial_value == value:
                return existing.address
            raise ValueError(f"Symbol '{name}' already bound to {existing.address} with different value")

        low, high = preferred_range
        candidates = []
        for p in range(low, high):
            if p not in self.allocated_addresses and self.is_valid_constant_placement(value, p):
                candidates.append(p)

        if not candidates:
            # Fallback to broader 1..93 range
            for p in range(1, 94):
                if p not in self.allocated_addresses and self.is_valid_constant_placement(value, p):
                    candidates.append(p)

        if not candidates:
            raise ValueError(f"No strict-compliant slot found in 1..93 for constant value {value}")

        chosen = candidates[0]
        self.allocated_addresses.add(chosen)
        self.cells[chosen] = value
        self.symbols[name] = Symbol(
            name=name,
            address=chosen,
            size=1,
            kind="constant",
            initial_value=value
        )
        return chosen

    def alloc_buffer(self, name: str, size: int, base: Optional[int] = None) -> int:
        """Allocate a contiguous data buffer ensuring topological clearance."""
        if name in self.symbols:
            raise ValueError(f"Symbol '{name}' already exists")

        if base is None:
            # Find first available block after low memory (e.g. >= 200)
            candidate = 200
            while True:
                conflict = False
                for p in range(candidate, candidate + size):
                    if p in self.allocated_addresses:
                        conflict = True
                        candidate = p + 1
                        break
                if not conflict:
                    base = candidate
                    break

        for p in range(base, base + size):
            if p in self.allocated_addresses:
                raise ValueError(f"Buffer '{name}' collides with allocated address {p}")
            self.allocated_addresses.add(p)

        self.symbols[name] = Symbol(
            name=name,
            address=base,
            size=size,
            kind="buffer"
        )
        return base

    def set_label(self, name: str, address: Optional[int] = None) -> int:
        """Bind a label to current code pointer self.c or specified address."""
        addr = self.c if address is None else address
        self.symbols[name] = Symbol(
            name=name,
            address=addr,
            size=0,
            kind="label"
        )
        return addr

    def resolve(self, name: str) -> int:
        """Resolve a symbol name to its physical address."""
        if name not in self.symbols:
            raise KeyError(f"Undefined symbol: '{name}'")
        return self.symbols[name].address

    def check_topological_distance(self, c_addr: int, d_addr: int) -> bool:
        """Verify min(|C - D|, 59049 - |C - D|) >= min_delta."""
        diff = abs(c_addr - d_addr)
        toroidal_dist = min(diff, MEM_SIZE - diff)
        return toroidal_dist >= self.min_delta

    def emit_op(self, op: str, label: Optional[str] = None):
        """Emit an instruction at current code pointer self.c."""
        if label:
            self.set_label(label, self.c)

        if not self.check_topological_distance(self.c, self.d):
            self.violations.append(
                f"Topological violation at step: C={self.c}, D={self.d}, dist={min(abs(self.c - self.d), MEM_SIZE - abs(self.c - self.d))}"
            )

        self.cells[self.c] = encode(op, self.c)
        self.allocated_addresses.add(self.c)
        self.c += 1
        if op != 'v':
            self.d += 1

    def steer_d_low(self, target: int, max_steps: int = 50):
        """Steer pointer D to target in low memory using BFS with 'o' and 'j'."""
        if self.d == target:
            return

        queue = deque([(self.d, [])])
        seen = set()
        path = None
        while queue:
            cur_d, route = queue.popleft()
            if cur_d == target:
                path = route
                break
            if cur_d in seen or not (1 <= cur_d < 98) or len(route) > max_steps:
                continue
            seen.add(cur_d)

            # Try jump 'j'
            ptr = target - 1
            if strict_byte(ptr, cur_d) and (cur_d not in self.cells or self.cells[cur_d] == ptr):
                queue.appendleft((target, route + [('j', cur_d, ptr)]))
            elif cur_d in self.cells:
                dest = self.cells[cur_d] + 1
                if 1 <= dest < 98:
                    queue.append((dest, route + [('j', cur_d, self.cells[cur_d])]))

            # Advance by NOP 'o'
            queue.append((cur_d + 1, route + [('o', cur_d, None)]))

        if path is None:
            raise ValueError(f"Failed to steer D from {self.d} to {target} within budget")

        for op, address, value in path:
            if op == 'j':
                self.cells[address] = value
                self.allocated_addresses.add(address)
                self.emit_op('j')
                self.d = value + 1
            else:
                self.emit_op('o')

    def build_image(self) -> bytes:
        """Export full byte array strictly validated under Olmstead 1998 rules."""
        max_addr = max(self.cells.keys()) if self.cells else 0
        total_len = max(max_addr + 1, 2)
        out = []
        for p in range(total_len):
            if p in self.cells:
                v = self.cells[p]
            else:
                v = encode('o', p)
            if not strict_byte(v, p):
                raise ValueError(f"Cell {p} has invalid value {v} under Olmstead strict loader")
            out.append(v)
        return bytes(out)

    def export_symbols_manifest(self) -> dict:
        """Export symbol map and topological audit."""
        return {
            "symbol_count": len(self.symbols),
            "symbols": {
                name: {
                    "address": s.address,
                    "size": s.size,
                    "kind": s.kind,
                    "initial_value": s.initial_value,
                }
                for name, s in self.symbols.items()
            },
            "topological_violations": self.violations,
            "min_delta_enforced": self.min_delta,
        }
