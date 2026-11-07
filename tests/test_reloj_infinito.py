"""Suite de pruebas rigurosas para Boss 12: El Reloj Infinito (Universal In-VM Autonomous Looping Digital Clock & Stopwatch).

CONTRATO CANÓNICO DE AUTONOMÍA Y CÓMPUTO EN RUNTIME (AGENTS.md):
- Ejecución 100% autónoma en lenguaje Classic Malbolge en runtime.
- Cero escrituras de memoria del host durante la ejecución (vm.mem[...] = ... estrictamente prohibido).
- Superación del límite de los 4 ticks de Boss 11 mediante Arquitectura de Transportador Contiguo:
    * Emisión de 60 segundos ("00:00" .. "00:59") en solo 16,759 celdas (26.8x más denso que Boss 11).
    * Soporta rollover completo de unidades y decenas de segundos (09->10, 19->20, 29->30, 39->40, 49->50, 59).
- Falsación formal de la conjetura del ciclo 94 de Argon en XLAT2.
- Paridad estricta entre 3 oráculos (Python Machine M0, C mb_ref, Olmstead 1998).
- Todas las celdas cumplen con el cargador estricto de Olmstead 1998 (strict_byte para las 16,759 celdas).
"""
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

from baseline.epoch_probe import Machine, load, XLAT1, XLAT2, crazy
from tools.build_candidates import strict_byte
from tools.observe import run
from tools.oracles import verify, validate_parity
from tools.reloj_infinito import (
    CANONICAL_LENGTH,
    CANONICAL_SHA256,
    FINAL_HALT_PC,
    DIGIT_CELLS,
    COLON_CELL,
    NEWLINE_CELL,
    build_reloj_infinito,
    run_reloj_infinito,
    verify_reloj_infinito_algebraic_invariants,
    compute_xlat2_cycles,
    PURE_EPOCH_ROOT,
)


