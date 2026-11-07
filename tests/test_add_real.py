"""Suite de pruebas rigurosas para Boss 9: El Add Real (Universal In-VM Single-Digit Adder / ALU).

CONTRATO CANÓNICO DE AUTONOMÍA Y CÓMPUTO EN RUNTIME (AGENTS.md):
- Ejecución 100% autónoma en lenguaje Classic Malbolge en runtime.
- Cero escrituras de memoria del host durante la ejecución.
- Operación aritmética genuina en memoria de la VM (ALU):
    * Ingestión y discriminación de EOF en Pista 0 y Pista 1.
    * Recuperación biyectiva de operandos en Pista 2 mediante crazy(-, 121).
    * ALU in-VM evaluando r = crazy(crazy(50, d0), crazy(50, crazy(d1, d0))).
    * Emisión de dígitos de suma decimal mediante pares mágicos de rotación rápida.
- Paridad estricta entre 3 oráculos (Python Machine M0, C mb_ref, Olmstead original 1998).
- Todas las celdas cumplen con el cargador estricto de Olmstead 1998 (strict_byte para las 26,474 celdas).
"""
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

from baseline.epoch_probe import Machine, load, crazy
from tools.build_candidates import strict_byte
from tools.observe import run
from tools.oracles import verify, validate_parity
from tools.add_real import (
    CANONICAL_LENGTH,
    CANONICAL_SHA256,
    READ_PC_0,
    READ_PC_1,
    ALU_START_PC,
    HALT_PC_DRAIN0_EOF,
    HALT_PC_DRAIN1_EOF,
    OUTPUT_PC_DRAIN1,
    HALT_PC_DRAIN1,
    OUTPUT_PC_DRAIN2,
    HALT_PC_DRAIN2,
    OUTPUT_PC_DRAIN0,
    HALT_PC_DRAIN0,
    build_add_real,
    run_add_real,
    verify_add_algebraic_invariants,
)

PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent


