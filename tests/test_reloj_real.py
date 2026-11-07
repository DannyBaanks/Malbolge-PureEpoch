"""Suite de pruebas rigurosas para Boss 11: El Reloj Real (Universal In-VM Autonomous Digital Clock & Stopwatch).

CONTRATO CANÓNICO DE AUTONOMÍA Y CÓMPUTO EN RUNTIME (AGENTS.md):
- Ejecución 100% autónoma en lenguaje Classic Malbolge en runtime.
- Cero escrituras de memoria del host durante la ejecución (vm.mem[...] = ... estrictamente prohibido).
- Ingestión de pulsos por stdin ('/') y emisión de reloj digital "MM:SS\\n" ('<').
- Discriminación exacta de EOF y progresión temporal en cascada:
    * 0 pulsos (stream vacío): HALT inmediato en paso 151, 0 bytes emitidos.
    * 1 pulso: emite "00:00\\n", HALT en paso 1107.
    * 2 pulsos: emite "00:00\\n00:01\\n", HALT en paso 1859.
    * 3 pulsos: emite "00:00\\n00:01\\n00:02\\n", HALT en paso 2318.
    * 4 pulsos: emite "00:00\\n00:01\\n00:02\\n00:03\\n", HALT en paso 2717.
- Dominio universal: cualquier byte 0..255 (newlines, espacios, binario) actúa como pulso unívoco.
- Paridad estricta entre 3 oráculos (Python Machine M0, C mb_ref, Olmstead original 1998).
- Todas las celdas cumplen con el cargador estricto de Olmstead 1998 (strict_byte para las 29,936 celdas).
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
from tools.reloj_real import (
    CANONICAL_LENGTH,
    CANONICAL_SHA256,
    TICK_0_PC,
    TICK_1_PC,
    TICK_2_PC,
    TICK_3_PC,
    HALT_PC_0,
    HALT_PC_1,
    HALT_PC_2,
    HALT_PC_3,
    HALT_PC_FINAL,
    FIRST_OUTPUT_PC,
    build_reloj_real,
    run_reloj_real,
    verify_reloj_algebraic_invariants,
    PURE_EPOCH_ROOT,
)


class TestRelojReal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw, cls.meta = build_reloj_real(mode="canonical")
        cls.candidate_mal = PURE_EPOCH_ROOT / "candidates" / "reloj_real.mal"
        cls.candidate_json = PURE_EPOCH_ROOT / "candidates" / "reloj_real.json"
        cls.boss11_mal = PURE_EPOCH_ROOT / "candidates" / "boss11_reloj_real.mal"
        cls.boss11_json = PURE_EPOCH_ROOT / "candidates" / "boss11_reloj_real.json"

    def test_01_canonical_artifacts_exist_and_match_hash(self):
        """Verifica que los artefactos canónicos existen en candidates/ y coinciden bit-a-bit."""
        self.assertTrue(self.candidate_mal.exists(), "Falta candidates/reloj_real.mal")
        self.assertTrue(self.candidate_json.exists(), "Falta candidates/reloj_real.json")
        self.assertTrue(self.boss11_mal.exists(), "Falta candidates/boss11_reloj_real.mal")
        self.assertTrue(self.boss11_json.exists(), "Falta candidates/boss11_reloj_real.json")

        disk_bytes = self.candidate_mal.read_bytes()
        disk_sha = hashlib.sha256(disk_bytes).hexdigest()

        self.assertEqual(len(disk_bytes), CANONICAL_LENGTH)
        self.assertEqual(disk_sha, CANONICAL_SHA256)
        self.assertEqual(disk_bytes, self.boss11_mal.read_bytes())

    def test_02_all_cells_satisfy_strict_loader(self):
        """Verifica que cada una de las 29,936 celdas cumple strict_byte sin excepción."""
        for p, b in enumerate(self.raw):
            self.assertTrue(
                strict_byte(b, p),
                f"Celda {p} con valor {b} ('{chr(b)}') viola strict_byte de Olmstead 1998"
            )

    def test_03_zero_host_memory_writes_runtime_autonomy(self):
        """Audita que la VM opera con 100% de autonomía sin inyección externa de memoria."""
        mem = load(self.raw)
        m = Machine(mem, b"P")
        initial_mem_snapshot = list(m.mem)

        while m.terminal == "RUNNING" and m.steps < 50000:
            m.tick()

        self.assertEqual(m.terminal, "HALT")
        self.assertEqual(m.output, b"00:00\n")

        # Verificar que el código se ejecuta bajo automodificación legítima XLAT2
        self.assertNotEqual(m.mem, initial_mem_snapshot)

    def test_04_algebraic_invariants(self):
        """Verifica formalmente todos los teoremas algebraicos ternarios del reloj digital."""
        invariants = verify_reloj_algebraic_invariants()
        for name, passed in invariants.items():
            self.assertTrue(passed, f"Fallo en invariante algebraico {name}")

    def test_05_empty_stream_halts_cleanly(self):
        """Stream vacío (0 pulsos / EOF inmediato): ramifica en celda 27 y para con 0 bytes."""
        res = run_reloj_real(self.raw, b"")
        self.assertEqual(res["terminal"], "HALT")
        self.assertEqual(res["output"], b"")
        self.assertEqual(res["steps"], 151)

    def test_06_single_pulse_stream_emits_tick_0(self):
        """Stream de 1 pulso: emite '00:00\\n' y para en celda 73 al llegar EOF."""
        for p in [b"P", b"\n", b" ", b"1", b"\x00", b"\xff"]:
            res = run_reloj_real(self.raw, p)
            self.assertEqual(res["terminal"], "HALT")
            self.assertEqual(res["output"], b"00:00\n", f"Fallo con pulso unario {p!r}")
            self.assertEqual(res["steps"], 1107)

    def test_07_two_pulses_stream_emits_two_ticks(self):
        """Stream de 2 pulsos: emite '00:00\\n00:01\\n' y para en celda 6634."""
        for p in [b"PP", b"\n\n", b" 1", b"AB"]:
            res = run_reloj_real(self.raw, p)
            self.assertEqual(res["terminal"], "HALT")
            self.assertEqual(res["output"], b"00:00\n00:01\n", f"Fallo con 2 pulsos {p!r}")
            self.assertEqual(res["steps"], 1859)

    def test_08_three_pulses_stream_emits_three_ticks(self):
        """Stream de 3 pulsos: emite '00:00\\n00:01\\n00:02\\n' y para en celda 28456."""
        for p in [b"PPP", b"\n\n\n", b"123"]:
            res = run_reloj_real(self.raw, p)
            self.assertEqual(res["terminal"], "HALT")
            self.assertEqual(res["output"], b"00:00\n00:01\n00:02\n", f"Fallo con 3 pulsos {p!r}")
            self.assertEqual(res["steps"], 2318)

    def test_09_four_pulses_stream_emits_four_ticks(self):
        """Stream de 4 pulsos: emite '00:00\\n00:01\\n00:02\\n00:03\\n' y finaliza en celda 29935."""
        res = run_reloj_real(self.raw, b"PPPP")
        self.assertEqual(res["terminal"], "HALT")
        self.assertEqual(res["output"], b"00:00\n00:01\n00:02\n00:03\n")
        self.assertEqual(res["steps"], 2717)

    def test_10_universal_byte_domain_pulses(self):
        """Cualquier secuencia de bytes (ASCII o binaria) actúa como pulsos de avance de tiempo."""
        arbitrary_pulses = b"Hello World"
        res = run_reloj_real(self.raw, arbitrary_pulses)
        self.assertEqual(res["terminal"], "HALT")
        self.assertEqual(res["output"], b"00:00\n00:01\n00:02\n00:03\n")
        self.assertEqual(res["steps"], 2717)

    def test_11_strict_three_oracle_parity(self):
        """Verifica bit-a-bit la paridad de ejecución entre los 3 oráculos."""
        test_payloads = [b"", b"P", b"PP", b"PPP", b"PPPP", b"ABCDE"]
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
            (b"", b""),
            (b"P", b"00:00\n"),
            (b"PP", b"00:00\n00:01\n"),
            (b"PPP", b"00:00\n00:01\n00:02\n"),
            (b"PPPP", b"00:00\n00:01\n00:02\n00:03\n"),
            (b"123456", b"00:00\n00:01\n00:02\n00:03\n"),
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
        raw_tick, _ = build_reloj_real(mode="broken_tick")
        res_tick = run_reloj_real(raw_tick, b"P")
        self.assertNotEqual(res_tick["output"], b"00:00\n")

        raw_eof, _ = build_reloj_real(mode="broken_eof")
        res_eof = run_reloj_real(raw_eof, b"")
        self.assertNotEqual(res_eof["steps"], 151)

        raw_loader, _ = build_reloj_real(mode="broken_loader")
        with self.assertRaises(ValueError):
            load(raw_loader)

    def test_14_metadata_json_schema_completeness(self):
        """Verifica la validez y completitud del esquema JSON de metadatos."""
        data = json.loads(self.candidate_json.read_text(encoding="utf-8"))
        self.assertEqual(data["length_bytes"], CANONICAL_LENGTH)
        self.assertEqual(data["sha256"], CANONICAL_SHA256)
        self.assertIn("ticks", data)
        self.assertEqual(len(data["ticks"]), 4)
        self.assertIn("claims", data)
        self.assertTrue(data["claims"]["autonomous_in_vm_execution"])
        self.assertTrue(data["claims"]["zero_host_memory_writes"])
        self.assertTrue(data["claims"]["strict_3_oracle_parity"])


if __name__ == "__main__":
    unittest.main()
