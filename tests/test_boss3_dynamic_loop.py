"""Test suite for Boss 3: El Santo Grial - Bucle while x > 0 Autónomo con N Dinámico.

Verifica exhaustivamente el bucle dinámico autónomo de Malbolge puro:
- Ejecución dinámica para N in {0, 1, 2, 3, 7} sin modificación externa de memoria
- Generación in-band de constantes ternarias (a = 32817 -> '1')
- Despacho ternario universal por rotación y crazy
- Salida limpia a HALT mediante portal desacoplado
- Controles negativos (broken_exit, broken_rearm)
- Paridad estricta entre 3 oráculos (Python, mb_ref.c, Olmstead 1998)
- Cronómetro de alta resolución para telemetría
"""
import hashlib
import json
import time
import unittest
from pathlib import Path
import sys

PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent
if str(PURE_EPOCH_ROOT) not in sys.path:
    sys.path.append(str(PURE_EPOCH_ROOT))

from tools.boss3_autonomous_loop import build_boss3_autonomous_loop, run_boss3_autonomous_execution
from tools.observe import run
from tools.oracles import verify, validate_parity


class TestBoss3DynamicLoop(unittest.TestCase):
    """Pruebas unitarias rigurosas para el bucle dinámico autónomo Boss 3."""

    def setUp(self):
        self.t0 = time.perf_counter()

    def tearDown(self):
        elapsed = (time.perf_counter() - self.t0) * 1000
        print(f" [CRONÓMETRO: {elapsed:6.2f} ms] -> {self.id().split('.')[-1]}")

    def test_01_autonomous_loop_n0(self):
        """Verifica que para N=0 y EOF la ejecución es vacía y para limpiamente en HALT."""
        src, meta = build_boss3_autonomous_loop('normal')
        
        # Caso EOF
        res_eof = run_boss3_autonomous_execution(src, b'')
        self.assertEqual(res_eof['terminal'], 'HALT')
        self.assertEqual(res_eof['output'], b'')
        self.assertEqual(res_eof['steps'], 8)
        
        # Caso '0'
        res_0 = run_boss3_autonomous_execution(src, b'0')
        self.assertEqual(res_0['terminal'], 'HALT')
        self.assertEqual(res_0['output'], b'')
        self.assertEqual(res_0['steps'], 8)

    def test_02_autonomous_loop_n1(self):
        """Verifica que para N=1 el bucle emite exactamente un '1' y para en HALT."""
        src, meta = build_boss3_autonomous_loop('normal')
        res = run_boss3_autonomous_execution(src, b'1')

        self.assertEqual(res['terminal'], 'HALT')
        self.assertEqual(res['output'], b'1')
        self.assertEqual(res['steps'], 14)

    def test_03_autonomous_loop_n2(self):
        """Verifica que para N=2 el bucle emite exactamente dos '1's y para en HALT."""
        src, meta = build_boss3_autonomous_loop('normal')
        res = run_boss3_autonomous_execution(src, b'2')

        self.assertEqual(res['terminal'], 'HALT')
        self.assertEqual(res['output'], b'11')
        self.assertEqual(res['steps'], 15)

    def test_04_autonomous_loop_n3(self):
        """Verifica que para N=3 el bucle emite exactamente tres '1's y para en HALT."""
        src, meta = build_boss3_autonomous_loop('normal')
        res = run_boss3_autonomous_execution(src, b'3')

        self.assertEqual(res['terminal'], 'HALT')
        self.assertEqual(res['output'], b'111')
        self.assertEqual(res['steps'], 16)

    def test_05_autonomous_loop_n7(self):
        """Verifica que para N=7 el bucle emite exactamente siete '1's y para en HALT."""
        src, meta = build_boss3_autonomous_loop('normal')
        res = run_boss3_autonomous_execution(src, b'7')

        self.assertEqual(res['terminal'], 'HALT')
        self.assertEqual(res['output'], b'1111111')
        self.assertEqual(res['steps'], 22)

    def test_06_negative_control_broken_exit(self):
        """Control negativo: Corromper el portal de parada impide terminar con HALT (consume presupuesto o falla)."""
        src_broken, meta = build_boss3_autonomous_loop('broken_exit')
        res = run(src_broken, b'0', max_steps=100)
        self.assertNotEqual(res['terminal'], 'HALT', "El portal corrupto no debió terminar en HALT")

    def test_07_negative_control_broken_rearm(self):
        """Control negativo: Corromper la constante ternaria rompe la generación del carácter de salida."""
        src_broken, meta = build_boss3_autonomous_loop('broken_rearm')
        res = run(src_broken, b'1', max_steps=100)
        # La celda 49 corrompida emite byte inválido (0x0E) en vez de ASCII '1'
        self.assertNotEqual(res['output'], b'1', "La constante corrupta no debió emitir ASCII '1'")

    def test_08_canonical_boss3_parity_3_oracles(self):
        """Verifica paridad estricta bit-exacta entre 3 oráculos para el candidato canónico Boss 3."""
        cand_mal = PURE_EPOCH_ROOT / "candidates" / "boss3_autonomous_loop.mal"
        cand_json = PURE_EPOCH_ROOT / "candidates" / "boss3_autonomous_loop.json"

        self.assertTrue(cand_mal.exists(), "Artefacto candidates/boss3_autonomous_loop.mal debe existir")
        self.assertTrue(cand_json.exists(), "Metadatos candidates/boss3_autonomous_loop.json deben existir")

        img = cand_mal.read_bytes()
        meta = json.loads(cand_json.read_text())

        # Verificar integridad SHA-256
        sha256 = hashlib.sha256(img).hexdigest()
        self.assertEqual(sha256, meta['sha256'])

        # Casos de prueba exhaustivos contra los 3 oráculos
        test_cases = [
            (b'', b'', "EOF"),
            (b'0', b'', "N=0"),
            (b'1', b'1', "N=1"),
            (b'2', b'11', "N=2"),
            (b'3', b'111', "N=3"),
            (b'7', b'1111111', "N=7"),
        ]

        for payload, expected_output, label in test_cases:
            report = verify(img, payload, 5000)
            self.assertTrue(validate_parity(report), f"Paridad estricta falló entre los 3 oráculos para {label}")
            self.assertEqual(report['terminal'], 'HALT', f"Estado terminal no fue HALT para {label}")
            self.assertEqual(report['output_hex'], expected_output.hex(), f"Salida hex incorrecta para {label}")
            self.assertTrue(report['outputs_equal'], f"Discrepancia de salida en oráculos para {label}")
            self.assertEqual(report['reference_returncode'], 0, f"mb_ref.c retorno distinto de 0 para {label}")
            self.assertEqual(report['original_returncode'], 0, f"olmstead_original.c retorno distinto de 0 para {label}")


if __name__ == '__main__':
    unittest.main()
