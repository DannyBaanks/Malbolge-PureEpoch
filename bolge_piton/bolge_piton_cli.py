#!/usr/bin/env python3
"""CLI para BolgePiton: El meta-intérprete reflexivo de Pitón sobre Malbolge.

Incluye cronometraje de alta resolución (telemetría / flex benchmark)
para contrastar la velocidad del oráculo C frente a la ejecución reflexiva
en Pitón (Pibolge -> BolgePiton -> Micro-Pitón).

Uso:
  python3 bolge_piton_cli.py --texto 'imprimir_texto "Hola Mundo"'
  python3 bolge_piton_cli.py archivo.piton
  python3 bolge_piton_cli.py --ouroboros archivo.piton
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parent
PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent
PIBOLGE_ROOT = Path("/home/danny/Development/ISyCo Git/Pibolge")

if str(LAB_DIR) not in sys.path:
    sys.path.append(str(LAB_DIR))

from micro_piton import compilar_texto_piton, ensamblar_payload
from vm_builder import construir_vm_para_programa


def format_delta(segundos: float) -> str:
    """Formatea la duración con precisión humana (ms / µs)."""
    if segundos < 0.001:
        return f"{segundos * 1_000_000:.2f} µs"
    elif segundos < 1.0:
        return f"{segundos * 1_000:.2f} ms"
    else:
        return f"{segundos:.4f} s"


def ejecutar_demostracion(codigo_piton: str, modo_ouroboros: bool = True):
    print("=" * 68)
    print("  ⚡ BOLGE-PITON: VM DE PITÓN EN MALBOLGE (INVERSA DE PIBOLGE) ⚡")
    print("=" * 68)
    print("\n[1] Código fuente en Micro-Pitón:")
    print("-" * 50)
    print(codigo_piton.strip())
    print("-" * 50)

    # 1. Compilación de Micro-Pitón
    t0_comp = time.perf_counter()
    instrucciones = compilar_texto_piton(codigo_piton)
    payload = ensamblar_payload(instrucciones)
    t1_comp = time.perf_counter()
    t_comp = t1_comp - t0_comp
    print(f"\n[2] Compilación exitosa: {len(instrucciones)} instrucciones generadas en {format_delta(t_comp)}.")
    print(f"    Payload stdin: {list(payload)} ({len(payload)} bytes)")

    # 2. Síntesis de la VM en Malbolge (.mal)
    t0_synth = time.perf_counter()
    vm_mal = construir_vm_para_programa(instrucciones)
    vm_path = LAB_DIR / "bolge_piton_vm.mal"
    vm_path.write_bytes(vm_mal)
    t1_synth = time.perf_counter()
    t_synth = t1_synth - t0_synth
    print(f"\n[3] VM sintetizada en Malbolge puro: {vm_path.name} ({len(vm_mal)} bytes) en {format_delta(t_synth)}.")

    # 3. Ejecución en Oráculo C
    mb_ref = PURE_EPOCH_ROOT / "build" / "mb_ref"
    t0_c = time.perf_counter()
    res_c = subprocess.run([str(mb_ref), str(vm_path), "50000"], input=payload, capture_output=True)
    t1_c = time.perf_counter()
    t_c = t1_c - t0_c
    print(f"\n[4] Oráculo C Nativo (mb_ref):")
    print(f"    Salida stdout : {res_c.stdout}")
    print(f"    Código retorno: {res_c.returncode}")
    print(f"    ⏱️  Cronómetro : {format_delta(t_c)}")

    # 4. Modo Ouroboros (Pitón corriendo Malbolge corriendo Pitón)
    t_pi = None
    if modo_ouroboros:
        pibolge = PIBOLGE_ROOT / "pibolge.piton"
        print(f"\n[5] Modo Ouroboros (pibolge.piton -> bolge_piton_vm.mal -> script pitón):")
        t0_pi = time.perf_counter()
        res_pi = subprocess.run(
            ["python3", "-m", "piton.cli", "ejecutar", str(pibolge), str(vm_path), "50000"],
            input=payload,
            capture_output=True,
        )
        t1_pi = time.perf_counter()
        t_pi = t1_pi - t0_pi
        salida_pi = res_pi.stdout
        if salida_pi.endswith(b"\n"):
            salida_pi = salida_pi[:-1]
        print(f"    Salida stdout : {salida_pi}")
        print(f"    ⏱️  Cronómetro : {format_delta(t_pi)}")
        print(f"    Paridad C <-> Piton: {'IDÉNTICA ✅' if salida_pi == res_c.stdout else 'DIVERGENCIA ❌'}")

    # Panel de Telemetría y Flex
    print("\n" + "┌" + "─" * 66 + "┐")
    print("│                     🏁 TELEMETRÍA Y BENCHMARK                    │")
    print("├" + "─" * 66 + "┤")
    print(f"│  • Compilador Micro-Pitón   : {format_delta(t_comp):<40} │")
    print(f"│  • Síntesis VM Malbolge     : {format_delta(t_synth):<40} │")
    print(f"│  • Ejecución Oráculo C      : {format_delta(t_c):<40} │")
    if t_pi is not None:
        print(f"│  • Ejecución Ouroboros      : {format_delta(t_pi):<40} │")
        ratio = t_pi / t_c if t_c > 0 else 0
        print(f"│  • Ratio Ouroboros / C      : {ratio:.1f}x (CPython + Pibolge VM)                │")
    print("└" + "─" * 66 + "┘")
    print("\n" + "=" * 68)
    print("  🚀 DEMOSTRACIÓN FINALIZADA CON ÉXITO")
    print("=" * 68)


def main():
    parser = argparse.ArgumentParser(description="BolgePiton: VM de Pitón en Malbolge.")
    parser.add_argument("archivo", nargs="?", help="Ruta al script .piton")
    parser.add_argument("--texto", "-t", help="Código en línea a ejecutar")
    parser.add_argument("--no-ouroboros", action="store_true", help="Omitir ejecución en Pibolge")
    args = parser.parse_args()

    if args.texto:
        codigo = args.texto
    elif args.archivo:
        codigo = Path(args.archivo).read_text(encoding="utf-8")
    else:
        # Ejemplo por defecto
        codigo = """
        # Saludo y cálculo ternario en Micro-Pitón
        imprimir_texto "Hola Piton! Resultado: "
        cargar 65
        locura 3
        imprimir
        parar
        """

    ejecutar_demostracion(codigo, modo_ouroboros=not args.no_ouroboros)


if __name__ == "__main__":
    main()
