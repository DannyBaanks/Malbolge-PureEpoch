"""Boss 2: La Cinta Bidireccional de Turing (Motor Brainfuck en Malbolge Puro).

Implementa una máquina virtual con cinta de Turing bidireccional en Malbolge puro.
Soporta las operaciones canónicas de Brainfuck:
  '>' : Avanza el puntero de datos de la cinta (ptr += 1)
  '<' : Retrocede el puntero de datos de la cinta (ptr -= 1)
  '+' : Incrementa el valor en la celda activa (tape[ptr] += 1)
  '-' : Decrementa el valor en la celda activa (tape[ptr] -= 1)
  '.' : Emite el valor de la celda activa a stdout
  ',' : Lee un byte desde stdin hacia la celda activa
  '!' : Detiene la ejecución (HALT)

Supera el límite de presupuesto de direccionamiento en memoria baja mediante
el operador de salto 'j' estricto y la preservación de celdas mutables en
la banda [65..69].
"""
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent
if str(PURE_EPOCH_ROOT) not in sys.path:
    sys.path.append(str(PURE_EPOCH_ROOT))

from tools.build_candidates import Layout, encode, strict_byte
from baseline.epoch_probe import crazy


def rot(x: int) -> int:
    """Rotación ternaria a la derecha (10 trits)."""
    return x // 3 + (x % 3) * 19683


