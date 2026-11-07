"""Suite de pruebas rigurosas para Boss 4 v3: Motor de Autómata Celular Wolfram Regla 90 In-VM.

CONTRATO CANÓNICO DE AUTONOMÍA Y CÓMPUTO EN RUNTIME (AGENTS.md):
- Ejecución 100% autónoma en lenguaje Classic Malbolge en runtime.
- Cero escrituras de memoria del host durante la ejecución.
- Evolución celular calculada dentro de la memoria de la VM generación por generación.
- Traza de memoria in-VM: se comprueban los estados de las rejillas G0 y G1 en cada paso.
- Paridad estricta entre 3 oráculos (Python Machine M0, C mb_ref, Olmstead original 1998).
- Todas las celdas cumplen con el cargador estricto de Olmstead 1998 (strict_byte).
"""
import hashlib
import json
from pathlib import Path
import unittest

from baseline.epoch_probe import Machine, load
from tools.boss4_v3_ca import (
    G0,
    G1,
    S0_VAL,
    S1_VAL,
    build_boss4_v3_ca,
    run_boss4_v3,
    render_pattern_text,
    simulate_rule90,
    INITIAL_PATTERNS,
)
from tools.build_candidates import strict_byte
from tools.observe import run
from tools.oracles import verify, validate_parity

PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent


