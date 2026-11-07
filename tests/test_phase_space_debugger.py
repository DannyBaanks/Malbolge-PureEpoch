"""Unit and behavioral verification for PhaseSpaceDebugger."""
import json
from pathlib import Path
import pytest

from tools.phase_space_debugger import PhaseSpaceDebugger, PhaseSpaceProfile
from tools.build_candidates import encode

ROOT = Path(__file__).resolve().parents[1]


def test_phase_space_profile_minimal_program():
    """Verify phase space metrics for a clean halting program."""
    debugger = PhaseSpaceDebugger(min_delta=42)
    # Minimal program: 'v' at 0
    src = bytes([encode('v', 0), encode('o', 1)])
    profile = debugger.profile_execution(src, b"", max_steps=10)
    
    assert profile.terminal == "HALT"
    assert profile.total_steps == 0
    # At cold boot step 0, C=0 and D=0 (toroidal distance 0)
    assert profile.min_toroidal_delta == 0
    assert len(profile.heatmap_bins) == 64


def test_phase_space_profile_boss13():
    """Verify phase space metrics on Boss 13 (In-VM BCD carry)."""
    boss13_path = ROOT / "candidates/boss13_reloj_carry.mal"
    if not boss13_path.exists():
        pytest.skip("Boss 13 candidate file not found")
    
    src = boss13_path.read_bytes()
    debugger = PhaseSpaceDebugger(min_delta=42)
    profile = debugger.profile_execution(src, b"", max_steps=50000)
    
    assert profile.terminal == "HALT"
    assert profile.total_steps == 1806
    assert profile.code_cells_count > 0
    assert profile.data_written_cells_count > 0
    
    # Render ASCII heatmap
    heatmap = debugger.render_ascii_heatmap(profile)
    assert len(heatmap) == 66  # '[' + 64 chars + ']'
    assert heatmap.startswith("[") and heatmap.endswith("]")
