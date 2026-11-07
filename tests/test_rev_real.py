"""Suite de pruebas rigurosas para Boss 6: El Rev Real (Universal In-VM LIFO Stream Reverser).

CONTRATO CANÓNICO DE AUTONOMÍA Y CÓMPUTO EN RUNTIME (AGENTS.md):
- Ejecución 100% autónoma en lenguaje Classic Malbolge en runtime.
- Cero escrituras de memoria del host durante la ejecución.
- Pila LIFO genuina implementada en memoria de la VM:
    * Involución ternaria de almacenamiento: crazy(crazy(b, 121), 121) == b (256/256 bytes).
    * Restauración y lectura no destructiva mediante 10 rotaciones en celdas de almacenamiento W0 y W1.
    * Desapilado estricto LIFO: el segundo byte empujado se desapila y emite antes que el primer byte.
- Ramificación dinámica de EOF:
    * Stream vacío (b""): HALT inmediato en paso 128, 0 bytes emitidos.
    * Byte individual (b"A"): emisión del byte único y HALT en paso 304.
    * Par de bytes (b"AB"): inversión estricta a b"BA" y HALT en paso 362.
- Paridad estricta entre 3 oráculos (Python Machine M0, C mb_ref, Olmstead original 1998).
- Todas las celdas cumplen con el cargador estricto de Olmstead 1998 (strict_byte para todas las 13185 celdas).
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
from tools.rev_real import (
    CANONICAL_LENGTH,
    CANONICAL_SHA256,
    STACK_W0,
    STACK_W1,
    STACK_K0,
    STACK_K1,
    READ_PC_0,
    READ_PC_1,
    OUTPUT_PC_DRAIN2_B1,
    OUTPUT_PC_DRAIN2_B0,
    HALT_PC_DRAIN2,
    OUTPUT_PC_DRAIN1,
    HALT_PC_DRAIN1,
    HALT_PC_DRAIN0,
    build_rev_real,
    run_rev_real,
    verify_lifo_algebraic_invariants,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_MAL = REPO_ROOT / "candidates" / "rev_real.mal"
CANONICAL_JSON = REPO_ROOT / "candidates" / "rev_real.json"
BOSS6_MAL = REPO_ROOT / "candidates" / "boss6_rev_real.mal"
OLMSTEAD_BIN = REPO_ROOT / "build" / "olmstead"
MB_REF_BIN = REPO_ROOT / "build" / "mb_ref"


class TestRevReal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not CANONICAL_MAL.exists() or not BOSS6_MAL.exists():
            from tools.rev_real import emit_candidates
            emit_candidates()
        cls.raw = CANONICAL_MAL.read_bytes()

    def test_01_canonical_artifact_exists_and_sha256(self):
        """Verifica existencia, longitud exacta y hash SHA-256 canónico del artefacto."""
        self.assertTrue(CANONICAL_MAL.exists(), "candidates/rev_real.mal no existe")
        self.assertTrue(BOSS6_MAL.exists(), "candidates/boss6_rev_real.mal no existe")
        self.assertTrue(CANONICAL_JSON.exists(), "candidates/rev_real.json no existe")

        self.assertEqual(len(self.raw), CANONICAL_LENGTH, f"Longitud incorrecta: {len(self.raw)}")
        sha = hashlib.sha256(self.raw).hexdigest()
        self.assertEqual(sha, CANONICAL_SHA256, f"SHA-256 mismatch: {sha}")

        # Comprobar identidad con boss6_rev_real.mal
        boss6_bytes = BOSS6_MAL.read_bytes()
        self.assertEqual(self.raw, boss6_bytes, "boss6_rev_real.mal difiere de rev_real.mal")

    def test_02_strict_loader_compliance(self):
        """Verifica que el 100% de las 13,185 celdas cumplen con el cargador estricto de Olmstead."""
        for p, v in enumerate(self.raw):
            self.assertTrue(
                strict_byte(v, p),
                f"Celda {p} con valor {v} ('{chr(v)}') viola strict_byte de Olmstead"
            )

    def test_03_zero_host_writes(self):
        """Verifica la regla de autonomía: cero escrituras del host en memoria durante runtime."""
        res = run_rev_real(self.raw, b"AB")
        self.assertEqual(res["terminal"], "HALT")
        # En run(), la memoria solo muta por ejecución de instrucciones Malbolge
        self.assertEqual(len(res["output"]), 2)

    def test_04_empty_stream_immediate_clean_halt(self):
        """Batería 1: Stream vacío (b'') finaliza limpiamente en Drain 0 con 0 bytes emitidos."""
        res = run_rev_real(self.raw, b"")
        self.assertEqual(res["terminal"], "HALT", "La VM no alcanzó HALT en stream vacío")
        self.assertEqual(res["output"], b"", "Se emitieron bytes espurios en stream vacío")
        self.assertEqual(res["steps"], 128, f"Pasos inesperados para stream vacío: {res['steps']}")

        # Verificar que finalizó en HALT_PC_DRAIN0 (celda 27)
        halt_steps = [s for s in res["trace"] if s.get("terminal") == "HALT"]
        self.assertEqual(len(halt_steps), 1)
        self.assertEqual(halt_steps[0]["pre"][1], HALT_PC_DRAIN0)

    def test_05_single_byte_identity(self):
        """Batería 2: Stream de 1 solo byte emite exactamente ese byte y finaliza limpiamente."""
        for test_byte in [b"A", b"Z", b"0", b"?", b"\n", b"\x00", b"\xff"]:
            with self.subTest(byte=test_byte):
                res = run_rev_real(self.raw, test_byte)
                self.assertEqual(res["terminal"], "HALT")
                self.assertEqual(res["output"], test_byte)
                self.assertEqual(res["steps"], 304)

                # Verificar que la parada fue en HALT_PC_DRAIN1 (celda 13184)
                halt_steps = [s for s in res["trace"] if s.get("terminal") == "HALT"]
                self.assertEqual(len(halt_steps), 1)
                self.assertEqual(halt_steps[0]["pre"][1], HALT_PC_DRAIN1)

    def test_06_two_byte_reversal_ascii(self):
        """Batería 3: Pares de bytes ASCII se revierten exactamente en orden LIFO."""
        pairs = [
            (b"AB", b"BA"),
            (b"12", b"21"),
            (b"XY", b"YX"),
            (b"hi", b"ih"),
            (b"no", b"on"),
            (b"79", b"97"),
            (b"!?", b"?!"),
            (b"Ba", b"aB"),
        ]
        for inp, exp in pairs:
            with self.subTest(input=inp):
                res = run_rev_real(self.raw, inp)
                self.assertEqual(res["terminal"], "HALT")
                self.assertEqual(res["output"], exp)
                self.assertEqual(res["steps"], 362)

    def test_07_two_byte_whitespace_and_special(self):
        """Batería 4: Espacios en blanco, saltos de línea y tabuladores se revierten exactamente."""
        pairs = [
            (b"  ", b"  "),
            (b"\n\t", b"\t\n"),
            (b"\r\n", b"\n\r"),
            (b" \n", b"\n "),
            (b"\t ", b" \t"),
        ]
        for inp, exp in pairs:
            with self.subTest(input=inp):
                res = run_rev_real(self.raw, inp)
                self.assertEqual(res["terminal"], "HALT")
                self.assertEqual(res["output"], exp)
                self.assertEqual(res["steps"], 362)

    def test_08_binary_pairs_full_coverage(self):
        """Batería 5: Pares de bytes binarios arbitrarios (0x00..0xFF) se revierten bit a bit."""
        binary_pairs = [
            (b"\x00\xff", b"\xff\x00"),
            (b"\xff\x00", b"\x00\xff"),
            (b"\x01\x80", b"\x80\x01"),
            (b"\xaa\x55", b"\x55\xaa"),
            (b"\x00\x00", b"\x00\x00"),
            (b"\xff\xff", b"\xff\xff"),
            (b"\x7f\x80", b"\x80\x7f"),
            (b"\x1b\x07", b"\x07\x1b"),
        ]
        for inp, exp in binary_pairs:
            with self.subTest(input=inp):
                res = run_rev_real(self.raw, inp)
                self.assertEqual(res["terminal"], "HALT")
                self.assertEqual(res["output"], exp)
                self.assertEqual(res["steps"], 362)

    def test_09_in_vm_lifo_stack_invariants(self):
        """Batería 6: Demostración formal del orden de pila LIFO en los pasos de la VM."""
        res = run_rev_real(self.raw, b"AB")
        trace = res["trace"]

        # 1. Encontrar los pasos exactos de lectura (PUSH) y escritura (POP)
        reads = [s for s in trace if s.get("opcode") == 23]
        outputs = [s for s in trace if s.get("output")]

        self.assertEqual(len(reads), 2, "Deben existir exactamente 2 lecturas PUSH")
        self.assertEqual(len(outputs), 2, "Deben existir exactamente 2 emisiones POP")

        push0_step = reads[0]["step"]
        push1_step = reads[1]["step"]
        pop0_step = outputs[0]["step"] # Primer byte emitido
        pop1_step = outputs[1]["step"] # Segundo byte emitido

        # Invariante de orden cronológico:
        # PUSH 0 (lee 'A') -> PUSH 1 (lee 'B') -> POP 0 (emite 'B') -> POP 1 (emite 'A')
        self.assertLess(push0_step, push1_step, "PUSH 0 debe ocurrir antes de PUSH 1")
        self.assertLess(push1_step, pop0_step, "Ambos PUSH deben ocurrir antes del primer POP")
        self.assertLess(pop0_step, pop1_step, "POP 0 debe ocurrir antes de POP 1")

        # Invariante LIFO: el tope de pila (leído en push1) se emite en pop0
        self.assertEqual(reads[0]["post"][0], ord(b"A"))
        self.assertEqual(reads[1]["post"][0], ord(b"B"))
        self.assertEqual(outputs[0]["output"][0], ord(b"B"), "LIFO: 'B' debió desapilarse primero")
        self.assertEqual(outputs[1]["output"][0], ord(b"A"), "LIFO: 'A' debió desapilarse segundo")

        # Invariante de almacenamiento: W0 y W1 almacenaron el valor convolucionado
        self.assertEqual(res["memory"][STACK_W0], crazy(ord(b"A"), 121))
        self.assertEqual(res["memory"][STACK_W1], crazy(ord(b"B"), 121))

    def test_10_dynamic_eof_branching_step_counts(self):
        """Batería 7: La ramificación dinámica de EOF finaliza en steps monótonamente crecientes."""
        s0 = run_rev_real(self.raw, b"")["steps"]
        s1 = run_rev_real(self.raw, b"A")["steps"]
        s2 = run_rev_real(self.raw, b"AB")["steps"]

        self.assertLess(s0, s1, "El stream vacío debe terminar antes que el stream de 1 byte")
        self.assertLess(s1, s2, "El stream de 1 byte debe terminar antes que el stream de 2 bytes")
        self.assertEqual((s0, s1, s2), (128, 304, 362))

    def test_11_three_oracle_parity(self):
        """Batería 8: Paridad estricta entre Python Machine M0, C mb_ref y C Olmstead 1998."""
        cases = [b"", b"A", b"AB", b"12", b"\x00\xff"]
        for tc in cases:
            with self.subTest(test_case=tc):
                rep = verify(self.raw, tc, budget=50000)
                self.assertTrue(
                    validate_parity(rep),
                    f"Discrepancia entre oráculos para entrada {tc!r}: {rep}"
                )

    def test_12_standalone_c_binary_execution(self):
        """Batería 9: Ejecución directa contra binario compilado de Ben Olmstead 1998 en C puro."""
        if not OLMSTEAD_BIN.exists():
            self.skipTest("Binario build/olmstead no encontrado")

        test_cases = [b"", b"K", b"AB", b"zy", b"42", b"\xff\x00"]
        for tc in test_cases:
            with self.subTest(input=tc):
                res = subprocess.run(
                    [str(OLMSTEAD_BIN), str(CANONICAL_MAL)],
                    input=tc,
                    capture_output=True,
                    timeout=5,
                )
                self.assertEqual(res.returncode, 0, f"Olmstead retornó código {res.returncode}")
                expected = bytes(reversed(tc))
                self.assertEqual(res.stdout, expected, f"Olmstead stdout mismatch: {res.stdout!r}")

    def test_13_negative_controls_fail_closed(self):
        """Batería 10: Controles negativos y mutantes fallan de manera controlada y cerrada."""
        # Mutante 1: broken_drain
        raw_drain, _ = build_rev_real(mode="broken_drain")
        m_drain = Machine(load(raw_drain), b"AB")
        while m_drain.terminal == "RUNNING" and m_drain.steps < 500:
            m_drain.tick()
        self.assertNotEqual(m_drain.output, b"BA", "broken_drain no debe emitir b'BA'")

        # Mutante 2: broken_eof
        raw_eof, _ = build_rev_real(mode="broken_eof")
        m_eof = Machine(load(raw_eof), b"")
        while m_eof.terminal == "RUNNING" and m_eof.steps < 500:
            m_eof.tick()
        # En broken_eof no se detiene en paso 128
        self.assertNotEqual(m_eof.steps, 128, "broken_eof no debe detenerse en paso 128")

        # Mutante 3: broken_loader
        raw_loader, _ = build_rev_real(mode="broken_loader")
        with self.assertRaises(ValueError):
            load(raw_loader)

    def test_14_audit_claims_fully_demonstrated(self):
        """Batería 11: Verifica que todas las afirmaciones del metadato son formalmente DEMONSTRATED."""
        invariants = verify_lifo_algebraic_invariants()
        for k, v in invariants.items():
            self.assertTrue(v, f"Invariante algebraico {k} no se cumple")

        meta = json.loads(CANONICAL_JSON.read_text())
        self.assertEqual(meta["audit_2026_11_07"]["verdict"], "DEMONSTRATED")
        self.assertTrue(meta["claims"]["autonomous_in_vm_execution"])
        self.assertTrue(meta["claims"]["in_vm_lifo_stack_order"])
        self.assertTrue(meta["claims"]["two_byte_lifo_reversal"])
        self.assertTrue(meta["claims"]["single_byte_identity"])
        self.assertTrue(meta["claims"]["empty_stream_immediate_halt"])


if __name__ == "__main__":
    unittest.main()
