#!/usr/bin/env python3
"""CLI para ejecutar Boss 7: El Wc Real (Universal In-VM Stream Byte Counter en Classic Malbolge).

REGLA FUNDAMENTAL DE AUTONOMÍA:
- El programa se ejecuta 100% de manera autónoma en lenguaje Malbolge en runtime.
- El binario .mal lee stdin mediante '/', discrimina internamente EOF y longitud de flujo,
  y emite el dígito de conteo decimal mediante '<'.
- Cero intervención del host ni escrituras de memoria durante la ejecución.
- Verificación estricta entre 3 oráculos (Python Machine, C mb_ref, Olmstead 1998).
- Modo silencioso (-q/--quiet) para uso transparente como filtro en tuberías Unix (drop-in wc -c).
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time

PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent
if str(PURE_EPOCH_ROOT) not in sys.path:
    sys.path.append(str(PURE_EPOCH_ROOT))

from tools.wc_real import (
    CANONICAL_LENGTH,
    CANONICAL_SHA256,
    READ_PC_0,
    READ_PC_1,
    READ_PC_2,
    OUTPUT_PC_DRAIN0,
    HALT_PC_DRAIN0,
    OUTPUT_PC_DRAIN1,
    HALT_PC_DRAIN1,
    OUTPUT_PC_DRAIN2,
    HALT_PC_DRAIN2,
    OUTPUT_PC_DRAIN3,
    HALT_PC_DRAIN3,
    build_wc_real,
    run_wc_real,
)
from tools.oracles import verify, validate_parity

DEFAULT_MAL = PURE_EPOCH_ROOT / "candidates" / "wc_real.mal"


def main():
    parser = argparse.ArgumentParser(
        description="CLI de Boss 7: El Wc Real (Universal In-VM Stream Byte Counter en Classic Malbolge)"
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
        help="Ruta al binario .mal (por defecto candidates/wc_real.mal)"
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
        help="Modo silencioso (drop-in wc -c): escribe únicamente el dígito de conteo a stdout"
    )
    parser.add_argument(
        "--budget", type=int, default=100000,
        help="Límite máximo de instrucciones para la VM (por defecto 100,000)"
    )
    parser.add_argument(
        "--trace-counter", action="store_true",
        help="Mostrar operaciones de discriminación helicoidal y drenaje en memoria de la VM"
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
        payload = b"ABC"

    # Cargar o sintetizar binario
    if args.source.exists() and args.mode == "normal":
        src = args.source.read_bytes()
    else:
        src, _ = build_wc_real(mode=args.mode)

    # Modo silencioso para tuberías Unix (drop-in wc -c)
    if args.quiet:
        res = run_wc_real(src, payload, max_steps=args.budget)
        sys.stdout.buffer.write(res["output"])
        sys.stdout.buffer.flush()
        return

    print("=" * 78)
    print("BOSS 7: EL WC REAL (UNIVERSAL IN-VM STREAM BYTE COUNTER)")
    print("=" * 78)
    print(f"Modo:               {args.mode}")
    print(f"Binario:            {args.source.name} ({len(src)} bytes)")
    print(f"Payload Stdin:      {len(payload)} bytes -> {payload!r}")
    print("-" * 78)

    t0 = time.perf_counter()
    res = run_wc_real(src, payload, max_steps=args.budget)
    t_ms = (time.perf_counter() - t0) * 1000.0

    print(f"Estado Terminal:    {res['terminal']}")
    print(f"Pasos ejecutados:   {res['steps']}")
    print(f"Tiempo Python VM:   {t_ms:.2f} ms")
    print(f"Salida ('<'):       {res['output']!r} -> {res['output'].decode('latin1', errors='replace')}")

    if args.trace_counter and "trace" in res:
        print("-" * 78)
        print(" 🔍 TRAZA DE CONTEO Y DISCRIMINACIÓN HELICOIDAL:")
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
