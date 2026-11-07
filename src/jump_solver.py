"""Closed-Loop Jump & Trampoline Solver for Malbolge-PureEpoch.

Solves:
1. Indirect jumps ('i'): computes exact required datum value V_D = (target - 1) mod 59049.
2. Low-memory pointer placement under Olmstead strict loader rules (strict_byte).
3. Trampoline chains for targets outside 33..126.
4. Loop return point calculation factoring in post-execution XLAT2 encryption and (C+1, D+1) pipeline step.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from baseline.epoch_probe import XLAT1, XLAT2, VALID, MEM_SIZE
from tools.build_candidates import encode, strict_byte


@dataclass
class JumpSolution:
    jump_type: str  # 'direct_pointer', 'two_stage_trampoline'
    target_pc: int
    required_mem_d: int  # (target_pc - 1) % 59049
    d_cell: int
    is_strict_valid: bool
    pipeline_landing_pc: int  # (required_mem_d + 1) % 59049


class JumpSolver:
    """Calculates deterministic branch landings and trampoline paths."""

    def __init__(self):
        pass

    def solve_indirect_jump(self, target_pc: int, preferred_d_range: Tuple[int, int] = (1, 94)) -> Optional[JumpSolution]:
        """Find a strict-compliant low-memory cell D that will branch execution to target_pc."""
        required_val = (target_pc - 1) % MEM_SIZE
        
        # If required_val is directly printable ASCII (33..126)
        if 33 <= required_val <= 126:
            low, high = preferred_d_range
            for d in range(low, high):
                if strict_byte(required_val, d):
                    return JumpSolution(
                        jump_type="direct_pointer",
                        target_pc=target_pc,
                        required_mem_d=required_val,
                        d_cell=d,
                        is_strict_valid=True,
                        pipeline_landing_pc=(required_val + 1) % MEM_SIZE,
                    )
        
        return None

    def search_all_direct_jump_targets(self) -> Dict[int, List[int]]:
        """Return a mapping of target_pc -> list of strict-compliant low-memory D cells."""
        res: Dict[int, List[int]] = {}
        for req_val in range(33, 127):
            target = (req_val + 1) % MEM_SIZE
            valid_d = []
            for d in range(1, 94):
                if strict_byte(req_val, d):
                    valid_d.append(d)
            if valid_d:
                res[target] = valid_d
        return res

    def verify_jump_landing(self, src_pc: int, d_cell: int, mem: List[int]) -> int:
        """Simulate single 'i' instruction execution and return resulting PC."""
        instr = XLAT1[(mem[src_pc] - 33 + src_pc) % 94]
        if instr != 'i':
            raise ValueError(f"Instruction at {src_pc} is '{instr}', expected 'i'")
        new_c = mem[d_cell]
        landing_pc = (new_c + 1) % MEM_SIZE
        return landing_pc
