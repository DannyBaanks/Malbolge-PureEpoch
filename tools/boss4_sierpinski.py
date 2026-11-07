"""Boss 4: Renderizador del Triángulo de Sierpiński en Classic Malbolge.

AUDITORÍA 2026-11-07 — veredicto NOT_DEMONSTRATED para "evolución dinámica de autómata celular en runtime":
- El fractal se calcula previamente en Python (rule90 offline) y se sintetiza como código Malbolge en línea recta.
- Las emisiones usan portales de rotación invertibles en memoria baja [37, 43, 56] y emisión por tramos con '<'.
- Experimento de falsificación: dos estados de entrada distintos producen la misma salida (0 bytes leídos).
Lo que sí está demostrado: programa Malbolge válido, 0 escrituras del host, cargador estricto y paridad 3 oráculos.
"""
import hashlib
import json
from pathlib import Path
import sys
from typing import Dict, List, Optional, Tuple

PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent
if str(PURE_EPOCH_ROOT) not in sys.path:
    sys.path.append(str(PURE_EPOCH_ROOT))

from baseline.epoch_probe import Machine, load
from tools.build_candidates import Layout, encode, strict_byte
from tools.observe import run


def rule90(state: List[int]) -> List[int]:
    """Calcula la siguiente generación de la Regla 90 de Wolfram (vecindad periódica)."""
    n = len(state)
    return [state[(i - 1) % n] ^ state[(i + 1) % n] for i in range(n)]


def generate_sierpinski_text(generations: int = 8, width: int = 15) -> str:
    """Genera la representación textual esperada del Triángulo de Sierpiński."""
    state = [0] * width
    state[width // 2] = 1
    lines = []
    for _ in range(generations):
        s = "".join("*" if x else " " for x in state) + "\n"
        lines.append(s)
        state = rule90(state)
    return "".join(lines)


def get_runs(s: str) -> List[Tuple[str, int]]:
    """Descompone una cadena en tramos contiguos de caracteres idénticos (run-length)."""
    if not s:
        return []
    runs = []
    cur_ch = s[0]
    count = 1
    for ch in s[1:]:
        if ch == cur_ch:
            count += 1
        else:
            runs.append((cur_ch, count))
            cur_ch = ch
            count = 1
    runs.append((cur_ch, count))
    return runs


def build_boss4_sierpinski(generations: int = 8, mode: str = "normal") -> Tuple[bytes, dict]:
    """Construye el artefacto Malbolge (.mal) para el Autómata Celular de Sierpiński."""
    if mode not in {"normal", "broken_space", "broken_star", "broken_halt"}:
        raise ValueError(f"Modo no soportado: {mode}")

    layout = Layout(encode)
    CELL_SPACE = 37  # rot 1 da 32 (' '), rot 9 restaura 96
    CELL_NL = 43     # rot 2 da 10 ('\\n'), rot 8 restaura 90
    CELL_STAR = 56   # rot 10 da 42 ('*'), celda invariante

    val_space = 97 if mode == "broken_space" else 96
    val_star = 43 if mode == "broken_star" else 42
    val_nl = 90

    layout.cells[CELL_SPACE] = val_space
    layout.cells[CELL_NL] = val_nl
    layout.cells[CELL_STAR] = val_star
    layout.mutable.update({CELL_SPACE, CELL_NL, CELL_STAR})

    def load_space():
        layout.seek(CELL_SPACE)
        layout.emit("*")

    def restore_space():
        for _ in range(9):
            layout.seek(CELL_SPACE)
            layout.emit("*")

    def load_star():
        for _ in range(10):
            layout.seek(CELL_STAR)
            layout.emit("*")

    def load_nl():
        for _ in range(2):
            layout.seek(CELL_NL)
            layout.emit("*")

    def restore_nl():
        for _ in range(8):
            layout.seek(CELL_NL)
            layout.emit("*")

    # Generar el fractal de Sierpiński línea a línea
    width = 15
    state = [0] * width
    state[width // 2] = 1
    lines = []
    for _ in range(generations):
        s = "".join("*" if x else " " for x in state) + "\n"
        lines.append(s)
        state = rule90(state)

    for line in lines:
        for ch, count in get_runs(line):
            if ch == " ":
                load_space()
                for _ in range(count):
                    layout.emit("<")
                restore_space()
            elif ch == "*":
                load_star()
                for _ in range(count):
                    layout.emit("<")
            elif ch == "\n":
                load_nl()
                for _ in range(count):
                    layout.emit("<")
                restore_nl()

    if mode == "broken_halt":
        layout.emit("o")  # no se emite HALT
    else:
        layout.emit("v")  # HALT limpio

    img = layout.image()
    sha = hashlib.sha256(img).hexdigest()
    expected_text = "".join(lines)

    meta = {
        "title": "Boss 4: Autómata Celular Wolfram Regla 90 (El Triángulo de Sierpiński)",
        "kind": "CELLULAR_AUTOMATON_RULE90",
        "mode": mode,
        "generations": generations,
        "grid_width": width,
        "length_bytes": len(img),
        "sha256": sha,
        "output_chars": len(expected_text),
        "expected_output_hex": expected_text.encode("ascii").hex(),
        "portal_cells": {
            "space": {"address": CELL_SPACE, "initial": val_space, "rot_to_load": 1, "rot_to_restore": 9},
            "newline": {"address": CELL_NL, "initial": val_nl, "rot_to_load": 2, "rot_to_restore": 8},
            "star": {"address": CELL_STAR, "initial": val_star, "rot_to_load": 10, "rot_to_restore": 0},
        },
        "claims": {
            "is_malbolge_program": True,
            "renders_correct_sierpinski_fractal": True,
            "zero_external_memory_writes": True,
            "strict_loader_compliant": True,
            "strict_3_oracle_parity": True,
            "computes_rule90_in_vm_runtime": False,
            "evolves_arbitrary_input_state": False,
        },
        "audit_2026_11_07": {
            "verdict": "NOT_DEMONSTRATED",
            "classification": "unrolled_fractal_renderer_with_rotation_portals",
            "consumed_input_bytes": 0,
            "runtime_state_evolution": False,
        },
    }
    return img, meta


def run_boss4_execution(img: bytes, payload: bytes = b"", max_steps: int = 50000) -> dict:
    """Ejecuta el autómata celular en la máquina virtual Malbolge."""
    return run(img, payload, max_steps)


def main():
    print("=" * 70)
    print(" Sintetizando Boss 4: Autómata Celular (El Triángulo de Sierpiński)...")
    print("=" * 70)
    img, meta = build_boss4_sierpinski(generations=8, mode="normal")

    cand_dir = PURE_EPOCH_ROOT / "candidates"
    cand_dir.mkdir(exist_ok=True)
    mal_path = cand_dir / "boss4_sierpinski.mal"
    json_path = cand_dir / "boss4_sierpinski.json"

    mal_path.write_bytes(img)
    json_path.write_text(json.dumps(meta, indent=2))

    print(f"✅ Artefacto Malbolge generado: {mal_path} ({len(img)} bytes)")
    print(f"✅ Metadatos guardados:         {json_path}")
    print(f"🔒 SHA-256:                    {meta['sha256']}")
    print(f"📐 Generaciones:               {meta['generations']}")
    print(f"📊 Salida esperada:            {meta['output_chars']} caracteres")


if __name__ == "__main__":
    main()
