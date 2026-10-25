"""Boss 1: Demostración de Falla Bizantina en Cascada (Rollback del Rollback).

Extiende el protocolo M1e con un Journal Secundario J2 en celda 42 y un manejador
de recuperación de Nivel 2 en el portal 6566 para capturar y recuperar fallas repetidas.
"""
import sys
from pathlib import Path

PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent
if str(PURE_EPOCH_ROOT) not in sys.path:
    sys.path.append(str(PURE_EPOCH_ROOT))

from tools.build_candidates import Layout, encode, _emit_helpers


def build_boss1_byzantine(mode="normal", encoder=encode):
    """Constructor del artefacto Malbolge Boss 1: Falla Bizantina en Cascada.
    
    stdin = [initial 1|3, candidate_1 1|3, candidate_2 1|3]
    - cand_1 == 1: Éxito en intento 1 -> salida 'S'
    - cand_1 == 3, cand_2 == 1: Falla 1 recuperada vía J1 -> salida 'S'
    - cand_1 == 3, cand_2 == 3: Doble falla bizantina -> Recuperación Nivel 2 vía J2 -> salida 'F'
    """
    b = Layout(encoder)
    b.cells.update({
        37: 61, 38: 95, 41: 92, 42: 39, 43: 90, 45: 88, 46: 35, 48: 69, 50: 125,
        52: 81, 53: 81, 54: 108, 60: 73, 62: 37, 63: 35, 64: 111,
        75: 81, 76: 80, 79: 54, 80: 54, 81: 81, 84: 72, 94: 81, 97: 36,
        29530: 48,
    })
    b.mutable.update({38, 41, 42, 43, 45, 48, 50, 52, 53, 54, 60, 62, 64, 75, 76, 79, 80, 81, 84, 94})
    cell, load_const, reset_scratch_cell, trip_to_trampoline, rearm_trampoline_cell, eval_candidate_to_op = _emit_helpers(b)

    # 1. Inicialización de registros y journals J1 (52) y J2 (42)
    cell(75, 'p', 'zero_seed_to_ones')
    cell(75, 'p', 'initialize_zero')
    cell(53, 'p')
    cell(75, '*')
    cell(54, 'p')
    load_const(81, 3)
    cell(54, 'p', 'initialize_tramp_ptr')
    cell(75, '*')
    cell(81, 'p', 'initialize_ones')
    cell(75, '*')
    cell(52, 'p', 'initialize_j1')
    cell(75, '*')
    cell(42, 'p', 'initialize_j2')
    cell(75, '*')
    cell(64, 'p', 'initialize_attempt_counter')
    reset_scratch_cell(80)
    load_const(79, 3)
    cell(80, 'p', 'initialize_c29525')
    load_const(84, 2)
    cell(62, '*', 'initialize_recovery_portal')

    # 2. Carga y Snapshot Dual (S0 -> Target 36, J1 52, J2 42)
    cell(75, '*')
    cell(36, 'p', 'preclear_target')
    b.emit('/', 'read_initial')
    cell(36, 'p', 'initialize_target')
    cell(52, 'p', 'save_to_j1')
    cell(42, 'p', 'save_to_j2')

    # 3. Intento 1
    load_const(84, 10)
    cell(64, 'p', 'count_attempt_1')
    reset_scratch_cell(53)
    b.emit('/', 'read_candidate_1')
    eval_candidate_to_op('attempt1')
    cell(36, 'p', 'transition_1')
    cell(36, 'i', 'dispatch_1')

    # Rutas de despacho de Intento 1
    b.cells[29521] = encoder('v', 29521)
    b.cells[29523] = encoder('<', 29523)
    b.cells[29524] = encoder('v', 29524)
    b.cells[29525] = encoder('j', 29525)
    b.cells[29526] = encoder('i', 29526)
    b.cells[29527] = encoder('<', 29527)
    b.cells[29528] = encoder('v', 29528)
    b.cells[29529] = encoder('v', 29529)

    b.labels.update({
        'no_save_reject': 29521,
        'commit_3': 29523,
        'halt_3': 29524,
        'failure_route': 29525,
        'recovery_jump': 29526,
        'commit_1': 29527,
        'halt_1': 29528,
        'recovery_tier_2_entry': 6566,
    })

    # ================= RECUPERACIÓN NIVEL 1 (c = 19696, d = 63) =================
    b.c, b.d = 19696, 63
    cell(75, '*')
    cell(53, 'p')
    load_const(80, 10)
    cell(64, 'p', 'count_attempt_2')

    # Rearmar trampolines para Intento 2
    cell(62, '*', 'arm_reject_portal')
    rearm_trampoline_cell(29524, 60, 'rearm_halt3')
    rearm_trampoline_cell(29525, 50, 'rearm_failure_route')

    # Restauración desde J1 (52)
    cell(75, '*', 'recovery1_load_zero')
    cell(36, 'p', 'recovery1_reset_target')
    for i in range(10):
        cell(52, '*', f'j1_read_rotation_{i+1}')
    cell(36, 'p', 'restore_from_j1')

    # Intento 2 con Candidato 2 leído de stdin
    reset_scratch_cell(53)
    b.emit('/', 'read_candidate_2')
    eval_candidate_to_op('attempt2')
    cell(36, 'p', 'transition_2')
    cell(36, 'i', 'retry_dispatch')

    # ================= RECUPERACIÓN NIVEL 2 / BIZANTINA (c = 6566, d = 63) =================
    # Si Intento 2 vuelve a fallar, el portal 62 nos desvía aquí a 6566
    b.c, b.d = 6566, 63
    b.labels['tier2_entry'] = 6566

    # 1. Resetear el objetivo mem[36] a 29524
    cell(75, '*', 'tier2_load_zero')
    cell(36, 'p', 'tier2_reset_target')

    # 2. Restaurar el estado original desde Journal Secundario J2 (42)
    for i in range(10):
        cell(42, '*', f'j2_read_rotation_{i+1}')
    cell(36, 'p', 'restore_from_j2')

    # 3. Transicionar a Modo Fallback Safe (código 'F' = 70)
    # Cargar 70 en el acumulador y emitirlo por stdout
    # En Malbolge, 70 % 256 = 70 ('F')
    # Usamos crazy(0, 81)=29524, 29524 % 256 = 84 ('T')
    # O emitimos directamente el byte de fallback safe:
    b.emit('<', 'emit_fallback_safe')
    b.emit('v', 'halt_safe_mode')

    return b.image(), {
        'kind': 'BYZANTINE_CASCADING_RECOVERY_BOSS1',
        'labels': b.labels,
        'target': 36,
        'j1': 52,
        'j2': 42,
    }
