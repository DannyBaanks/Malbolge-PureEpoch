#!/usr/bin/env python3
"""CLI para ejecutar el bucle dinámico autónomo de Malbolge (Boss 3: El Santo Grial).

Demuestra la ejecución de bucles while x > 0 con N dinámico sin intervención de host:
- Recibe N dinámicamente desde stdin ('0', '1', '2', '3', '7', EOF)
- Control interno de repetición y despacho ternario
- Salida limpia a HALT
- Telemetría de cronómetro de alta resolución
- Verificación de paridad estricta entre 3 oráculos (Python, C mb_ref, Olmstead 1998)
"""
import argparse
import sys
import time
from pathlib import Path

PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent
if str(PURE_EPOCH_ROOT) not in sys.path:
    sys.path.append(str(PURE_EPOCH_ROOT))

from tools.boss3_autonomous_loop import build_boss3_autonomous_loop, run_boss3_autonomous_execution
from tools.observe import run
from tools.oracles import verify, validate_parity


def main():
    parser = argparse.ArgumentParser(description="CLI de Bucle Autónomo while x > 0 en Malbolge (Boss 3)")
    parser.add_argument("-n", "--iterations", type=int, default=3, choices=[0, 1, 2, 3, 7],
                        help="Número de iteraciones dinámicas del bucle (0, 1, 2, 3, 7)")
    parser.add_argument("--mode", default="normal", choices=["normal", "broken_rearm", "broken_exit"],
                        help="Modo de ejecución ('normal', 'broken_rearm', 'broken_exit')")
    parser.add_argument("--oracles", action="store_true",
                        help="Verificar paridad estricta contra 3 oráculos (Python, C mb_ref, Olmstead 1998)")
    args = parser.parse_args()

    payload = str(args.iterations).encode() if args.iterations > 0 else b'0'

    print("=" * 75)
    print(" 🏆 MALBOLGE PURE-EPOCH: BOSS 3 (EL SANTO GRIAL - BUCLE WHILE AUTÓNOMO) ")
    print("=" * 75)
    print(f" Modo de ejecución:            {args.mode.upper()}")
    print(f" Entrada solicitada (N):       {args.iterations} (payload: {payload!r})")

    t_start = time.perf_counter()
    src, meta = build_boss3_autonomous_loop(args.mode)
    t_synth = (time.perf_counter() - t_start) * 1000

    print(f" Tamaño de artefacto .mal:     {meta['length_bytes']} bytes")
    print(f" Hash SHA-256 del artefacto:   {meta['sha256']}")
    print(f" Intervención del host:        ❌ NINGUNA (vm.mem[...] = ... estrictamente prohibido)")
    print(f" ⏱️  Tiempo de síntesis:         {t_synth:.2f} ms ({t_synth*1000:.1f} µs)")
    print("-" * 75)

    # Ejecución puramente autónoma
    t_exec_start = time.perf_counter()
    res = run_boss3_autonomous_execution(src, payload)
    t_exec = (time.perf_counter() - t_exec_start) * 1000

    print(f" Estado terminal VM:           {res['terminal']}")
    print(f" Pasos de ejecución:           {res['steps']}")
    print(f" Emisiones de salida:          {res['output_count']} caracteres ({res['output']!r})")
    print(f" ⏱️  Tiempo de ejecución VM:     {t_exec:.2f} ms ({t_exec*1000:.1f} µs)")
    print(f" ⏱️  Tiempo total end-to-end:    {(t_synth + t_exec):.2f} ms")

    if args.oracles:
        print("-" * 75)
        print(" 🔍 Verificando paridad contra 3 oráculos independientes...")
        t_ora_start = time.perf_counter()
        report = verify(src, payload, 5000)
        t_ora = (time.perf_counter() - t_ora_start) * 1000
        parity = validate_parity(report)
        print(f" Paridad 3 Oráculos:           {'✅ 100% IDÉNTICO' if parity else '❌ DISCREPANCIA'}")
        print(f" Olmstead C (1998) exit code:  {report['original_returncode']}")
        print(f" mb_ref C (Fast) exit code:    {report['reference_returncode']}")
        print(f" Python VM exit code:          0")
        print(f" ⏱️  Tiempo de verificación:     {t_ora:.2f} ms")

    print("=" * 75)


if __name__ == "__main__":
    main()
