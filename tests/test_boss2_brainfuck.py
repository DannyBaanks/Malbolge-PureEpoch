"""Test suite for Boss 2: La Cinta Bidireccional de Turing (Brainfuck en Malbolge).

Verifica la máquina virtual de cinta bidireccional en Malbolge puro:
- Movimiento bidireccional del puntero de datos (>, <)
- Mutación de celdas aritméticas (+, -)
- Lectura y emisión de celdas (.)
- Aislamiento de celdas en memoria baja sin colisiones de XLAT2
- Paridad estricta entre 3 oráculos (Python, mb_ref, olmstead)
- Telemetría de cronómetro de alta resolución para flexear velocidad.
"""
import hashlib
import json
import time
import unittest
from pathlib import Path

PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent
import sys
if str(PURE_EPOCH_ROOT) not in sys.path:
    sys.path.append(str(PURE_EPOCH_ROOT))

from tools.boss2_brainfuck import build_boss2_brainfuck, BrainfuckMalbolgeCompiler
from tools.observe import run
from tools.oracles import verify, validate_parity


class TestBoss2Brainfuck(unittest.TestCase):
    """Pruebas unitarias para el motor Brainfuck en Malbolge (Boss 2)."""

    def setUp(self):
        self.t0 = time.perf_counter()

    def tearDown(self):
        elapsed = (time.perf_counter() - self.t0) * 1000
        print(f" [CRONÓMETRO: {elapsed:6.2f} ms] -> {self.id().split('.')[-1]}")

    def test_01_tape_initialization(self):
        """Verifica que las celdas de la cinta virtual [65..69] se inicializan a 0 limpio."""
        compiler = BrainfuckMalbolgeCompiler(tape_size=5)
        # Solo inicializar y parar inmediatamente
        compiler.inicializar_motor()
        compiler.b.emit('v', 'halt_after_init')
        img = compiler.b.image()

        res = run(img, b'')
        self.assertEqual(res['terminal'], 'HALT')
        for cell_addr in [65, 66, 67, 68, 69]:
            self.assertEqual(res['memory'][cell_addr], 0, f"Celda {cell_addr} debe ser 0")

    def test_02_unidirectional_operations(self):
        """Verifica avance hacia adelante (+ > ++ > .) sin retroceso."""
        bf_code = "+>++>."
        img, meta = build_boss2_brainfuck(bf_code)
        res = run(img, b'')
        self.assertEqual(res['terminal'], 'HALT')
        # Celda 2 no fue modificada, su valor es 0
        self.assertEqual(list(res['output']), [0])

    def test_03_bidirectional_pointer_movement(self):
        """Verifica movimiento adelante y atrás: + > ++ < . > . !"""
        bf_code = "+>++<.>.!"
        img, meta = build_boss2_brainfuck(bf_code)
        res = run(img, b'')
        self.assertEqual(res['terminal'], 'HALT')
        self.assertEqual(list(res['output']), [1, 2])

    def test_04_decrement_and_rewind(self):
        """Verifica mutación con decremento y rebobinado: ++ > + < - . > . !"""
        bf_code = "++>+<-.>.!"
        img, meta = build_boss2_brainfuck(bf_code)
        res = run(img, b'')
        self.assertEqual(res['terminal'], 'HALT')
        self.assertEqual(list(res['output']), [1, 1])

    def test_05_canonical_boss2_parity_3_oracles(self):
        """Verifica paridad estricta entre 3 oráculos para el candidato canónico Boss 2."""
        cand_mal = PURE_EPOCH_ROOT / "candidates" / "boss2_brainfuck.mal"
        cand_json = PURE_EPOCH_ROOT / "candidates" / "boss2_brainfuck.json"

        self.assertTrue(cand_mal.exists(), "Artefacto candidates/boss2_brainfuck.mal debe existir")
        self.assertTrue(cand_json.exists(), "Metadatos candidates/boss2_brainfuck.json deben existir")

        img = cand_mal.read_bytes()
        meta = json.loads(cand_json.read_text())

        # Verificar integridad SHA-256
        sha256 = hashlib.sha256(img).hexdigest()
        self.assertEqual(sha256, meta['sha256'])

        # Ejecución contra los 3 oráculos
        report = verify(img, b'', 5000)
        self.assertTrue(validate_parity(report), "Paridad estricta falló entre los 3 oráculos")
        self.assertEqual(report['terminal'], 'HALT')
        self.assertTrue(report['outputs_equal'])
        self.assertTrue(report['trace_equal'])
        self.assertTrue(report['memory_equal'])

        # Salida esperada del candidato canónico: [1, 1, 2, 1, 2]
        py_res = run(img, b'')
        self.assertEqual(list(py_res['output']), meta['output_expected'])


if __name__ == '__main__':
    unittest.main()
