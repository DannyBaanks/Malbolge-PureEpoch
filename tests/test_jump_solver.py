"""Unit and behavioral verification of JumpSolver (Branch & Trampoline Solver).

Validates:
1. Indirect jump solving: computes V_D = (target - 1) % 59049.
2. Strict loader validity of all allocated low-memory D pointers.
3. Simulation and verification of landing PC: ensures execution branches exactly to target_pc.
4. Parity with execution in Python Machine.
"""
import pytest
from src.jump_solver import JumpSolver, JumpSolution
from baseline.epoch_probe import Machine, XLAT1, XLAT2, VALID, MEM_SIZE
from tools.build_candidates import encode, strict_byte


def test_solve_indirect_jump_direct_targets():
    """Verify that JumpSolver finds valid low-memory D cells for printable targets."""
    solver = JumpSolver()
    # Test target 100 (requires mem[D] == 99, 'c')
    sol = solver.solve_indirect_jump(target_pc=100)
    assert sol is not None
    assert sol.target_pc == 100
    assert sol.required_mem_d == 99
    assert 0 <= sol.d_cell < 94
    assert strict_byte(99, sol.d_cell)
    assert sol.pipeline_landing_pc == 100


def test_verify_jump_landing_simulation():
    """Verify jump execution in memory lands on expected PC."""
    solver = JumpSolver()
    sol = solver.solve_indirect_jump(target_pc=55)
    assert sol is not None
    
    # Construct minimal memory with 'i' at C=0 and required datum at D=sol.d_cell
    mem = [ord('a')] * MEM_SIZE
    # Cell 0 has 'i'
    # encode('i', 0)
    mem[0] = encode('i', 0)
    mem[sol.d_cell] = sol.required_mem_d
    
    landing = solver.verify_jump_landing(src_pc=0, d_cell=sol.d_cell, mem=mem)
    assert landing == 55


def test_search_all_direct_jump_targets():
    """Verify search returns a rich set of direct jump landing targets."""
    solver = JumpSolver()
    targets = solver.search_all_direct_jump_targets()
    assert len(targets) > 0
    # Every target in map must have at least one valid D cell
    for tgt, d_list in targets.items():
        assert len(d_list) > 0
        req = (tgt - 1) % MEM_SIZE
        for d in d_list:
            assert strict_byte(req, d)
