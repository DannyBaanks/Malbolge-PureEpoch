#!/usr/bin/env python3
"""CLI para ejecutar Boss 6: El Rev Real (Universal In-VM LIFO Stream Reverser en Classic Malbolge).

REGLA FUNDAMENTAL DE AUTONOMÍA:
- El programa se ejecuta 100% de manera autónoma en lenguaje Malbolge en runtime.
- El binario .mal lee stdin mediante '/', empuja los bytes a la pila LIFO en memoria de la VM,
  discrimina EOF internamente y emite los bytes en orden inverso (desapilando LIFO) mediante '<'.
- Cero intervención del host ni escrituras de memoria durante la ejecución.
- Verificación estricta entre 3 oráculos (Python Machine, C mb_ref, Olmstead 1998).
- Modo silencioso (-q/--quiet) para uso transparente como filtro en tuberías Unix (drop-in rev).
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time

PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent
if str(PURE_EPOCH_ROOT) not in sys.path:
    sys.path.append(str(PURE_EPOCH_ROOT))

from tools.rev_real import (
    CANONICAL_LENGTH,
    CANONICAL_SHA256,
    STACK_W0,
    STACK_W1,
    STACK_K0,
    STACK_K1,
    READ_PC_0,
    READ_PC_1,
    OUTPUT_PC_DRAIN2_B1,
    OUTPUT_PC_DRAIN2_B0,
    HALT_PC_DRAIN2,
    OUTPUT_PC_DRAIN1,
    HALT_PC_DRAIN1,
    HALT_PC_DRAIN0,
    build_rev_real,
    run_rev_real,
)
from tools.oracles import verify, validate_parity

DEFAULT_MAL = PURE_EPOCH_ROOT / "candidates" / "rev_real.mal"


def main():
    parser = argparse.ArgumentParser(
        description="CLI de Boss 6: El Rev Real (Universal In-VM LIFO Stream Reverser en Classic Malbolge)"
    )
    parser.add_argument(
        "-i", "--input", default=None,
        help="Cadena de entrada directa a pasar por stdin a la VM"
    )
    parser.add_argument(
        "-f", "--file", type=Path, default=None,
        help="Archivo cuya información binaria será enviada a stdin de la VM"
    )
    parser.add_argument(
        "--source", type=Path, default=DEFAULT_MAL,
        help="Ruta al binario .mal (por defecto candidates/rev_real.mal)"
    )
    parser.add_argument(
        "--mode", default="normal", choices=["normal", "broken_drain", "broken_eof", "broken_loader"],
        help="Modo de ejecución/mutación ('normal', 'broken_drain', 'broken_eof', 'broken_loader')"
    )
    parser.add_argument(
        "--oracle", "--oracles", action="store_true", dest="oracles",
        help="Verificar paridad estricta entre 3 oráculos (Python Machine, C mb_ref, Olmstead 1998)"
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true",
        help="Modo silencioso (drop-in rev): escribe únicamente la salida revertida a stdout"
    )
    parser.add_argument(
        "--budget", type=int, default=100000,
        help="Límite máximo de instrucciones para la VM (por defecto 100,000)"
    )
    parser.add_argument(
        "--trace-stack", action="store_true",
        help="Mostrar operaciones de empuje y desapilado LIFO en memoria de la VM"
    )
    args = parser.parse_args()

    # Determinar el payload de entrada
    if args.input is not None:
        payload = args.input.encode("latin1" if any(ord(c) > 127 for c in args.input) else "utf-8")
    elif args.file is not None:
        payload = args.file.read_bytes()
    elif not sys.stdin.isatty():
        payload = sys.stdin.buffer.read()
    else:
        payload = b"AB"

    # Cargar o sintetizar binario
    if args.source.exists() and args.mode == "normal":
        src = args.source.read_bytes()
    else:
        src, _ = build_rev_real(mode=args.mode)

    # Modo silencioso para tuberías Unix (drop-in rev)
    if args.quiet:
        try:
            res = run_rev_real(src, payload, max_steps=args.budget)
            sys.stdout.buffer.write(res["output"])
            sys.stdout.buffer.flush()
            sys.exit(0 if res["terminal"] == "HALT" else 1)
        except Exception as e:
            sys.stderr.write(f"Error en ejecución Malbolge: {e}\n")
            sys.exit(2)

    print("=" * 78)
    print(" 🔄 MALBOLGE PURE-EPOCH: BOSS 6 (EL REV REAL - IN-VM LIFO STREAM REVERSER) ")
    print("=" * 78)
    print(f" Entrada ({len(payload)} bytes):           {payload[:50]!r}{'...' if len(payload) > 50 else ''}")
    print(f" Binario Malbolge:             {args.source if args.source.exists() else 'En memoria'} ({len(src)} bytes)")
    print(f" Modo de ejecución:            {args.mode.upper()}")
    print(f" Intervención del host:        ❌ NINGUNA (vm.mem[...] = ... estrictamente prohibido)")
    print("-" * 78)

    t_start = time.perf_counter()
    try:
        res = run_rev_real(src, payload, max_steps=args.budget)
    except Exception as e:
        print(f"❌ Error al cargar/ejecutar binario: {e}")
        sys.exit(1)
    t_exec = (time.perf_counter() - t_start) * 1000

    out = res["output"]
    expected = bytes(reversed(payload))
    match = (out == expected)

    print(f" Estado terminal VM:           {res['terminal']}")
    print(f" Pasos de ejecución:           {res['steps']}")
    print(f" Salida emitida:               {out!r} ({len(out)} bytes)")
    print(f" Inversión LIFO bit-a-bit:     {'✅ EXACT REVERSAL' if match else '❌ MISMATCH'}")
    print(f" ⏱️  Tiempo de ejecución VM:     {t_exec:.2f} ms")

    if args.trace_stack and "trace" in res:
        print("-" * 78)
        print(" 🔍 TRAZA DE PILA LIFO IN-VM:")
        reads = [s for s in res["trace"] if s.get("opcode") == 23]
        outputs = [s for s in res["trace"] if s.get("output")]
        halts = [s for s in res["trace"] if s.get("terminal") == "HALT"]

        print(f"   Operaciones PUSH (lecturas '/'):   {len(reads)}")
        for i, s in enumerate(reads):
            byte_val = s["post"][0]
            ch_str = chr(byte_val) if 32 <= byte_val <= 126 else f"EOF(0x{byte_val:04x})" if byte_val == 59048 else f"0x{byte_val:02x}"
            print(f"     [PUSH {i}] Step {s['step']}: PC={s['pre'][1]}, leído={ch_str}")

        print(f"   Operaciones POP (emisiones '<'):   {len(outputs)}")
        for i, s in enumerate(outputs):
            byte_val = s["output"][0]
            ch_str = chr(byte_val) if 32 <= byte_val <= 126 else f"0x{byte_val:02x}"
            print(f"     [POP  {i}] Step {s['step']}: PC={s['pre'][1]}, emitido={ch_str}")

        print(f"   Operación HALT ('v'):              {len(halts)}")
        for s in halts:
            print(f"     [HALT]  Step {s['step']}: PC={s['pre'][1]}")

    # Verificación de oráculos si fue solicitada
    if args.oracles:
        print("-" * 78)
        print(" 🏛️  VERIFICACIÓN DE PARIDAD ENTRE 3 ORÁCULOS...")
        try:
            rep = verify(src, payload, budget=args.budget)
            parity_ok = validate_parity(rep)
            print(f"   Python Machine M0:          {rep['terminal']} (pasos: {rep['steps_excluding_halt']})")
            print(f"   C mb_ref (Olmstead spec):   rc={rep['reference_returncode']}")
            print(f"   C original (Olmstead 1998): rc={rep['original_returncode']}")
            print(f"   Paridad estricta (trace/mem/reg/out): {'✅ PASS' if parity_ok else '❌ FAIL'}")
        except Exception as e:
            print(f"   ❌ Error en verificación de oráculos: {e}")

    print("=" * 78)


if __name__ == "__main__":
    main()