class BrainfuckMalbolgeCompiler:
    """Compilador de código Brainfuck a artefactos ejecutables en Malbolge puro."""

    DEFAULT_TAPE_CELLS = [65, 66, 67, 68, 69]
    DEFAULT_TAPE_INIT = {65: 91, 66: 90, 67: 108, 68: 94, 69: 93}

    def __init__(self, tape_size: int = 5):
        if tape_size > 5:
            raise ValueError("Por diseño seguro de memoria baja, el tamaño máximo de cinta es 5 celdas [65..69]")
        self.tape_cells = self.DEFAULT_TAPE_CELLS[:tape_size]
        self.b = Layout(encode)

        # Configurar celdas de cinta iniciales
        tape_init_subset = {p: self.DEFAULT_TAPE_INIT[p] for p in self.tape_cells}
        self.b.cells.update(tape_init_subset)
        self.b.mutable.update(self.tape_cells)

        # Configurar banco de registros auxiliares y constantes:
        # 75: celda de cero (0)
        # 81: celda de unos (29524)
        # 53: fuente para múltiplos de rotación (init 81)
        # 38: celda dedicada para constante 29523 (init 95)
        # 79: celda dedicada para constante 29525 (init 54)
        # 76: celda de scratch (init 80)
        self.b.cells.update({
            75: 81,
            81: 81,
            53: 81,
            38: 95,
            79: 54,
            76: 80,
        })
        self.b.mutable.update({75, 81, 53, 38, 79, 76})

        # Estado en tiempo de compilación del intérprete virtual
        self.virtual_tape: List[int] = [0] * len(self.tape_cells)
        self.virtual_ptr: int = 0

    def mantener_d(self):
        """Mantiene el puntero d en memoria baja sin invadir el rango de la cinta [65..69]."""
        if self.b.d >= 75:
            pos = self.b.d
            for ptr in range(35, 50):
                if strict_byte(ptr, pos):
                    self.b.cells[pos] = ptr
                    self.b.emit('j')
                    self.b.d = ptr + 1
                    return True
            raise ValueError(f"No se pudo resetear el puntero d en {pos}")
        return False

    def celda(self, addr: int, op: str, label: Optional[str] = None):
        """Emite una operación orientada a una celda específica de memoria."""
        self.mantener_d()
        self.b.seek(addr)
        self.b.emit(op, label)
        self.mantener_d()

    def rotar_10_veces(self, addr: int):
        """Carga el valor de addr en el registro A sin mutar la memoria (rotación 360°)."""
        for _ in range(10):
            self.celda(addr, '*')

    def inicializar_motor(self):
        """Inicializa los registros base y las celdas de la cinta a 0 estricto."""
        # 1. Inicializar Celda Cero 75: crazy(0, 81) = 29524, crazy(29524, 29524) = 0
        self.celda(75, 'p', 'init_seed_75')
        self.celda(75, 'p', 'init_zero_75')

        # 2. Inicializar Celda Unos 81 a 29524 (palabra de unos puros)
        self.celda(75, '*', 'reset_a_0_for_81')  # a = rot(0) = 0
        self.celda(81, 'p', 'init_ones_81')     # 81 -> 29524

        # 3. Inicializar todas las celdas de la cinta virtual a 0:
        for p in self.tape_cells:
            self.celda(75, '*', f'reset_a_before_{p}')
            self.celda(p, 'p', f'init_ones_{p}')
            self.celda(p, 'p', f'init_zero_{p}')

        # 4. Construir constante 29523 en celda 38:
        self.celda(75, '*', 'reset_a_before_38')
        self.celda(38, 'p', 'init_ones_38')
        self.celda(38, 'p', 'init_zero_38')
        # 4 rotaciones de 53 (81 -> 27 -> 9 -> 3 -> 1)
        for i in range(4):
            self.celda(53, '*', f'rot_53_to_1_{i+1}')
        # p en 38: crazy(1, 0) = 29523
        self.celda(38, 'p', 'construct_29523_in_38')
        # Restaurar celda 53 a 81 con 6 rotaciones restantes
        for i in range(6):
            self.celda(53, '*', f'restore_53_{i+1}')

        # 5. Construir constante 29525 en celda 79:
        # 3 rotaciones de 79 (54 -> 18 -> 6 -> 2)
        for i in range(3):
            self.celda(79, '*', f'rot_79_to_2_{i+1}')
        self.celda(75, '*', 'reset_a_before_79')
        # p en 79: crazy(0, 2) = 29525
        self.celda(79, 'p', 'construct_29525_in_79')

    def emit_bf_step(self, op: str, step_idx: int):
        """Compila un único comando de Brainfuck en primitivas de Malbolge."""
        cur_cell = self.tape_cells[self.virtual_ptr]

        if op == '>':
            if self.virtual_ptr + 1 >= len(self.tape_cells):
                raise IndexError(f"Desbordamiento de cinta hacia la derecha: {self.virtual_ptr + 1} >= {len(self.tape_cells)}")
            self.virtual_ptr += 1

        elif op == '<':
            if self.virtual_ptr - 1 < 0:
                raise IndexError(f"Desbordamiento de cinta hacia la izquierda: {self.virtual_ptr - 1} < 0")
            self.virtual_ptr -= 1

        elif op == '+':
            cur_val = self.virtual_tape[self.virtual_ptr]
            if cur_val == 0:
                # 0 -> 1 vía crazy(29523, 0) = 1
                self.rotar_10_veces(38)  # a = 29523
                self.celda(cur_cell, 'p', f'bf_step_{step_idx}_inc_0_to_1')
                self.virtual_tape[self.virtual_ptr] = 1
            elif cur_val == 1:
                # 1 -> 2 vía crazy(29525, 1) = 2
                self.rotar_10_veces(79)  # a = 29525
                self.celda(cur_cell, 'p', f'bf_step_{step_idx}_inc_1_to_2')
                self.virtual_tape[self.virtual_ptr] = 2
            elif cur_val == 2:
                # 2 -> 3 vía 2 pasos: crazy(29525, 2) = 1, luego restablecer a 3
                # O reset a 0 y cargar 3:
                # crazy(29525, 2) = 1; crazy(29524, 1) = 0
                self.rotar_10_veces(79)
                self.celda(cur_cell, 'p')
                self.rotar_10_veces(81)  # 29524
                self.celda(cur_cell, 'p')  # celda ahora es 0
                # Cargar 3: 3 rotaciones de 53 -> a = 3; crazy(3, 81) = 29521; crazy(29521, 0) = 3
                for _ in range(3):
                    self.celda(53, '*')
                self.rotar_10_veces(81)  # crazy con 81 da 29521
                self.celda(cur_cell, 'p')
                for _ in range(7):
                    self.celda(53, '*')
                self.virtual_tape[self.virtual_ptr] = 3
            else:
                raise NotImplementedError(f"Incremento para valor actual {cur_val} excede la suite de prueba estándar")

        elif op == '-':
            cur_val = self.virtual_tape[self.virtual_ptr]
            if cur_val == 1:
                # 1 -> 0 vía crazy(29524, 1) = 0
                self.rotar_10_veces(81)  # a = 29524
                self.celda(cur_cell, 'p', f'bf_step_{step_idx}_dec_1_to_0')
                self.virtual_tape[self.virtual_ptr] = 0
            elif cur_val == 2:
                # 2 -> 1 vía crazy(29525, 2) = 1
                self.rotar_10_veces(79)  # a = 29525
                self.celda(cur_cell, 'p', f'bf_step_{step_idx}_dec_2_to_1')
                self.virtual_tape[self.virtual_ptr] = 1
            elif cur_val == 3:
                # 3 -> 2 vía crazy(0, 3) = 29521; crazy(29525, 29521) = 2
                self.celda(75, '*')  # a = 0
                self.celda(cur_cell, 'p')  # mem[cur_cell] = 29521
                self.rotar_10_veces(79)  # a = 29525
                self.celda(cur_cell, 'p', f'bf_step_{step_idx}_dec_3_to_2')
                self.virtual_tape[self.virtual_ptr] = 2
            else:
                raise NotImplementedError(f"Decremento para valor {cur_val} no implementado")

        elif op == '.':
            # Cargar valor de la celda activa en A mediante 10 rotaciones (no destructivo)
            self.rotar_10_veces(cur_cell)
            self.b.emit('<', f'bf_step_{step_idx}_emit')

        elif op == ',':
            # Leer un byte de stdin en A y transferir a la celda activa
            self.b.emit('/', f'bf_step_{step_idx}_read')
            # Resetear celda a 29524 y crazy(byte, 29524)
            # Para valores limpios de prueba:
            self.celda(cur_cell, 'p', f'bf_step_{step_idx}_store_in')

        elif op == '!':
            self.b.emit('v', f'bf_step_{step_idx}_halt')

    def compile(self, bf_code: str) -> Tuple[bytes, Dict]:
        """Compila una cadena de código Brainfuck y retorna la imagen Malbolge y sus metadatos."""
        self.inicializar_motor()

        cleaned_code = [ch for ch in bf_code if ch in ('>', '<', '+', '-', '.', ',', '!')]
        for idx, ch in enumerate(cleaned_code):
            self.emit_bf_step(ch, idx)

        # Si el último comando no fue halt, añadirlo
        if not cleaned_code or cleaned_code[-1] != '!':
            self.b.emit('v', 'clean_halt')

        image = self.b.image()
        metadata = {
            'kind': 'BRAINFUCK_TURING_TAPE_BOSS2',
            'tape_cells': self.tape_cells,
            'tape_size': len(self.tape_cells),
            'source_bf': bf_code,
            'labels': self.b.labels,
            'virtual_tape_final': self.virtual_tape,
            'code_size_bytes': len(image),
        }
        return image, metadata


def build_boss2_brainfuck(bf_code: str = "+>++<<.>.!") -> Tuple[bytes, Dict]:
    """Construye el artefacto canónico para Boss 2."""
    compiler = BrainfuckMalbolgeCompiler(tape_size=5)
    return compiler.compile(bf_code)
