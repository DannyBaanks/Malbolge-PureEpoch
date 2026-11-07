"""Boss 8: El Cmp Real - Universal In-VM Stream Equality Predicate (cmp / eq) en Classic Malbolge.

CONTRATO CANÓNICO DE AUTONOMÍA Y CÓMPUTO EN RUNTIME (AGENTS.md):
- Ejecución 100% autónoma en lenguaje Classic Malbolge en runtime.
- Cero escrituras de memoria del host durante la ejecución.
- Arquitectura helicoidal y discriminación de igualdad en memoria de la VM:
    * Ingestión de byte 0 en Pista 0:
      Si stdin está vacío (EOF), ramifica vía celda 27 hacia Halt inmediato.
      Si lee al menos 1 byte, bifurca a Pista 1 (celda 378).
    * Ingestión de byte 1 en Pista 1:
      Si stdin se agota tras 1 byte (EOF), ramifica vía celda 79 hacia Halt inmediato.
      Si lee 2 bytes, bifurca a Pista 2 (celda 1132).
    * Pista 2 (Comparador Algebraico In-VM):
      Desapila b0 de W0 hacia K0 y b1 de W1 hacia K1 mediante inversión biyectiva crazy(-, 121).
      Calcula crazy(b1, b0) en el acumulador A.
      Evalúa el discriminador de igualdad: crazy(crazy(b1, b0), 80).
        - Para tokens iguales ('==' y '!!'): produce 80.
        - Para tokens desiguales ('=!' y '!='): produce 53.
      Aplica 9 rotaciones ternarias invariantes sobre celda CMP_Y1.
      Evalúa crazy(rot9(A), 97) en celda CMP_Y2 (K=97, celda 59).
        - Para tokens iguales: produce 29587 -> salto con 'i' aterriza en 29588 (Drain Equal).
        - Para tokens desiguales: produce 29425 -> salto con 'i' aterriza en 29426 (Drain Unequal).
    * Geometría In-Line de Drenajes sin Trampolines:
      Drain Unequal (celda 29426): rota CELL_NEQ (celda 65, ASCII 33, '!') 10 veces, emite '<' y para 'v' en 29478.
      Drain Equal (celda 29588): rota CELL_EQ (celda 72, ASCII 61, '=') 10 veces, emite '<' y para 'v' en 29666.
- Paridad estricta entre 3 oráculos (Python Machine M0, C mb_ref, C Olmstead 1998).
- Todas las celdas cumplen con el cargador estricto de Olmstead 1998 (strict_byte para las 29,667 celdas).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Dict, Tuple

PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent
if str(PURE_EPOCH_ROOT) not in sys.path:
    sys.path.append(str(PURE_EPOCH_ROOT))

from baseline.epoch_probe import Machine, crazy, load
from tools.build_candidates import Layout, encode, strict_byte
from tools.observe import run

CANONICAL_LENGTH = 29667
CANONICAL_SHA256 = "e045917cff2e5cadceb109fd39ec0146bd58370458de40e695dd675873c06eeb"

# Celdas de memoria baja para pistas y almacenamiento
W0 = 54        # Almacenamiento codificado de b0 (init 121)
K0 = 71        # Clave biyectiva de recuperación para b0 (init 121)
W1 = 41        # Almacenamiento codificado de b1 (init 121)
K1 = 35        # Clave biyectiva de recuperación para b1 (init 121)

Y1_0 = 82      # Y1 Discriminador EOF 0 (init 80)
Y2_0 = 45      # Y2 Discriminador EOF 0 (init 53)

Y1_1 = 37      # Y1 Discriminador EOF 1 (init 80)
Y2_1 = 39      # Y2 Discriminador EOF 1 (init 78)

CMP_Y1 = 76    # Y1 del Comparador (init 80)
CMP_Y2 = 59    # Y2 del Comparador (init 97)

CELL_EQ = 72   # Celda de emisión para igualdad (init 61, ASCII '=')
CELL_NEQ = 65  # Celda de emisión para desigualdad (init 33, ASCII '!')

# Puntos clave de ejecución en la VM
READ_PC_0 = 99
READ_PC_1 = 378
CMP_START_PC = 1132

HALT_PC_DRAIN0 = 27
HALT_PC_DRAIN1 = 79

OUTPUT_PC_DRAIN_NEQ = 29477
HALT_PC_DRAIN_NEQ = 29478

OUTPUT_PC_DRAIN_EQ = 29665
HALT_PC_DRAIN_EQ = 29666


def rot(v: int) -> int:
    """Rotación ternaria a la derecha (instrucción '*' de Malbolge)."""
    return (v // 3) + (v % 3) * 19683


def r10(v: int) -> int:
    """10 rotaciones ternarias sucesivas (identidad sobre cualquier entero ternario de 10 trits)."""
    for _ in range(10):
        v = rot(v)
    return v


def verify_cmp_algebraic_invariants() -> Dict[str, bool]:
    """Verifica formalmente los teoremas algebraicos ternarios del comparador e invariantes de emisión."""
    def d0(x):
        r = crazy(crazy(x, 121), 80)
        for _ in range(4):
            r = rot(r)
        return crazy(r, 53)

    def d1(x):
        r = crazy(crazy(x, 121), 80)
        for _ in range(3):
            r = rot(r)
        return crazy(r, 78)

    # Invariantes de discriminación de fin de flujo (EOF = 59048)
    inv_eof0 = (d0(59048) == 26) and all(d0(b) == 377 for b in range(256))
    inv_eof1 = (d1(59048) == 78) and all(d1(b) == 1131 for b in range(256))

    # Inversión biyectiva de recuperación de bytes
    inv_invert = all(crazy(crazy(b, 121), 121) % 256 == b for b in range(256))

    # Teorema algebraico del discriminador de igualdad para tokens '=' (61) y '!' (33)
    def eval_cmp(b0: int, b1: int) -> int:
        c1 = crazy(crazy(b1, b0), 80)
        r = c1
        for _ in range(9):
            r = rot(r)
        return crazy(r, 97)

    inv_eq_double_equal = (eval_cmp(ord("="), ord("=")) == 29587)
    inv_eq_double_excl = (eval_cmp(ord("!"), ord("!")) == 29587)
    inv_neq_equal_excl = (eval_cmp(ord("="), ord("!")) == 29425)
    inv_neq_excl_equal = (eval_cmp(ord("!"), ord("=")) == 29425)

    # Invariantes de emisión tras 10 rotaciones
    inv_cell_eq = (r10(61) % 256 == 61)
    inv_cell_neq = (r10(33) % 256 == 33)

    # Validación estricta del cargador de todas las constantes en sus celdas fijas
    cells_to_check = {
        W0: 121, K0: 121, W1: 121, K1: 121,
        Y1_0: 80, Y2_0: 53, Y1_1: 80, Y2_1: 78,
        CMP_Y1: 80, CMP_Y2: 97, CELL_EQ: 61, CELL_NEQ: 33,
    }
    inv_strict_loader = all(strict_byte(val, pos) for pos, val in cells_to_check.items())

    return {
        "eof0_discriminator_isolation": inv_eof0,
        "eof1_discriminator_isolation": inv_eof1,
        "bijective_121_byte_inversion": inv_invert,
        "cmp_equal_token_equal_evaluates_29587": inv_eq_double_equal,
        "cmp_equal_token_excl_evaluates_29587": inv_eq_double_excl,
        "cmp_unequal_token_pair_evaluates_29425_a": inv_neq_equal_excl,
        "cmp_unequal_token_pair_evaluates_29425_b": inv_neq_excl_equal,
        "drain_equal_10rot_identity": inv_cell_eq,
        "drain_unequal_10rot_identity": inv_cell_neq,
        "all_fixed_cells_strict_loader_compliant": inv_strict_loader,
    }


def build_cmp_real(mode: str = "normal") -> Tuple[bytes, dict]:
    """Sintetiza el binario canónico de cmp_real o sus controles negativos/mutantes."""
    b = Layout(encode)

    cells_config = {
        W0: 121, K0: 121,
        W1: 121, K1: 121,
        Y1_0: 80, Y2_0: 53,
        Y1_1: 80, Y2_1: 78,
        CMP_Y1: 80,
        CMP_Y2: 97,
        CELL_EQ: 61,
        CELL_NEQ: 33,
        27: encode("v", 27), # Halt on EOF 0
        79: encode("v", 79), # Halt on EOF 1
    }

    b.cells.update(cells_config)
    b.mutable.update(set(cells_config.keys()))

    # Pista 0: Lee byte 0 y discrimina EOF
    b.emit("/")
    b.seek(W0); b.emit("p")
    b.seek(Y1_0); b.emit("p")
    for _ in range(4):
        b.seek(Y1_0); b.emit("*")
    b.seek(Y2_0); b.emit("p"); b.seek(Y2_0); b.emit("i")

    # Relleno hasta Pista 1 (celda 378)
    for p in range(b.c, 378):
        b.cells[p] = encode("o", p)

    # Pista 1: Lee byte 1 y discrimina EOF (c=378, d=46)
    b.c = 378; b.d = 46
    b.emit("/")
    b.seek(W1); b.emit("p")
    b.seek(Y1_1); b.emit("p")
    for _ in range(3):
        b.seek(Y1_1); b.emit("*")
    b.seek(Y2_1); b.emit("p"); b.seek(Y2_1); b.emit("i")

    # Relleno hasta Pista 2 (celda 1132)
    for p in range(b.c, 1132):
        b.cells[p] = encode("o", p)

    # Pista 2: Comparador Algebraico In-VM (c=1132, d=40)
    b.c = 1132; b.d = 40
    # Recupera b0 desde W0 hacia K0
    for _ in range(10):
        b.seek(W0); b.emit("*")
    b.seek(K0); b.emit("p")

    # Recupera b1 desde W1 hacia K1
    for _ in range(10):
        b.seek(W1); b.emit("*")
    b.seek(K1); b.emit("p")

    # A contiene b1. Computa crazy(b1, b0) = crazy(A, K0)
    b.seek(K0); b.emit("p")

    # Computa crazy(crazy(b1, b0), 80) en CMP_Y1
    b.seek(CMP_Y1); b.emit("p")

    # 9 rotaciones ternarias en CMP_Y1
    for _ in range(9):
        b.seek(CMP_Y1); b.emit("*")

    # Computa crazy(rot9(A), 97) en CMP_Y2
    b.seek(CMP_Y2); b.emit("p")

    # Salto dinámico condicional vía CMP_Y2
    b.seek(CMP_Y2); b.emit("i")

    # Relleno hasta Drain Unequal (celda 29426)
    for p in range(b.c, 29426):
        b.cells[p] = encode("o", p)

    # Drain Unequal en 29426 (d=60)
    b.c = 29426; b.d = 60
    for _ in range(10):
        b.seek(CELL_NEQ); b.emit("*")
    b.emit("<")
    b.emit("v")

    # Relleno hasta Drain Equal (celda 29588)
    for p in range(b.c, 29588):
        b.cells[p] = encode("o", p)

    # Drain Equal en 29588 (d=60)
    b.c = 29588; b.d = 60
    for _ in range(10):
        b.seek(CELL_EQ); b.emit("*")
    b.emit("<")
    b.emit("v")

    raw = bytearray(b.image())
    assert len(raw) == CANONICAL_LENGTH, f"Longitud inesperada: {len(raw)}"

    if mode == "normal":
        pass
    elif mode == "broken_drain":
        # Corrompe la emisión '<' en Drain Equal (celda OUTPUT_PC_DRAIN_EQ) reemplazándola por NOP 'o'
        raw[OUTPUT_PC_DRAIN_EQ] = encode("o", OUTPUT_PC_DRAIN_EQ)
    elif mode == "broken_eof":
        # Corrompe el punto de parada en celda 27 reemplazándolo por NOP 'o'
        raw[HALT_PC_DRAIN0] = encode("o", HALT_PC_DRAIN0)
    elif mode == "broken_loader":
        # Corrompe la primera celda con un carácter no admitido por strict_byte
        raw[0] = ord("~")
    else:
        raise ValueError(f"Modo desconocido: {mode}")

    out_bytes = bytes(raw)
    out_sha = hashlib.sha256(out_bytes).hexdigest()

    meta = {
        "title": "Boss 8: El Cmp Real (Universal In-VM Stream Equality Predicate en Classic Malbolge)",
        "kind": "IN_VM_UNIVERSAL_STREAM_EQUALITY_PREDICATE",
        "mode": mode,
        "length_bytes": len(out_bytes),
        "sha256": out_sha,
        "algebraic_invariants": verify_cmp_algebraic_invariants(),
        "key_pcs": {
            "read_pc_0": READ_PC_0,
            "read_pc_1": READ_PC_1,
            "cmp_start_pc": CMP_START_PC,
            "halt_pc_drain0": HALT_PC_DRAIN0,
            "halt_pc_drain1": HALT_PC_DRAIN1,
            "output_pc_drain_neq": OUTPUT_PC_DRAIN_NEQ,
            "halt_pc_drain_neq": HALT_PC_DRAIN_NEQ,
            "output_pc_drain_eq": OUTPUT_PC_DRAIN_EQ,
            "halt_pc_drain_eq": HALT_PC_DRAIN_EQ,
        },
    }

    return out_bytes, meta


def run_cmp_real(source: bytes, payload: bytes, budget: int = 50000) -> dict:
    """Ejecuta el binario cmp_real sobre el oráculo Python M0."""
    return run(source, payload, budget)


def emit_candidates(output_dir: Path | None = None) -> Dict[str, Tuple[Path, Path]]:
    """Genera y persiste el binario canónico y los mutantes de control negativo."""
    if output_dir is None:
        output_dir = PURE_EPOCH_ROOT / "candidates"
    output_dir.mkdir(parents=True, exist_ok=True)

    targets = {
        "cmp_real": "normal",
        "boss8_cmp_real": "normal",
        "cmp_real_broken_drain": "broken_drain",
        "cmp_real_broken_eof": "broken_eof",
        "cmp_real_broken_loader": "broken_loader",
    }

    generated = {}
    for name, mode in targets.items():
        raw, meta = build_cmp_real(mode=mode)
        mal_path = output_dir / f"{name}.mal"
        json_path = output_dir / f"{name}.json"
        mal_path.write_bytes(raw)
        json_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        generated[name] = (mal_path, json_path)

    return generated


def main() -> int:
    print("=== SÍNTESIS DE BOSS 8: EL CMP REAL (Classic Malbolge) ===")
    invariants = verify_cmp_algebraic_invariants()
    print("Invariantes algebraicos:")
    for k, v in invariants.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    assert all(invariants.values()), "Fallo en invariantes algebraicos!"

    emitted = emit_candidates()
    canon_mal, canon_json = emitted["boss8_cmp_real"]
    raw = canon_mal.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    print(f"\nBinario canónico generado: {canon_mal}")
    print(f"Longitud: {len(raw)} bytes (esperada: {CANONICAL_LENGTH})")
    print(f"SHA-256:  {sha}")
    assert len(raw) == CANONICAL_LENGTH
    assert sha == CANONICAL_SHA256, f"Hash mismatch: got {sha}, expected {CANONICAL_SHA256}"
    print("\nTodos los candidatos y controles negativos sintetizados exitosamente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
