#!/usr/bin/env python3
"""CLI para ejecutar Boss 4 v3: Motor de Autómata Celular Wolfram Regla 90 In-VM en Malbolge.

REGLA FUNDAMENTAL DE AUTONOMÍA:
- El autómata celular se ejecuta 100% de manera autónoma en lenguaje Malbolge en runtime.
- El binario .mal lee el estado de entrada desde stdin ('1', '2', '3'), calcula el hash in-VM y
  ejecuta la evolución de 8 generaciones mediante aritmética crazy entre vecinos de memoria.
- Traza de memoria in-VM: verifica la evolución celular real dentro de m.mem[G0] y m.mem[G1].
- Verificación estricta entre 3 oráculos (Python Machine, C mb_ref, Olmstead 1998).
"""
import argparse
from pathlib import Path
import sys
import time

PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent
if str(PURE_EPOCH_ROOT) not in sys.path:
    sys.path.append(str(PURE_EPOCH_ROOT))

from baseline.epoch_probe import Machine, load
from tools.boss4_v3_ca import (
    G0,
    G1,
    S0_VAL,
    S1_VAL,
    build_boss4_v3_ca,
    run_boss4_v3,
)
from tools.oracles import verify, validate_parity

DEFAULT_MAL = PURE_EPOCH_ROOT / "candidates" / "boss4_v3_ca.mal"


def main():
    parser = argparse.ArgumentParser(
        description="CLI de Boss 4 v3: Motor de Autómata Celular Wolfram Regla 90 In-VM en Malbolge"
    )
    parser.add_argument(
        "-s", "--state", default=None, choices=["1", "2", "3"],
        help="Estado inicial ('1'=Sierpinski [0,0,1,0,0], '2'=Doble Pulso [0,1,1,0,0], '3'=Alternado [0,1,0,1,0])"
    )
    parser.add_argument(
        "--source", type=Path, default=DEFAULT_MAL,
        help="Ruta al binario .mal precompilado (por defecto candidates/boss4_v3_ca.mal)"
    )
    parser.add_argument(
        "--mode", default="normal", choices=["normal", "broken_hash", "broken_halt"],
        help="Modo de síntesis ('normal', 'broken_hash', 'broken_halt')"
    )
    parser.add_argument(
        "--oracle", "--oracles", action="store_true", dest="oracles",
        help="Verificar paridad estricta entre 3 oráculos (Python Machine, C mb_ref, Olmstead 1998)"
    )
    parser.add_argument(
        "--trace-memory", action="store_true",
        help="Inspeccionar y mostrar la traza de bits en celdas de memoria de la VM generación por generación"
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

    print("=" * 78)
    print(" 🔺 MALBOLGE PURE-EPOCH: BOSS 4 v3 (MOTOR DE AUTÓMATA CELULAR IN-VM REGLA 90) ")
    print("=" * 78)
    print(f" Entrada proporcionada (stdin): {payload!r} (ASCII {payload.decode('ascii', errors='replace')})")

    # Cargar o sintetizar binario
    meta = None
    if args.source.exists() and args.mode == "normal":
        src = args.source.read_bytes()
        print(f" Binario cargado de disco:     {args.source} ({len(src)} bytes)")
    else:
        t_start = time.perf_counter()
        src, meta = build_boss4_v3_ca(mode=args.mode)
        t_synth = (time.perf_counter() - t_start) * 1000
        print(f" Binario sintetizado en memoria ({len(src)} bytes, {t_synth:.2f} ms)")

    print(f" Intervención del host:        ❌ NINGUNA (vm.mem[...] = ... estrictamente prohibido)")
    print(f" Modo de ejecución:            {args.mode.upper()}")
    print("-" * 78)

    # Ejecución sin escrituras del host
    t_exec_start = time.perf_counter()
    res = run_boss4_v3(src, payload)
    t_exec = (time.perf_counter() - t_exec_start) * 1000

    input_consumed = res.get("registers", [0, 0, 0, 0])[3] if "registers" in res else 1

    print(f" Estado terminal VM:           {res['terminal']}")
    print(f" Pasos de ejecución:           {res['steps']}")
    print(f" Bytes de entrada leídos (/):  {input_consumed}")
    print(f" Emisiones de salida (<):      {len(res['output'])} caracteres ({len(res['output'].splitlines())} líneas)")
    print(f" ⏱️  Tiempo de ejecución VM:     {t_exec:.2f} ms")
    print("=" * 78)
    print(" 🎨 SALIDA FRACTAL DEL AUTÓMATA CELULAR EN RUNTIME (8 GENERACIONES):")
    print("=" * 78)
    try:
        print(res["output"].decode("ascii"))
    except UnicodeDecodeError:
        print(repr(res["output"]))
    print("=" * 78)

    if args.trace_memory:
        print(" 🔬 TRAZA DE MEMORIA IN-VM (CELDA POR CELDA, GENERACIÓN POR GENERACIÓN):")
        print("=" * 78)
        if meta is None:
            _, meta = build_boss4_v3_ca(mode="normal")
        state_key = payload.decode("ascii", errors="ignore")
        track_name = "track1_sierpinski" if state_key == "1" else ("track2_double_pulse" if state_key == "2" else "track3_triplet")
        bps = meta["breakpoints"][track_name]

        m = Machine(load(src), payload)
        bp_idx = 0
        while m.terminal == "RUNNING" and bp_idx < len(bps):
            if m.c == bps[bp_idx]["pc"]:
                bp = bps[bp_idx]
                gen = bp["generation"]
                exp = bp["expected_bits"]
                cells = bp["grid_cells"]
                mem_vals = [m.mem[c] for c in cells]
                actual_bits = [1 if v == S1_VAL else (0 if v == S0_VAL else f"?({v})") for v in mem_vals]
                grid_name = "G0" if cells == G0 else "G1"
                status_str = "✅ COINCIDE" if actual_bits == exp else "❌ DISCREPANCIA"
                print(f" Gen {gen} [{grid_name} {cells}]: bits={actual_bits} | mem={mem_vals} | {status_str}")
                bp_idx += 1
            m.tick()
        print("=" * 78)

    if args.oracles:
        print(" 🔍 Verificando paridad estricta entre 3 oráculos...")
        t_ora_start = time.perf_counter()
        rep = verify(src, payload, budget=30000)
        t_ora = (time.perf_counter() - t_ora_start) * 1000

        print(f" Oráculo Python (M0):         HALT={rep['terminal']=='HALT'} ({rep['steps_excluding_halt']} pasos)")
        print(f" Oráculo C Ref (mb_ref):      EXIT={rep['reference_returncode']}")
        print(f" Oráculo C Olmstead (1998):   EXIT={rep['original_returncode']}")
        print(f" Paridad de trazas completas:  {rep['trace_equal']}")
        print(f" Paridad de memoria (59049):   {rep['memory_equal']}")
        print(f" Paridad de registros (a,c,d): {rep['registers_equal']}")
        print(f" Paridad de salida stdout:     {rep['outputs_equal']}")
        print(f" ⏱️  Tiempo de verificación:     {t_ora:.2f} ms")
        print("-" * 78)

        if validate_parity(rep):
            print(" 🏆 VEREDICTO DE ORÁCULOS: PARIDAD ESTRICTA 100% DEMOSTRADA")
        else:
            print(" ❌ VEREDICTO DE ORÁCULOS: PARIDAD FALLIDA")
            sys.exit(1)
        print("=" * 78)


if __name__ == "__main__":
    main()
