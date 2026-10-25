"""Test Suite para Boss 1: Falla Bizantina en Cascada (Rollback del Rollback).

Demuestra la recuperación en 2 niveles de transacciones anidadas:
- Nivel 0: Camino limpio (0 fallas).
- Nivel 1: Falla primaria recuperada desde Journal J1 (celda 52).
- Nivel 2: Falla secundaria consecutiva (bizantina) detectada in-band y recuperada
  desde Journal Secundario J2 (celda 42) hacia modo Safe-Mode certificado.
"""
import unittest
from pathlib import Path

from tools import boss1_byzantine, observe
from tools.oracles import verify


class TestBoss1Byzantine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source, cls.meta = boss1_byzantine.build_boss1_byzantine()

    def test_01_clean_path_zero_faults(self):
        """Caso A: Candidato 1 válido -> commit directo sin visitas a recuperación."""
        res = observe.run(self.source, b"\x01\x01\x01")
        self.assertEqual(res["terminal"], "HALT")
        self.assertEqual(res["output"], b"V")
        pcs = [e["pre"][1] for e in res["trace"]]
        self.assertEqual(pcs.count(self.meta["labels"]["recovery_jump"]), 0)
        self.assertEqual(pcs.count(self.meta["labels"]["recovery_tier_2_entry"]), 0)

    def test_02_single_fault_tier1_recovery(self):
        """Caso B: Falla en Intento 1 -> Restauración desde J1 (52) -> Intento 2 exitoso."""
        res = observe.run(self.source, b"\x01\x03\x01")
        self.assertEqual(res["terminal"], "HALT")
        self.assertEqual(res["output"], b"V")
        pcs = [e["pre"][1] for e in res["trace"]]
        # Visitó recuperación de Nivel 1 exactamente 1 vez
        self.assertEqual(pcs.count(self.meta["labels"]["recovery_jump"]), 1)
        # Cero visitas a recuperación de Nivel 2
        self.assertEqual(pcs.count(self.meta["labels"]["recovery_tier_2_entry"]), 0)

    def test_03_cascading_double_fault_tier2_byzantine(self):
        """Caso C (Boss 1): Falla en Intento 1 Y Falla en Intento 2 -> Restauración J2 (42)."""
        res = observe.run(self.source, b"\x01\x03\x03", max_steps=10000)
        self.assertEqual(res["terminal"], "HALT")
        # El estado inicial 1 fue restaurado desde J2 y emitido como diagnóstico
        self.assertEqual(res["output"], b"\x01")
        pcs = [e["pre"][1] for e in res["trace"]]
        # Visitó Nivel 1 y Nivel 2
        self.assertGreaterEqual(pcs.count(self.meta["labels"]["recovery_jump"]), 1)
        self.assertEqual(pcs.count(self.meta["labels"]["recovery_tier_2_entry"]), 1)

    def test_04_cascading_double_fault_initial_3(self):
        """Caso D: Misma doble falla con selector inicial 3 -> Restaura estado 3 desde J2."""
        res = observe.run(self.source, b"\x03\x03\x03", max_steps=10000)
        self.assertEqual(res["terminal"], "HALT")
        self.assertEqual(res["output"], b"\x03")
        pcs = [e["pre"][1] for e in res["trace"]]
        self.assertEqual(pcs.count(self.meta["labels"]["recovery_tier_2_entry"]), 1)

    def test_05_three_oracle_parity(self):
        """Paridad estricta entre Python, mb_ref (C) y Olmstead original de 1998."""
        for payload in [b"\x01\x01\x01", b"\x01\x03\x01", b"\x01\x03\x03", b"\x03\x03\x03"]:
            with self.subTest(payload=payload):
                report = verify(self.source, payload)
                for key in ["trace_equal", "memory_equal", "registers_equal", "terminal_equal", "outputs_equal"]:
                    self.assertTrue(report[key], f"Discrepancia en {key} con payload {list(payload)}")
                self.assertEqual(report["reference_returncode"], 0)
                self.assertEqual(report["original_returncode"], 0)


if __name__ == "__main__":
    unittest.main()
