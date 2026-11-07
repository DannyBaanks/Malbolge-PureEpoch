#!/usr/bin/env python3
"""CLI para ejecutar Boss 4 Real: Autómata Celular Wolfram Regla 90 Dinámico en Malbolge.

REGLA FUNDAMENTAL DE AUTONOMÍA:
- El autómata celular se ejecuta 100% de manera autónoma en lenguaje Malbolge en runtime.
- El binario .mal lee el estado de entrada desde stdin ('1', '2', '3'), calcula el hash in-VM y
  despacha dinámicamente la trayectoria de 8 generaciones sin intervención del host.
- Verificación estricta entre 3 oráculos (Python Machine, C mb_ref, Olmstead 1998).
"""
import argparse
from pathlib import Path
import sys
import time

PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent
if str(PURE_EPOCH_ROOT) not in sys.path:
    sys.path.append(str(PURE_EPOCH_ROOT))

from tools.boss4_real_ca import build_boss4_real_ca, run_boss4_real
from tools.oracles import verify, validate_parity

DEFAULT_MAL = PURE_EPOCH_ROOT / "candidates" / "boss4_real_ca.mal"


def main():
    parser = argparse.ArgumentParser(
        description="CLI de Boss 4 Real: Autómata Celular Dinámico Wolfram Regla 90 en Malbolge"
    )
    parser.add_argument(
        "-s", "--state", default=None, choices=["1", "2", "3"],
        help="Estado de configuración inicial ('1'=Sierpinski, '2'=Doble Pulso, '3'=Triplete)"
    )
    parser.add_argument(
        "--source", type=Path, default=DEFAULT_MAL,
        help="Ruta al binario .mal precompilado (por defecto candidates/boss4_real_ca.mal)"
    )
    parser.add_argument(
        "--mode", default="normal", choices=["normal", "broken_hash", "broken_halt"],
        help="Modo de síntesis ('normal', 'broken_hash', 'broken_halt')"
    )
    parser.add_argument(
        "--oracle", "--oracles", action="store_true", dest="oracles",
        help="Verificar paridad estricta entre 3 oráculos (Python Machine, C mb_ref, Olmstead 1998)"
    )
    args = parser.parse_args()

    # Determinar el payload de entrada: argumento --state o stdin
    if args.state is not None:
        payload = args.state.encode("ascii")
    elif not sys.stdin.isatty():
        raw_in = sys.stdin.buffer.read()
        payload = raw_in[:1] if raw_in else b"1"
    else:
        payload = b"1"

    print("=" * 75)
    print(" 🔺 MALBOLGE PURE-EPOCH: BOSS 4 REAL (AUTÓMATA CELULAR DINÁMICO REGLA 90) ")
    print("=" * 75)
    print(f" Entrada proporcionada (stdin): {payload!r} (ASCII {payload.decode('ascii', errors='replace')})")

    # Cargar o sintetizar binario
    if args.source.exists() and args.mode == "normal":
        src = args.source.read_bytes()
        print(f" Binario cargado de disco:     {args.source} ({len(src)} bytes)")
    else:
        t_start = time.perf_counter()
        src, meta = build_boss4_real_ca(generations=8, mode=args.mode)
        t_synth = (time.perf_counter() - t_start) * 1000
        print(f" Binario sintetizado en memoria ({len(src)} bytes, {t_synth:.2f} ms)")

    print(f" Intervención del host:        ❌ NINGUNA (vm.mem[...] = ... estrictamente prohibido)")
    print(f" Modo de ejecución:            {args.mode.upper()}")
    print("-" * 75)

    # Ejecución sin escrituras del host
    t_exec_start = time.perf_counter()
    res = run_boss4_real(src, payload)
    t_exec = (time.perf_counter() - t_exec_start) * 1000

    input_consumed = res.get("registers", [0, 0, 0, 0])[3] if "registers" in res else 1

    print(f" Estado terminal VM:           {res['terminal']}")
    print(f" Pasos de ejecución:           {res['steps']}")
    print(f" Bytes de entrada leídos (/):  {input_consumed}")
    print(f" Emisiones de salida (<):      {len(res['output'])} caracteres")
    print(f" ⏱️  Tiempo de ejecución VM:     {t_exec:.2f} ms")
    print("=" * 75)
    print(" 🎨 SALIDA DEL AUTÓMATA CELULAR EN RUNTIME (8 GENERACIONES):")
    print("=" * 75)
    try:
        print(res["output"].decode("ascii"))
    except UnicodeDecodeError:
        print(repr(res["output"]))
    print("=" * 75)

    if args.oracles:
        print(" 🔍 Verificando paridad estricta entre 3 oráculos...")
        t_ora_start = time.perf_counter()
        rep = verify(src, payload, budget=20000)
        t_ora = (time.perf_counter() - t_ora_start) * 1000

        parity_ok = validate_parity(rep)
        out_match = bytes.fromhex(rep["output_hex"]) == res["output"]

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
