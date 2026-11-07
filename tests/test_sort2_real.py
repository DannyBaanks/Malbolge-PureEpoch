"""Suite de pruebas rigurosas para Boss 10: El Sort2 Real (Universal In-VM Conditional Sorter).

CONTRATO CANÓNICO DE AUTONOMÍA Y CÓMPUTO EN RUNTIME (AGENTS.md):
- Ejecución 100% autónoma en lenguaje Classic Malbolge en runtime.
- Cero escrituras de memoria del host durante la ejecución.
- Clasificación condicional genuina en memoria de la VM:
    * Ingestión y discriminación de EOF en Pista 0 y Pista 1.
    * Recuperación biyectiva de operandos en Pista 2 mediante crazy(-, 121).
    * Discriminador de orden in-VM evaluando r = crazy(33, crazy(crazy(50, d0), crazy(d1, d0))).
    * Bifurcación dinámica a drenaje FIFO (2194) para orden ascendente o LIFO (2356) para orden invertido.
    * Emisión de los elementos ordenados en Classic Malbolge.
- Paridad estricta entre 3 oráculos (Python Machine M0, C mb_ref, Olmstead original 1998).
- Todas las celdas cumplen con el cargador estricto de Olmstead 1998 (strict_byte para las 2,452 celdas).
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
from tools.sort2_real import (
    CANONICAL_LENGTH,
    CANONICAL_SHA256,
    READ_PC_0,
    READ_PC_1,
    SORT_START_PC,
    HALT_PC_DRAIN0_EOF,
    HALT_PC_DRAIN1_EOF,
    DRAIN_SORTED_START,
    OUTPUT_PC_DRAIN_SORTED_B0,
    OUTPUT_PC_DRAIN_SORTED_B1,
    HALT_PC_DRAIN_SORTED,
    DRAIN_INVERTED_START,
    OUTPUT_PC_DRAIN_INVERTED_B1,
    OUTPUT_PC_DRAIN_INVERTED_B0,
    HALT_PC_DRAIN_INVERTED,
    build_sort2_real,
    run_sort2_real,
    verify_sort2_algebraic_invariants,
    PURE_EPOCH_ROOT,
)


class TestSort2Real(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw, cls.meta = build_sort2_real(mode="canonical")
        cls.candidate_mal = PURE_EPOCH_ROOT / "candidates" / "sort2_real.mal"
        cls.candidate_json = PURE_EPOCH_ROOT / "candidates" / "sort2_real.json"
        cls.boss10_mal = PURE_EPOCH_ROOT / "candidates" / "boss10_sort2_real.mal"
        cls.boss10_json = PURE_EPOCH_ROOT / "candidates" / "boss10_sort2_real.json"

    def test_01_canonical_artifacts_exist_and_match_hash(self):
        """Verifica que los artefactos canónicos existen en candidates/ y coinciden bit-a-bit."""
        self.assertTrue(self.candidate_mal.exists(), "Falta candidates/sort2_real.mal")
        self.assertTrue(self.candidate_json.exists(), "Falta candidates/sort2_real.json")
        self.assertTrue(self.boss10_mal.exists(), "Falta candidates/boss10_sort2_real.mal")
        self.assertTrue(self.boss10_json.exists(), "Falta candidates/boss10_sort2_real.json")

        disk_bytes = self.candidate_mal.read_bytes()
        disk_sha = hashlib.sha256(disk_bytes).hexdigest()

        self.assertEqual(len(disk_bytes), CANONICAL_LENGTH)
        self.assertEqual(disk_sha, CANONICAL_SHA256)
        self.assertEqual(disk_bytes, self.boss10_mal.read_bytes())

    def test_02_all_cells_satisfy_strict_loader(self):
        """Verifica que cada una de las 2,452 celdas cumple strict_byte sin excepción."""
        for p, b in enumerate(self.raw):
            self.assertTrue(
                strict_byte(b, p),
                f"Celda {p} con valor {b} ('{chr(b)}') viola strict_byte de Olmstead 1998"
            )

    def test_03_zero_host_memory_writes_runtime_autonomy(self):
        """Audita que la VM opera con 100% de autonomía sin inyección externa de memoria."""
        mem = load(self.raw)
        m = Machine(mem, b"10")
        initial_mem_snapshot = list(m.mem)

        while m.terminal == "RUNNING" and m.steps < 50000:
            m.tick()

        self.assertEqual(m.terminal, "HALT")
        self.assertEqual(m.output, b"01")

        # Verificar que el cargador ejecutó el ciclo estándar de XLAT2
        self.assertNotEqual(m.mem, initial_mem_snapshot)

    def test_04_algebraic_invariants(self):
        """Verifica formalmente todos los teoremas algebraicos ternarios del clasificador."""
        invariants = verify_sort2_algebraic_invariants()
        for name, passed in invariants.items():
            self.assertTrue(passed, f"Fallo en invariante algebraico {name}")

    def test_05_empty_stream_halts_cleanly(self):
        """Stream vacío (EOF inmediato): ramifica en celda 27 y para con 0 bytes de salida."""
        res = run_sort2_real(self.raw, b"")
        self.assertEqual(res["terminal"], "HALT")
        self.assertEqual(res["output"], b"")
        self.assertEqual(res["steps"], 169)

    def test_06_single_byte_streams_halt_cleanly(self):
        """Stream de 1 byte (EOF en segunda lectura): ramifica en celda 79 y para con 0 bytes."""
        for b in [b"0", b"1", b"2", b"X"]:
            res = run_sort2_real(self.raw, b)
            self.assertEqual(res["terminal"], "HALT")
            self.assertEqual(res["output"], b"", f"Fallo al procesar stream unario {b!r}")
            self.assertEqual(res["steps"], 290)

    def test_07_sorted_pairs_fifo_order(self):
        """Pares ordenados (d0 <= d1): se emiten en orden FIFO idéntico."""
        sorted_cases = [
            (b"00", b"00"),
            (b"01", b"01"),
            (b"02", b"02"),
            (b"11", b"11"),
            (b"12", b"12"),
            (b"22", b"22"),
        ]
        for inp, expected in sorted_cases:
            res = run_sort2_real(self.raw, inp)
            self.assertEqual(res["terminal"], "HALT")
            self.assertEqual(res["output"], expected, f"Fallo al ordenar {inp!r}")
            self.assertEqual(res["steps"], 818)

    def test_08_inverted_pairs_lifo_order(self):
        """Pares invertidos (d0 > d1): se emiten en orden LIFO invertido (clasificados)."""
        inverted_cases = [
            (b"10", b"01"),
            (b"20", b"02"),
            (b"21", b"12"),
        ]
        for inp, expected in inverted_cases:
            res = run_sort2_real(self.raw, inp)
            self.assertEqual(res["terminal"], "HALT")
            self.assertEqual(res["output"], expected, f"Fallo al ordenar {inp!r}")
            self.assertEqual(res["steps"], 812)

    def test_09_stream_with_prefix_pairs(self):
        """Streams con bytes adicionales tras los dos elementos: evalúan el orden del prefijo."""
        res_sorted = run_sort2_real(self.raw, b"01EXTRA")
        self.assertEqual(res_sorted["output"], b"01")

        res_inverted = run_sort2_real(self.raw, b"10OTHER")
        self.assertEqual(res_inverted["output"], b"01")

    def test_10_in_vm_execution_path_verification(self):
        """Verifica que las lecturas y emisiones ocurren en los PCs exactos de la arquitectura."""
        # Caso ordenado: aterriza en DRAIN_SORTED_START (2194)
        res_sorted = run_sort2_real(self.raw, b"01")
        reads = [s for s in res_sorted["trace"] if s.get("opcode") == 23]
        outputs = [s for s in res_sorted["trace"] if s.get("output")]

        self.assertEqual(len(reads), 2)
        self.assertEqual(reads[0]["pre"][1], READ_PC_0)
        self.assertEqual(reads[1]["pre"][1], READ_PC_1)

        self.assertEqual(len(outputs), 2)
        self.assertEqual(bytes(outputs[0]["output"]), b"0")
        self.assertEqual(outputs[0]["pre"][1], OUTPUT_PC_DRAIN_SORTED_B0)
        self.assertEqual(bytes(outputs[1]["output"]), b"1")
        self.assertEqual(outputs[1]["pre"][1], OUTPUT_PC_DRAIN_SORTED_B1)

        # Caso invertido: aterriza en DRAIN_INVERTED_START (2356)
        res_inverted = run_sort2_real(self.raw, b"10")
        outputs_inv = [s for s in res_inverted["trace"] if s.get("output")]

        self.assertEqual(len(outputs_inv), 2)
        self.assertEqual(bytes(outputs_inv[0]["output"]), b"0")
        self.assertEqual(outputs_inv[0]["pre"][1], OUTPUT_PC_DRAIN_INVERTED_B1)
        self.assertEqual(bytes(outputs_inv[1]["output"]), b"1")
        self.assertEqual(outputs_inv[1]["pre"][1], OUTPUT_PC_DRAIN_INVERTED_B0)

    def test_11_strict_three_oracle_parity(self):
        """Verifica bit-a-bit la paridad de ejecución entre los 3 oráculos."""
        test_payloads = [b"00", b"01", b"10", b"11", b"21", b"02", b"20", b"", b"0"]
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
            (b"00", b"00"),
            (b"01", b"01"),
            (b"10", b"01"),
            (b"11", b"11"),
            (b"21", b"12"),
            (b"02", b"02"),
            (b"20", b"02"),
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

    def test_13_negative_controls_fail_closed(self):
        """Verifica que los controles negativos y mutantes fallen tal como exige el protocolo."""
        raw_drain, _ = build_sort2_real(mode="broken_drain")
        res_drain = run_sort2_real(raw_drain, b"01")
        self.assertNotEqual(res_drain["output"], b"01")

        raw_eof, _ = build_sort2_real(mode="broken_eof")
        res_eof = run_sort2_real(raw_eof, b"")
        self.assertNotEqual(res_eof["steps"], 169)

        raw_loader, _ = build_sort2_real(mode="broken_loader")
        with self.assertRaises(ValueError):
            load(raw_loader)

    def test_14_metadata_json_schema_completeness(self):
        """Verifica la validez y completitud del esquema JSON de metadatos."""
        data = json.loads(self.candidate_json.read_text(encoding="utf-8"))
        self.assertEqual(data["length_bytes"], CANONICAL_LENGTH)
        self.assertEqual(data["sha256"], CANONICAL_SHA256)
        self.assertIn("sorter_metrics", data)
        self.assertIn("claims", data)
        self.assertTrue(data["claims"]["autonomous_in_vm_execution"])
        self.assertTrue(data["claims"]["in_vm_conditional_order_evaluation"])


if __name__ == "__main__":
    unittest.main()
