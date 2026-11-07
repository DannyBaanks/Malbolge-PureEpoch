"""Suite de pruebas rigurosas para Boss 13: El Acarreo Temporal In-VM (In-VM BCD Ripple-Carry Clock Engine).

CONTRATO CANÓNICO DE AUTONOMÍA Y CÓMPUTO EN RUNTIME (AGENTS.md):
- Ejecución 100% autónoma en lenguaje Classic Malbolge en runtime.
- Cero escrituras de memoria del host durante la ejecución (vm.mem[...] = ... estrictamente prohibido).
- Transición 00:59 -> 01:00 computada enteramente dentro de la VM mediante aritmética de acarreo:
    * Registro S1: 57 ('9') -> 48 ('0') con acarreo
    * Registro S10: 53 ('5') -> 48 ('0') con acarreo (módulo 60)
    * Registro M1: 48 ('0') -> 49 ('1') acarreo absorbido
    * Registro M10: 48 ('0') sin cambio
- Sin secuencias de timestamps precompiladas por Python.
- Paridad estricta entre 3 oráculos (Python Machine M0, C mb_ref, Olmstead 1998).
- Todas las celdas cumplen con el cargador estricto de Olmstead 1998 (strict_byte para las 1,905 celdas).
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
from tools.reloj_carry import (
    CANONICAL_LENGTH,
    CANONICAL_SHA256,
    REG_M10,
    REG_M1,
    REG_S10,
    REG_S1,
    build_reloj_carry,
    run_reloj_carry,
    verify_reloj_carry_algebraic_invariants,
    PURE_EPOCH_ROOT,
)


class TestRelojCarry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw, cls.meta = build_reloj_carry(mode="canonical")
        cls.candidate_mal = PURE_EPOCH_ROOT / "candidates" / "reloj_carry.mal"
        cls.candidate_json = PURE_EPOCH_ROOT / "candidates" / "reloj_carry.json"
        cls.boss13_mal = PURE_EPOCH_ROOT / "candidates" / "boss13_reloj_carry.mal"
        cls.boss13_json = PURE_EPOCH_ROOT / "candidates" / "boss13_reloj_carry.json"

    def test_01_canonical_artifacts_exist_and_match_hash(self):
        """Verifica que los artefactos canónicos existen en candidates/ y coinciden bit-a-bit."""
        self.assertTrue(self.candidate_mal.exists(), "Falta candidates/reloj_carry.mal")
        self.assertTrue(self.candidate_json.exists(), "Falta candidates/reloj_carry.json")
        self.assertTrue(self.boss13_mal.exists(), "Falta candidates/boss13_reloj_carry.mal")
        self.assertTrue(self.boss13_json.exists(), "Falta candidates/boss13_reloj_carry.json")

        disk_bytes = self.candidate_mal.read_bytes()
        disk_sha = hashlib.sha256(disk_bytes).hexdigest()

        self.assertEqual(len(disk_bytes), CANONICAL_LENGTH)
        self.assertEqual(disk_sha, CANONICAL_SHA256)
        self.assertEqual(disk_bytes, self.boss13_mal.read_bytes())

    def test_02_all_cells_satisfy_strict_loader(self):
        """Verifica que cada una de las 1,905 celdas cumple strict_byte sin excepción."""
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
        self.assertEqual(m.steps, 1806)
        self.assertEqual(m.output, b"00:59\n01:00\n")

        # Verificar que la memoria fue mutada por la semántica natural de Malbolge
        self.assertNotEqual(m.mem, initial_mem_snapshot)

    def test_04_algebraic_invariants(self):
        """Verifica los teoremas algebraicos de acarreo BCD en Classic Malbolge."""
        invariants = verify_reloj_carry_algebraic_invariants()
        for name, passed in invariants.items():
            self.assertTrue(passed, f"Fallo en invariante algebraico {name}")

    def test_05_in_vm_computed_carry_register_transition(self):
        """Audita paso a paso la mutación in-VM de los registros durante el acarreo en cascada."""
        mem = load(self.raw)
        m = Machine(mem, b"")

        # 1. Estado inicial antes del acarreo
        self.assertEqual(m.mem[REG_M10], 48)  # '0'
        self.assertEqual(m.mem[REG_M1], 48)   # '0'
        self.assertEqual(m.mem[REG_S10], 53)  # '5'
        self.assertEqual(m.mem[REG_S1], 57)   # '9'

        # Ejecutar Display 1
        while len(m.output) < 6:
            m.tick()
        self.assertEqual(m.output, b"00:59\n")
        self.assertEqual(m.mem[REG_M10], 48)
        self.assertEqual(m.mem[REG_M1], 48)
        self.assertEqual(m.mem[REG_S10], 53)
        self.assertEqual(m.mem[REG_S1], 57)

        # Ejecutar el motor de acarreo in-VM hasta completarlo
        carry_end = self.meta["carry_metrics"]["carry_pc_end"]
        while m.c < carry_end and m.terminal == "RUNNING":
            m.tick()

        # 2. Estado mutado in-VM tras el acarreo en cascada
        self.assertEqual(m.mem[REG_M10], 48, "M10 debe permanecer en '0'")
        self.assertEqual(m.mem[REG_M1], 49, "M1 debió absorber acarreo y cambiar a '1'")
        self.assertEqual(m.mem[REG_S10], 48, "S10 debió hacer rollover mod 60 y cambiar a '0'")
        self.assertEqual(m.mem[REG_S1], 48, "S1 debió hacer rollover y cambiar a '0'")

        # Ejecutar Display 2 y HALT
        while m.terminal == "RUNNING":
            m.tick()

        self.assertEqual(m.output, b"00:59\n01:00\n")
        self.assertEqual(m.terminal, "HALT")

    def test_06_exact_output_0059_to_0100(self):
        """Verifica que la salida completa coincide exactamente con '00:59\\n01:00\\n'."""
        res = run_reloj_carry(self.raw, b"", max_steps=50000)
        self.assertEqual(res["terminal"], "HALT")
        self.assertEqual(res["output"], b"00:59\n01:00\n")

    def test_07_clean_halt_steps(self):
        """Verifica que la máquina alcanza HALT limpio en exactamente 1,806 pasos."""
        res = run_reloj_carry(self.raw, b"", max_steps=50000)
        self.assertEqual(res["steps"], 1806)

    def test_08_triple_oracle_parity(self):
        """Verifica bit-a-bit la paridad de salida entre Machine M0, C mb_ref y Olmstead 1998."""
        report = verify(self.raw, b"", budget=50000)
        self.assertTrue(validate_parity(report), "Discrepancia en paridad estricta entre 3 oráculos")
        self.assertEqual(report["terminal"], "HALT")
        self.assertEqual(report["reference_returncode"], 0)
        self.assertEqual(report["original_returncode"], 0)
        self.assertTrue(report["outputs_equal"])
        self.assertEqual(bytes.fromhex(report["output_hex"]), b"00:59\n01:00\n")

    def test_09_c_olmstead_standalone_execution(self):
        """Ejecuta el binario canónico en build/olmstead (C puro 1998) de forma independiente."""
        olm_bin = PURE_EPOCH_ROOT / "build" / "olmstead"
        self.assertTrue(olm_bin.exists(), "Falta build/olmstead compilado")

        proc = subprocess.run([str(olm_bin), str(self.candidate_mal)], capture_output=True)
        self.assertEqual(proc.returncode, 0, f"Olmstead 1998 retornó código no cero: {proc.returncode}")
        self.assertEqual(proc.stdout, b"00:59\n01:00\n")

    def test_10_negative_control_broken_carry(self):
        """Control negativo: Corromper la constante de acarreo impide la transición a '01:00'."""
        raw_mut, _ = build_reloj_carry(mode="broken_carry")
        res = run_reloj_carry(raw_mut, b"", max_steps=50000)
        # La salida no debe contener '01:00'
        lines = res["output"].decode("latin1", errors="replace").strip().splitlines()
        if len(lines) >= 2:
            self.assertNotEqual(lines[1], "01:00")
        else:
            self.assertNotEqual(res["output"], b"00:59\n01:00\n")

    def test_11_negative_control_broken_eof(self):
        """Control negativo: Corromper la parada HALT impide finalizar limpiamente en paso 1,806."""
        raw_mut, _ = build_reloj_carry(mode="broken_eof")
        res = run_reloj_carry(raw_mut, b"", max_steps=3000)
        self.assertNotEqual(res["steps"], 1806)

    def test_12_negative_control_broken_loader(self):
        """Control negativo: Corromper una celda viola strict_byte y es rechazada por el cargador."""
        raw_mut, _ = build_reloj_carry(mode="broken_loader")
        with self.assertRaises(ValueError):
            load(raw_mut)


if __name__ == "__main__":
    unittest.main()