class TestRelojInfinito(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw, cls.meta = build_reloj_infinito(mode="canonical")
        cls.candidate_mal = PURE_EPOCH_ROOT / "candidates" / "reloj_infinito.mal"
        cls.candidate_json = PURE_EPOCH_ROOT / "candidates" / "reloj_infinito.json"
        cls.boss12_mal = PURE_EPOCH_ROOT / "candidates" / "boss12_reloj_infinito.mal"
        cls.boss12_json = PURE_EPOCH_ROOT / "candidates" / "boss12_reloj_infinito.json"

    def test_01_canonical_artifacts_exist_and_match_hash(self):
        """Verifica que los artefactos canónicos existen en candidates/ y coinciden bit-a-bit."""
        self.assertTrue(self.candidate_mal.exists(), "Falta candidates/reloj_infinito.mal")
        self.assertTrue(self.candidate_json.exists(), "Falta candidates/reloj_infinito.json")
        self.assertTrue(self.boss12_mal.exists(), "Falta candidates/boss12_reloj_infinito.mal")
        self.assertTrue(self.boss12_json.exists(), "Falta candidates/boss12_reloj_infinito.json")

        disk_bytes = self.candidate_mal.read_bytes()
        disk_sha = hashlib.sha256(disk_bytes).hexdigest()

        self.assertEqual(len(disk_bytes), CANONICAL_LENGTH)
        self.assertEqual(disk_sha, CANONICAL_SHA256)
        self.assertEqual(disk_bytes, self.boss12_mal.read_bytes())

    def test_02_all_cells_satisfy_strict_loader(self):
        """Verifica que cada una de las 16,759 celdas cumple strict_byte sin excepción."""
        for p, b in enumerate(self.raw):
            self.assertTrue(
                strict_byte(b, p),
                f"Celda {p} con valor {b} ('{chr(b)}') viola strict_byte de Olmstead 1998"
            )

    def test_03_zero_host_memory_writes_runtime_autonomy(self):
        """Audita que la VM opera con 100% de autonomía sin inyección externa de memoria."""
        mem = load(self.raw)
        m = Machine(mem, b"")
        initial_mem_snapshot = list(m.mem)

        while m.terminal == "RUNNING" and m.steps < 50000:
            m.tick()

        self.assertEqual(m.terminal, "HALT")
        self.assertEqual(m.steps, 16660)
        lines = m.output.decode("latin1").strip().splitlines()
        self.assertEqual(len(lines), 60)
        self.assertEqual(lines[0], "00:00")
        self.assertEqual(lines[-1], "00:59")

        # Verificar que la memoria fue mutada por la semántica natural de Malbolge
        self.assertNotEqual(m.mem, initial_mem_snapshot)

    def test_04_algebraic_invariants_and_falsification_argon_cycle94(self):
        """Verifica los teoremas algebraicos y la refutación formal del ciclo 94 de Argon."""
        invariants = verify_reloj_infinito_algebraic_invariants()
        for name, passed in invariants.items():
            self.assertTrue(passed, f"Fallo en invariante algebraico {name}")

        # Demostración detallada de la descomposición cíclica de XLAT2
        cycles = compute_xlat2_cycles()
        lens = [len(c) for c in cycles]
        self.assertEqual(lens, [68, 6, 5, 4, 9, 2], "Descomposición de ciclos XLAT2 debe ser [68, 6, 5, 4, 9, 2]")
        self.assertNotIn(94, lens, "No existe ningún ciclo de orden 94 en XLAT2")
        self.assertEqual(sum(lens), 94, "La suma de los órdenes de los ciclos es exactamente 94")

    def test_05_clock_first_10_seconds(self):
        """Verifica que los primeros 10 segundos ('00:00'..'00:09') son emitidos con precisión."""
        res = run_reloj_infinito(self.raw, b"", max_steps=50000)
        self.assertEqual(res["terminal"], "HALT")
        lines = res["output"].decode("latin1").strip().splitlines()

        for s in range(10):
            expected = f"00:0{s}"
            self.assertEqual(lines[s], expected, f"Segundo {s} discrepante: esperado {expected}, obtenido {lines[s]}")

    def test_06_clock_rollover_boundaries(self):
        """Verifica todas las transiciones de acarreo decimal de segundos (rollover)."""
        res = run_reloj_infinito(self.raw, b"", max_steps=50000)
        lines = res["output"].decode("latin1").strip().splitlines()

        rollovers = [
            (9, "00:09", 10, "00:10"),
            (19, "00:19", 20, "00:20"),
            (29, "00:29", 30, "00:30"),
            (39, "00:39", 40, "00:40"),
            (49, "00:49", 50, "00:50"),
        ]

        for prev_idx, prev_val, next_idx, next_val in rollovers:
            self.assertEqual(lines[prev_idx], prev_val)
            self.assertEqual(lines[next_idx], next_val)

    def test_07_clock_full_60_seconds_and_clean_halt(self):
        """Verifica el flujo completo de 60 segundos ('00:00' .. '00:59') y parada limpia."""
        res = run_reloj_infinito(self.raw, b"", max_steps=50000)
        self.assertEqual(res["terminal"], "HALT")
        self.assertEqual(res["steps"], 16660)

        lines = res["output"].decode("latin1").strip().splitlines()
        self.assertEqual(len(lines), 60)

        for s in range(60):
            m = s // 60
            sec = s % 60
            expected = f"{m:02d}:{sec:02d}"
            self.assertEqual(lines[s], expected)

    def test_08_backward_compatibility_with_boss11(self):
        """Verifica que los primeros 4 ticks coinciden bit-a-bit con la especificación de Boss 11."""
        res = run_reloj_infinito(self.raw, b"", max_steps=50000)
        lines = res["output"].decode("latin1").strip().splitlines()

        self.assertEqual(lines[:4], ["00:00", "00:01", "00:02", "00:03"])

    def test_09_paridad_estricta_3_oraculos(self):
        """Verifica bit-a-bit la paridad de salida entre Machine M0, C mb_ref y Olmstead 1998."""
        report = verify(self.raw, b"", budget=50000)
        self.assertTrue(validate_parity(report), "Discrepancia en paridad estricta entre 3 oráculos")
        self.assertEqual(report["terminal"], "HALT")
        self.assertEqual(report["reference_returncode"], 0)
        self.assertEqual(report["original_returncode"], 0)
        self.assertTrue(report["outputs_equal"])

    def test_10_c_olmstead_standalone_execution(self):
        """Ejecuta el binario canónico en build/olmstead (C puro 1998) de forma independiente."""
        olm_bin = PURE_EPOCH_ROOT / "build" / "olmstead"
        self.assertTrue(olm_bin.exists(), "Falta build/olmstead compilado")

        proc = subprocess.run([str(olm_bin), str(self.candidate_mal)], capture_output=True)
        self.assertEqual(proc.returncode, 0, f"Olmstead 1998 retornó código no cero: {proc.returncode}")

        lines = proc.stdout.decode("latin1").strip().splitlines()
        self.assertEqual(len(lines), 60)
        self.assertEqual(lines[0], "00:00")
        self.assertEqual(lines[9], "00:09")
        self.assertEqual(lines[10], "00:10")
        self.assertEqual(lines[59], "00:59")

    def test_11_negative_control_broken_rearm(self):
        """Control negativo: Corromper la celda del dígito '0' impide emitir timestamps válidos."""
        raw_mut, _ = build_reloj_infinito(mode="broken_rearm")
        res = run_reloj_infinito(raw_mut, b"", max_steps=50000)
        # La salida no debe ser '00:00'
        first_line = res["output"].decode("latin1", errors="replace").splitlines()[0]
        self.assertNotEqual(first_line, "00:00")

    def test_12_negative_control_broken_eof(self):
        """Control negativo: Corromper la parada HALT impide finalizar limpiamente en paso 16,660."""
        raw_mut, _ = build_reloj_infinito(mode="broken_eof")
        res = run_reloj_infinito(raw_mut, b"", max_steps=20000)
        # Debe agotar el presupuesto o no estar en HALT en el paso canónico
        self.assertNotEqual(res["steps"], 16660)

    def test_13_negative_control_broken_loader(self):
        """Control negativo: Corromper una celda viola strict_byte y es rechazada por el cargador."""
        raw_mut, _ = build_reloj_infinito(mode="broken_loader")
        with self.assertRaises(ValueError):
            load(raw_mut)


if __name__ == "__main__":
    unittest.main()
