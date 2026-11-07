#!/usr/bin/env python3
"""CLI para ejecutar Boss 13: El Acarreo Temporal In-VM (In-VM BCD Ripple-Carry Clock Engine).

REGLA FUNDAMENTAL DE AUTONOMÍA (AGENTS.md):
- El programa se ejecuta 100% de manera autónoma en lenguaje Malbolge en runtime.
- Cero intervención del host ni escrituras de memoria durante la ejecución (vm.mem[...] = ... prohibido).
- Verificación estricta entre 3 oráculos (Python Machine M0, C mb_ref, Olmstead 1998).
- Modo silencioso (-q/--quiet) para uso transparente como filtro en tuberías Unix.
- Modo telemetría (--telemetry/--trace) para observar en detalle la mutación in-VM de los registros.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent
if str(PURE_EPOCH_ROOT) not in sys.path:
    sys.path.append(str(PURE_EPOCH_ROOT))

from tools.reloj_carry import (
    CANONICAL_LENGTH,
    CANONICAL_SHA256,
    REG_M10,
    REG_M1,
    REG_S10,
    REG_S1,
    build_reloj_carry,
    run_reloj_carry,
    verify_reloj_carry_algebraic_invariants,
)
from baseline.epoch_probe import Machine, load
from tools.oracles import verify, validate_parity

DEFAULT_MAL = PURE_EPOCH_ROOT / "candidates" / "reloj_carry.mal"


def main():
    parser = argparse.ArgumentParser(
        description="CLI de Boss 13: El Acarreo Temporal In-VM (In-VM BCD Ripple-Carry Transition 00:59 -> 01:00)"
    )
    parser.add_argument(
        "--source", type=Path, default=DEFAULT_MAL,
        help="Ruta al binario .mal (por defecto candidates/reloj_carry.mal)"
    )
    parser.add_argument(
        "--mode", default="canonical", choices=["canonical", "broken_carry", "broken_eof", "broken_loader"],
        help="Modo de ejecución/mutación ('canonical', 'broken_carry', 'broken_eof', 'broken_loader')"
    )
    parser.add_argument(
        "--oracle", "--oracles", action="store_true", dest="oracles",
        help="Verificar paridad estricta entre 3 oráculos (Python Machine, C mb_ref, Olmstead 1998)"
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true",
        help="Modo silencioso: escribe únicamente la salida del reloj a stdout (filtro Unix)"
    )
    parser.add_argument(
        "--telemetry", "--trace", action="store_true", dest="telemetry",
        help="Modo telemetría: muestra los valores de los registros antes, durante y después del acarreo in-VM"
    )
    parser.add_argument(
        "--info", action="store_true",
        help="Muestra informe detallado sobre los teoremas algebraicos de acarreo ternario"
    )
    parser.add_argument(
        "--budget", type=int, default=50000,
        help="Límite máximo de instrucciones para la VM (por defecto 50,000)"
    )
    args = parser.parse_args()

    if args.info:
        invariants = verify_reloj_carry_algebraic_invariants()
        print("=" * 70)
        print("BOSS 13: EL ACARREO TEMPORAL IN-VM — TEORÍA Y ÁLGEBRA TERNARIA")
        print("=" * 70)
        print("1. Invariantes Algebraicos:")
        for k, v in invariants.items():
            print(f"   * {k}: {'PASS' if v else 'FAIL'}")
        print("\n2. Álgebra del Acarreo en Cascada (Ripple-Carry) In-VM:")
        print("   * s1 (unidades de segundo): 57 ('9') -> 48 ('0') con acarreo:")
        print("     z1 = crazy(33, 57) = 29554")
        print("     k1 = crazy(33, 75) = 29563")
        print("     new_s1 = crazy(k1, z1) = 48 ('0')")
        print("   * s10 (decenas de segundo): 53 ('5') -> 48 ('0') (módulo 60) con acarreo:")
        print("     z10 = crazy(35, 53) = 29506")
        print("     k10 = crazy(39, 36) = 29485")
        print("     new_s10 = crazy(k10, z10) = 48 ('0')")
        print("   * m1 (unidades de minuto): 48 ('0') -> 49 ('1') (acarreo absorbido):")
        print("     km1 = crazy(40, 40) = 29484")
        print("     new_m1 = crazy(km1, 48) = 49 ('1')")
        print("   * m10 (decenas de minuto): permanece en 48 ('0')")
        print("=" * 70)
        return

    # Cargar o sintetizar binario
    if args.source.exists() and args.mode == "canonical":
        src = args.source.read_bytes()
    else:
        src, _ = build_reloj_carry(mode=args.mode)

    # Modo silencioso (filtro Unix)
    if args.quiet:
        res = run_reloj_carry(src, b"", max_steps=args.budget)
        sys.stdout.write(res["output"].decode("latin1", errors="replace"))
        sys.stdout.flush()
        return

    # Modo telemetría detallada
    if args.telemetry:
        print("=" * 70, flush=True)
        print("BOSS 13: TELEMETRÍA DE ACARREO TEMPORAL EN MEMORIA DE LA VM", flush=True)
        print("=" * 70, flush=True)
        mem = load(src)
        vm = Machine(mem, b"")

        print("1. Estado Inicial de Registros:", flush=True)
        print(f"   REG_M10 (celda {REG_M10}): {vm.mem[REG_M10]} ('{chr(vm.mem[REG_M10])}')", flush=True)
        print(f"   REG_M1  (celda {REG_M1}):  {vm.mem[REG_M1]} ('{chr(vm.mem[REG_M1])}')", flush=True)
        print(f"   REG_S10 (celda {REG_S10}): {vm.mem[REG_S10]} ('{chr(vm.mem[REG_S10])}')", flush=True)
        print(f"   REG_S1  (celda {REG_S1}):  {vm.mem[REG_S1]} ('{chr(vm.mem[REG_S1])}')", flush=True)

        # Ejecutar Display 1
        while len(vm.output) < 6:
            vm.tick()
        print(f"\n2. Emisión Display 1 (Paso {vm.steps}): {vm.output.decode('latin1').strip()}", flush=True)

        # Ejecutar Carry Engine
        meta_raw, meta = build_reloj_carry(mode=args.mode)
        carry_end = meta["carry_metrics"]["carry_pc_end"]
        while vm.c < carry_end and vm.terminal == "RUNNING":
            vm.tick()

        print(f"\n3. Estado de Registros POST-ACARREO IN-VM (Paso {vm.steps}):", flush=True)
        print(f"   REG_M10 (celda {REG_M10}): {vm.mem[REG_M10]} ('{chr(vm.mem[REG_M10])}')", flush=True)
        print(f"   REG_M1  (celda {REG_M1}):  {vm.mem[REG_M1]} ('{chr(vm.mem[REG_M1])}')  [ACARREO APLICADO 0 -> 1]", flush=True)
        print(f"   REG_S10 (celda {REG_S10}): {vm.mem[REG_S10]} ('{chr(vm.mem[REG_S10])}')  [ROLLOVER MOD 60 5 -> 0]", flush=True)
        print(f"   REG_S1  (celda {REG_S1}):  {vm.mem[REG_S1]} ('{chr(vm.mem[REG_S1])}')  [ROLLOVER UNIDADES 9 -> 0]", flush=True)

        # Ejecutar Display 2 y HALT
        while vm.terminal == "RUNNING":
            vm.tick()

        lines = vm.output.decode("latin1").strip().splitlines()
        print(f"\n4. Emisión Display 2 (Paso {vm.steps}): {lines[-1] if len(lines) > 1 else ''}", flush=True)
        print(f"5. Estado Terminal: {vm.terminal} (Pasos totales: {vm.steps:,})", flush=True)
        print("=" * 70, flush=True)
        return

    # Ejecución estándar con resumen
    res = run_reloj_carry(src, b"", max_steps=args.budget)
    lines = res["output"].decode("latin1", errors="replace").strip().splitlines()

    print("=" * 70)
    print("BOSS 13: EL ACARREO TEMPORAL IN-VM (00:59 -> 01:00)")
    print("=" * 70)
    print(f"Modo: {args.mode}")
    print(f"Celdas fuente: {len(src):,} bytes | SHA-256: {CANONICAL_SHA256[:16]}...")
    print(f"Instrucciones ejecutadas: {res['steps']:,} pasos | Estado terminal: {res['terminal']}")
    print("-" * 70)
    print("SALIDA DEL RELOJ DIGITAL:")
    for line in lines:
        print(f"  {line}")
    print("-" * 70)

    if args.oracles:
        print("\nVerificando paridad estricta entre 3 oráculos (Python Machine, C mb_ref, C Olmstead)...")
        report = verify(src, b"", budget=args.budget)
        parity_ok = validate_parity(report)
        print(f"  * Oráculos idénticos: {'PASS' if parity_ok else 'FAIL'}")
        print(f"  * Retorno C mb_ref: {report['reference_returncode']}")
        print(f"  * Retorno C Olmstead: {report['original_returncode']}")
        if not parity_ok:
            sys.exit(1)

    print("=" * 70)


if __name__ == "__main__":
    main()
