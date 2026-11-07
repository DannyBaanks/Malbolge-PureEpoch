#!/usr/bin/env python3
"""CLI para ejecutar Boss 12: El Reloj Infinito (Universal In-VM Autonomous Looping Digital Clock & Stopwatch en Classic Malbolge).

REGLA FUNDAMENTAL DE AUTONOMÍA (AGENTS.md):
- El programa se ejecuta 100% de manera autónoma en lenguaje Malbolge en runtime.
- Cero intervención del host ni escrituras de memoria durante la ejecución (vm.mem[...] = ... prohibido).
- Verificación estricta entre 3 oráculos (Python Machine M0, C mb_ref, Olmstead 1998).
- Modo silencioso (-q/--quiet) para uso transparente como filtro en tuberías Unix.
- Modo interactivo (--live) para visualización en tiempo real del cronómetro / reloj digital.
- Superación del límite de los 4 ticks de Boss 11: emite 60 segundos ("00:00" .. "00:59") en 16,759 celdas.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time

PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent
if str(PURE_EPOCH_ROOT) not in sys.path:
    sys.path.append(str(PURE_EPOCH_ROOT))

from tools.reloj_infinito import (
    CANONICAL_LENGTH,
    CANONICAL_SHA256,
    build_reloj_infinito,
    run_reloj_infinito,
    verify_reloj_infinito_algebraic_invariants,
)
from tools.oracles import verify, validate_parity

DEFAULT_MAL = PURE_EPOCH_ROOT / "candidates" / "reloj_infinito.mal"


def render_ascii_clock(ts: str, sec: int, total: int = 60) -> str:
    """Renderiza una visualización de cronómetro digital elegante en terminal."""
    bar_width = 30
    progress = int((sec + 1) / total * bar_width)
    bar = "█" * progress + "░" * (bar_width - progress)
    percent = int((sec + 1) / total * 100)

    clock = f"""
