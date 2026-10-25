#!/usr/bin/env python3
"""CLI para ejecutar código Brainfuck sobre el motor PureEpoch de Malbolge.

Demuestra la VM de Turing bidireccional (Boss 2) con telemetría de alta resolución.
"""
import argparse
import sys
import time
from pathlib import Path

PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent
if str(PURE_EPOCH_ROOT) not in sys.path:
    sys.path.append(str(PURE_EPOCH_ROOT))

from tools.boss2_brainfuck import build_boss2_brainfuck, BrainfuckMalbolgeCompiler
from tools.observe import run
from tools.oracles import verify, validate_parity


def main():
    parser = argparse.ArgumentParser(description="CLI de Brainfuck sobre Malbolge Puro (Boss 2)")
    parser.add_argument("code", nargs="?", default="++>+>++<<-.>.>.>+.<.!",
                        help="Código Brainfuck a ejecutar (ej: '++>+<-.>.!')")
    parser.add_argument("--oracles", action="store_true",
                        help="Ejecutar contra los 3 oráculos (Python, C mb_ref, Olmstead 1998)")
    args = parser.parse_args()

    print("=" * 70)
    print(" 🚀 MALBOLGE PURE-EPOCH: BOSS 2 (BRAINFUCK TURING TAPE) ")
    print("=" * 70)
    print(f" Código Brainfuck de entrada: {args.code}")

    t_start = time.perf_counter()
    compiler = BrainfuckMalbolgeCompiler(tape_size=5)
    img, meta = compiler.compile(args.code)
    t_compile = (time.perf_counter() - t_start) * 1000

    print(f" Tamaño de cinta virtual:      {meta['tape_size']} celdas {meta['tape_cells']}")
    print(f" Tamaño de artefacto .mal:     {meta['code_size_bytes']} bytes")
    print(f" ⏱️  Tiempo de compilación:      {t_compile:.2f} ms")
    print("-" * 70)

    # Ejecución
    t_exec_start = time.perf_counter()
    res = run(img, b'', max_steps=10000)
    t_exec = (time.perf_counter() - t_exec_start) * 1000

    print(f" Estado terminal VM:           {res['terminal']}")
    print(f" Pasos de ejecución:           {res['steps']}")
    print(f" Salida (bytes numéricos):     {list(res['output'])}")
    print(f" Salida (raw bytes):           {bytes(res['output'])!r}")
    print(f" Cinta final en memoria:       {meta['virtual_tape_final']}")
    print(f" ⏱️  Tiempo de ejecución VM:     {t_exec:.2f} ms")
    print(f" ⏱️  Tiempo total end-to-end:    {(t_compile + t_exec):.2f} ms")

    if args.oracles:
        print("-" * 70)
        print(" 🔍 Verificando paridad contra 3 oráculos independientes...")
        t_ora_start = time.perf_counter()
        report = verify(img, b'', 10000)
        t_ora = (time.perf_counter() - t_ora_start) * 1000
        parity = validate_parity(report)
        print(f" Paridad 3 Oráculos:           {'✅ 100% IDÉNTICO' if parity else '❌ DISCREPANCIA'}")
        print(f" Olmstead C (1998) exit code:  {report['original_returncode']}")
        print(f" ⏱️  Tiempo de verificación:     {t_ora:.2f} ms")

    print("=" * 70)


if __name__ == "__main__":
    main()
