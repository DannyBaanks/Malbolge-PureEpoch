"""Micro-Pitón: Compilador y ensamblador de la ISA minimalista de Pitón para BolgePiton.

Define la sintaxis en español de Micro-Pitón y su compilación a la secuencia
de tokens y operandos ejecutables por la VM en Malbolge.
"""
from typing import List, Tuple, Union

# Definición de Opcodes de Micro-Pitón
OP_EMITIR = 1       # emitir <byte>: emite directamente a stdout
OP_CARGAR = 2       # cargar <byte>: carga al acumulador
OP_LOCURA = 3       # locura <byte>: aplica crazy(acumulador, byte)
OP_IMPRIMIR_ACC = 4 # imprimir: emite el valor del acumulador a stdout
OP_PARAR = 5        # parar: HALT limpio


class Instruccion:
    def __init__(self, op: int, arg: int = 0, comentario: str = ""):
        self.op = op
        self.arg = arg
        self.comentario = comentario

    def __repr__(self):
        return f"Instruccion(op={self.op}, arg={self.arg}, comentario='{self.comentario}')"


def compilar_texto_piton(codigo: str) -> List[Instruccion]:
    """Parsea un script de Micro-Pitón en español a una lista de instrucciones."""
    instrucciones = []
    lineas = codigo.strip().splitlines()
    for num_linea, linea in enumerate(lineas, 1):
        linea = linea.split("#")[0].strip()
        if not linea:
            continue
        partes = linea.split()
        cmd = partes[0].lower()
        if cmd == "emitir":
            if len(partes) < 2:
                raise ValueError(f"Línea {num_linea}: 'emitir' requiere un argumento (número o carácter)")
            arg = partes[1]
            val = ord(arg[1:-1]) if (arg.startswith('"') or arg.startswith("'")) and len(arg) >= 3 else int(arg)
            instrucciones.append(Instruccion(OP_EMITIR, val, f"emitir {val}"))
        elif cmd == "imprimir_texto":
            # Azúcar sintáctica: emite cada carácter de un string
            texto = linea[len("imprimir_texto"):].strip()
            if (texto.startswith('"') and texto.endswith('"')) or (texto.startswith("'") and texto.endswith("'")):
                texto = texto[1:-1]
            for ch in texto:
                instrucciones.append(Instruccion(OP_EMITIR, ord(ch), f"emitir '{ch}'"))
        elif cmd == "cargar":
            if len(partes) < 2:
                raise ValueError(f"Línea {num_linea}: 'cargar' requiere un argumento numérico")
            val = int(partes[1])
            instrucciones.append(Instruccion(OP_CARGAR, val, f"cargar {val}"))
        elif cmd == "locura":
            if len(partes) < 2:
                raise ValueError(f"Línea {num_linea}: 'locura' requiere un operando numérico")
            val = int(partes[1])
            instrucciones.append(Instruccion(OP_LOCURA, val, f"locura {val}"))
        elif cmd == "imprimir":
            instrucciones.append(Instruccion(OP_IMPRIMIR_ACC, 0, "imprimir acumulador"))
        elif cmd == "parar" or cmd == "alto":
            instrucciones.append(Instruccion(OP_PARAR, 0, "parar"))
        else:
            raise ValueError(f"Línea {num_linea}: instrucción desconocida '{cmd}'")
    
    # Asegurar parada explícita al final
    if not instrucciones or instrucciones[-1].op != OP_PARAR:
        instrucciones.append(Instruccion(OP_PARAR, 0, "parar automático"))
    return instrucciones


def ensamblar_payload(instrucciones: List[Instruccion]) -> bytes:
    """Serializa la lista de instrucciones a la corriente de bytes para stdin de Malbolge."""
    payload = bytearray()
    for inst in instrucciones:
        if inst.op == OP_EMITIR:
            payload.append(inst.arg % 256)
        elif inst.op in (OP_CARGAR, OP_LOCURA):
            payload.append(inst.arg % 256)
    return bytes(payload)
