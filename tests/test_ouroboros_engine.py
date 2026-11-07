"""Unit and algebraic verification of the OuroborosEngine (XLAT2 Cycle Dynamics).

Validates:
1. Exact 6-cycle decomposition: [68, 9, 6, 5, 4, 2] summing to 94.
2. Period-2 orbit 'F' <-> 'J'.
3. Period-4 orbit '*r}i' containing rot1 ('*') and jump ('i').
4. Period-5 orbit ')f`<3' containing output ('<').
5. Opcode trajectory prediction over multiple loop passes.
"""
import pytest
from src.ouroboros_engine import OuroborosEngine, compute_xlat2_cycles, CYCLES
from baseline.epoch_probe import XLAT2


def test_xlat2_cycle_decomposition_exhaustive():
    """Verify that all 94 ASCII printable characters decompose into exactly 6 disjoint cycles."""
    cycles = compute_xlat2_cycles()
    assert len(cycles) == 6
    lengths = [c.length for c in cycles]
    assert lengths == [68, 9, 6, 5, 4, 2]
    assert sum(lengths) == 94

    all_bytes = set()
    for c in cycles:
        for b in c.bytes:
            assert 33 <= b <= 126
            assert b not in all_bytes
            all_bytes.add(b)
    assert len(all_bytes) == 94


def test_period_2_orbit():
    """Verify 'F' (70) and 'J' (74) form a closed period-2 orbit under XLAT2."""
    engine = OuroborosEngine()
    c_f, off_f = engine.get_orbit(ord('F'))
    c_j, off_j = engine.get_orbit(ord('J'))
    assert c_f.length == 2
    assert c_j.length == 2
    assert c_f.chars == "FJ"
    assert XLAT2[ord('F') - 33] == 'J'
    assert XLAT2[ord('J') - 33] == 'F'


def test_period_4_orbit():
    """Verify '*r}i' forms a closed period-4 orbit connecting '*' and 'i'."""
    engine = OuroborosEngine()
    c, off = engine.get_orbit(ord('*'))
    assert c.length == 4
    assert c.chars == "*r}i"
    # Verify each hop under XLAT2
    assert XLAT2[ord('*') - 33] == 'r'
    assert XLAT2[ord('r') - 33] == '}'
    assert XLAT2[ord('}') - 33] == 'i'
    assert XLAT2[ord('i') - 33] == '*'


def test_period_5_orbit():
    """Verify ')f`<3' forms a closed period-5 orbit containing output '<'."""
    engine = OuroborosEngine()
    c, off = engine.get_orbit(ord('<'))
    assert c.length == 5
    assert c.chars == ")f`<3"
    assert XLAT2[ord('<') - 33] == '3'


def test_opcode_trajectory():
    """Verify opcode trajectory prediction matches sequential XLAT2 mutations."""
    engine = OuroborosEngine()
    # Position 0 with initial byte ord('*')
    traj = engine.opcode_trajectory(ord('*'), pos=0, count=8)
    assert len(traj) == 8
    # Period 4 means traj[0..3] == traj[4..7]
    assert traj[0:4] == traj[4:8]


def test_loop_restoration_lcm():
    """Verify LCM calculation for multi-cell self-restoration."""
    engine = OuroborosEngine()
    # Cell 1 from period 2, Cell 2 from period 4, Cell 3 from period 5
    period = engine.calculate_loop_restoration_period([ord('F'), ord('*'), ord('<')])
    # LCM(2, 4, 5) = 20
    assert period == 20
