"""Generador de la VM BolgePiton en Malbolge puro.

Utiliza el motor Layout y el codificador estricto de PureEpoch para
sintetizar un programa Malbolge válido que actúa como máquina virtual
para el bytecode de Micro-Pitón.
"""
import sys
from pathlib import Path
from typing import List

# Importar el motor de candidatos y el codificador canónico de PureEpoch
PURE_EPOCH_ROOT = Path(__file__).resolve().parent.parent
if str(PURE_EPOCH_ROOT) not in sys.path:
    sys.path.append(str(PURE_EPOCH_ROOT))

from tools.build_candidates import Layout, encode, strict_byte
from baseline.epoch_probe import crazy

from micro_piton import (
    OP_EMITIR,
    OP_CARGAR,
    OP_LOCURA,
    OP_IMPRIMIR_ACC,
    OP_PARAR,
    Instruccion,
    compilar_texto_piton,
    ensamblar_payload,
)


def mantener_d_en_rango_bajo(b):
    """Mantiene el puntero d en memoria baja [1..70] usando saltos 'j' válidos."""
    if b.d >= 60:
        pos = b.d
        for ptr in range(35, 55):
            if strict_byte(ptr, pos):
                b.cells[pos] = ptr
                b.emit("j")
                b.d = ptr + 1
                return True
        raise ValueError(f"No se encontró un puntero válido para resetear d en {pos}")
    return False


def construir_vm_para_programa(instrucciones: List[Instruccion]) -> bytes:
    """Construye un artefacto Malbolge .mal especializado para ejecutar el script de Micro-Pitón."""
    b = Layout(encode)
    
    # Celda 75 en memoria baja servirá como acumulador (ACC)
    b.cells[75] = 81
    b.mutable.add(75)

    def celda(direccion, operacion, etiqueta=None):
        mantener_d_en_rango_bajo(b)
        b.seek(direccion)
        b.emit(operacion, etiqueta)
        mantener_d_en_rango_bajo(b)

    # Fase de inicialización de la VM: Poner a cero el acumulador en celda 75
    # Identidad PureEpoch: crazy(0, 81) = 29524 (unos puros), crazy(29524, 29524) = 0
    celda(75, "p", "init_unos_75")
    celda(75, "p", "init_cero_75")

    # Fase de ejecución de instrucciones
    for idx, inst in enumerate(instrucciones):
        etiqueta_paso = f"inst_{idx}"
        mantener_d_en_rango_bajo(b)
        if inst.op == OP_EMITIR:
            # Lee byte de stdin y lo emite inmediatamente a stdout
            b.emit("/", f"{etiqueta_paso}_leer")
            b.emit("<", f"{etiqueta_paso}_emitir")
        elif inst.op == OP_CARGAR:
            # Leer el byte de stdin y computar crazy(byte, mem[75])
            # (Con mem[75] inicializado a 0, esto deposita la representación base en el acumulador)
            b.emit("/", f"{etiqueta_paso}_leer_const")
            celda(75, "p", f"{etiqueta_paso}_guardar_acc")
        elif inst.op == OP_LOCURA:
            # Leer el operando de stdin y aplicar crazy(operando, acc)
            b.emit("/", f"{etiqueta_paso}_leer_op")
            celda(75, "p", f"{etiqueta_paso}_aplicar_locura")
        elif inst.op == OP_IMPRIMIR_ACC:
            # Cargar el acumulador a registro A si es necesario y emitir a stdout
            b.emit("<", f"{etiqueta_paso}_imprimir_acc")
        elif inst.op == OP_PARAR:
            b.emit("v", f"{etiqueta_paso}_parar")

    # Si la última instrucción no fue HALT, asegurar parada
    if not instrucciones or instrucciones[-1].op != OP_PARAR:
        b.emit("v", "parar_final")

    return b.image()
