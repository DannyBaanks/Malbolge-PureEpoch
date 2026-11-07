#!/usr/bin/env python3
"""CLI para ejecutar Boss 10: El Sort2 Real (Universal In-VM Conditional Sorter en Classic Malbolge).

REGLA FUNDAMENTAL DE AUTONOMÍA:
- El programa se ejecuta 100% de manera autónoma en lenguaje Malbolge en runtime.
- El binario .mal lee stdin mediante '/', evalúa internamente el orden relativo de los elementos en VM,
  y emite los elementos en orden ordenado mediante '<'.
- Cero intervención del host ni escrituras de memoria durante la ejecución.
- Verificación estricta entre 3 oráculos (Python Machine, C mb_ref, Olmstead 1998).
- Modo silencioso (-q/--quiet) para uso transparente como filtro en tuberías Unix (drop-in sort2 / min-max sorter).
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time

PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent
if str(PURE_EPOCH_ROOT) not in sys.path:
    sys.path.append(str(PURE_EPOCH_ROOT))

from tools.sort2_real import (
    CANONICAL_LENGTH,
    CANONICAL_SHA256,
    READ_PC_0,
    READ_PC_1,
    SORT_START_PC,
    HALT_PC_DRAIN0_EOF,
    HALT_PC_DRAIN1_EOF,
    DRAIN_SORTED_START,
    OUTPUT_PC_DRAIN_SORTED_B0,
    OUTPUT_PC_DRAIN_SORTED_B1,
    HALT_PC_DRAIN_SORTED,
    DRAIN_INVERTED_START,
    OUTPUT_PC_DRAIN_INVERTED_B1,
    OUTPUT_PC_DRAIN_INVERTED_B0,
    HALT_PC_DRAIN_INVERTED,
    build_sort2_real,
    run_sort2_real,
)
from tools.oracles import verify, validate_parity

DEFAULT_MAL = PURE_EPOCH_ROOT / "candidates" / "sort2_real.mal"


def main():
    parser = argparse.ArgumentParser(
        description="CLI de Boss 10: El Sort2 Real (Universal In-VM Conditional Sorter en Classic Malbolge)"
    )
    parser.add_argument(
        "-i", "--input", default=None,
        help="Cadena de entrada directa a pasar por stdin a la VM (ej. '10' o '01')"
    )
    parser.add_argument(
        "-f", "--file", type=Path, default=None,
        help="Archivo cuya información binaria será enviada a stdin de la VM"
    )
    parser.add_argument(
        "--source", type=Path, default=DEFAULT_MAL,
        help="Ruta al binario .mal (por defecto candidates/sort2_real.mal)"
    )
    parser.add_argument(
        "--mode", default="canonical", choices=["canonical", "broken_drain", "broken_eof", "broken_loader"],
        help="Modo de ejecución/mutación ('canonical', 'broken_drain', 'broken_eof', 'broken_loader')"
    )
    parser.add_argument(
        "--oracle", "--oracles", action="store_true", dest="oracles",
        help="Verificar paridad estricta entre 3 oráculos (Python Machine, C mb_ref, Olmstead 1998)"
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true",
        help="Modo silencioso (drop-in sort2): escribe únicamente los bytes ordenados a stdout"
    )
    parser.add_argument(
        "--budget", type=int, default=100000,
        help="Límite máximo de instrucciones para la VM (por defecto 100,000)"
    )
    parser.add_argument(
        "--trace-sort", action="store_true",
        help="Mostrar operaciones de clasificación y discriminación en memoria de la VM"
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
        payload = b"10"

    # Cargar o sintetizar binario
    if args.source.exists() and args.mode == "canonical":
        src = args.source.read_bytes()
    else:
        src, _ = build_sort2_real(mode=args.mode)

    # Modo silencioso para tuberías Unix (drop-in sort2)
    if args.quiet:
        res = run_sort2_real(src, payload, max_steps=args.budget)
        sys.stdout.buffer.write(res["output"])
        sys.stdout.buffer.flush()
        return

    print("=" * 78)
    print("BOSS 10: EL SORT2 REAL (UNIVERSAL IN-VM CONDITIONAL BUBBLE SORTER)")
    print("=" * 78)
    print(f"Modo:               {args.mode}")
    print(f"Binario:            {args.source.name} ({len(src)} bytes)")
    print(f"Payload Stdin:      {len(payload)} bytes -> {payload!r}")
    print("-" * 78)

    t0 = time.perf_counter()
    res = run_sort2_real(src, payload, max_steps=args.budget)
    t_ms = (time.perf_counter() - t0) * 1000.0

    print(f"Estado Terminal:    {res['terminal']}")
    print(f"Pasos ejecutados:   {res['steps']}")
    print(f"Tiempo Python VM:   {t_ms:.2f} ms")
    print(f"Salida ('<'):       {res['output']!r} -> {res['output'].decode('latin1', errors='replace')}")

    if args.trace_sort and "trace" in res:
        print("-" * 78)
        print(" 🔍 TRAZA DE CLASIFICACIÓN EN VM:")
        reads = [s for s in res["trace"] if s.get("opcode") == 23]
        outputs = [s for s in res["trace"] if s.get("output")]
        halts = [s for s in res["trace"] if s.get("terminal") == "HALT"]

        print(f"   Operaciones de lectura ('/'):      {len(reads)}")
        for i, s in enumerate(reads):
            byte_val = s["post"][0]
            ch_str = chr(byte_val) if 32 <= byte_val <= 126 else f"EOF(0x{byte_val:04x})" if byte_val == 59048 else f"0x{byte_val:02x}"
            print(f"     [READ {i}] Step {s['step']}: PC={s['pre'][1]}, leído={ch_str}")

        print(f"   Operaciones de emisión ('<'):      {len(outputs)}")
        for i, s in enumerate(outputs):
            byte_val = s["output"][0]
            ch_str = chr(byte_val) if 32 <= byte_val <= 126 else f"0x{byte_val:02x}"
            print(f"     [OUT  {i}] Step {s['step']}: PC={s['pre'][1]}, emitido={ch_str}")

        print(f"   Operación de parada ('v'):         {len(halts)}")
        for s in halts:
            print(f"     [HALT]  Step {s['step']}: PC={s['pre'][1]}")

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
