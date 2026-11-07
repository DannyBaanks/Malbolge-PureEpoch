#!/usr/bin/env python3
"""CLI para ejecutar Boss 5: El Cat Real (Universal In-VM Streaming Cat en Malbolge).

REGLA FUNDAMENTAL DE AUTONOMÍA:
- El programa se ejecuta 100% de manera autónoma en lenguaje Malbolge en runtime.
- El binario .mal lee stdin mediante '/', discrimina EOF internamente mediante crazy arithmetic,
  y emite cada byte mediante '<'. Cero intervención del host ni escrituras de memoria.
- Verificación estricta entre 3 oráculos (Python Machine, C mb_ref, Olmstead 1998).
- Modo silencioso (-q/--quiet) para uso transparente en tuberías Unix (drop-in cat).
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time

PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent
if str(PURE_EPOCH_ROOT) not in sys.path:
    sys.path.append(str(PURE_EPOCH_ROOT))

from tools.cat_real import (
    CANONICAL_LENGTH,
    CANONICAL_SHA256,
    READ_PC,
    OUTPUT_PC,
    HALT_PC,
    STEPS_PER_BYTE,
    build_cat_real,
    run_cat_real,
)
from tools.oracles import verify, validate_parity

DEFAULT_MAL = PURE_EPOCH_ROOT / "candidates" / "cat_real.mal"


def main():
    parser = argparse.ArgumentParser(
        description="CLI de Boss 5: El Cat Real (Universal In-VM Streaming Cat en Classic Malbolge)"
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
        help="Ruta al binario .mal (por defecto candidates/cat_real.mal)"
    )
    parser.add_argument(
        "--mode", default="normal", choices=["normal", "broken_rearm", "broken_eof", "broken_loader"],
        help="Modo de ejecución/mutación ('normal', 'broken_rearm', 'broken_eof', 'broken_loader')"
    )
    parser.add_argument(
        "--oracle", "--oracles", action="store_true", dest="oracles",
        help="Verificar paridad estricta entre 3 oráculos (Python Machine, C mb_ref, Olmstead 1998)"
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true",
        help="Modo silencioso (drop-in cat): escribe únicamente la salida procesada por la VM a stdout"
    )
    parser.add_argument(
        "--budget", type=int, default=2000000,
        help="Límite máximo de instrucciones para la VM (por defecto 2,000,000)"
    )
    parser.add_argument(
        "--trace-loop", action="store_true",
        help="Mostrar métricas detalladas de las iteraciones del bucle interno"
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
        payload = b"Hello, Malbolge Real Cat!\n"

    # Cargar o sintetizar binario
    if args.source.exists() and args.mode == "normal":
        src = args.source.read_bytes()
    else:
        src, _ = build_cat_real(mode=args.mode)

    # Modo silencioso para tuberías
    if args.quiet:
        try:
            res = run_cat_real(src, payload, max_steps=args.budget)
            sys.stdout.buffer.write(res["output"])
            sys.stdout.buffer.flush()
            sys.exit(0 if res["terminal"] == "HALT" else 1)
        except Exception as e:
            sys.stderr.write(f"Error en ejecución Malbolge: {e}\n")
            sys.exit(2)

    print("=" * 78)
    print(" 🐱 MALBOLGE PURE-EPOCH: BOSS 5 (EL CAT REAL - UNIVERSAL STREAMING CAT) ")
    print("=" * 78)
    print(f" Entrada ({len(payload)} bytes):           {payload[:50]!r}{'...' if len(payload) > 50 else ''}")
    print(f" Binario Malbolge:             {args.source if args.source.exists() else 'En memoria'} ({len(src)} bytes)")
    print(f" Modo de ejecución:            {args.mode.upper()}")
    print(f" Intervención del host:        ❌ NINGUNA (vm.mem[...] = ... estrictamente prohibido)")
    print("-" * 78)

    t_start = time.perf_counter()
    try:
        res = run_cat_real(src, payload, max_steps=args.budget)
    except Exception as e:
        print(f"❌ Error al cargar/ejecutar binario: {e}")
        sys.exit(1)
    t_exec = (time.perf_counter() - t_start) * 1000

    out = res["output"]
    match = (out == payload)

    print(f" Estado terminal VM:           {res['terminal']}")
    print(f" Pasos de ejecución:           {res['steps']}")
    print(f" Salida emitida:               {len(out)} bytes")
    print(f" Coincidencia exacta bit-a-bit: {'✅ EXACT MATCH' if match else '❌ MISMATCH'}")
    print(f" ⏱️  Tiempo de ejecución VM:     {t_exec:.2f} ms")

    if args.trace_loop and "trace" in res:
        read_steps = [i for i, s in enumerate(res["trace"]) if s.get("opcode") == 23]
        out_steps = [i for i, s in enumerate(res["trace"]) if s.get("output")]
        halt_steps = [i for i, s in enumerate(res["trace"]) if s.get("terminal") == "HALT"]
        print("-" * 78)
        print(" 🔍 MÉTRICAS DEL BUCLE IN-VM:")
        print(f"   Lecturas ('/' en PC {READ_PC}):     {len(read_steps)} veces")
        print(f"   Escrituras ('<' en PC {OUTPUT_PC}):   {len(out_steps)} veces")
        print(f"   Parada ('v' en PC {HALT_PC}):       {len(halt_steps)} veces")
        if len(read_steps) >= 2:
            deltas = [read_steps[k] - read_steps[k-1] for k in range(1, len(read_steps))]
            print(f"   Período observado de ciclo: {set(deltas)} pasos (esperado: {STEPS_PER_BYTE})")

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
    print("Salida recibida:")
    sys.stdout.buffer.write(out)
    if not out.endswith(b"\n"):
        sys.stdout.buffer.write(b"\n")
    sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
