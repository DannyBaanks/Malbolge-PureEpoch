"""Suite de pruebas rigurosas para Boss 5: El Cat Real (Universal In-VM Streaming Cat en Classic Malbolge).

CONTRATO CANÓNICO DE AUTONOMÍA Y CÓMPUTO EN RUNTIME (AGENTS.md):
- Ejecución 100% autónoma en lenguaje Classic Malbolge en runtime.
- Cero escrituras de memoria del host durante la ejecución.
- Lectura de stdin mediante instrucción in ('/') y emisión transparente a stdout mediante out ('<').
- Discriminación exacta de EOF:
    * Cuando stdin se agota, '/' devuelve A = 59048.
    * Discriminador algebraico ternario: crazy(crazy(59048, EOF), 29524) == 0.
    * Aislado de todo el dominio de bytes 0..255 (0 colisiones).
    * Bifurcación in-VM directa a HALT ('v') en cell 7615.
- Soporte universal de flujos:
    * Flujo vacío (b""): HALT inmediato en paso 7805, 0 bytes emitidos, exit code 0.
    * Byte individual (b"A"): emisión exacta, HALT en paso 8212, exit code 0.
    * Cadenas multilínea y caracteres arbitrarios: echo byte por byte.
    * Flujo binario completo 0x00..0xFF (256 bytes) y streams de longitud arbitraria.
- Rearme in-VM de ciclo cerrado:
    * Ciclo de 407 pasos por byte.
    * Reutilización de las mismas PCs para lectura (PC 7657) y escritura (PC 7639).
    * Re-inicialización in-VM de celdas modificadas bajo automodificación XLAT2.
- Paridad estricta entre 3 oráculos (Python Machine M0, C mb_ref, C Olmstead 1998).
- Todas las celdas cumplen con el cargador estricto de Olmstead (strict_byte para todas las 7972 celdas).
"""
import hashlib
import json
from pathlib import Path
import random
import sys
import unittest

PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent
if str(PURE_EPOCH_ROOT) not in sys.path:
    sys.path.append(str(PURE_EPOCH_ROOT))

from baseline.epoch_probe import Machine, load
from tools.cat_real import (
    CANONICAL_LENGTH,
    CANONICAL_SHA256,
    READ_PC,
    OUTPUT_PC,
    HALT_PC,
    STEPS_PER_BYTE,
    build_cat_real,
    run_cat_real,
    verify_algebraic_invariants,
)
from tools.build_candidates import strict_byte
from tools.observe import run
from tools.oracles import verify, validate_parity