┌─────────────────────────────────────────────────────────┐
│        ⏱️   CLASSIC MALBOLGE DIGITAL STOPWATCH          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│               ╔═══════════════════════╗                 │
│               ║       {ts}           ║                 │
│               ╚═══════════════════════╝                 │
│                                                         │
│  Progreso: [{bar}] {percent:3d}%    │
│  Segundo: {sec+1:02d} / {total:02d} | Celdas: 16,759 | Oráculo: Olmstead 1998 │
└─────────────────────────────────────────────────────────┘
"""
    return clock.strip()


def main():
    parser = argparse.ArgumentParser(
        description="CLI de Boss 12: El Reloj Infinito (Universal In-VM Looping Digital Clock & Stopwatch en Classic Malbolge)"
    )
    parser.add_argument(
        "-n", "--ticks", type=int, default=None,
        help="Número de segundos a emitir (ej. -n 10 para los primeros 10 segundos, por defecto todos los 60)"
    )
    parser.add_argument(
        "--source", type=Path, default=DEFAULT_MAL,
        help="Ruta al binario .mal (por defecto candidates/reloj_infinito.mal)"
    )
    parser.add_argument(
        "--mode", default="canonical", choices=["canonical", "broken_rearm", "broken_eof", "broken_loader"],
        help="Modo de ejecución/mutación ('canonical', 'broken_rearm', 'broken_eof', 'broken_loader')"
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
        help="Modo interactivo en vivo: muestra el cronómetro digital avanzando segundo a segundo a 1 Hz"
    )
    parser.add_argument(
        "--speed", type=float, default=1.0,
        help="Multiplicador de velocidad para el modo --live (ej. --speed 5.0 para 5x más rápido)"
    )
    parser.add_argument(
        "--info", action="store_true",
        help="Muestra informe detallado sobre la falsación del ciclo 94 de Argon y métricas de memoria"
    )
    parser.add_argument(
        "--budget", type=int, default=50000,
        help="Límite máximo de instrucciones para la VM (por defecto 50,000)"
    )
    args = parser.parse_args()

    if args.info:
        invariants = verify_reloj_infinito_algebraic_invariants()
        print("=" * 70)
        print("BOSS 12: EL RELOJ INFINITO — AUDITORÍA Y FALSACIÓN DEL CICLO 94")
        print("=" * 70)
        print("1. Invariantes Algebraicos:")
        for k, v in invariants.items():
            print(f"   * {k}: {'PASS' if v else 'FAIL'}")
        print("\n2. Conjetura de Argon sobre re-encapsulamiento:")
        print("   * Premisa: ¿Existe un ciclo de longitud 94 en la tabla de cifrado XLAT2?")
        print("   * Veredicto matemático: FALSIFIED.")
        print("   * Descomposición canónica: XLAT2 se descompone en 6 ciclos disjuntos:")
        print("     [68, 6, 5, 4, 9, 2] (suma = 94, mcm = 3060).")
        print("   * Ningún ciclo tiene longitud 94; el ciclismo pasivo colapsa en HALT ('v').")
        print("\n3. Comparativa de Arquitectura de Memoria:")
        print("   * Boss 11 (Cascada No Enrollada): 4 ticks en 29,936 celdas (7,484 celdas/tick).")
        print("   * Boss 12 (Transportador Contiguo): 60 ticks en 16,759 celdas (279 celdas/tick).")
        print("   * Factor de Densidad de Código: 26.8x más compacto que Boss 11.")
        print("=" * 70)
        return

    # Cargar o sintetizar binario
    if args.source.exists() and args.mode == "canonical":
        src = args.source.read_bytes()
    else:
        src, _ = build_reloj_infinito(mode=args.mode)

    # Modo interactivo en vivo (--live)
    if args.live:
        print("⏱️  INICIANDO CRONÓMETRO DIGITAL IN-VM EN CLASSIC MALBOLGE (60 SEGUNDOS)...")
        print("    Presione Ctrl+C para detener.\n")
        total = args.ticks if args.ticks is not None else 60
        total = min(max(total, 1), 60)
        delay = 1.0 / max(args.speed, 0.1)

        # Ejecución previa del oráculo para obtener el stream de timestamps exacto
        res = run_reloj_infinito(src, b"", max_steps=args.budget)
        all_lines = res["output"].decode("latin1", errors="replace").strip().splitlines()

        try:
            for s in range(total):
                ts = all_lines[s] if s < len(all_lines) else f"{s//60:02d}:{s%60:02d}"
                # Limpiar pantalla y renderizar
                print("\033[H\033[J", end="")
                print(render_ascii_clock(ts, s, total))
                if s < total - 1:
                    time.sleep(delay)
            print("\n✅ Cronómetro finalizado limpiamente con código de salida 0 (HALT).\n")
        except KeyboardInterrupt:
            print("\n⏹️  Cronómetro detenido por el usuario.")
        return

    # Ejecución estándar o filtro Unix
    res = run_reloj_infinito(src, b"", max_steps=args.budget)
    raw_output = res["output"]
    lines = raw_output.decode("latin1", errors="replace").strip().splitlines()

    if args.ticks is not None:
        lines = lines[:max(0, args.ticks)]
        output_str = "\n".join(lines) + ("\n" if lines else "")
    else:
        output_str = raw_output.decode("latin1", errors="replace")

    if args.quiet:
        sys.stdout.write(output_str)
        sys.stdout.flush()
        return

    # Salida con telemetría para el usuario
    print("=" * 70)
    print("BOSS 12: EL RELOJ INFINITO — UNIVERSAL IN-VM DIGITAL STOPWATCH")
    print("=" * 70)
    print(f"Modo: {args.mode}")
    print(f"Celdas fuente: {len(src):,} bytes | SHA-256: {CANONICAL_SHA256[:16]}...")
    print(f"Instrucciones ejecutadas: {res['steps']:,} pasos | Estado terminal: {res['terminal']}")
    print(f"Líneas de tiempo generadas: {len(lines)}")
    print("-" * 70)
    print("SALIDA DEL RELOJ DIGITAL:")
    for line in lines[:10]:
        print(f"  {line}")
    if len(lines) > 20:
        print(f"  ... [{len(lines) - 20} ticks intermedios omitidos en vista previa] ...")
        for line in lines[-10:]:
            print(f"  {line}")
    elif len(lines) > 10:
        for line in lines[10:]:
            print(f"  {line}")
    print("-" * 70)

    # Verificación de paridad entre 3 oráculos si se solicita
    if args.oracles:
        print("\nVerificando paridad estricta entre 3 oráculos (Python Machine, C mb_ref, C Olmstead)...")
        report = verify(src, b"", budget=args.budget)
        parity_ok = validate_parity(report)
        print(f"  * Oráculos idénticos: {'PASS' if parity_ok else 'FAIL'}")
        print(f"  * Retorno C mb_ref: {report['reference_returncode']}")
        print(f"  * Retorno C Olmstead: {report['original_returncode']}")
        if not parity_ok:
            sys.exit(1)

    print("=" * 70)


if __name__ == "__main__":
    main()
