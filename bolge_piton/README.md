# BolgePiton — VM de Pitón en Malbolge (La Inversa de Pibolge)

**Laboratorio experimental:** ISyCo Labs / PureEpoch Multi-Epoch Substrate  
**Fecha:** 2026-10-25  
**Estado:** `DEMONSTRATED` — Paridad 4/4 en Oráculo C (`mb_ref`) y Oráculo Pitón (`pibolge.piton`).

---

## 1. Motivación y Antecedentes

En el ecosistema ISyCo, **Pibolge** ([pibolge.piton](file:///home/danny/Development/ISyCo%20Git/Pibolge/pibolge.piton)) es un intérprete canónico de Malbolge Classic escrito enteramente en **Pitón** (el lenguaje de Danny que compila y ejecuta Python con gramática en español).

**BolgePiton** resuelve la pregunta simétrica fundamental:
> *¿Puede Malbolge actuar como Máquina Virtual para ejecutar código de Pitón?*

Históricamente, construir un intérprete dentro de Malbolge era considerado imposible debido a la automutación criptográfica de su memoria (`XLAT1`/`XLAT2`), la ausencia de memoria direccionable lineal y la falta de un ciclo de lectura/rearme.

Gracias a los avances de **PureEpoch** (octubre 2026):
1. **Identidad de Inicialización a Cero:** Se genera el estado base `0` sin violar el loader de Malbolge mediante la secuencia idempotente `crazy(0, 81) = 29524` (unos trits) y `crazy(29524, 29524) = 0`.
2. **Punteros y Ventanas en Memoria Baja ($D \setminus C \setminus E$):** El acumulador virtual se aloja en la celda `75` y se mantiene el puntero de datos `d` acotado en `[35..55]` mediante saltos dinámicos `j` sin tocar el acumulador `a`.
3. **Multi-Instrucción y Despacho:** La VM lee el flujo de bytes desde `stdin` con `/` y despacha operaciones de emisión directa `<`, acumulación `p` o parada `v`.

---

## 2. Arquitectura de Tres Capas (El Ciclo Ouroboros)

```
+-------------------------------------------------------------+
| Nivel 0: Host Runtime (CPython 3.12 / Ubuntu 24.04)         |
+-------------------------------------------------------------+
                              │
                              ▼
+-------------------------------------------------------------+
| Nivel 1: Pibolge (pibolge.piton)                            |
|          Intérprete de Malbolge escrito en Pitón             |
+-------------------------------------------------------------+
                              │
                              ▼
+-------------------------------------------------------------+
| Nivel 2: BolgePiton (bolge_piton_vm.mal)                    |
|          Máquina Virtual de 184 bytes en Malbolge puro      |
+-------------------------------------------------------------+
                              │
                              ▼
+-------------------------------------------------------------+
| Nivel 3: Micro-Pitón (script .piton)                         |
|          imprimir_texto "Hola Piton! Resultado: "           |
|          cargar 65                                          |
|          locura 3                                           |
|          imprimir                                           |
|          parar                                              |
+-------------------------------------------------------------+
                              │
                              ▼
             Salida: "Hola Piton! Resultado: Q"
```

---

## 3. Resultados Experimentales

La suite [`ouroboros_test.py`](ouroboros_test.py) evalúa 4 propiedades formales:

| Test ID | Caso de Prueba | Oráculo C (`mb_ref`) | Oráculo Pitón (`pibolge.piton`) | Veredicto |
|---|---|---|---|---|
| **T1** | Emisión de Texto en Español (`"Hola"`) | `b"Hola"` | `b"Hola"` | **PASS** |
| **T2** | Operación Ternaria en VM (`crazy(3, crazy(65, 0))` = `81`) | `b"Q"` | `b"Q"` | **PASS** |
| **T3** | Cadena Completa con Estado (`"ISyCo Piton!"`) | `b"ISyCo Piton!"` | `b"ISyCo Piton!"` | **PASS** |
| **T4** | Control Negativo / Falsación (inyección divergente `B != A`) | Divergencia confirmada | Divergencia confirmada | **PASS** |

---

## 4. Archivos del Laboratorio

- [`micro_piton.py`](micro_piton.py): Compilador del lenguaje Micro-Pitón y emisor de payloads.
- [`vm_builder.py`](vm_builder.py): Generador de la VM en Malbolge (`Layout`, codificación estricta y resets de `d`).
- [`bolge_piton_cli.py`](bolge_piton_cli.py): Interfaz CLI y demostración interactiva en terminal.
- [`ouroboros_test.py`](ouroboros_test.py): Suite formal de pruebas automatizadas.
- [`GUIA.md`](GUIA.md): Guía de uso humano obligatoria.
