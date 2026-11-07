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

    def test_06_tier2_restore_depends_on_j2(self):
        """Control de auditoría (2026-10-27): corromper J2 al entrar a 6566 cambia el restore.

        La escritura en mem[42] la hace el test, no el protocolo: es un control negativo,
        no parte del camino demostrado.
        """
        from baseline.epoch_probe import Machine, load

        def run_with_j2(payload, j2_value):
            m = Machine(load(self.source), payload)
            poked = False
            for _ in range(20000):
                if not poked and m.c == self.meta["labels"]["recovery_tier_2_entry"]:
                    m.mem[42] = j2_value
                    poked = True
                m.tick()
                if m.terminal != "RUNNING":
                    break
            self.assertTrue(poked)
            return m.terminal, m.output, m.mem[36]

        # J2 de initial=3 dentro de una corrida initial=1 restaura 3, y viceversa
        self.assertEqual(run_with_j2(b"\x01\x03\x03", 29521), ("HALT", b"\x03", 3))
        self.assertEqual(run_with_j2(b"\x03\x03\x03", 29523), ("HALT", b"\x01", 1))
        # Basura en J2 -> basura restaurada
        self.assertEqual(run_with_j2(b"\x01\x03\x03", 12345), ("HALT", b"\x91", 24721))


if __name__ == "__main__":
    unittest.main()