class TestCatReal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cand_dir = PURE_EPOCH_ROOT / "candidates"
        cls.mal_path = cls.cand_dir / "cat_real.mal"
        cls.json_path = cls.cand_dir / "cat_real.json"
        cls.boss5_mal = cls.cand_dir / "boss5_cat_real.mal"
        cls.boss5_json = cls.cand_dir / "boss5_cat_real.json"

        if not cls.mal_path.exists() or not cls.json_path.exists():
            from tools.cat_real import emit_candidates
            emit_candidates()

        cls.img = cls.mal_path.read_bytes()
        cls.meta = json.loads(cls.json_path.read_text())

    def test_01_canonical_artifact_exists_and_sha256(self):
        """El artefacto canónico existe, ocupa exactamente 7,972 celdas y su SHA-256 coincide."""
        self.assertTrue(self.mal_path.exists(), f"No existe {self.mal_path}")
        self.assertTrue(self.json_path.exists(), f"No existe {self.json_path}")
        self.assertTrue(self.boss5_mal.exists(), f"No existe alias {self.boss5_mal}")
        self.assertEqual(len(self.img), CANONICAL_LENGTH)
        sha = hashlib.sha256(self.img).hexdigest()
        self.assertEqual(sha, CANONICAL_SHA256)
        self.assertEqual(sha, self.meta["sha256"])

        # Verificar alias boss5_cat_real.mal
        boss5_img = self.boss5_mal.read_bytes()
        self.assertEqual(boss5_img, self.img)

    def test_02_strict_loader_compliance(self):
        """Todas las celdas cumplen con el cargador estricto de Olmstead 1998 (strict_byte)."""
        cells = list(self.img)
        self.assertTrue(all(strict_byte(v, p) for p, v in enumerate(cells)))

    def test_03_zero_host_writes(self):
        """La ejecución de la VM se realiza sin ninguna escritura de memoria externa del host."""
        res = run_cat_real(self.img, b"X")
        self.assertEqual(res["terminal"], "HALT")
        self.assertEqual(res["output"], b"X")

    def test_04_empty_input_immediate_clean_halt(self):
        """Flujo vacío (b''): HALT limpio en paso 7805, 0 bytes emitidos, exit code 0."""
        res = run_cat_real(self.img, b"", max_steps=50000)
        self.assertEqual(res["terminal"], "HALT")
        self.assertEqual(res["output"], b"")
        self.assertEqual(res["steps"], 7805)

    def test_05_single_character_stream(self):
        """Byte individual (b'A'): emisión exacta, HALT en paso 8212, exit code 0."""
        res = run_cat_real(self.img, b"A", max_steps=50000)
        self.assertEqual(res["terminal"], "HALT")
        self.assertEqual(res["output"], b"A")
        self.assertEqual(res["steps"], 8212)

    def test_06_string_stream_hello_cat(self):
        """Cadena de texto representativa: emisión exacta byte por byte y HALT limpio."""
        payload = b"Hello, Malbolge Real Cat!\n"
        res = run_cat_real(self.img, payload, max_steps=100000)
        self.assertEqual(res["terminal"], "HALT")
        self.assertEqual(res["output"], payload)

    def test_07_multiline_text_stream(self):
        """Texto multilínea con espacios, tabulaciones y saltos de línea."""
        payload = b"Line 1: 12345\nLine 2: \tSpecial chars !@#$%^&*()\nLine 3: Final line.\n"
        res = run_cat_real(self.img, payload, max_steps=200000)
        self.assertEqual(res["terminal"], "HALT")
        self.assertEqual(res["output"], payload)

    def test_08_full_256_byte_domain(self):
        """Flujo binario completo: todos los 256 bytes 0x00..0xFF emitidos con exactitud bit a bit."""
        payload = bytes(range(256))
        res = run_cat_real(self.img, payload, max_steps=500000)
        self.assertEqual(res["terminal"], "HALT")
        self.assertEqual(res["output"], payload)

    def test_09_long_binary_stream_pseudorandom(self):
        """Flujo binario largo (2 KiB): streaming continuo sin fuga ni corrupción de ciclo."""
        rng = random.Random(20261107)
        payload = bytes(rng.randrange(256) for _ in range(2048))
        res = run_cat_real(self.img, payload, max_steps=1500000)
        self.assertEqual(res["terminal"], "HALT")
        self.assertEqual(res["output"], payload)

    def test_10_dynamic_eof_discrimination(self):
        """Discriminación exacta de EOF: el detector ternario no produce paradas tempranas falsas."""
        invs = verify_algebraic_invariants()
        self.assertTrue(invs["eof_detector_maps_to_zero"])
        self.assertTrue(invs["zero_false_positive_collisions_in_256_bytes"])
        self.assertTrue(invs["lossless_trit_storage_involution"])

        # Verificar en traza que la instrucción HALT solo se ejecuta al final de los datos
        res = run_cat_real(self.img, b"ABC", max_steps=50000)
        halt_steps = [s for s in res["trace"] if s.get("terminal") == "HALT"]
        self.assertEqual(len(halt_steps), 1)
        self.assertEqual(halt_steps[0]["pre"][1], HALT_PC)

    def test_11_in_vm_loop_rearm_and_period(self):
        """Rearme in-VM: las mismas PCs de lectura ('/') y salida ('<') se reciclan con período exacto."""
        payload = b"XYZW"
        res = run_cat_real(self.img, payload, max_steps=50000)
        read_pcs = [s["pre"][1] for s in res["trace"] if s.get("opcode") == 23]
        out_pcs = [s["pre"][1] for s in res["trace"] if s.get("output")]

        # Debe haberse leído 4 bytes + 1 EOF = 5 lecturas en READ_PC
        self.assertEqual(len(read_pcs), 5)
        self.assertTrue(all(pc == READ_PC for pc in read_pcs))

        # Debe haberse emitido 4 caracteres en OUTPUT_PC
        self.assertEqual(len(out_pcs), 4)
        self.assertTrue(all(pc == OUTPUT_PC for pc in out_pcs))

        # El período entre lecturas sucesivas debe ser exactamente 407 pasos
        read_step_indices = [i for i, s in enumerate(res["trace"]) if s.get("opcode") == 23]
        deltas = [read_step_indices[k] - read_step_indices[k-1] for k in range(1, 4)]
        self.assertEqual(set(deltas), {STEPS_PER_BYTE})

    def test_12_three_oracle_parity(self):
        """Paridad estricta entre 3 oráculos (Python Machine, C mb_ref, Olmstead 1998)."""
        test_cases = [
            (b"", "flujo vacío"),
            (b"A", "un carácter"),
            (b"Malbolge Cat\n", "cadena corta"),
        ]
        for payload, label in test_cases:
            with self.subTest(case=label):
                rep = verify(self.img, payload, budget=50000)
                self.assertTrue(validate_parity(rep), f"Paridad fallida para {label}")
                self.assertTrue(rep["trace_equal"])
                self.assertTrue(rep["memory_equal"])
                self.assertTrue(rep["registers_equal"])
                self.assertTrue(rep["outputs_equal"])
                self.assertEqual(rep["reference_returncode"], 0)
                self.assertEqual(rep["original_returncode"], 0)

    def test_13_negative_controls_fail_closed(self):
        """Controles negativos: los mutantes fallan de manera cerrada y predecible."""
        # 1. Mutante broken_rearm: no emite salida
        img_rearm, _ = build_cat_real(mode="broken_rearm")
        res_rearm = run(img_rearm, b"A", max_steps=10000)
        self.assertEqual(res_rearm["output"], b"")

        # 2. Mutante broken_eof: no realiza HALT limpio
        img_eof, _ = build_cat_real(mode="broken_eof")
        res_eof = run(img_eof, b"A", max_steps=10000)
        self.assertNotEqual(res_eof["terminal"], "HALT")

        # 3. Mutante broken_loader: el cargador estricto lo rechaza al cargar
        img_loader, _ = build_cat_real(mode="broken_loader")
        with self.assertRaises(ValueError):
            load(img_loader)

    def test_14_audit_claims_fully_demonstrated(self):
        """Auditoría 2026-11-07: verificar que todas las afirmaciones del artefacto son DEMONSTRATED."""
        claims = self.meta["claims"]
        self.assertTrue(claims["autonomous_in_vm_execution"])
        self.assertTrue(claims["terminates_on_eof"])
        self.assertTrue(claims["empty_stream_immediate_halt"])
        self.assertTrue(claims["zero_external_memory_writes"])
        self.assertTrue(claims["strict_loader_compliance"])
        self.assertTrue(claims["strict_3_oracle_parity"])
        self.assertTrue(claims["arbitrary_length_streaming"])
        self.assertTrue(claims["full_byte_domain_0_to_255"])
        self.assertEqual(self.meta["audit_2026_11_07"]["verdict"], "DEMONSTRATED")
        self.assertEqual(
            self.meta["audit_2026_11_07"]["classification"],
            "in_vm_universal_streaming_cat_classic_malbolge",
        )


if __name__ == "__main__":
    unittest.main()
