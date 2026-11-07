#!/usr/bin/env python3
"""CLI para ejecutar Boss 11: El Reloj Real (Universal In-VM Autonomous Digital Clock & Stopwatch en Classic Malbolge).

REGLA FUNDAMENTAL DE AUTONOMÍA (AGENTS.md):
- El programa se ejecuta 100% de manera autónoma en lenguaje Malbolge en runtime.
- El binario .mal lee pulsos de tiempo de stdin mediante '/', procesa la cascada de estados
  temporales en memoria interna, y emite el reloj digital en formato "MM:SS\\n" mediante '<'.
- Cero intervención del host ni escrituras de memoria durante la ejecución (vm.mem[...] = ... prohibido).
- Verificación estricta entre 3 oráculos (Python Machine M0, C mb_ref, Olmstead 1998).
- Modo silencioso (-q/--quiet) para uso transparente como filtro en tuberías Unix.
- Modo interactivo (--live) para visualización en tiempo real del cronómetro / reloj digital.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time

PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent
if str(PURE_EPOCH_ROOT) not in sys.path:
    sys.path.append(str(PURE_EPOCH_ROOT))

from tools.reloj_real import (
    CANONICAL_LENGTH,
    CANONICAL_SHA256,
    TICK_0_PC,
    TICK_1_PC,
    TICK_2_PC,
    TICK_3_PC,
    HALT_PC_0,
    HALT_PC_1,
    HALT_PC_2,
    HALT_PC_3,
    HALT_PC_FINAL,
    build_reloj_real,
    run_reloj_real,
)
from tools.oracles import verify, validate_parity

DEFAULT_MAL = PURE_EPOCH_ROOT / "candidates" / "reloj_real.mal"


def main():
    parser = argparse.ArgumentParser(
        description="CLI de Boss 11: El Reloj Real (Universal In-VM Digital Clock & Stopwatch en Classic Malbolge)"
    )
    parser.add_argument(
        "-n", "--ticks", type=int, default=None,
        help="Número de pulsos/segundos a ejecutar (ej. -n 3 para 3 ticks de reloj)"
    )
    parser.add_argument(
        "-i", "--input", default=None,
        help="Cadena de entrada directa de pulsos a pasar por stdin a la VM (ej. 'P', 'PP', 'PPP')"
    )
    parser.add_argument(
        "-f", "--file", type=Path, default=None,
        help="Archivo cuyos bytes serán leídos como pulsos por stdin de la VM"
    )
    parser.add_argument(
        "--source", type=Path, default=DEFAULT_MAL,
        help="Ruta al binario .mal (por defecto candidates/reloj_real.mal)"
    )
    parser.add_argument(
        "--mode", default="canonical", choices=["canonical", "broken_tick", "broken_eof", "broken_loader"],
        help="Modo de ejecución/mutación ('canonical', 'broken_tick', 'broken_eof', 'broken_loader')"
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
        "--live", action="store_true",
        help="Modo interactivo en vivo: muestra el cronómetro digital avanzando segundo a segundo"
    )
    parser.add_argument(
        "--budget", type=int, default=100000,
        help="Límite máximo de instrucciones para la VM (por defecto 100,000)"
    )
    args = parser.parse_args()

    # Cargar o sintetizar binario
    if args.source.exists() and args.mode == "canonical":
        src = args.source.read_bytes()
    else:
        src, _ = build_reloj_real(mode=args.mode)

    # Modo interactivo en vivo (--live)
    if args.live:
        print("⏱️  INICIANDO CRONÓMETRO DIGITAL IN-VM EN CLASSIC MALBOLGE...")
        print("    Presione Ctrl+C para detener.")
        try:
            for t in range(1, 5):
                pulses = b"P" * t
                res = run_reloj_real(src, pulses, max_steps=args.budget)
                lines = res["output"].decode("latin1", errors="replace").strip().splitlines()
                current_time = lines[-1] if lines else "00:00"
                # Formato visual grande
                sys.stdout.write(f"\r\033[K[MALBOLGE VM IN-CLOCK] 🕒 TIEMPO: {current_time} (Paso {res['steps']})")
                sys.stdout.flush()
                time.sleep(1.0)
            print("\n✅ Rango de 4 ticks completado con éxito en Malbolge VM.")
        except KeyboardInterrupt:
            print("\n⏹️  Cronómetro detenido por el usuario.")
        return

    # Determinar el payload de pulsos de entrada
    if args.ticks is not None:
        payload = b"P" * max(0, args.ticks)
    elif args.input is not None:
        payload = args.input.encode("latin1" if any(ord(c) > 127 for c in args.input) else "utf-8")
    elif args.file is not None:
        payload = args.file.read_bytes()
    elif not sys.stdin.isatty():
        payload = sys.stdin.buffer.read()
    else:
        # Por defecto: 4 pulsos (rango completo de ticks 00:00..00:03)
        payload = b"PPPP"

    # Modo silencioso para tuberías Unix
    if args.quiet:
        res = run_reloj_real(src, payload, max_steps=args.budget)
        sys.stdout.buffer.write(res["output"])
        sys.stdout.buffer.flush()
        return

    print("=" * 78)
    print("BOSS 11: EL RELOJ REAL (IN-VM DIGITAL CLOCK & STOPWATCH EN CLASSIC MALBOLGE)")
    print("=" * 78)
    print(f"Modo:               {args.mode}")
    print(f"Binario:            {args.source.name} ({len(src)} bytes)")
    print(f"Pulsos recibidos:   {len(payload)} pulsos -> {payload!r}")
    print("-" * 78)

    t0 = time.perf_counter()
    res = run_reloj_real(src, payload, max_steps=args.budget)
    t_ms = (time.perf_counter() - t0) * 1000.0

    print(f"Estado Terminal:    {res['terminal']}")
    print(f"Pasos ejecutados:   {res['steps']}")
    print(f"Tiempo Python VM:   {t_ms:.2f} ms")
    print(f"Salida ('<'):       {res['output']!r}")
    print("Visualización del Reloj:")
    clock_lines = res["output"].decode("latin1", errors="replace").splitlines()
    if clock_lines:
        for idx, line in enumerate(clock_lines):
            print(f"  [TICK {idx}] 🕒 {line}")
    else:
        print("  (Ninguna emisión - stream vacío / EOF inmediato)")

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
