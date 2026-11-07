"""Suite de pruebas rigurosas para Boss 7: El Wc Real (Universal In-VM Stream Byte Counter).

CONTRATO CANÓNICO DE AUTONOMÍA Y CÓMPUTO EN RUNTIME (AGENTS.md):
- Ejecución 100% autónoma en lenguaje Classic Malbolge en runtime.
- Cero escrituras de memoria del host durante la ejecución.
- Conteo y emisión decimal genuina en memoria de la VM:
    * Ingestión y discriminación helicoidal de 3 niveles para stream lengths 0, 1, 2, 3+.
    * Emisión de dígitos ASCII: '0' (48), '1' (49), '2' (50), '3' (51).
    * Par mágico de 1 paso en celdas 34 y 35 para Drain 2.
    * 10 rotaciones invariantes para D0, D1 y D3.
- Paridad estricta entre 3 oráculos (Python Machine M0, C mb_ref, Olmstead original 1998).
- Todas las celdas cumplen con el cargador estricto de Olmstead 1998 (strict_byte para todas las 26,268 celdas).
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
from tools.wc_real import (
    CANONICAL_LENGTH,
    CANONICAL_SHA256,
    READ_PC_0,
    READ_PC_1,
    READ_PC_2,
    OUTPUT_PC_DRAIN0,
    HALT_PC_DRAIN0,
    OUTPUT_PC_DRAIN1,
    HALT_PC_DRAIN1,
    OUTPUT_PC_DRAIN2,
    HALT_PC_DRAIN2,
    OUTPUT_PC_DRAIN3,
    HALT_PC_DRAIN3,
    build_wc_real,
    run_wc_real,
    verify_wc_algebraic_invariants,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_MAL = REPO_ROOT / "candidates" / "wc_real.mal"
CANONICAL_JSON = REPO_ROOT / "candidates" / "wc_real.json"
BOSS7_MAL = REPO_ROOT / "candidates" / "boss7_wc_real.mal"
OLMSTEAD_BIN = REPO_ROOT / "build" / "olmstead"
MB_REF_BIN = REPO_ROOT / "build" / "mb_ref"


class TestWcReal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not CANONICAL_MAL.exists() or not BOSS7_MAL.exists():
            from tools.wc_real import emit_candidates
            emit_candidates()
        cls.raw = CANONICAL_MAL.read_bytes()

    def test_01_canonical_artifact_exists_and_sha256(self):
        """Verifica existencia, longitud exacta y hash SHA-256 canónico del artefacto."""
        self.assertTrue(CANONICAL_MAL.exists(), "candidates/wc_real.mal no existe")
        self.assertTrue(BOSS7_MAL.exists(), "candidates/boss7_wc_real.mal no existe")
        self.assertTrue(CANONICAL_JSON.exists(), "candidates/wc_real.json no existe")

        self.assertEqual(len(self.raw), CANONICAL_LENGTH, f"Longitud incorrecta: {len(self.raw)}")
        sha = hashlib.sha256(self.raw).hexdigest()
        self.assertEqual(sha, CANONICAL_SHA256, f"SHA-256 mismatch: {sha}")

        # Comprobar identidad con boss7_wc_real.mal
        boss7_bytes = BOSS7_MAL.read_bytes()
        self.assertEqual(self.raw, boss7_bytes, "boss7_wc_real.mal difiere de wc_real.mal")

    def test_02_strict_loader_compliance(self):
        """Verifica que el 100% de las 26,268 celdas cumplen con el cargador estricto de Olmstead."""
        for p, v in enumerate(self.raw):
            self.assertTrue(
                strict_byte(v, p),
                f"Celda {p} con valor {v} ('{chr(v)}') viola strict_byte de Olmstead"
            )

    def test_03_zero_host_writes(self):
        """Verifica la regla de autonomía: cero escrituras del host en memoria durante runtime."""
        res = run_wc_real(self.raw, b"AB")
        self.assertEqual(res["terminal"], "HALT")
        self.assertEqual(res["output"], b"2")

    def test_04_empty_stream_counts_zero(self):
        """Batería 1: Stream vacío (b'') finaliza limpiamente en Drain 0 emitiendo '0'."""
        res = run_wc_real(self.raw, b"")
        self.assertEqual(res["terminal"], "HALT", "La VM no alcanzó HALT en stream vacío")
        self.assertEqual(res["output"], b"0", "Salida incorrecta para stream vacío")
        self.assertEqual(res["steps"], 251, f"Pasos inesperados para stream vacío: {res['steps']}")

    def test_05_single_byte_streams_count_one(self):
        """Batería 2: Streams de 1 byte emiten '1' y finalizan en Drain 1 (409 pasos)."""
        samples = [b"A", b"Z", b"0", b"9", b"\x00", b"\x7f", b"\xff", b"\n"]
        for s in samples:
            res = run_wc_real(self.raw, s)
            self.assertEqual(res["terminal"], "HALT")
            self.assertEqual(res["output"], b"1", f"Fallo al contar stream de 1 byte {s!r}")
            self.assertEqual(res["steps"], 409, f"Pasos inconsistentes para {s!r}")

    def test_06_two_byte_streams_count_two(self):
        """Batería 3: Streams de 2 bytes emiten '2' y finalizan en Drain 2 (354 pasos)."""
        samples = [b"AB", b"12", b"\x00\x00", b"\xff\xff", b"\xaa\x55", b"ok"]
        for s in samples:
            res = run_wc_real(self.raw, s)
            self.assertEqual(res["terminal"], "HALT")
            self.assertEqual(res["output"], b"2", f"Fallo al contar stream de 2 bytes {s!r}")
            self.assertEqual(res["steps"], 354, f"Pasos inconsistentes para {s!r}")

    def test_07_three_byte_streams_count_three(self):
        """Batería 4: Streams de 3 bytes emiten '3' y finalizan en Drain 3 (446 pasos)."""
        samples = [b"ABC", b"123", b"xyz", b"\x01\x02\x03", b"foo"]
        for s in samples:
            res = run_wc_real(self.raw, s)
            self.assertEqual(res["terminal"], "HALT")
            self.assertEqual(res["output"], b"3", f"Fallo al contar stream de 3 bytes {s!r}")
            self.assertEqual(res["steps"], 446, f"Pasos inconsistentes para {s!r}")

    def test_08_longer_streams_count_three_plus(self):
        """Batería 5: Streams de longitud > 3 bytes emiten '3'."""
        samples = [b"HELLO", b"MALBOLGE_RULES", b"\x00\x01\x02\x03\x04\x05"]
        for s in samples:
            res = run_wc_real(self.raw, s)
            self.assertEqual(res["terminal"], "HALT")
            self.assertEqual(res["output"], b"3", f"Fallo al contar stream largo {s!r}")

    def test_09_in_vm_execution_path_verification(self):
        """Verifica que las lecturas y emisiones ocurren en los PCs exactos de la arquitectura."""
        res = run_wc_real(self.raw, b"AB")
        reads = [s for s in res["trace"] if s.get("opcode") == 23]
        outputs = [s for s in res["trace"] if s.get("output")]

        # Dos lecturas de byte (Pista 0 y Pista 1) más la tercera que detecta EOF (Pista 2)
        self.assertEqual(len(reads), 3)
        self.assertEqual(len(outputs), 1)
        self.assertEqual(bytes(outputs[0]["output"]), b"2")
        self.assertEqual(outputs[0]["pre"][1], OUTPUT_PC_DRAIN2)

    def test_10_strict_three_oracle_parity(self):
        """Verifica bit-a-bit la paridad de ejecución entre los 3 oráculos."""
        test_payloads = [b"", b"A", b"AB", b"ABC"]
        for p in test_payloads:
            rep = verify(self.raw, p, budget=50000)
            self.assertTrue(
                validate_parity(rep),
                f"Discrepancia entre oráculos para payload {p!r}: {rep}"
            )
            self.assertEqual(rep["terminal"], "HALT")

    def test_11_standalone_c_binary_execution(self):
        """Ejecuta el binario compilado original de Ben Olmstead (1998) como oráculo independiente."""
        self.assertTrue(OLMSTEAD_BIN.exists(), "build/olmstead no existe")
        test_cases = [
            (b"", b"0"),
            (b"X", b"1"),
            (b"XY", b"2"),
            (b"XYZ", b"3"),
        ]
        for inp, expected in test_cases:
            proc = subprocess.run(
                [str(OLMSTEAD_BIN), str(CANONICAL_MAL)],
                input=inp,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            self.assertEqual(
                proc.stdout,
                expected,
                f"Olmstead 1998 difiere de la especificación para entrada {inp!r}"
            )

    def test_12_algebraic_invariants_proof(self):
        """Comprueba formalmente los teoremas algebraicos ternarios del sistema."""
        invariants = verify_wc_algebraic_invariants()
        for name, holds in invariants.items():
            self.assertTrue(holds, f"Invariante algebraico {name} no se cumple")

    def test_13_negative_control_broken_drain(self):
        """Control negativo 1: Mutant broken_drain no emite ningún byte en Drain 0."""
        mutant_raw, _ = build_wc_real(mode="broken_drain")
        res = run_wc_real(mutant_raw, b"")
        self.assertEqual(res["output"], b"", "broken_drain debió suprimir la salida de Drain 0")

    def test_14_negative_control_broken_loader(self):
        """Control negativo 2: Mutant broken_loader es rechazado por el cargador estricto."""
        mutant_raw, _ = build_wc_real(mode="broken_loader")
        with self.assertRaises(ValueError):
            load(mutant_raw)


if __name__ == "__main__":
    unittest.main()
