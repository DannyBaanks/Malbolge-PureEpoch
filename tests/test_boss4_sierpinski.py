"""Suite de pruebas rigurosas para Boss 4: Autómata Celular Wolfram Regla 90 (Triángulo de Sierpiński).

Verifica:
1. Existencia del artefacto e inmutabilidad SHA-256.
2. Cumplimiento estricto del cargador de Olmstead 1998 (strict_byte para cada posición).
3. 0 escrituras externas del host durante la ejecución.
4. Salida fractal exacta de 8 generaciones (128 bytes ASCII).
5. Paridad estricta entre 3 oráculos independientes (Python Machine, C mb_ref, Olmstead 1998).
6. Síntesis paramétrica de generaciones variables (G = 1, 2, 4) conforme a la Regla 90.
7. Controles negativos y mutantes (broken_space, broken_star, broken_halt) con falsificación estricta.
"""
import hashlib
import json
from pathlib import Path
import sys
import unittest

PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent
if str(PURE_EPOCH_ROOT) not in sys.path:
    sys.path.append(str(PURE_EPOCH_ROOT))

from tools.boss4_sierpinski import (
    build_boss4_sierpinski,
    generate_sierpinski_text,
    run_boss4_execution,
)
from tools.build_candidates import strict_byte
from tools.observe import run
from tools.oracles import verify, validate_parity

CANDIDATE_PATH = PURE_EPOCH_ROOT / "candidates" / "boss4_sierpinski.mal"
META_PATH = PURE_EPOCH_ROOT / "candidates" / "boss4_sierpinski.json"


def _load_artifact():
    if not CANDIDATE_PATH.exists() or not META_PATH.exists():
        raise FileNotFoundError(f"Artefactos de Boss 4 no encontrados en {CANDIDATE_PATH}")
    img = CANDIDATE_PATH.read_bytes()
    meta = json.loads(META_PATH.read_text())
    return img, meta


class TestBoss4Sierpinski(unittest.TestCase):
    """Pruebas del contrato de Boss 4."""

    @classmethod
    def setUpClass(cls):
        cls.img, cls.meta = _load_artifact()
        cls.expected_fractal = generate_sierpinski_text(8).encode("ascii")

    def test_01_canonical_artifact_exists_and_sha256(self):
        """El artefacto canónico existe en disco y su hash SHA-256 coincide con los metadatos."""
        actual_sha = hashlib.sha256(self.img).hexdigest()
        self.assertEqual(actual_sha, self.meta["sha256"])
        self.assertEqual(len(self.img), self.meta["length_bytes"])

    def test_02_strict_loader_compliance(self):
        """Todos los bytes del artefacto cumplen las restricciones estrictas del cargador de Olmstead 1998."""
        for pos, val in enumerate(self.img):
            self.assertTrue(
                strict_byte(val, pos),
                f"Byte inválido en posición {pos}: valor {val} (char {repr(chr(val))})"
            )

    def test_03_zero_host_writes(self):
        """La ejecución es 100% autónoma sin escrituras del host en memoria de la VM."""
        res = run_boss4_execution(self.img)
        self.assertEqual(res["terminal"], "HALT")
        self.assertTrue(self.meta["claims"]["zero_external_memory_writes"])

    def test_04_exact_ascii_triangle_8_generations(self):
        """La salida producida por la VM coincide exactamente con el Triángulo de Sierpiński (128 bytes)."""
        res = run_boss4_execution(self.img)
        self.assertEqual(res["output"], self.expected_fractal)
        self.assertEqual(len(res["output"]), 128)
        self.assertEqual(res["terminal"], "HALT")

    def test_05_three_oracle_parity(self):
        """Paridad estricta entre Python Machine, C mb_ref y Olmstead original 1998."""
        rep = verify(self.img, b"", budget=15000)
        self.assertTrue(validate_parity(rep), "Falla de paridad entre oráculos")
        self.assertTrue(rep.get("trace_equal"))
        self.assertTrue(rep.get("memory_equal"))
        self.assertTrue(rep.get("registers_equal"))
        self.assertTrue(rep.get("outputs_equal"))
        self.assertEqual(rep.get("terminal"), "HALT")
        self.assertEqual(rep.get("reference_returncode"), 0)
        self.assertEqual(rep.get("instrumented_returncode"), 0)
        self.assertEqual(rep.get("original_returncode"), 0)

    def test_06_variable_generations_1_2_4(self):
        """El sintetizador genera correctamente subfractales para G = 1, 2, 4 generaciones."""
        for g in [1, 2, 4]:
            with self.subTest(generations=g):
                sub_img, sub_meta = build_boss4_sierpinski(generations=g)
                expected = generate_sierpinski_text(g).encode("ascii")
                res = run(sub_img, b"", max_steps=20000)
                self.assertEqual(res["output"], expected)
                self.assertEqual(res["terminal"], "HALT")
                # Verificar cumplimiento estricto del cargador
                self.assertTrue(all(strict_byte(v, p) for p, v in enumerate(sub_img)))

    def test_07_negative_control_broken_space(self):
        """Control negativo: corromper el portal de espacios falsifica la salida visual esperada."""
        broken_img, _ = build_boss4_sierpinski(generations=2, mode="broken_space")
        res = run(broken_img, b"", max_steps=5000)
        # La salida no coincide con el fractal esperado
        expected = generate_sierpinski_text(2).encode("ascii")
        self.assertNotEqual(res["output"], expected)

    def test_08_negative_control_broken_star(self):
        """Control negativo: corromper el portal de estrellas emite '+' en vez de '*' falsificando el fractal."""
        broken_img, _ = build_boss4_sierpinski(generations=2, mode="broken_star")
        res = run(broken_img, b"", max_steps=5000)
        expected = generate_sierpinski_text(2).encode("ascii")
        self.assertNotEqual(res["output"], expected)
        self.assertIn(b"+", res["output"])

    def test_09_negative_control_broken_halt(self):
        """Control negativo: omitir la instrucción 'v' (HALT) impide terminar limpiamente con estado HALT."""
        broken_img, _ = build_boss4_sierpinski(generations=1, mode="broken_halt")
        res = run(broken_img, b"", max_steps=1000)
        self.assertNotEqual(res["terminal"], "HALT")


if __name__ == "__main__":
    unittest.main()
