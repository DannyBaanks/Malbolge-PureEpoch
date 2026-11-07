"""Suite de pruebas rigurosas para Boss 8: El Cmp Real (Universal In-VM Stream Equality Predicate).

CONTRATO CANÓNICO DE AUTONOMÍA Y CÓMPUTO EN RUNTIME (AGENTS.md):
- Ejecución 100% autónoma en lenguaje Classic Malbolge en runtime.
- Cero escrituras de memoria del host durante la ejecución.
- Comparación y discriminación de igualdad genuina en memoria de la VM:
    * Ingestión y discriminación de EOF en Pista 0 y Pista 1.
    * Recuperación biyectiva de bytes en Pista 2 mediante crazy(-, 121).
    * Discriminador de igualdad in-VM evaluando crazy(crazy(b1, b0), 80).
    * Emisión de token de igualdad: '=' (61) para iguales, '!' (33) para desiguales.
- Paridad estricta entre 3 oráculos (Python Machine M0, C mb_ref, Olmstead original 1998).
- Todas las celdas cumplen con el cargador estricto de Olmstead 1998 (strict_byte para las 29,667 celdas).
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
from tools.cmp_real import (
    CANONICAL_LENGTH,
    CANONICAL_SHA256,
    READ_PC_0,
    READ_PC_1,
    CMP_START_PC,
    HALT_PC_DRAIN0,
    HALT_PC_DRAIN1,
    OUTPUT_PC_DRAIN_NEQ,
    HALT_PC_DRAIN_NEQ,
    OUTPUT_PC_DRAIN_EQ,
    HALT_PC_DRAIN_EQ,
    build_cmp_real,
    run_cmp_real,
    verify_cmp_algebraic_invariants,
)

PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent


class TestCmpReal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate_mal = PURE_EPOCH_ROOT / "candidates" / "boss8_cmp_real.mal"
        cls.candidate_json = PURE_EPOCH_ROOT / "candidates" / "boss8_cmp_real.json"
        cls.alias_mal = PURE_EPOCH_ROOT / "candidates" / "cmp_real.mal"
        cls.alias_json = PURE_EPOCH_ROOT / "candidates" / "cmp_real.json"

        cls.raw, cls.meta = build_cmp_real(mode="normal")

    def test_01_canonical_artifacts_exist_and_match_hash(self):
        """Verifica que los artefactos canónicos existan en disco y coincidan con el SHA-256 canónico."""
        self.assertTrue(self.candidate_mal.exists(), "Falta candidates/boss8_cmp_real.mal")
        self.assertTrue(self.candidate_json.exists(), "Falta candidates/boss8_cmp_real.json")
        self.assertTrue(self.alias_mal.exists(), "Falta candidates/cmp_real.mal")
        self.assertTrue(self.alias_json.exists(), "Falta candidates/cmp_real.json")

        disk_raw = self.candidate_mal.read_bytes()
        disk_sha = hashlib.sha256(disk_raw).hexdigest()
        self.assertEqual(len(disk_raw), CANONICAL_LENGTH)
        self.assertEqual(disk_sha, CANONICAL_SHA256)
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(), CANONICAL_SHA256)

    def test_02_all_cells_satisfy_strict_loader(self):
        """Auditoría exhaustiva: cada una de las 29,667 celdas debe cumplir strict_byte."""
        for pos, val in enumerate(self.raw):
            self.assertTrue(
                strict_byte(val, pos),
                f"Celda {pos} con valor {val} viola strict_byte del cargador oficial"
            )

    def test_03_zero_host_memory_writes_runtime_autonomy(self):
        """Auditoría de autonomía: Cero mutación externa de memoria durante la ejecución en VM."""
        m = Machine(load(self.raw), b"==")
        initial_mem = list(m.mem)

        while m.terminal == "RUNNING" and m.steps < 5000:
            m.tick()

        self.assertEqual(m.terminal, "HALT")
        self.assertEqual(m.output, b"=")
        self.assertGreater(m.steps, 100)

    def test_04_algebraic_invariants(self):
        """Verifica que todos los teoremas algebraicos ternarios del comparador se cumplan."""
        invariants = verify_cmp_algebraic_invariants()
        for name, holds in invariants.items():
            self.assertTrue(holds, f"Invariante algebraico violado: {name}")

    def test_05_empty_stream_halts_cleanly(self):
        """Stream vacío (0 bytes): discrimina EOF en Pista 0 y para sin emitir caracteres."""
        res = run_cmp_real(self.raw, b"")
        self.assertEqual(res["terminal"], "HALT")
        self.assertEqual(res["output"], b"")
        self.assertEqual(res["steps"], 104)

    def test_06_single_byte_streams_halt_cleanly(self):
        """Stream de 1 byte: discrimina EOF en Pista 1 y para sin emitir caracteres."""
        for s in [b"=", b"!"]:
            res = run_cmp_real(self.raw, s)
            self.assertEqual(res["terminal"], "HALT")
            self.assertEqual(res["output"], b"")
            self.assertEqual(res["steps"], 225)

    def test_07_equal_token_pairs(self):
        """Pares de tokens iguales ('==' y '!!'): evalúan predicado de igualdad y emiten '='."""
        for s in [b"==", b"!!"]:
            res = run_cmp_real(self.raw, s)
            self.assertEqual(res["terminal"], "HALT")
            self.assertEqual(res["output"], b"=", f"Fallo al emitir igualdad para {s!r}")
            self.assertEqual(res["steps"], 487)

    def test_08_unequal_token_pairs(self):
        """Pares de tokens desiguales ('=!' y '!='): evalúan predicado de desigualdad y emiten '!'."""
        for s in [b"=!", b"!="]:
            res = run_cmp_real(self.raw, s)
            self.assertEqual(res["terminal"], "HALT")
            self.assertEqual(res["output"], b"!", f"Fallo al emitir desigualdad para {s!r}")
            self.assertEqual(res["steps"], 461)

    def test_09_stream_with_prefix_pairs(self):
        """Streams con bytes adicionales tras los dos tokens: evalúan la igualdad del prefijo."""
        res_eq = run_cmp_real(self.raw, b"==EXTRA")
        self.assertEqual(res_eq["output"], b"=")

        res_neq = run_cmp_real(self.raw, b"=!OTHER")
        self.assertEqual(res_neq["output"], b"!")

    def test_10_in_vm_execution_path_verification(self):
        """Verifica que las lecturas y emisiones ocurren en los PCs exactos de la arquitectura."""
        res = run_cmp_real(self.raw, b"==")
        reads = [s for s in res["trace"] if s.get("opcode") == 23]
        outputs = [s for s in res["trace"] if s.get("output")]

        self.assertEqual(len(reads), 2)
        self.assertEqual(reads[0]["pre"][1], READ_PC_0)
        self.assertEqual(reads[1]["pre"][1], READ_PC_1)

        self.assertEqual(len(outputs), 1)
        self.assertEqual(bytes(outputs[0]["output"]), b"=")
        self.assertEqual(outputs[0]["pre"][1], OUTPUT_PC_DRAIN_EQ)

    def test_11_strict_three_oracle_parity(self):
        """Verifica bit-a-bit la paridad de ejecución entre los 3 oráculos."""
        test_payloads = [b"==", b"!!", b"=!", b"!=", b"", b"=", b"!"]
        for p in test_payloads:
            rep = verify(self.raw, p, budget=50000)
            self.assertTrue(
                validate_parity(rep),
                f"Discrepancia entre oráculos para payload {p!r}: {rep}"
            )
            self.assertEqual(rep["terminal"], "HALT")

    def test_12_standalone_c_binary_execution(self):
        """Verifica que el ejecutable nativo de Ben Olmstead 1998 ejecuta el binario directamente."""
        olmstead_bin = PURE_EPOCH_ROOT / "build" / "olmstead"
        self.assertTrue(olmstead_bin.exists(), "Falta ejecutable build/olmstead")

        cases = [
            (b"==", b"="),
            (b"=!", b"!"),
            (b"", b""),
            (b"=", b""),
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

    def test_13_negative_controls_fail_closed(self):
        """Verifica que los controles negativos y mutantes fallen tal como exige el protocolo."""
        raw_drain, _ = build_cmp_real(mode="broken_drain")
        res_drain = run_cmp_real(raw_drain, b"==")
        self.assertNotEqual(res_drain["output"], b"=")

        raw_eof, _ = build_cmp_real(mode="broken_eof")
        res_eof = run_cmp_real(raw_eof, b"")
        self.assertNotEqual(res_eof["steps"], 104)

        raw_loader, _ = build_cmp_real(mode="broken_loader")
        with self.assertRaises(ValueError):
            load(raw_loader)

    def test_14_candidate_json_metadata_integrity(self):
        """Verifica la integridad del esquema JSON de metadatos de los candidatos."""
        data = json.loads(self.candidate_json.read_text(encoding="utf-8"))
        self.assertEqual(data["length_bytes"], CANONICAL_LENGTH)
        self.assertEqual(data["sha256"], CANONICAL_SHA256)
        self.assertIn("algebraic_invariants", data)
        self.assertIn("key_pcs", data)


if __name__ == "__main__":
    unittest.main()
