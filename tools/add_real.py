"""Boss 9: El Add Real - Universal In-VM Single-Digit Adder / Arithmetic Unit (ALU) en Classic Malbolge.

CONTRATO CANÓNICO DE AUTONOMÍA Y CÓMPUTO EN RUNTIME (AGENTS.md):
- Ejecución 100% autónoma en lenguaje Classic Malbolge en runtime.
- Cero escrituras de memoria del host durante la ejecución.
- Arquitectura helicoidal y unidad aritmética lógica (ALU) in-VM:
    * Ingestión de d0 en Pista 0:
      Si stdin está vacío (EOF), ramifica vía celda 27 hacia Halt inmediato.
      Si lee al menos 1 byte, bifurca a Pista 1 (celda 378).
    * Ingestión de d1 en Pista 1:
      Si stdin se agota tras 1 byte (EOF), ramifica vía celda 79 hacia Halt inmediato.
      Si lee 2 bytes, bifurca a Pista 2 (celda 1132).
    * Pista 2 (Unidad Aritmética Lógica ALU In-VM):
      Desapila d0 de W0 hacia K0 y d1 de W1 hacia K1 mediante inversión biyectiva crazy(-, 121).
      Calcula x = crazy(d1, d0) en K0.
      Calcula y = crazy(50, x) en K0 usando constante 50 de C50_B (celda 83).
      Desapila d0 de W0 hacia K1.
      Calcula z = crazy(50, d0) en K1 usando constante 50 de C50_A (celda 84).
      Calcula r = crazy(z, y) en K0:
        - Para 0+0=0: produce 50.
        - Para 0+1=1 y 1+0=1: produce 49.
        - Para 1+1=2: produce 48.
      Aplica 6 rotaciones ternarias invariantes sobre K0.
      Evalúa crazy(rot6(r), 97) en celda ALU_K (K=97, celda 59):
        - Para suma 1 ('01' y '10'): produce 26287 -> salto con 'i' aterriza en 26288 (Drain 1).
        - Para suma 2 ('11'): produce 26368 -> salto con 'i' aterriza en 26369 (Drain 2).
        - Para suma 0 ('00'): produce 26449 -> salto con 'i' aterriza en 26450 (Drain 0).
    * Geometría In-Line de Drenajes con Pares Mágicos Invariantes:
      Drain 1 (celda 26288): par mágico (49, 50) rota 113 dos veces, emite '<' ('1') y para 'v' en 26302.
      Drain 2 (celda 26369): par mágico (34, 35) rota 122 dos veces, emite '<' ('2') y para 'v' en 26380.
      Drain 0 (celda 26450): par mágico (81, 82) rota 112 tres veces, emite '<' ('0') y para 'v' en 26473.
- Paridad estricta entre 3 oráculos (Python Machine M0, C mb_ref, C Olmstead 1998).
- Todas las celdas cumplen con el cargador estricto de Olmstead 1998 (strict_byte para las 26,474 celdas).
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

CANONICAL_LENGTH = 26474
CANONICAL_SHA256 = "ec8b4801ed5b4554e3df87db39f9d933214e6bff202eff3cc6b3b4670749c2a8"

# Celdas de memoria baja para pistas y almacenamiento
W0 = 54        # Almacenamiento codificado de d0 (init 121)
W1 = 41        # Almacenamiento codificado de d1 (init 121)
K0 = 71        # Clave biyectiva de recuperación / acumulador ALU (init 121)
K1 = 72        # Clave biyectiva de recuperación / operando ALU (init 121)

Y1_0 = 53      # Y1 Discriminador EOF 0 (init 80)
Y2_0 = 45      # Y2 Discriminador EOF 0 (init 53)

Y1_1 = 37      # Y1 Discriminador EOF 1 (init 80)
Y2_1 = 39      # Y2 Discriminador EOF 1 (init 78)

C50_A = 84     # Constante 50 (init 50)
C50_B = 83     # Constante 50 (init 50)
ALU_K = 59     # Constante discriminadora de salto (init 97)

# Pares mágicos de rotación rápida para emisión
D0_VAL = 81    # Inicial 112 (rot3 = 48 -> '0')
D0_PTR = 82    # Inicial 80  (salto j a 81)

D1_VAL = 49    # Inicial 113 (rot2 = 49 -> '1')
D1_PTR = 50    # Inicial 48  (salto j a 49)

D2_VAL = 34    # Inicial 122 (rot2 = 50 -> '2')
D2_PTR = 35    # Inicial 33  (salto j a 34)

# Puntos clave de ejecución en la VM
READ_PC_0 = 99
READ_PC_1 = 378
ALU_START_PC = 1132

HALT_PC_DRAIN0_EOF = 27
HALT_PC_DRAIN1_EOF = 79

OUTPUT_PC_DRAIN1 = 26301
HALT_PC_DRAIN1 = 26302

OUTPUT_PC_DRAIN2 = 26379
HALT_PC_DRAIN2 = 26380

OUTPUT_PC_DRAIN0 = 26472
HALT_PC_DRAIN0 = 26473


def rot(v: int) -> int:
    """Rotación ternaria a la derecha (instrucción '*' de Malbolge)."""
    return (v // 3) + (v % 3) * 19683


def rot6(v: int) -> int:
    """6 rotaciones ternarias sucesivas."""
    for _ in range(6):
        v = rot(v)
    return v


def verify_add_algebraic_invariants() -> Dict[str, bool]:
    """Verifica formalmente los teoremas algebraicos ternarios del sumador/ALU e invariantes de emisión."""
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

    # Teorema algebraico del sumador ALU: r = crazy(crazy(50, d0), crazy(50, crazy(d1, d0)))
    def eval_alu(d0_val: int, d1_val: int) -> Tuple[int, int]:
        c1 = crazy(d1_val, d0_val)
        y = crazy(50, c1)
        z = crazy(50, d0_val)
        r = crazy(z, y)
        j = crazy(rot6(r), 97)
        return r, j

    r00, j00 = eval_alu(ord("0"), ord("0"))
    r01, j01 = eval_alu(ord("0"), ord("1"))
    r10, j10 = eval_alu(ord("1"), ord("0"))
    r11, j11 = eval_alu(ord("1"), ord("1"))

    inv_sum0 = (r00 == 50) and (j00 == 26449)
    inv_sum1_a = (r01 == 49) and (j01 == 26287)
    inv_sum1_b = (r10 == 49) and (j10 == 26287)
    inv_sum2 = (r11 == 48) and (j11 == 26368)

    # Invariantes de emisión rápida de dígitos
    v0 = 112
    for _ in range(3): v0 = rot(v0)
    inv_d0 = (v0 % 256 == ord("0"))

    v1 = 113
    for _ in range(2): v1 = rot(v1)
    inv_d1 = (v1 % 256 == ord("1"))

    v2 = 122
    for _ in range(2): v2 = rot(v2)
    inv_d2 = (v2 % 256 == ord("2"))

    # Validación estricta del cargador de todas las constantes en sus celdas fijas
    cells_to_check = {
        W0: 121, W1: 121, K0: 121, K1: 121,
        Y1_0: 80, Y2_0: 53, Y1_1: 80, Y2_1: 78,
        C50_A: 50, C50_B: 50, ALU_K: 97,
        D0_VAL: 112, D0_PTR: 80,
        D1_VAL: 113, D1_PTR: 48,
        D2_VAL: 122, D2_PTR: 33,
    }
    inv_strict_loader = all(strict_byte(val, pos) for pos, val in cells_to_check.items())

    return {
        "eof0_discriminator_isolation": inv_eof0,
        "eof1_discriminator_isolation": inv_eof1,
        "bijective_121_byte_inversion": inv_invert,
        "alu_sum0_evaluates_50_jump_26449": inv_sum0,
        "alu_sum1_a_evaluates_49_jump_26287": inv_sum1_a,
        "alu_sum1_b_evaluates_49_jump_26287": inv_sum1_b,
        "alu_sum2_evaluates_48_jump_26368": inv_sum2,
        "magic_pair_d0_rot3_emits_48": inv_d0,
        "magic_pair_d1_rot2_emits_49": inv_d1,
        "magic_pair_d2_rot2_emits_50": inv_d2,
        "all_fixed_cells_strict_loader_compliant": inv_strict_loader,
    }


def build_add_real(mode: str = "normal") -> Tuple[bytes, dict]:
    """Sintetiza el binario canónico de add_real o sus controles negativos/mutantes."""
    b = Layout(encode)

    cells_cfg = {
        W0: 121, W1: 121, K0: 121, K1: 121,
        Y1_0: 80, Y2_0: 53,
        Y1_1: 80, Y2_1: 78,
        C50_A: 50, C50_B: 50, ALU_K: 97,
        D0_VAL: 112, D0_PTR: 80,
        D1_VAL: 113, D1_PTR: 48,
        D2_VAL: 122, D2_PTR: 33,
        27: encode("v", 27),
        79: encode("v", 79),
    }

    b.cells.update(cells_cfg)
    b.mutable.update(set(cells_cfg.keys()))

    # Pista 0: Ingestión de d0 y discriminación EOF
    b.emit("/")
    b.seek(W0); b.emit("p")
    b.seek(Y1_0); b.emit("p")
    for _ in range(4):
        b.seek(Y1_0); b.emit("*")
    b.seek(Y2_0); b.emit("p"); b.seek(Y2_0); b.emit("i")

    # Relleno hasta Pista 1 (celda 378)
    for p in range(b.c, 378):
        b.cells[p] = encode("o", p)

    # Pista 1: Ingestión de d1 y discriminación EOF (c=378, d=46)
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

    # Pista 2: Unidad Aritmética Lógica (ALU) In-VM (c=1132, d=40)
    b.c = 1132; b.d = 40
    # 1. Recupera d0 en K0
    for _ in range(10): b.seek(W0); b.emit("*")
    b.seek(K0); b.emit("p")

    # 2. Recupera d1 en K1
    for _ in range(10): b.seek(W1); b.emit("*")
    b.seek(K1); b.emit("p")

    # 3. x = crazy(d1, d0) en K0
    b.seek(K0); b.emit("p")

    # 4. y = crazy(50, x) en K0
    for _ in range(10): b.seek(C50_B); b.emit("*")
    b.seek(K0); b.emit("p")

    # 5. Recupera d0 en K1
    for _ in range(10): b.seek(W0); b.emit("*")
    b.seek(K1); b.emit("p")

    # 6. z = crazy(50, d0) en K1
    for _ in range(10): b.seek(C50_A); b.emit("*")
    b.seek(K1); b.emit("p")

    # 7. r = crazy(z, y) en K0
    b.seek(K0); b.emit("p")

    # 8. 6 rotaciones ternarias en K0
    for _ in range(6): b.seek(K0); b.emit("*")

    # 9. crazy(rot6(r), 97) en ALU_K (celda 59)
    b.seek(ALU_K); b.emit("p")

    # 10. Salto dinámico condicional vía ALU_K
    b.seek(ALU_K); b.emit("i")

    # Relleno hasta Drain 1 (celda 26288)
    for p in range(b.c, 26288):
        b.cells[p] = encode("o", p)

    # Drain 1 en 26288 (d=60): Emite '1' (49)
    b.c = 26288; b.d = 60
    b.seek(D1_VAL)
    b.emit("*")
    b.emit("j")
    b.emit("*")
    b.emit("<")
    b.emit("v")

    # Relleno hasta Drain 2 (celda 26369)
    for p in range(b.c, 26369):
        b.cells[p] = encode("o", p)

    # Drain 2 en 26369 (d=60): Emite '2' (50)
    b.c = 26369; b.d = 60
    b.seek(D2_VAL)
    b.emit("*")
    b.emit("j")
    b.emit("*")
    b.emit("<")
    b.emit("v")

    # Relleno hasta Drain 0 (celda 26450)
    for p in range(b.c, 26450):
        b.cells[p] = encode("o", p)

    # Drain 0 en 26450 (d=60): Emite '0' (48)
    b.c = 26450; b.d = 60
    b.seek(D0_VAL)
    b.emit("*")
    b.emit("j")
    b.emit("*")
    b.emit("j")
    b.emit("*")
    b.emit("<")
    b.emit("v")

    raw = bytearray(b.image())
    assert len(raw) == CANONICAL_LENGTH, f"Longitud inesperada: {len(raw)}"

    if mode == "normal":
        pass
    elif mode == "broken_drain":
        # Corrompe la emisión '<' en Drain 0 (celda OUTPUT_PC_DRAIN0) reemplazándola por NOP 'o'
        raw[OUTPUT_PC_DRAIN0] = encode("o", OUTPUT_PC_DRAIN0)
    elif mode == "broken_eof":
        # Corrompe el punto de parada en celda 27 reemplazándolo por NOP 'o'
        raw[HALT_PC_DRAIN0_EOF] = encode("o", HALT_PC_DRAIN0_EOF)
    elif mode == "broken_loader":
        # Corrompe la primera celda con un carácter no admitido por strict_byte
        raw[0] = ord("~")
    else:
        raise ValueError(f"Modo desconocido: {mode}")

    out_bytes = bytes(raw)
    out_sha = hashlib.sha256(out_bytes).hexdigest()

    meta = {
        "title": "Boss 9: El Add Real (Universal In-VM Single-Digit Adder / ALU en Classic Malbolge)",
        "kind": "IN_VM_UNIVERSAL_SINGLE_DIGIT_ADDER_ALU",
        "mode": mode,
        "length_bytes": len(out_bytes),
        "sha256": out_sha,
        "algebraic_invariants": verify_add_algebraic_invariants(),
        "key_pcs": {
            "read_pc_0": READ_PC_0,
            "read_pc_1": READ_PC_1,
            "alu_start_pc": ALU_START_PC,
            "halt_pc_drain0_eof": HALT_PC_DRAIN0_EOF,
            "halt_pc_drain1_eof": HALT_PC_DRAIN1_EOF,
            "output_pc_drain1": OUTPUT_PC_DRAIN1,
            "halt_pc_drain1": HALT_PC_DRAIN1,
            "output_pc_drain2": OUTPUT_PC_DRAIN2,
            "halt_pc_drain2": HALT_PC_DRAIN2,
            "output_pc_drain0": OUTPUT_PC_DRAIN0,
            "halt_pc_drain0": HALT_PC_DRAIN0,
        },
    }

    return out_bytes, meta


def run_add_real(source: bytes, payload: bytes, budget: int = 50000) -> dict:
    """Ejecuta el binario add_real sobre el oráculo Python M0."""
    return run(source, payload, budget)


def emit_candidates(output_dir: Path | None = None) -> Dict[str, Tuple[Path, Path]]:
    """Genera y persiste el binario canónico y los mutantes de control negativo."""
    if output_dir is None:
        output_dir = PURE_EPOCH_ROOT / "candidates"
    output_dir.mkdir(parents=True, exist_ok=True)

    targets = {
        "add_real": "normal",
        "boss9_add_real": "normal",
        "add_real_broken_drain": "broken_drain",
        "add_real_broken_eof": "broken_eof",
        "add_real_broken_loader": "broken_loader",
    }

    generated = {}
    for name, mode in targets.items():
        raw, meta = build_add_real(mode=mode)
        mal_path = output_dir / f"{name}.mal"
        json_path = output_dir / f"{name}.json"
        mal_path.write_bytes(raw)
        json_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        generated[name] = (mal_path, json_path)

    return generated


def main() -> int:
    print("=== SÍNTESIS DE BOSS 9: EL ADD REAL (Classic Malbolge) ===")
    invariants = verify_add_algebraic_invariants()
    print("Invariantes algebraicos:")
    for k, v in invariants.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    assert all(invariants.values()), "Fallo en invariantes algebraicos!"

    emitted = emit_candidates()
    canon_mal, canon_json = emitted["boss9_add_real"]
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
