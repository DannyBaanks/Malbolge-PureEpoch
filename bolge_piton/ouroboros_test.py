"""Ouroboros Test Suite: Demostración formal de la VM BolgePiton.

Verifica la equivalencia semántica y el ciclo reflexivo completo:
Nivel 0: Host Python (CPython 3.12)
Nivel 1: Intérprete Malbolge escrito en Pitón (Pibolge)
Nivel 2: Intérprete Pitón escrito en Malbolge (BolgePiton)
Nivel 3: Programa escrito en Micro-Pitón en español

Incluye cronometraje de alta resolución para cada prueba (flex telemetry).
"""
import os
import sys
import time
import subprocess
import unittest
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parent
REPO_ROOT = LAB_DIR.parents[2]
PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent
PIBOLGE_ROOT = Path("/home/danny/Development/ISyCo Git/Pibolge")

if str(PURE_EPOCH_ROOT) not in sys.path:
    sys.path.append(str(PURE_EPOCH_ROOT))
if str(LAB_DIR) not in sys.path:
    sys.path.append(str(LAB_DIR))

from baseline.epoch_probe import crazy
from micro_piton import compilar_texto_piton, ensamblar_payload
from vm_builder import construir_vm_para_programa

MB_REF_BIN = PURE_EPOCH_ROOT / "build" / "mb_ref"
PIBOLGE_SCRIPT = PIBOLGE_ROOT / "pibolge.piton"


def format_ms(segundos: float) -> str:
    return f"{segundos * 1000:.2f} ms"


class TestBolgePitonOuroboros(unittest.TestCase):
    def setUp(self):
        self.assertTrue(MB_REF_BIN.is_file(), f"Oráculo C no encontrado en {MB_REF_BIN}")
        self.assertTrue(PIBOLGE_SCRIPT.is_file(), f"Pibolge no encontrado en {PIBOLGE_SCRIPT}")

    def ejecutar_en_oraculo_c(self, bytecode_mal: bytes, payload_stdin: bytes, max_pasos: int = 50000):
        temp_mal = LAB_DIR / "temp_run.mal"
        try:
            temp_mal.write_bytes(bytecode_mal)
            t0 = time.perf_counter()
            res = subprocess.run(
                [str(MB_REF_BIN), str(temp_mal), str(max_pasos)],
                input=payload_stdin,
                capture_output=True,
                check=False,
            )
            t1 = time.perf_counter()
            self.assertEqual(res.returncode, 0, f"Error en C VM: {res.stderr.decode(errors='replace')}")
            return res.stdout, (t1 - t0)
        finally:
            if temp_mal.exists():
                temp_mal.unlink()

    def ejecutar_en_pibolge_piton(self, bytecode_mal: bytes, payload_stdin: bytes, max_pasos: int = 50000):
        temp_mal = LAB_DIR / "temp_run.mal"
        try:
            temp_mal.write_bytes(bytecode_mal)
            t0 = time.perf_counter()
            res = subprocess.run(
                ["python3", "-m", "piton.cli", "ejecutar", str(PIBOLGE_SCRIPT), str(temp_mal), str(max_pasos)],
                input=payload_stdin,
                capture_output=True,
                check=False,
            )
            t1 = time.perf_counter()
            self.assertEqual(res.returncode, 0, f"Error en Pibolge: {res.stderr.decode(errors='replace')}")
            salida = res.stdout
            if salida.endswith(b"\n"):
                salida = salida[:-1]
            return salida, (t1 - t0)
        finally:
            if temp_mal.exists():
                temp_mal.unlink()

    def test_01_saludo_hola_micro_piton(self):
        """Prueba 1: Un programa en español emite 'Hola' interpretado por Malbolge."""
        codigo = """
        imprimir_texto "Hola"
        parar
        """
        instrucciones = compilar_texto_piton(codigo)
        payload = ensamblar_payload(instrucciones)
        vm_mal = construir_vm_para_programa(instrucciones)

        # 1. Ejecución sobre el oráculo C (mb_ref)
        salida_c, t_c = self.ejecutar_en_oraculo_c(vm_mal, payload)
        self.assertEqual(salida_c, b"Hola")

        # 2. Ejecución sobre el oráculo Pitón (Pibolge: Pitón corriendo Malbolge corriendo Pitón)
        salida_piton, t_pi = self.ejecutar_en_pibolge_piton(vm_mal, payload)
        self.assertEqual(salida_piton, b"Hola")

        print(f"\n   ⏱️  [CRONÓMETRO T1] Oráculo C: {format_ms(t_c)} | Pibolge Ouroboros: {format_ms(t_pi)} | Paridad: 100% OK")

    def test_02_operacion_ternaria_locura(self):
        """Prueba 2: Micro-Pitón ejecuta una operación ternaria crazy calculada en Malbolge."""
        b1 = 65  # 'A'
        b2 = 3
        esperado_val = crazy(b2, crazy(b1, 0)) % 256
        esperado_bytes = bytes([esperado_val])  # 81 -> b'Q'

        codigo = f"""
        cargar {b1}
        locura {b2}
        imprimir
        parar
        """
        instrucciones = compilar_texto_piton(codigo)
        payload = ensamblar_payload(instrucciones)
        vm_mal = construir_vm_para_programa(instrucciones)

        # 1. En C VM
        salida_c, t_c = self.ejecutar_en_oraculo_c(vm_mal, payload)
        self.assertEqual(salida_c, esperado_bytes)

        # 2. En Pibolge (Ouroboros)
        salida_piton, t_pi = self.ejecutar_en_pibolge_piton(vm_mal, payload)
        self.assertEqual(salida_piton, esperado_bytes)

        print(f"\n   ⏱️  [CRONÓMETRO T2] Oráculo C: {format_ms(t_c)} | Pibolge Ouroboros: {format_ms(t_pi)} | Paridad: 100% OK")

    def test_03_frase_isyco_piton(self):
        """Prueba 3: Cadena completa 'ISyCo Piton!' con paridad dual."""
        mensaje = "ISyCo Piton!"
        codigo = f"""
        imprimir_texto "{mensaje}"
        parar
        """
        instrucciones = compilar_texto_piton(codigo)
        payload = ensamblar_payload(instrucciones)
        vm_mal = construir_vm_para_programa(instrucciones)

        salida_c, t_c = self.ejecutar_en_oraculo_c(vm_mal, payload)
        salida_piton, t_pi = self.ejecutar_en_pibolge_piton(vm_mal, payload)

        self.assertEqual(salida_c, mensaje.encode("ascii"))
        self.assertEqual(salida_piton, mensaje.encode("ascii"))

        print(f"\n   ⏱️  [CRONÓMETRO T3] Oráculo C: {format_ms(t_c)} | Pibolge Ouroboros: {format_ms(t_pi)} | Paridad: 100% OK")

    def test_04_control_negativo_falsacion(self):
        """Prueba 4: Falsación. Un payload alterado produce divergencia observable."""
        codigo = """
        imprimir_texto "A"
        parar
        """
        instrucciones = compilar_texto_piton(codigo)
        vm_mal = construir_vm_para_programa(instrucciones)
        payload_corrupto = b"B"  # Inyectamos 'B' en vez de 'A'

        salida_c, t_c = self.ejecutar_en_oraculo_c(vm_mal, payload_corrupto)
        self.assertEqual(salida_c, b"B")
        self.assertNotEqual(salida_c, b"A")

        print(f"\n   ⏱️  [CRONÓMETRO T4] Control negativo en C: {format_ms(t_c)} | Falsación confirmada")


if __name__ == "__main__":
    unittest.main()
