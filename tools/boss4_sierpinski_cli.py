#!/usr/bin/env python3
"""CLI para ejecutar el Autómata Celular Wolfram Regla 90 (El Triángulo de Sierpiński) en Malbolge.

Ejecuta el fractal autónomo en Classic Malbolge:
- Genera el Triángulo de Sierpiński mediante evolución discreta de la Regla 90
- Telemetría de cronómetro de alta resolución
- Verificación opcional de paridad estricta entre 3 oráculos (Python Machine, C mb_ref, Olmstead 1998)
- 0 escrituras del host durante la ejecución de la VM
"""
import argparse
from pathlib import Path
import sys
import time

PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent
if str(PURE_EPOCH_ROOT) not in sys.path:
    sys.path.append(str(PURE_EPOCH_ROOT))

from tools.boss4_sierpinski import build_boss4_sierpinski, run_boss4_execution
from tools.oracles import verify, validate_parity


def main():
    parser = argparse.ArgumentParser(
        description="CLI del Autómata Celular Wolfram Regla 90 (Triángulo de Sierpiński) en Malbolge"
    )
    parser.add_argument(
        "-g", "--generations", type=int, default=8, choices=[1, 2, 4, 8],
        help="Número de generaciones del autómata celular a calcular (1, 2, 4, 8; defecto 8)"
    )
    parser.add_argument(
        "--mode", default="normal", choices=["normal", "broken_space", "broken_star", "broken_halt"],
        help="Modo de síntesis ('normal', 'broken_space', 'broken_star', 'broken_halt')"
    )
    parser.add_argument(
        "--oracles", action="store_true",
        help="Verificar paridad estricta entre 3 oráculos (Python Machine, C mb_ref, Olmstead 1998)"
    )
    args = parser.parse_args()

    print("=" * 75)
    print(" 🔺 MALBOLGE PURE-EPOCH: BOSS 4 (AUTÓMATA CELULAR - TRIÁNGULO DE SIERPIŃSKI) ")
    print("=" * 75)
    print(f" Modo de ejecución:            {args.mode.upper()}")
    print(f" Generaciones solicitadas:     {args.generations}")

    t_start = time.perf_counter()
    src, meta = build_boss4_sierpinski(generations=args.generations, mode=args.mode)
    t_synth = (time.perf_counter() - t_start) * 1000

    print(f" Tamaño de artefacto .mal:     {meta['length_bytes']} bytes")
    print(f" Hash SHA-256 del artefacto:   {meta['sha256']}")
    print(f" Intervención del host:        ❌ NINGUNA (vm.mem[...] = ... estrictamente prohibido)")
    print(f" ⏱️  Tiempo de síntesis:         {t_synth:.2f} ms ({t_synth*1000:.1f} µs)")
    print("-" * 75)

    # Ejecución sin escrituras del host
    t_exec_start = time.perf_counter()
    res = run_boss4_execution(src)
    t_exec = (time.perf_counter() - t_exec_start) * 1000

    print(f" Estado terminal VM:           {res['terminal']}")
    print(f" Pasos de ejecución:           {res['steps']}")
    print(f" Emisiones de salida:          {len(res['output'])} caracteres")
    print(f" ⏱️  Tiempo de ejecución VM:     {t_exec:.2f} ms")
    print("=" * 75)
    print(" 🎨 SALIDA DEL AUTÓMATA CELULAR (ASCII FRACTAL):")
    print("=" * 75)
    try:
        print(res['output'].decode('ascii'))
    except UnicodeDecodeError:
        print(repr(res['output']))
    print("=" * 75)

    if args.oracles:
        print(" 🔍 Verificando paridad estricta entre 3 oráculos...")
        t_ora_start = time.perf_counter()
        rep = verify(src, b"", budget=15000)
        t_ora = (time.perf_counter() - t_ora_start) * 1000

        parity_ok = validate_parity(rep)
        out_match = bytes.fromhex(rep['output_hex']) == res['output']

        print(f"    - Traza idéntica (Python == C == Olmstead): {rep.get('trace_equal')}")
        print(f"    - Memoria final idéntica (59049 celdas):     {rep.get('memory_equal')}")
        print(f"    - Registros idénticos (A, C, D):            {rep.get('registers_equal')}")
        print(f"    - Salida idéntica bit a bit:                {rep.get('outputs_equal')} (longitud: {len(res['output'])})")
        print(f"    - Códigos de salida:                        Ref={rep.get('reference_returncode')}, Inst={rep.get('instrumented_returncode')}, Olmstead={rep.get('original_returncode')}")
        print(f" ⏱️  Tiempo de 3 oráculos:                      {t_ora:.2f} ms")

        if parity_ok and out_match:
            print(" ✅ PARIDAD DE 3 ORÁCULOS: CERTIFICADA Y DEMOSTRADA.")
        else:
            print(" ❌ PARIDAD DE 3 ORÁCULOS FALLIDA.")
            sys.exit(1)


if __name__ == "__main__":
    main()
