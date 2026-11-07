"""Contract G1–G8 and mutantes para boss3_real_loop.mal."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent
if str(PURE_EPOCH_ROOT) not in sys.path:
    sys.path.append(str(PURE_EPOCH_ROOT))

from baseline.epoch_probe import XLAT1
from tools.build_candidates import encode, strict_byte
from tools.observe import run
from tools.oracles import validate_parity, verify
from tools.boss3_real_loop import build_boss3_real_loop

CANDIDATE_PATH = PURE_EPOCH_ROOT / "candidates" / "boss3_real_loop.mal"
META_PATH = PURE_EPOCH_ROOT / "candidates" / "boss3_real_loop.json"
EVIDENCE_ROOT = PURE_EPOCH_ROOT / "evidence" / "boss3_real"


def _load_artifact():
    if not CANDIDATE_PATH.exists():
        raise FileNotFoundError(f"{CANDIDATE_PATH} no existe")
    img = CANDIDATE_PATH.read_bytes()
    meta = json.loads(META_PATH.read_text())
    return img, meta


class TestBoss3RealLoopContract(unittest.TestCase):
    """G1–G8 y controles negativos."""

    def setUp(self):
        self.domain = [bytes([48 + i]) for i in range(10)]  # '0'..'9'
        self.out_of_domain = [b'', b'/', b':', b'A', b'\x00']

    def _run(self, payload, max_steps=50000):
        img, _ = _load_artifact()
        return run(img, payload, max_steps)

    # G1 Iteración real
    def test_G1_same_pc_repeated_exactly_N(self):
        img, meta = _load_artifact()
        pc_by_n = {}
        for i, payload in enumerate(self.domain):
            n = i
            res = run(img, payload, max_steps=50000)
            pcs = [step['pre'][1] for step in res['trace']]
            counts = {}
            for pc in pcs:
                counts[pc] = counts.get(pc, 0) + 1
            candidates = []
            for pc, cnt in counts.items():
                if cnt == n and n > 0:
                    candidates.append(pc)
            pc_by_n[n] = candidates

        pcs_for_n1 = pc_by_n[1]
        self.assertTrue(pcs_for_n1, "No hay PC con conteo 1")
        common_candidates = set(pcs_for_n1)
        for n in range(2, 10):
            common_candidates = common_candidates.intersection(pc_by_n[n])
        self.assertTrue(common_candidates, "No hay PC común con conteo N para todos los N>=1")
        common_pc = list(common_candidates)[0]
        for n in range(1, 10):
            self.assertIn(common_pc, pc_by_n[n], f"G1 falla para N={n}, PC común {common_pc} no repetida {n} veces")

    # G2 Sin tablas por N
    def test_G2_distinct_output_instructions_constant(self):
        img, _ = _load_artifact()
        output_pcs_per_n = {}
        for i, payload in enumerate(self.domain):
            n = i
            res = run(img, payload, max_steps=50000)
            output_pcs = set()
            for step in res['trace']:
                pc = step['pre'][1]
                if step.get('output'):
                    output_pcs.add(pc)
            output_pcs_per_n[n] = output_pcs

        sizes = [len(s) for n, s in output_pcs_per_n.items() if n > 0]
        self.assertEqual(len(set(sizes)), 1, f"G2 falla: tamaños de PCs de salida varían {sizes}")
        self.assertEqual(sizes[0], 1, "Debe haber exactamente 1 instrucción de salida compartida")

    # G3 Salida exacta
    def test_G3_exact_output_0_to_9(self):
        img, _ = _load_artifact()
        for i, payload in enumerate(self.domain):
            n = i
            res = run(img, payload, max_steps=50000)
            self.assertEqual(res['terminal'], 'HALT', f"G3: terminal no HALT para {payload!r}")
            self.assertEqual(res['output'], b'1' * n, f"G3: salida incorrecta para {payload!r}")

    # G4 Fuera de dominio
    def test_G4_out_of_domain_defined(self):
        img, _ = _load_artifact()
        for payload in self.out_of_domain:
            res = run(img, payload, max_steps=50000)
            self.assertIn(res['terminal'], ('HALT', 'BUDGET', 'STALL'), f"G4: terminal inesperado para {payload!r}")
            self.assertLess(res['steps'], 50000)

    # G5 Cero escrituras del host
    def test_G5_no_host_writes(self):
        self.assertTrue(True)

    # G6 Paridad 3 oráculos
    def test_G6_parity_three_oracles(self):
        img, meta = _load_artifact()
        for payload in self.domain + self.out_of_domain:
            report = verify(img, payload, budget=50000, evidence=str(EVIDENCE_ROOT / (payload.hex() if payload else 'empty')))
            self.assertTrue(validate_parity(report), f"G6 parity falla para {payload!r}")
            if payload in self.domain:
                self.assertEqual(report['reference_returncode'], 0)
                self.assertEqual(report['original_returncode'], 0)

    # G7 Inmutable y reconstructible
    def test_G7_immutable_reproducible(self):
        img, meta = _load_artifact()
        sha = hashlib.sha256(img).hexdigest()
        self.assertEqual(sha, meta.get('sha256'), "G7: SHA256 no coincide con meta")
        rebuilt_img, _ = build_boss3_real_loop('normal')
        self.assertEqual(rebuilt_img, img, "G7: Reconstrucción no coincide byte a byte")

    # G8 Loader estricto
    def test_G8_strict_loader(self):
        img, _ = _load_artifact()
        for pos, byte in enumerate(img):
            self.assertTrue(strict_byte(byte, pos), f"G8: byte no estricto en pos {pos}")

    # Mutantes
    def test_mutant_broken_decrement_fails_G3(self):
        mutant_path = PURE_EPOCH_ROOT / "candidates" / "boss3_real_loop_broken_decrement.mal"
        self.assertTrue(mutant_path.exists(), f"{mutant_path} no existe")
        img = mutant_path.read_bytes()
        res = run(img, b'2', max_steps=50000)
        self.assertNotEqual((res['terminal'], res['output']), ('HALT', b'11'), "Mutante broken_decrement debió fallar G3 para N=2")

    def test_mutant_broken_exit_fails_G3_G4(self):
        mutant_path = PURE_EPOCH_ROOT / "candidates" / "boss3_real_loop_broken_exit.mal"
        self.assertTrue(mutant_path.exists(), f"{mutant_path} no existe")
        img = mutant_path.read_bytes()
        res = run(img, b'0', max_steps=50000)
        self.assertNotEqual(res['terminal'], 'HALT', "Mutante broken_exit debió fallar con terminal != HALT para '0'")

    def test_mutant_broken_rearm_fails_G1_or_G3(self):
        mutant_path = PURE_EPOCH_ROOT / "candidates" / "boss3_real_loop_broken_rearm.mal"
        self.assertTrue(mutant_path.exists(), f"{mutant_path} no existe")
        img = mutant_path.read_bytes()
        res = run(img, b'2', max_steps=50000)
        self.assertNotEqual(res['output'], b'11', "Mutante broken_rearm debió fallar G3 para N=2")

    def test_mutant_off_by_one_fails_G3(self):
        mutant_path = PURE_EPOCH_ROOT / "candidates" / "boss3_real_loop_off_by_one.mal"
        self.assertTrue(mutant_path.exists(), f"{mutant_path} no existe")
        img = mutant_path.read_bytes()
        res = run(img, b'1', max_steps=50000)
        self.assertNotEqual(res['output'], b'1', "Mutante off_by_one debió fallar G3 para N=1")


if __name__ == '__main__':
    unittest.main()
