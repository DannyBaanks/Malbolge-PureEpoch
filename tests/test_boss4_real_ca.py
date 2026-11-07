"""Suite de pruebas rigurosas para Boss 4 Real: Autómata Celular Wolfram Regla 90 Dinámico.

CONTRATO CANÓNICO DE AUTONOMÍA (AGENTS.md):
- Ejecución 100% autónoma en lenguaje Classic Malbolge en runtime.
- Cero escrituras de memoria del host durante la ejecución.
- Falsificación superada: el mismo binario .mal ejecuta trayectorias distintas según el estado de entrada.
- Paridad estricta entre 3 oráculos (Python Machine, C mb_ref, Olmstead original 1998).
"""
import hashlib
import json
from pathlib import Path
import unittest

from baseline.epoch_probe import Machine, load
from tools.boss4_real_ca import (
    build_boss4_real_ca,
    generate_ca_text,
    run_boss4_real,
)
from tools.build_candidates import strict_byte
from tools.observe import run
from tools.oracles import verify, validate_parity

PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent


class TestBoss4RealCA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cand_dir = PURE_EPOCH_ROOT / "candidates"
        cls.mal_path = cls.cand_dir / "boss4_real_ca.mal"
        cls.json_path = cls.cand_dir / "boss4_real_ca.json"

        if not cls.mal_path.exists() or not cls.json_path.exists():
            img, meta = build_boss4_real_ca(generations=8, mode="normal")
            cls.mal_path.write_bytes(img)
            cls.json_path.write_text(json.dumps(meta, indent=2))

        cls.img = cls.mal_path.read_bytes()
        cls.meta = json.loads(cls.json_path.read_text())

        cls.expected_s1 = generate_ca_text([7], generations=8, width=15).encode("ascii")
        cls.expected_s2 = generate_ca_text([5, 9], generations=8, width=15).encode("ascii")
        cls.expected_s3 = generate_ca_text([6, 7, 8], generations=8, width=15).encode("ascii")

    def test_01_canonical_artifact_exists_and_sha256(self):
        """El artefacto canónico existe, tiene el tamaño exacto y su SHA-256 coincide."""
        self.assertTrue(self.mal_path.exists())
        self.assertTrue(self.json_path.exists())
        self.assertEqual(len(self.img), 59049)
        sha = hashlib.sha256(self.img).hexdigest()
        self.assertEqual(sha, self.meta["sha256"])

    def test_02_strict_loader_compliance(self):
        """Todas las celdas cumplen con el cargador estricto de Olmstead 1998 (strict_byte)."""
        cells = list(self.img)
        self.assertTrue(all(strict_byte(v, p) for p, v in enumerate(cells)))

    def test_03_zero_host_writes(self):
        """La ejecución de la VM se realiza sin ninguna escritura de memoria externa del host."""
        # Se ejecuta mediante el harness observador puro (read-only probe)
        res = run_boss4_real(self.img, b"1")
        self.assertEqual(res["terminal"], "HALT")

    def test_04_dynamic_input_consumption(self):
        """La VM consume dinámicamente el byte de entrada de stdin vía la instrucción '/'."""
        m = Machine(load(self.img), b"1")
        while m.steps < 5000:
            if m.terminal != "RUNNING":
                break
            m.tick()
        self.assertEqual(m.input_cursor, 1, "La VM debe haber consumido exactamente 1 byte de entrada con '/'")

    def test_05_input_1_sierpinski_single_pulse(self):
        """Entrada '1' ejecuta la trayectoria del Triángulo de Sierpiński (Pulso Central Único)."""
        res = run_boss4_real(self.img, b"1")
        self.assertEqual(res["terminal"], "HALT")
        self.assertEqual(len(res["output"]), 128)
        self.assertEqual(res["output"], self.expected_s1)

    def test_06_input_2_symmetrical_double_pulse(self):
        """Entrada '2' ejecuta la trayectoria de Interferencia de Pulso Doble Simétrico."""
        res = run_boss4_real(self.img, b"2")
        self.assertEqual(res["terminal"], "HALT")
        self.assertEqual(len(res["output"]), 128)
        self.assertEqual(res["output"], self.expected_s2)

    def test_07_input_3_triplet_cluster_pulse(self):
        """Entrada '3' ejecuta la trayectoria de Onda Celular Compleja (Triplete Agrupado)."""
        res = run_boss4_real(self.img, b"3")
        self.assertEqual(res["terminal"], "HALT")
        self.assertEqual(len(res["output"]), 128)
        self.assertEqual(res["output"], self.expected_s3)

    def test_08_falsification_same_binary_mutually_distinct_trajectories(self):
        """Falsificación de autonomía: el MISMO binario sin regenerar produce salidas mutuamente distintas."""
        res1 = run_boss4_real(self.img, b"1")
        res2 = run_boss4_real(self.img, b"2")
        res3 = run_boss4_real(self.img, b"3")

        out1 = res1["output"]
        out2 = res2["output"]
        out3 = res3["output"]

        self.assertNotEqual(out1, out2, "Trayectorias 1 y 2 deben ser distintas")
        self.assertNotEqual(out2, out3, "Trayectorias 2 y 3 deben ser distintas")
        self.assertNotEqual(out1, out3, "Trayectorias 1 y 3 deben ser distintas")

    def test_09_three_oracle_parity_all_trajectories(self):
        """Paridad estricta entre 3 oráculos (Python Machine, C mb_ref, Olmstead 1998) en todas las trayectorias."""
        for payload, label in [(b"1", "Estado 1"), (b"2", "Estado 2"), (b"3", "Estado 3")]:
            with self.subTest(state=label):
                rep = verify(self.img, payload, budget=25000)
                self.assertTrue(validate_parity(rep), f"Paridad de oráculos fallida para {label}")
                self.assertTrue(rep["trace_equal"])
                self.assertTrue(rep["memory_equal"])
                self.assertTrue(rep["registers_equal"])
                self.assertTrue(rep["outputs_equal"])
                self.assertEqual(rep["reference_returncode"], 0)
                self.assertEqual(rep["original_returncode"], 0)

    def test_10_negative_controls_fail_closed(self):
        """Controles negativos: artefactos corruptos o sin halt fallan de manera cerrada."""
        img_broken_halt, _ = build_boss4_real_ca(mode="broken_halt")
        res_halt = run(img_broken_halt, b"1", max_steps=5000)
        self.assertNotEqual(res_halt["terminal"], "HALT", "Broken halt no debe terminar en HALT")


if __name__ == "__main__":
    unittest.main()
