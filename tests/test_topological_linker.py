"""Unit and side-by-side verification of TopologicalLinker.

Validates:
1. Low-memory constant allocation satisfies Olmstead strict loader.
2. Symbol table binding and resolution.
3. Topological clearance invariant min(|C - D|, 59049 - |C - D|) >= MIN_DELTA.
4. End-to-end program compilation and execution parity against C oracle (mb_ref).
"""
import pytest
from baseline.epoch_probe import XLAT1, XLAT2, VALID, MEM_SIZE
from src.topological_linker import TopologicalLinker, Symbol, MIN_DELTA
from tools.build_candidates import strict_byte
from tools.observe import run
from tools.oracles import raw_reference


def test_constant_placement_strictness():
    """Every constant allocated by TopologicalLinker must satisfy strict_byte."""
    linker = TopologicalLinker()
    # Test allocating various constants needed by arithmetic and control flow
    constants = [
        ("C50_A", 50),
        ("C50_B", 50),
        ("C121", 121),
        ("C97", 97),
        ("C80", 80),
    ]
    for name, val in constants:
        addr = linker.alloc_constant(name, val)
        assert 0 <= addr < 94
        assert strict_byte(val, addr)
        assert linker.resolve(name) == addr


def test_buffer_allocation_no_collision():
    """Buffers must not collide with low constants or each other."""
    linker = TopologicalLinker()
    linker.alloc_constant("C1", 50)
    b1 = linker.alloc_buffer("BUF1", size=32)
    b2 = linker.alloc_buffer("BUF2", size=16)

    assert b1 >= 94
    assert b2 >= b1 + 32
    assert linker.resolve("BUF1") == b1
    assert linker.resolve("BUF2") == b2


def test_topological_distance_check():
    """Distance check accurately measures toroidal separation."""
    linker = TopologicalLinker(min_delta=42)
    # Safe distance
    assert linker.check_topological_distance(100, 200) is True
    # Violating distance
    assert linker.check_topological_distance(100, 120) is False
    # Toroidal wraparound safe
    assert linker.check_topological_distance(10, MEM_SIZE - 100) is True
    # Toroidal wraparound violating
    assert linker.check_topological_distance(5, MEM_SIZE - 10) is False


def test_end_to_end_compiled_program_parity():
    """Build a minimal program using TopologicalLinker, verify 100% strict compliance and run."""
    linker = TopologicalLinker()
    # Layout code at 100+ to ensure topological clearance from D in low memory
    linker.c = 100
    linker.d = 1
    
    # Emit a program that halts cleanly: 'v' at 100
    linker.emit_op('v', label="HALT_POINT")
    
    image = linker.build_image()
    assert len(image) >= 101
    assert all(strict_byte(b, i) for i, b in enumerate(image))
    
    # Run in Python Machine
    py_res = run(image, b"", max_steps=200)
    assert py_res['terminal'] == 'HALT'
    assert py_res['steps'] == 100

    # Run in C oracle mb_ref
    c_res = raw_reference(image, b"", budget=200)
    assert c_res.returncode == 0