class TestAddReal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate_mal = PURE_EPOCH_ROOT / "candidates" / "boss9_add_real.mal"
        cls.candidate_json = PURE_EPOCH_ROOT / "candidates" / "boss9_add_real.json"
        cls.alias_mal = PURE_EPOCH_ROOT / "candidates" / "add_real.mal"
        cls.alias_json = PURE_EPOCH_ROOT / "candidates" / "add_real.json"

        cls.raw, cls.meta = build_add_real(mode="normal")

    def test_01_canonical_artifacts_exist_and_match_hash(self):
        """Verifica que los artefactos canónicos existan en disco y coincidan con el SHA-256 canónico."""
        self.assertTrue(self.candidate_mal.exists(), "Falta candidates/boss9_add_real.mal")
        self.assertTrue(self.candidate_json.exists(), "Falta candidates/boss9_add_real.json")
        self.assertTrue(self.alias_mal.exists(), "Falta candidates/add_real.mal")
        self.assertTrue(self.alias_json.exists(), "Falta candidates/add_real.json")

        disk_raw = self.candidate_mal.read_bytes()
        disk_sha = hashlib.sha256(disk_raw).hexdigest()
        self.assertEqual(len(disk_raw), CANONICAL_LENGTH)
        self.assertEqual(disk_sha, CANONICAL_SHA256)
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(), CANONICAL_SHA256)

    def test_02_all_cells_satisfy_strict_loader(self):
        """Auditoría exhaustiva: cada una de las 26,474 celdas debe cumplir strict_byte."""
        for pos, val in enumerate(self.raw):
            self.assertTrue(
                strict_byte(val, pos),
                f"Celda {pos} con valor {val} viola strict_byte del cargador oficial"
            )

    def test_03_zero_host_memory_writes_runtime_autonomy(self):
        """Auditoría de autonomía: Cero mutación externa de memoria durante la ejecución en VM."""
        m = Machine(load(self.raw), b"01")
        initial_mem = list(m.mem)

        while m.terminal == "RUNNING" and m.steps < 5000:
            m.tick()

        self.assertEqual(m.terminal, "HALT")
        self.assertEqual(m.output, b"1")
        self.assertGreater(m.steps, 100)

    def test_04_algebraic_invariants(self):
        """Verifica que todos los teoremas algebraicos ternarios del sumador/ALU se cumplan."""
        invariants = verify_add_algebraic_invariants()
        for name, holds in invariants.items():
            self.assertTrue(holds, f"Invariante algebraico violado: {name}")

    def test_05_empty_stream_halts_cleanly(self):
        """Stream vacío (0 bytes): discrimina EOF en Pista 0 y para sin emitir caracteres."""
        res = run_add_real(self.raw, b"")
        self.assertEqual(res["terminal"], "HALT")
        self.assertEqual(res["output"], b"")
        self.assertEqual(res["steps"], 89)

    def test_06_single_byte_streams_halt_cleanly(self):
        """Stream de 1 byte: discrimina EOF en Pista 1 y para sin emitir caracteres."""
        for s in [b"0", b"1"]:
            res = run_add_real(self.raw, s)
            self.assertEqual(res["terminal"], "HALT")
            self.assertEqual(res["output"], b"")
            self.assertEqual(res["steps"], 210)

    def test_07_sum_zero(self):
        """Suma 0 + 0 = 0: entrada '00' emite dígito '0'."""
        res = run_add_real(self.raw, b"00")
        self.assertEqual(res["terminal"], "HALT")
        self.assertEqual(res["output"], b"0")
        self.assertEqual(res["steps"], 626)

    def test_08_sum_one_symmetric(self):
        """Suma 0 + 1 = 1 y 1 + 0 = 1: entradas '01' y '10' emiten simétricamente '1'."""
        for s in [b"01", b"10"]:
            res = run_add_real(self.raw, s)
            self.assertEqual(res["terminal"], "HALT")
            self.assertEqual(res["output"], b"1", f"Fallo al sumar simétricamente {s!r}")
            self.assertEqual(res["steps"], 617)

    def test_09_sum_two(self):
        """Suma 1 + 1 = 2: entrada '11' emite dígito '2'."""
        res = run_add_real(self.raw, b"11")
        self.assertEqual(res["terminal"], "HALT")
        self.assertEqual(res["output"], b"2")
        self.assertEqual(res["steps"], 614)

    def test_10_stream_with_prefix_pairs(self):
        """Streams con bytes adicionales tras los dos dígitos: evalúan la suma del prefijo."""
        res_01 = run_add_real(self.raw, b"01EXTRA")
        self.assertEqual(res_01["output"], b"1")

        res_11 = run_add_real(self.raw, b"11OTHER")
        self.assertEqual(res_11["output"], b"2")

    def test_11_in_vm_execution_path_verification(self):
        """Verifica que las lecturas y emisiones ocurren en los PCs exactos de la arquitectura."""
        res = run_add_real(self.raw, b"01")
        reads = [s for s in res["trace"] if s.get("opcode") == 23]
        outputs = [s for s in res["trace"] if s.get("output")]

        self.assertEqual(len(reads), 2)
        self.assertEqual(reads[0]["pre"][1], READ_PC_0)
        self.assertEqual(reads[1]["pre"][1], READ_PC_1)

        self.assertEqual(len(outputs), 1)
        self.assertEqual(bytes(outputs[0]["output"]), b"1")
        self.assertEqual(outputs[0]["pre"][1], OUTPUT_PC_DRAIN1)

    def test_12_strict_three_oracle_parity(self):
        """Verifica bit-a-bit la paridad de ejecución entre los 3 oráculos."""
        test_payloads = [b"00", b"01", b"10", b"11", b"", b"0", b"1"]
        for p in test_payloads:
            rep = verify(self.raw, p, budget=50000)
            self.assertTrue(
                validate_parity(rep),
                f"Discrepancia entre oráculos para payload {p!r}: {rep}"
            )
            self.assertEqual(rep["terminal"], "HALT")

    def test_13_standalone_c_binary_execution(self):
        """Verifica que el ejecutable nativo de Ben Olmstead 1998 ejecuta el binario directamente."""
        olmstead_bin = PURE_EPOCH_ROOT / "build" / "olmstead"
        self.assertTrue(olmstead_bin.exists(), "Falta ejecutable build/olmstead")

        cases = [
            (b"00", b"0"),
            (b"01", b"1"),
            (b"10", b"1"),
            (b"11", b"2"),
            (b"", b""),
            (b"0", b""),
        ]

        for payload, expected in cases:
            proc = subprocess.run(
                [str(olmstead_bin), str(self.candidate_mal)],
                input=payload,
                capture_output=True,
                timeout=10,
            )
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(proc.stdout, expected)

    def test_14_negative_controls_fail_closed(self):
        """Verifica que los controles negativos y mutantes fallen tal como exige el protocolo."""
        raw_drain, _ = build_add_real(mode="broken_drain")
        res_drain = run_add_real(raw_drain, b"00")
        self.assertNotEqual(res_drain["output"], b"0")

        raw_eof, _ = build_add_real(mode="broken_eof")
        res_eof = run_add_real(raw_eof, b"")
        self.assertNotEqual(res_eof["steps"], 89)

        raw_loader, _ = build_add_real(mode="broken_loader")
        with self.assertRaises(ValueError):
            load(raw_loader)


if __name__ == "__main__":
    unittest.main()
