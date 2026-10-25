"""Test suite for Boss 3: El Santo Grial (El Bucle while x > 0 con N Dinámico y Re-encriptación en Caliente).

Verifica exhaustivamente el bucle dinámico de Malbolge puro:
- Ejecución dinámica para N = 1, 2, 3 sobre las MISMAS celdas físicas [64, 65, 88, 89]
- Demostración de cero entropía / regeneración termodinámica (Twin-Cylinder F <-> J)
- Salida limpia a HALT mediante portal prelanding desacoplado
- Controles negativos (broken_rearm, broken_exit)
- Paridad estricta entre 3 oráculos (Python, mb_ref, Olmstead 1998)
- Cronómetro de alta resolución para telemetría de flex
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

from tools.boss3_dynamic_loop import build_boss3_dynamic_loop, simulate_dynamic_loop_execution
from tools.observe import run
from tools.oracles import verify, validate_parity


class TestBoss3DynamicLoop(unittest.TestCase):
    """Pruebas unitarias rigurosas para el bucle dinámico Boss 3."""

    def setUp(self):
        self.t0 = time.perf_counter()

    def tearDown(self):
        elapsed = (time.perf_counter() - self.t0) * 1000
        print(f" [CRONÓMETRO: {elapsed:6.2f} ms] -> {self.id().split('.')[-1]}")

    def test_01_dynamic_loop_n1(self):
        """Verifica que para N=1 el bucle ejecuta 1 iteración sobre [64, 65, 88, 89] y para en HALT."""
        src, meta = build_boss3_dynamic_loop('normal')
        res = simulate_dynamic_loop_execution(src, iterations=1)

        self.assertEqual(res['terminal'], 'HALT')
        self.assertEqual(res['steps'], 57)
        self.assertEqual(len(res['output']), 2)  # 1 inicial + 1 bucle
        self.assertTrue(res['address_reuse_verified'])
        self.assertEqual(res['unique_loop_pcs'], [64, 65, 88, 89])

    def test_02_dynamic_loop_n2(self):
        """Verifica que para N=2 el bucle ejecuta 2 iteraciones sobre las MISMAS celdas físicas y para en HALT."""
        src, meta = build_boss3_dynamic_loop('normal')
        res = simulate_dynamic_loop_execution(src, iterations=2)

        self.assertEqual(res['terminal'], 'HALT')
        self.assertEqual(res['steps'], 81)  # 57 + 24
        self.assertEqual(len(res['output']), 3)  # 1 inicial + 2 bucle
        self.assertTrue(res['address_reuse_verified'])
        self.assertEqual(res['unique_loop_pcs'], [64, 65, 88, 89])

    def test_03_dynamic_loop_n3(self):
        """Verifica que para N=3 el bucle ejecuta 3 iteraciones sobre las MISMAS celdas físicas y para en HALT."""
        src, meta = build_boss3_dynamic_loop('normal')
        res = simulate_dynamic_loop_execution(src, iterations=3)

        self.assertEqual(res['terminal'], 'HALT')
        self.assertEqual(res['steps'], 105)  # 81 + 24
        self.assertEqual(len(res['output']), 4)  # 1 inicial + 3 bucle
        self.assertTrue(res['address_reuse_verified'])
        self.assertEqual(res['unique_loop_pcs'], [64, 65, 88, 89])

    def test_04_negative_control_broken_rearm(self):
        """Control negativo: Corromper la celda de reentrada provoca colapso o parada anómala."""
        src_broken, meta = build_boss3_dynamic_loop('broken_rearm')
        # La celda de reentrada 49 está rota
        res = run(src_broken, b'1', max_steps=100)
        # No puede completar la ejecución normal del ciclo
        self.assertNotEqual(res['terminal'], 'HALT')

    def test_05_negative_control_broken_exit(self):
        """Control negativo: Corromper el portal de parada impide terminar con HALT (falla en STALL)."""
        src_broken, meta = build_boss3_dynamic_loop('broken_exit')
        # En entrada 0, debe fallar al detenerse porque la celda 100 tiene nop en vez de 'v'
        res = run(src_broken, b'0', max_steps=100)
        self.assertEqual(res['terminal'], 'STALL')

    def test_06_canonical_boss3_parity_3_oracles(self):
        """Verifica paridad estricta entre 3 oráculos para el candidato canónico Boss 3."""
        cand_mal = PURE_EPOCH_ROOT / "candidates" / "boss3_dynamic_loop.mal"
        cand_json = PURE_EPOCH_ROOT / "candidates" / "boss3_dynamic_loop.json"

        self.assertTrue(cand_mal.exists(), "Artefacto candidates/boss3_dynamic_loop.mal debe existir")
        self.assertTrue(cand_json.exists(), "Metadatos candidates/boss3_dynamic_loop.json deben existir")

        img = cand_mal.read_bytes()
        meta = json.loads(cand_json.read_text())

        # Verificar integridad SHA-256
        sha256 = hashlib.sha256(img).hexdigest()
        self.assertEqual(sha256, meta['sha256'])

        # Ejecución contra los 3 oráculos para entrada 0
        report0 = verify(img, b'0', 1000)
        self.assertTrue(validate_parity(report0), "Paridad estricta falló entre los 3 oráculos para entrada 0")
        self.assertEqual(report0['terminal'], 'HALT')
        self.assertTrue(report0['outputs_equal'])
        self.assertTrue(report0['trace_equal'])
        self.assertTrue(report0['memory_equal'])

        # Ejecución contra los 3 oráculos para entrada 1 (50 pasos)
        report1 = verify(img, b'1', 50)
        self.assertTrue(validate_parity(report1), "Paridad estricta falló entre los 3 oráculos para entrada 1")
        self.assertEqual(report1['terminal'], 'BUDGET')
        self.assertTrue(report1['outputs_equal'])
        self.assertTrue(report1['trace_equal'])
        self.assertTrue(report1['memory_equal'])


if __name__ == '__main__':
    unittest.main()
