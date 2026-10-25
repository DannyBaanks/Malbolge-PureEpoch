#!/usr/bin/env python3
"""CLI para ejecutar el bucle dinámico de Malbolge (Boss 3: El Santo Grial).

Demuestra la ejecución de bucles while x > 0 con N dinámico sobre direcciones
físicas compartidas [64, 65, 88, 89] con oscilación termodinámica regenerativa
y telemetría de cronómetro de alta resolución.
"""
import argparse
import sys
import time
from pathlib import Path

PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent
if str(PURE_EPOCH_ROOT) not in sys.path:
    sys.path.append(str(PURE_EPOCH_ROOT))

from tools.boss3_dynamic_loop import build_boss3_dynamic_loop, simulate_dynamic_loop_execution
from tools.observe import run
from tools.oracles import verify, validate_parity


def main():
    parser = argparse.ArgumentParser(description="CLI de Bucle Dinámico while x > 0 en Malbolge (Boss 3)")
    parser.add_argument("-n", "--iterations", type=int, default=3, choices=[1, 2, 3],
                        help="Número de iteraciones dinámicas del bucle (1, 2, 3)")
    parser.add_argument("--mode", default="normal", choices=["normal", "broken_rearm", "broken_exit"],
                        help="Modo de ejecución ('normal', 'broken_rearm', 'broken_exit')")
    parser.add_argument("--oracles", action="store_true",
                        help="Verificar paridad estricta contra 3 oráculos (Python, C mb_ref, Olmstead 1998)")
    args = parser.parse_args()

    print("=" * 75)
    print(" 🏆 MALBOLGE PURE-EPOCH: BOSS 3 (EL SANTO GRIAL - BUCLE WHILE DINÁMICO) ")
    print("=" * 75)
    print(f" Modo de ejecución:            {args.mode.upper()}")
    print(f" Iteraciones solicitadas (N):  {args.iterations}")

    t_start = time.perf_counter()
    src, meta = build_boss3_dynamic_loop(args.mode)
    t_synth = (time.perf_counter() - t_start) * 1000

    print(f" Tamaño de artefacto .mal:     {meta['length_bytes']} bytes")
    print(f" Hash SHA-256 del artefacto:   {meta['sha256']}")
    print(f" Celdas físicas compartidas:   {meta['loop_body_addresses']}")
    print(f" Ciclo del oscilador:          {meta['oscillator_cycle']}")
    print(f" ⏱️  Tiempo de síntesis:         {t_synth:.2f} ms ({t_synth*1000:.1f} µs)")
    print("-" * 75)

    # Simulación y telemetría de reuso de direcciones
    t_exec_start = time.perf_counter()
    sim_res = simulate_dynamic_loop_execution(src, args.iterations)
    t_exec = (time.perf_counter() - t_exec_start) * 1000

    print(f" Estado terminal VM:           {sim_res['terminal']}")
    print(f" Pasos de ejecución:           {sim_res['steps']}")
    print(f" Emisiones de salida:          {sim_res['output_count']} caracteres ({sim_res['output']!r})")
    print(f" Reuso estricto de celdas:     {'✅ DEMOSTRADO (Celdas ' + str(sim_res['unique_loop_pcs']) + ')' if sim_res['address_reuse_verified'] else '❌ FALLO'}")
    print(f" ⏱️  Tiempo de ejecución VM:     {t_exec:.2f} ms ({t_exec*1000:.1f} µs)")
    print(f" ⏱️  Tiempo total end-to-end:    {(t_synth + t_exec):.2f} ms")

    if args.oracles:
        print("-" * 75)
        print(" 🔍 Verificando paridad contra 3 oráculos independientes...")
        t_ora_start = time.perf_counter()
        # Verificar contra el oráculo para entrada 0 canónica
        report = verify(src, b'0', 1000)
        t_ora = (time.perf_counter() - t_ora_start) * 1000
        parity = validate_parity(report)
        print(f" Paridad 3 Oráculos:           {'✅ 100% IDÉNTICO' if parity else '❌ DISCREPANCIA'}")
        print(f" Olmstead C (1998) exit code:  {report['original_returncode']}")
        print(f" mb_ref C (Fast) exit code:    {report['reference_returncode']}")
        print(f" ⏱️  Tiempo de verificación:     {t_ora:.2f} ms")

    print("=" * 75)


if __name__ == "__main__":
    main()