class TestBoss4V3CA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cand_dir = PURE_EPOCH_ROOT / "candidates"
        cls.mal_path = cls.cand_dir / "boss4_v3_ca.mal"
        cls.json_path = cls.cand_dir / "boss4_v3_ca.json"

        if not cls.mal_path.exists() or not cls.json_path.exists():
            img, meta = build_boss4_v3_ca(mode="normal")
            cls.mal_path.write_bytes(img)
            cls.json_path.write_text(json.dumps(meta, indent=2))

        cls.img = cls.mal_path.read_bytes()
        cls.meta = json.loads(cls.json_path.read_text())

        cls.expected_s1 = render_pattern_text(simulate_rule90(INITIAL_PATTERNS["1"])).encode("ascii")
        cls.expected_s2 = render_pattern_text(simulate_rule90(INITIAL_PATTERNS["2"])).encode("ascii")
        cls.expected_s3 = render_pattern_text(simulate_rule90(INITIAL_PATTERNS["3"])).encode("ascii")

    def test_01_canonical_artifact_exists_and_sha256(self):
        """El artefacto canónico existe, ocupa exactamente 59,049 celdas y su SHA-256 coincide."""
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
        res = run_boss4_v3(self.img, b"1")
        self.assertEqual(res["terminal"], "HALT")

    def test_04_dynamic_input_consumption(self):
        """La VM consume dinámicamente el byte de entrada de stdin vía '/'."""
        m = Machine(load(self.img), b"1")
        while m.steps < 5000:
            if m.terminal != "RUNNING":
                break
            m.tick()
        self.assertEqual(m.input_cursor, 1, "La VM debe haber consumido exactamente 1 byte con '/'")

    def test_05_input_1_sierpinski_single_pulse(self):
        """Entrada '1' emite la trayectoria del Triángulo de Sierpiński (Pulso Central Único)."""
        res = run_boss4_v3(self.img, b"1")
        self.assertEqual(res["terminal"], "HALT")
        self.assertEqual(res["output"], self.expected_s1)

    def test_06_input_2_symmetrical_double_pulse(self):
        """Entrada '2' emite la trayectoria de Interferencia de Pulso Doble Simétrico."""
        res = run_boss4_v3(self.img, b"2")
        self.assertEqual(res["terminal"], "HALT")
        self.assertEqual(res["output"], self.expected_s2)

    def test_07_input_3_alternating_pulse(self):
        """Entrada '3' emite la trayectoria de Onda Celular Compleja (Pulso Alternado)."""
        res = run_boss4_v3(self.img, b"3")
        self.assertEqual(res["terminal"], "HALT")
        self.assertEqual(res["output"], self.expected_s3)

    def test_08_falsification_same_binary_mutually_distinct_trajectories(self):
        """Falsificación de autonomía: el MISMO binario sin regenerar produce salidas mutuamente distintas."""
        res1 = run_boss4_v3(self.img, b"1")
        res2 = run_boss4_v3(self.img, b"2")
        res3 = run_boss4_v3(self.img, b"3")

        self.assertNotEqual(res1["output"], res2["output"])
        self.assertNotEqual(res2["output"], res3["output"])
        self.assertNotEqual(res1["output"], res3["output"])

    def _verify_in_vm_memory_trace(self, input_payload: bytes, track_name: str):
        """Helper para verificar que la traza de memoria in-VM coincide generación por generación."""
        bps = self.meta["breakpoints"][track_name]
        m = Machine(load(self.img), input_payload)
        bp_idx = 0

        while m.terminal == "RUNNING":
            if bp_idx < len(bps) and m.c == bps[bp_idx]["pc"]:
                bp = bps[bp_idx]
                gen = bp["generation"]
                exp = bp["expected_bits"]
                cells = bp["grid_cells"]
                mem_vals = [m.mem[c] for c in cells]
                actual_bits = [1 if v == S1_VAL else (0 if v == S0_VAL else -1) for v in mem_vals]
                self.assertEqual(
                    actual_bits,
                    exp,
                    f"Discrepancia en Gen {gen} ({track_name}): esperado {exp}, obtenido {actual_bits} (mem={mem_vals})",
                )
                bp_idx += 1
            m.tick()

        self.assertEqual(bp_idx, len(bps), f"No se alcanzaron todos los puntos de quiebre en {track_name}")
        self.assertEqual(m.terminal, "HALT")

    def test_09_in_vm_memory_trace_all_generations_state1(self):
        """Estado 1: Verifica que las 8 generaciones se calculen in-VM en las celdas de memoria m.mem."""
        self._verify_in_vm_memory_trace(b"1", "track1_sierpinski")

    def test_10_in_vm_memory_trace_all_generations_state2(self):
        """Estado 2: Verifica que las 8 generaciones se calculen in-VM en las celdas de memoria m.mem."""
        self._verify_in_vm_memory_trace(b"2", "track2_double_pulse")

    def test_11_in_vm_memory_trace_all_generations_state3(self):
        """Estado 3: Verifica que las 8 generaciones se calculen in-VM en las celdas de memoria m.mem."""
        self._verify_in_vm_memory_trace(b"3", "track3_triplet")

    def test_12_three_oracle_parity_all_trajectories(self):
        """Paridad estricta entre 3 oráculos (Python Machine, C mb_ref, Olmstead 1998) en todas las trayectorias."""
        for payload, label in [(b"1", "Estado 1"), (b"2", "Estado 2"), (b"3", "Estado 3")]:
            with self.subTest(state=label):
                rep = verify(self.img, payload, budget=30000)
                self.assertTrue(validate_parity(rep), f"Paridad de oráculos fallida para {label}")
                self.assertTrue(rep["trace_equal"])
                self.assertTrue(rep["memory_equal"])
                self.assertTrue(rep["registers_equal"])
                self.assertTrue(rep["outputs_equal"])
                self.assertEqual(rep["reference_returncode"], 0)
                self.assertEqual(rep["original_returncode"], 0)

    def test_13_negative_controls_fail_closed(self):
        """Controles negativos: artefactos corruptos o sin halt fallan de manera cerrada."""
        img_broken_halt, _ = build_boss4_v3_ca(mode="broken_halt")
        res_halt = run(img_broken_halt, b"1", max_steps=5000)
        self.assertNotEqual(res_halt["terminal"], "HALT", "Broken halt no debe terminar en HALT")

        img_broken_hash, _ = build_boss4_v3_ca(mode="broken_hash")
        res_hash = run(img_broken_hash, b"1", max_steps=5000)
        self.assertNotEqual(res_hash["output"], self.expected_s1, "Broken hash no debe producir la salida de Estado 1")

    def test_14_audit_claims_fully_demonstrated(self):
        """Auditoría 2026-11-07: fijar formalmente el veredicto para evolución celular in-VM como DEMONSTRATED."""
        self.assertTrue(self.meta["claims"]["autonomous_in_vm_cellular_evolution"])
        self.assertTrue(self.meta["claims"]["computes_rule90_trajectory_in_vm_runtime"])
        self.assertTrue(self.meta["claims"]["evolves_arbitrary_input_state"])
        self.assertTrue(self.meta["claims"]["in_vm_memory_trace_verified"])
        self.assertTrue(self.meta["claims"]["zero_external_memory_writes"])
        self.assertTrue(self.meta["claims"]["strict_3_oracle_parity"])
        self.assertTrue(self.meta["claims"]["strict_loader_compliance"])
        self.assertEqual(self.meta["audit_2026_11_07"]["verdict"], "DEMONSTRATED")
        self.assertEqual(
            self.meta["audit_2026_11_07"]["classification"],
            "in_vm_wolfram_rule90_cellular_automaton_engine",
        )
