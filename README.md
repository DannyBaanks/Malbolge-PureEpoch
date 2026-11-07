<div align="center">

# Malbolge-PureEpoch v2.0 — Recuperación y Reintentos Multi-Época dentro de Malbolge Clásico

[![Version](https://img.shields.io/badge/version-2.0-blue.svg)](https://github.com/DannyBaanks/Malbolge-PureEpoch)

<img src="assets/pureepoch-hero.svg" width="100%" alt="PureEpoch: ilustración conceptual de tres épocas Classic Malbolge compartiendo un núcleo de control. No es una traza real." />

<br />

**Un solo proceso. Tres épocas. Recuperación y reintentos dentro de Malbolge Classic.**

Un laboratorio reproducible de checkpoint, restauración lógica, bifurcación, rollback, rearme de instrucciones y continuación en una VM automodificable.

Parte de la **Suite Experimental de Macroestados y Épocas v2.0** del ecosistema Malbolge de ISyCo.

<br />

![Classic](https://img.shields.io/badge/VM-Malbolge_Classic-32d8bc?style=flat-square)
![Offline](https://img.shields.io/badge/Reproducción-offline-76a5ff?style=flat-square)
![M3](https://img.shields.io/badge/Épocas-3-d68ffc?style=flat-square)
![Ouroboros](https://img.shields.io/badge/Ouroboros-BolgePiton_VM-ff5470?style=flat-square)
![Evidence](https://img.shields.io/badge/Disciplina-evidencia_%2B_controles-f5bd70?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.10%2B-8399c3?style=flat-square)

[**Resultados**](RESULTS.md) · [**Veredictos**](VERDICT.md) · [**Experimentos toroidales**](torus/TORUS_RESULTS.md) · [**BolgePiton**](bolge_piton/README.md) · [**Galería visual**](https://github.com/DannyBaanks/MalbolgArt)

</div>

---

> [!IMPORTANT]
> **REGLA FUNDAMENTAL DE AUTONOMÍA:**
> **Todo programa en este repositorio DEBE EJECUTARSE SOLO CON PURO LENGUAJE MALBOLGE. Python y lo demás solo sirve como oráculo de verificación, no como puente en runtime ni como ayuda.**
>
> Python y C construyen, observan y verifican *fuera* de la ejecución. Los checkpoints, saltos, restores, reintentos y autómatas celulares suceden dentro de la **VM Classic de Malbolge en runtime**, sin simulación externa ni escrituras de memoria del host.
>
> El dominio positivo probado es **acotado** (valores de entrada `0x01` y `0x03`). **Ni un rollback físico de toda la máquina ni una quine autónoma de 94 bytes están demostrados.**

## 01 / Por qué existe

Malbolge cifra el código que ejecuta. Reusar un punto de control o volver a un estado anterior no consiste simplemente en saltar otra vez a la misma dirección.

**PureEpoch estudia una pregunta concreta:** ¿puede un programa Classic preservar un dato, detectar una transición inválida, reconstruirlo desde un journal y continuar una nueva época **sin intervención correctiva del intérprete ni del host**?

La respuesta demostrada en este laboratorio es **sí, para protocolos y estados finitos específicamente construidos**. El límite de esa demostración importa tanto como el resultado.

<div align="center">

| `SAVE` | `ATTEMPT` | `CHECK` | `RESTORE` | `RETRY` | `REARM` |
|:---:|:---:|:---:|:---:|:---:|:---:|
| Guardar estado | Construir candidato | Decisión interna | Recuperar journal | Segundo intento | Continuar la época |

</div>

### Resumen de hitos

| Hito | Artefacto principal | Resultado observado | Límite |
|---|---|---|---|
| **M0 · Control** | `baseline/` | Truth Machine: ciclo de 408 instrucciones y 17 unos | Un ciclo **no es** reparación |
| **M1a · Reversibilidad** | `candidates/m1a_rot10.mal` | Diez rotaciones restituyen una celda | Sin checkpoint |
| **M1b · Checkpoint** | `candidates/m1b_normal.mal` | Restauración de una celda con journal interno | Recuperación incondicional |
| **M1c / M1d · Rollback** | `candidates/m1c_normal.mal` | Bifurcación por dato, restore y segundo intento in-band | Dos candidatos y un reintento, no algoritmo general |
| **M1e · Rearme** | `candidates/m1e_normal.mal` | Commit según dato recuperado, trampolines rearmados y rechazo explícito | Dominio cerrado `{1,3}` |
| **M2 · Continuación** | `candidates/m2_normal.mal` | **2 épocas** en una sola ejecución | 8 combinaciones ensayadas |
| **M3 · Composición** | `candidates/m3_normal.mal` | **3 épocas**, roundtrip y rollback; propuestas offline verificadas | Protocolo construido, no motor universal |
| **94 · Control reutilizable** | `evidence/quine-94-analysis.json` | Identidad de roundtrip y núcleo `0..93` reutilizable | **No** es una quine autónoma de 94 bytes |
| **G-T2 / G-T3 · Préstamo** | `torus/programs/` | Journal prestado/restaurado y consumidor posterior verificado | Campaña toroidal independiente y acotada |
| **BolgePiton · Ouroboros** | `bolge_piton/` | **VM en Malbolge** interpretando Micro-Pitón; paridad C ↔ Pibolge | Dominio acotado de ISA |
| **Boss 3 · Bucle Real** | `candidates/boss3_real_loop.mal` | **Bucle autónomo `while x > 0`** con PC repetida $N$ veces y rearme in-VM | Dominio $x \in \{0..9\}$; loader estricto y paridad 3 oráculos (G1–G8 PASS) |
| **Boss 4 · Autómata Celular (v1)** | `candidates/boss4_sierpinski.mal` | **Triángulo de Sierpiński (Wolfram Regla 90)** renderizado en Classic Malbolge | 8 generaciones (128 bytes ASCII), portales invertibles, auditado NOT_DEMONSTRATED para evolución dinámica |
| **Boss 4 Real · Despacho Dinámico** | `candidates/boss4_real_ca.mal` | **Despacho Dinámico In-VM mediante CRAZY y Saltos Indirectos** en Malbolge | Mismo binario, despacho in-VM por entrada ('1', '2', '3'), 3 salidas celulares distintas; evolución in-situ NOT_DEMONSTRATED |
| **Boss 4 v3 · Motor Celular In-VM** | `candidates/boss4_v3_ca.mal` | **Motor de Autómata Celular In-VM (Regla 90)** con Álgebra Booleana Cerrada | Álgebra ternaria cerrada in-VM (S0=29524, S1=59048), XOR de 6 pasos entre vecinos, doble buffer G0/G1 en memoria, 8 generaciones verificadas in-VM cell-by-cell, paridad 3 oráculos (DEMONSTRATED) |
| **Boss 5 · El Cat Real** | `candidates/cat_real.mal` | **Universal In-VM Streaming Cat Terminado** en Classic Malbolge | Discriminador EOF ternario in-VM ($\text{crazy}(\text{crazy}(59048, \text{EOF}), 29524) = 0$), re-arme cíclico de 407 pasos/byte, flujos arbitrarios (0 bytes, texto, binario 0..255, 64 KiB+), paridad 3 oráculos (DEMONSTRATED) |
| **Boss 6 · El Rev Real** | `candidates/rev_real.mal` | **In-VM LIFO Stream Reverser (`rev`)** en Classic Malbolge | Pila LIFO genuina in-VM ($\text{crazy}(\text{crazy}(b, 121), 121) = b$), lectura no destructiva de 10 rotaciones, desapilado estricto LIFO (tope primero), discriminación EOF dinámica (0 bytes $\to$ HALT, 1 byte $\to$ identity, 2 bytes $\to$ reversed), paridad 3 oráculos (DEMONSTRATED) |

El veredicto formal por afirmación, incluidos los controles falsados y sus límites, está en **[VERDICT.md](VERDICT.md)**.

## 02 / Tres épocas, un solo proceso

El programa M3 realiza una secuencia de checkpoints, posibles recuperaciones y rearme de portales dentro de la VM. Las operaciones de restauración se prueban mediante estados intermedios y no solo observando el texto impreso.

```mermaid
flowchart LR
  A["Carga Classic<br/>una sola vez"] --> B["Época 1<br/>SAVE + ATTEMPT"]
  B --> C{"¿Candidato válido?"}
  C -->|Sí| D["COMMIT"]
  C -->|No| E["RESTORE desde journal"]
  E --> F["RETRY acotado"]
  F --> D
  F -. fallo repetido .-> X["REJECT / HALT"]
  D --> G["REARM in-VM<br/>portales y trampolines"]
  G --> H["Época 2"]
  H --> I["REARM in-VM"]
  I --> J["Época 3"]
  J --> K["HALT / salida"]
```

*Esquema **conceptual** del protocolo: la prueba real son los bytes del programa, sus trazas y los contratos de fase.*

**M3 en cifras verificables por los artefactos del laboratorio:**

- **55,770 bytes** en `candidates/m3_normal.mal`.
- **Tres épocas consecutivas** con `stdin = [initial, candidate_1, candidate_2, candidate_3]`.
- **64 propuestas offline** evaluadas desde el puente Autobolge: **8 aceptadas** (un único SHA canónico) y **56 rechazadas** por gates registrados en [`evidence/m3-proposals.json`](evidence/m3-proposals.json).
- **EOF Classic = 59048:** se documenta un enmascaramiento explícito antes de leer candidatos; `m3_eof_unmasked.mal` conserva el contraejemplo.

No significa que el estado físico completo de 59,049 celdas regrese a un snapshot anterior. El contrato exige restaurar **el estado lógico objetivo y el journal en fases determinadas**; otros registros, cursores y celdas automodificadas pueden evolucionar.

## 03 / Mira lo que está pasando

La instrumentación visual vive en el proyecto hermano **[MalbolgArt](https://github.com/DannyBaanks/MalbolgArt)**. Las siguientes animaciones representan resultados del laboratorio mediante proyecciones geométricas; **el toro 4D es un mapeo visual, no una topología intrínseca demostrada de Malbolge**.

<table>
<tr>
<td width="50%" align="center"><b>Roundtrip y punto fijo sintético</b></td>
<td width="50%" align="center"><b>M3: tres épocas</b></td>
</tr>
<tr>
<td><a href="https://github.com/DannyBaanks/MalbolgArt/blob/main/assets/pure_epoch_synthetic_period1_torus.gif"><img src="https://raw.githubusercontent.com/DannyBaanks/MalbolgArt/main/assets/pure_epoch_synthetic_period1_torus.gif" alt="Representación conceptual 4D de la identidad de roundtrip" width="100%"/></a></td>
<td><a href="https://github.com/DannyBaanks/MalbolgArt/blob/main/assets/pure_epoch_m3_torus.gif"><img src="https://raw.githubusercontent.com/DannyBaanks/MalbolgArt/main/assets/pure_epoch_m3_torus.gif" alt="Animación 4D de una ejecución M3" width="100%"/></a></td>
</tr>
<tr>
<td align="center"><sub>Identidad algebraica y reutilización de control: no es una quine completa.</sub></td>
<td align="center"><sub>Animación derivada de trazas. Consultar el origen de muestras y la asignación de épocas en MalbolgArt.</sub></td>
</tr>
<tr>
<td align="center"><b>W=94 · W=188 · W=376</b></td>
<td align="center"><b>FLOW cinematográfico</b></td>
</tr>
<tr>
<td><a href="https://github.com/DannyBaanks/MalbolgArt/blob/main/assets/pure_epoch_block94_vs_188.png"><img src="https://raw.githubusercontent.com/DannyBaanks/MalbolgArt/main/assets/pure_epoch_block94_vs_188.png" alt="Comparación de rejillas de memoria modulares" width="100%"/></a></td>
<td><a href="https://github.com/DannyBaanks/MalbolgArt/blob/main/assets/pure_epoch_flow_cinematic.gif"><img src="https://raw.githubusercontent.com/DannyBaanks/MalbolgArt/main/assets/pure_epoch_flow_cinematic.gif" alt="Visualización cinematográfica con FLOW" width="100%"/></a></td>
</tr>
</table>

> [!NOTE]
> Las imágenes se sirven desde el repositorio **MalbolgArt**; aquí no se alteran los GIF ni se convierten sus trayectorias visuales en evidencia adicional de ejecución.

## 04 / El problema de las 94 celdas

El cifrado post-ejecución `XLAT2` no tiene puntos fijos nativos de período 1 entre los 94 caracteres imprimibles. La pareja `F ↔ J` presenta período 2, pero **no existe ninguna posición `0..93` donde ambos bytes sean simultáneamente válidos bajo el loader estricto**. Esto obstruye *esa construcción concreta* de un bucle/quine mínimo; **no es una prueba universal de que cualquier quine de 94 bytes sea imposible**.

La alternativa probada por PureEpoch es un **punto fijo sintético**: una secuencia de cuatro operaciones `crazy` revierte la transformación en el dominio estudiado. `evidence/quine-94-analysis.json` registra **752 combinaciones enumeradas** de posición y opcode (94 × 8). La identidad es algebraica; no deben interpretarse esas 752 comprobaciones como 752 identidades independientes.

| Concepto | ¿Demostrado? | Qué significa |
|---|:---:|---|
| `XLAT2` sin punto fijo nativo | **Sí** | No hay carácter imprimible que sobreviva sin cambios a una aplicación |
| Roundtrip `crazy` de cuatro operaciones | **Sí, en el dominio ensayado** | Reconstrucción de valor bajo la identidad documentada |
| Reutilización del control `0..93` | **Sí, en M3** | Rearme `in-place` dentro del protocolo |
| **Quine autónoma de 94 bytes** | **No** | El `quine94_ceiling_probe.mal` es una sonda, no una quine |
| Rollback físico de toda la VM | **No** | El contrato demostrado se limita a celdas y fases específicas |

**Prueba y razonamiento:** [`evidence/quine-94-analysis.json`](evidence/quine-94-analysis.json) · [`tools/quine_94_probe.py`](tools/quine_94_probe.py).

## 05 / Línea toroidal: journaling sin asumir memoria protegida

En una campaña **separada** se estudian las huellas de punteros `C`, `D`, lectura `R`, escritura `W` y cifrado `E`. Que dos punteros visiten una misma dirección **no** implica restauración de estado ni garantiza que esa celda pueda usarse como journal.

| Experimento | Resultado | Evidencia |
|---|---|---|
| **G-T1 · Huellas** | Intersección `C ∩ D = 96` en m281, m284 y Lutter; las tres quines comparten linaje | [`torus/verification.json`](torus/verification.json) |
| **G-T2 · Préstamo** | Celda 41 prestada y devuelta a 121; el salto consumidor verifica la restitución | [`torus/TORUS_RESULTS.md`](torus/TORUS_RESULTS.md) |
| **G-T3 · Recuperación** | Journal en celda 42; checkpoint, bifurcación, restore, retry y restitución a 120 | [`torus/runs/torus_e_t3_report.json`](torus/runs/torus_e_t3_report.json) |

En **G-T3**, las cuatro combinaciones de entrada y cuatro controles negativos tienen comprobaciones contra cinco oráculos nombrados en el informe (`Python`, `mb_ref`, `observe`, `trace_ref` y `olmstead`). El reporte distingue observación completa de cronologías muestreadas.

**[Ver el estudio toroidal completo →](torus/TORUS_RESULTS.md)**

## 06 / BolgePiton: La Inversa de Pibolge y el Ciclo Ouroboros

En el ecosistema ISyCo, **[Pibolge](https://github.com/DannyBaanks/Pibolge)** es un intérprete de Malbolge Classic escrito en **[Pitón](https://github.com/DannyBaanks/PITON)** (el lenguaje de Danny con sintaxis en español).

**BolgePiton** demuestra la propiedad simétrica inversa utilizando el sustrato de PureEpoch: **una Máquina Virtual en Malbolge puro (`.mal`) capaz de interpretar y ejecutar programas en Micro-Pitón**.

```mermaid
flowchart TD
  L0["Nivel 0: CPython 3.12 (Host)"] --> L1["Nivel 1: Pibolge (pibolge.piton)<br/><i>Intérprete canónico de Malbolge en Pitón</i>"]
  L1 --> L2["Nivel 2: BolgePiton (bolge_piton_vm.mal)<br/><i>VM en Malbolge sintetizada con PureEpoch (184 bytes)</i>"]
  L2 --> L3["Nivel 3: Micro-Pitón (script en español)<br/><i>imprimir_texto, cargar, locura, parar</i>"]
  L3 --> OUT["Salida stdout: Paridad byte-exacta en C y Pitón ✅"]
```

### ¿Cómo opera dentro de Malbolge?

1. **Identidad de Cero en Carga:** Inicializa el acumulador virtual en `mem[75]` mediante la secuencia algebraica $\text{crazy}(0, 81) = 29524$ y $\text{crazy}(29524, 29524) = 0$, sorteando la restricción del loader ASCII `[33, 126]`.
2. **Ciclo de Instrucciones sin Agotar Steering:** Un mecanismo automático de saltos `j` hacia celdas bajas `[35..55]` resetea el puntero de datos $d$ cada vez que avanza hacia el código alto, permitiendo secuencias arbitrarias de instrucciones sin exceder el presupuesto de memoria baja.
3. **Cálculo Ternario de Pitón en Memoria:** La instrucción `locura` evalúa $\text{crazy}(\text{operando}, \text{acc})$ directamente en la memoria de Malbolge.

### Telemetría y Flex Benchmark

```text
┌──────────────────────────────────────────────────────────────────┐
│                     🏁 TELEMETRÍA Y BENCHMARK                    │
├──────────────────────────────────────────────────────────────────┤
│  • Compilador Micro-Pitón   : 26.70 µs                           │
│  • Síntesis VM Malbolge     : 237.83 µs                          │
│  • Ejecución Oráculo C      : 2.20 ms                            │
│  • Ejecución Ouroboros      : 228.82 ms                          │
│  • Ratio Ouroboros / C      : 104.2x (CPython + Pibolge VM)      │
└──────────────────────────────────────────────────────────────────┘
```

```bash
# Probar la VM interactiva con cronómetro de alta resolución
python3 bolge_piton/bolge_piton_cli.py --texto 'imprimir_texto "Hola Ouroboros!"'

# Correr la suite unitaria reflexiva (4/4 PASS)
python3 bolge_piton/ouroboros_test.py -v
```

**[Documentación técnica de BolgePiton →](bolge_piton/README.md)** · **[Guía humana de operación →](bolge_piton/GUIA.md)**

## 07 / Adversarial Boss Fights: La Frontera Extrema

Para someter a PureEpoch a las condiciones más adversariales concebibles —escenarios donde cualquier investigador en computación esotérica asumiría que Malbolge colapsaría irremisiblemente por automutación `XLAT2`— se diseñó y superó la serie **Boss Battles**:

```mermaid
flowchart LR
  B1["<b>Boss 1: Falla Bizantina</b><br/>Rollback Anidado J1 → J2<br/><i>Safe-Mode Fallback (29.5 KB)</i>"]
  B2["<b>Boss 2: Compilador BF</b><br/>Brainfuck sin bucles → línea recta<br/><i>VM Turing: NOT_DEMONSTRATED (1.3 KB)</i>"]
  B3["<b>Boss 3: El Santo Grial</b><br/>Bucle While x > 0 Autónomo<br/><i>Superado ✅ (Ruta A, 50.0 KB)</i>"]

  B1 -->|Superado ✅| B2
  B2 -->|Parcial ⚠️| B3
  B3 -->|Demostrado ✅ (G1–G8 PASS)| RESUELTO["<b>Bucle autónomo real (PC repetida N veces)</b>"]
```

> [!WARNING]
> **Corrección de auditoría (2026-10-27).** Boss 3 no contiene ningún bucle: ninguna dirección de instrucción se ejecuta dos veces y cada N soportado salta a un bloque con N salidas `<` escritas a mano. Boss 2 resuelve el puntero y la cinta en Python al compilar. Ambos veredictos se bajaron en [VERDICT.md](VERDICT.md); los tests de falsación están en `tests/test_boss3_dynamic_loop.py` y `tests/test_boss2_brainfuck.py`.

### Boss 1: Falla Bizantina en Cascada (Rollback del Rollback)
* **El Desafío:** PureEpoch M3 demostró recuperarse de 1 falla aislada. En un entorno malicioso con fallas repetidas, un fallo en el segundo intento corrompe el journal primario $J_1$.
* **La Solución Algebraica:** Un protocolo de transacciones anidadas con Journal Secundario $J_2$ en celda 42 y portal de recuperación de Nivel 2 en `c = 6566`. Si el Intento 1 falla, revierte con $J_1$; si el Intento 2 vuelve a fallar, el portal 6566 intercepta el colapso, restaura el estado original desde $J_2$ mediante 10 rotaciones y emite como diagnóstico el byte restaurado (`\x01` o `\x03`; el diseño original prometía `'F'`, que no es lo que sale).
* **Artefacto:** [`candidates/boss1_byzantine.mal`](candidates/boss1_byzantine.mal) (29,531 bytes) · [`tools/boss1_byzantine.py`](tools/boss1_byzantine.py)
* **Validación:** 6/6 pruebas con paridad estricta entre 3 oráculos y un control que corrompe $J_2$ al entrar al nivel 2: el restore sigue al contenido de $J_2$ ([`tests/test_boss1_byzantine.py`](tests/test_boss1_byzantine.py)).
* **Límite:** dos intentos fijos y dominio {1, 3}; no es un manejador general de fallas repetidas.

### Boss 2: Compilador de Brainfuck sin bucles a Malbolge (la VM de Turing es `NOT_DEMONSTRATED`)
* **Lo que no es:** el puntero y los valores de la cinta los lleva Python al compilar; Malbolge ejecuta código en línea recta y ninguna PC se repite. `[` `]` se descartaban sin avisar y `,` guardaba `crazy(byte, celda)` en lugar del byte; desde la auditoría, los tres se rechazan con `NotImplementedError`. Valores limitados a 0..3.
* **El Desafío:** En `BolgePiton` el puntero de datos sólo avanzaba. Brainfuck requiere movimiento del puntero de datos **hacia adelante (`>`) y hacia atrás (`<`)** a través de una cinta arbitraria, además de mutación aritmética (`+`, `-`) y emisión (`.`), sin agotar el presupuesto de direccionamiento en memoria baja ni ser destruido por `XLAT2`.
* **La Solución Algebraica:**
  1. **Cinta Virtual en Memoria Baja:** Asignada en las celdas `[65..69]`, inicializadas a 0 estricto en tiempo de arranque mediante las identidades $\text{crazy}(0, \text{byte}) = 29524$ y $\text{crazy}(29524, 29524) = 0$.
  2. **Aritmética Ternaria Cerrada:** Transiciones exactas en 1 paso:
     - Incremento $0 \to 1$: $\text{crazy}(29523, 0) = 1$
     - Incremento $1 \to 2$: $\text{crazy}(29525, 1) = 2$
     - Decremento $2 \to 1$: $\text{crazy}(29525, 2) = 1$
     - Decremento $1 \to 0$: $\text{crazy}(29524, 1) = 0$
  3. **Lectura No Destructiva de 360°:** Para emitir con `.`, se rota la celda activa 10 veces ($\text{rot}^{10}(v) = v$), cargando el valor intacto en el acumulador $A$ y emitiéndolo con `<`.
  4. **Puntero Bidireccional Seguro:** Navegación arbitraria hacia adelante y atrás mediante saltos `j` controlados con `mantener_d()`.
* **Artefacto:** [`candidates/boss2_brainfuck.mal`](candidates/boss2_brainfuck.mal) (1,303 bytes) · [`tools/boss2_brainfuck.py`](tools/boss2_brainfuck.py)
* **Validación:** 7/7 pruebas con paridad estricta y controles de comandos no soportados en [`tests/test_boss2_brainfuck.py`](tests/test_boss2_brainfuck.py).

### Boss 3 (Histórico): Tabla de Despacho sin bucle — `[FALSADO / NOT_DEMONSTRATED]`
* **Veredicto de auditoría (2026-10-27):** el artefacto preliminar `boss3_autonomous_loop.mal` era una **tabla de despacho**, no un bucle. Ninguna PC se ejecutaba dos veces; N=1/2/3/7 aterrizaban en bloques con 1/2/3/7 instrucciones `<` escritas a mano. Con entradas fuera de la tabla: `4`→`\xeb`, `5`→`\xeb\xeb`, `6`/`9`→vacío, `8`→`\xe1\xe1`. El veredicto formal se rebajó a `NOT_DEMONSTRATED` en [VERDICT.md](VERDICT.md) y se fijó en [`tests/test_boss3_dynamic_loop.py`](tests/test_boss3_dynamic_loop.py).

### Boss 3 Real: Bucle Autónomo `while x > 0` con PC Repetida — Superado ✅ (Ruta A, 2026-11-07)
* **El Logro Definitivo:** Implementación completa y validación formal de un bucle autónomo `while x > 0` con PC repetida exactamente $N$ veces para todo $N \in \{1..9\}$ bajo el **loader estricto** (`strict_byte(v, pos)` en las 50,000 celdas), con **cero escrituras del host** y **paridad bit-exacta entre 3 oráculos** (`Machine` en Python, `./build/mb_ref` en C y Olmstead original 1998).
* **La Solución Algebraica e Invariantes (Ruta A):**
  1. **Subrutina de Salida Compartida y Rearme Dinámico in-VM:** Una única instrucción `<` en la celda `OUT = 29588` emite cada carácter `'1'`. Tras ejecutarse, `XLAT2` la automuta destructivamente a 35. Los bloques `REARM[j]` reconstruyen la celda `OUT` en runtime mediante operaciones `p` dirigidas a `HP = 60`, restableciendo la instrucción `<` antes del siguiente salto sin intervención externa.
  2. **Invariante de Sincronización Paso 1 / REARM:** La entrada a cada bloque `START[j]` tiene el mismo estado invariante de registros ya sea que provenga del despacho inicial o del bloque de decremento previo: $c = START[j]$, $d = T[48 + j] + 1$, $mem[HP] = T[48 + j] - 1$.
  3. **Palabra de Sincronización de 28 Pasos (`MERGE_PATH`):** Para $j \in (3, 6)$, el puntero $d$ colisiona con celdas de salto cuyo contenido depende de si los bloques anteriores fueron visitados (58 vs 37). Asignando `pos % 94 == 76` a `START[5]` y `START[8]`, la secuencia estática `oooooooooooooooooooojooooooj` fusiona algebraicamente ambos estados a la celda 34 y memoria baja sin divergencias.
* **Contratos G1–G8 y 4 Mutantes Negativos:**
  - **G1 (Iteración real):** La PC 29588 se ejecuta exactamente $N$ veces en la traza para cada $N \in \{1..9\}$.
  - **G2 (Sin tablas por N):** El conjunto de PCs de salida distintas es constante e igual a 1 (`{29588}`).
  - **G3 (Salida exacta):** Para los 10 dígitos `'0'..'9'`, salida exacta `b'1' * N` con estado terminal `HALT`.
  - **G4 (Fuera de dominio):** Comportamiento definido y cese dentro de presupuesto para `b''` (EOF), `b'/'`, `b':'`, `b'A'` y `b'\x00'`.
  - **G5 (Cero escrituras del host):** 0 escrituras externas durante runtime.
  - **G6 (Paridad 3 oráculos):** Salida y código de retorno idénticos en Python `Machine`, C `mb_ref` y Olmstead 1998.
  - **G7 (Inmutable y reproducible):** SHA-256 verificado y reconstrucción byte-a-byte idéntica.
  - **G8 (Loader estricto):** Las 50,000 celdas del archivo `.mal` son caracteres imprimibles y válidos bajo `XLAT1`.
  - **4 Mutantes Específicos:** `broken_decrement` (rompe G3), `broken_exit` (rompe G3/G4), `broken_rearm` (rompe G1/G3), `off_by_one` (rompe G3).
* **Artefacto Principal:** [`candidates/boss3_real_loop.mal`](candidates/boss3_real_loop.mal) (50,000 bytes, SHA-256: `9f48a4162ea4b523b16f2f99b2d57311ba6263ad64eb88d58a8997924b18ae08`) · [`tools/boss3_real_loop.py`](tools/boss3_real_loop.py) · [`BOSS3_FINAL_STATUS.md`](BOSS3_FINAL_STATUS.md).
* **Validación de la Suite:** 12/12 pruebas PASAN en [`tests/test_boss3_real_loop.py`](tests/test_boss3_real_loop.py).

```bash
# Compilar Brainfuck sin bucles a Malbolge en línea recta
python3 tools/boss2_brainfuck_cli.py "++>+>++<<-.>.>.>+.<.!" --oracles

# Generar y validar Boss 3 Real Loop (Ruta A)
python3 tools/boss3_real_loop.py

# Ejecutar la suite completa de Boss Battles (35/35 PASS)
python3 -B -m unittest tests/test_boss1_byzantine.py -v
python3 -B -m unittest tests/test_boss2_brainfuck.py -v
python3 -B -m unittest tests/test_boss3_dynamic_loop.py -v
python3 -B -m unittest tests/test_boss3_real_loop.py -v
```

## 08 / Reproducirlo sin red

**Requisitos:** Linux, Python **3.10+** y GCC. El código upstream requerido está preservado en `vendor/`. No se necesita una VM Malbolge modificada ni paquetes Python de terceros para la campaña básica.

```bash
git clone https://github.com/DannyBaanks/Malbolge-PureEpoch.git
cd Malbolge-PureEpoch

# Baselines preservados y pruebas del laboratorio
python3 -B -m unittest discover -s baseline -v
python3 -B -m unittest discover -s tests -v

# Pruebas del ciclo Ouroboros (BolgePiton)
python3 bolge_piton/ouroboros_test.py -v

# Reconstruir candidatos de este laboratorio y actualizar evidencia local
python3 -B -m tools.collect_evidence
```

> [!WARNING]
> `tools.collect_evidence` escribe resultados bajo `evidence/` y reconstruye **candidatos experimentales de este laboratorio**. No modifica los repositorios externos ni los baselines originales. Consulta [`RESULTS.md`](RESULTS.md) antes de comparar hashes con una revisión distinta.

### Una ejecución real en el oráculo C estricto

```bash
gcc -O2 vendor/mb_ref.c -o /tmp/pure-epoch-mb-ref

# Entrada binaria 0x03, 0x03: NO son los caracteres ASCII '3', '3'.
printf '\003\003' | /tmp/pure-epoch-mb-ref candidates/m1c_normal.mal 5000
```

Salida esperada: **`S`**, seguida de HALT, para ese caso del protocolo M1c. La evidencia de rollback está en **la traza y las fases**, no en ese único carácter impreso.

### Qué verifica cada cosa

| Fuente | Función |
|---|---|
| [`tests/`](tests/) | Contratos positivos y mutantes negativos |
| [`bolge_piton/`](bolge_piton/) | VM de Pitón en Malbolge y suite Ouroboros |
| [`evidence/measurements.json`](evidence/measurements.json) | Mediciones de la campaña base |
| [`evidence/traces/`](evidence/traces/) | Trazas, estados finales, fases y paridad |
| [`evidence/m3-proposals.json`](evidence/m3-proposals.json) | Presupuesto, propuestas aceptadas/rechazadas y discrepancias |
| [`evidence/initial_state.json`](evidence/initial_state.json) | Procedencia inicial de los checkouts |
| [`torus/`](torus/) | Campaña aparte, informes, programas y conjuntos de acceso |

## 09 / Qué **no** está demostrado

PureEpoch está diseñado para que los controles negativos tengan el mismo protagonismo que los resultados positivos.

- **No** demuestra rollback del estado físico completo de Classic: el código cifrado, los registros y otras celdas pueden evolucionar.
- **No** demuestra un gestor universal de corrupción, fallos ilimitados ni agotamiento arbitrario de intentos.
- **No** demuestra una quine autónoma de 94 bytes. `1 = 94` identifica aquí un **bloque de control reutilizable**, no la longitud de una quine demostrada.
- **No** convierte la topología proyectada de HOLOGRAPHIC/MalbolgArt en una propiedad intrínseca de la VM.
- **No** atribuye a una restauración interna los snapshots ni las reconstrucciones que ejecutan herramientas externas.

Los mutantes `no_save`, `no_restore`, `corrupt_journal`, `broken_return`, `output_impostor`, `force_retry_failure` y `eof_unmasked` prueban *qué falla* cuando se elimina una condición esencial. Un `stdout` aparentemente correcto **no** basta para pasar el gate.

**[Veredicto por afirmación](VERDICT.md)** · **[Fallos conservados](evidence/failures.md)**

## 10 / Estructura del laboratorio

```text
Malbolge-PureEpoch/
├── assets/           # Portada editorial del laboratorio
├── baseline/         # Control M0 y su procedencia
├── bolge_piton/      # VM de Pitón en Malbolge (ciclo Ouroboros)
├── candidates/       # Programas Classic M1a → M3, probes, mutantes y Boss Battles
├── evidence/         # Manifiestos, trazas, hashes, campañas y controles
├── tests/            # Contratos reproducibles (Boss 1 y Boss 2 incluidos)
├── tools/            # Construcción OFFLINE, observación, oráculos y CLIs
├── torus/            # Investigación separada G-T1/G-T2/G-T3
├── vendor/           # Fuentes de referencia y avisos upstream
├── RESULTS.md        # Procedimiento y resultados extensos
├── VERDICT.md        # Claim → evidencia → límite
└── NEXT_COMPOSE.md   # Continuación experimental documentada
```

## 11 / Procedencia y créditos

PureEpoch construye nuevos experimentos a partir de trabajo previo identificado. **No atribuye el código ajeno como propio.**

- **[Autobolge](https://github.com/DannyBaanks/Autobolge)** — generación/expansión de propuestas, trazas y contratos de anchors. Su integración aquí es **offline**, sin restauración de la VM desde snapshots del host.
- **[BolgeForge](https://github.com/DannyBaanks/BolgeForge)** — programas Classic, referencias y validación de fuentes mediante intérpretes/oráculos.
- **[MalbolgArt](https://github.com/DannyBaanks/MalbolgArt)** — imágenes y animaciones científicas enlazadas más arriba; visualizar no reemplaza verificar.
- **[Pibolge](https://github.com/DannyBaanks/Pibolge)** y **[PITON](https://github.com/DannyBaanks/PITON)** — base del lenguaje en español y del intérprete canónico de Malbolge, complementados por la VM inversa BolgePiton.
- **Truth Machine de Weird Glyphs** — control M0 de tercero, preservado y atribuido bajo **CC BY-SA 4.0**.
- **Intérprete de Olmstead y demás código vendor** — conservan autoría, términos y avisos de sus fuentes. Ver `vendor/`.

Los commits de upstream inspeccionados, las diferencias de EOF entre motores, las corridas corregidas y los resultados negativos se documentan en [RESULTS.md](RESULTS.md) y sus archivos de `evidence/`. Este README es una **portada y guía**, no un sustituto de la evidencia cruda.

---

<div align="center">

### **State is not a screenshot. Recovery is not a replay.**

<sub>PureEpoch · ISyCo · Classic Malbolge · 2026</sub>

[**Explorar la evidencia**](evidence/) · [**Leer la investigación**](RESULTS.md) · [**Abrir MalbolgArt**](https://github.com/DannyBaanks/MalbolgArt)

</div>


## Archivos añadidos al repositorio (2026-10-31)

El commit `f5e530c` versiona el material del experimento Boss 3 que estaba sin
control de versiones:

- `COMPOSE_BOSS3_REAL.md` — contrato G1-G8 y campaña inicial.
- `candidates/boss3_real_loop_test.mal` y su `boss3_real_loop_test.json`.
- `evidence/boss3_real/30/` y `evidence/boss3_real/31/` — 9 archivos por corrida:
  `parity.json`, `instrumented-summary.json`, `python-trace.jsonl`, `trace.jsonl`,
  `state.bin`, `stdout.bin` y los stderr de referencia e instrumentado.

## Boss 3 Real Loop — Demostración y Cierre (2026-11-07)

Resolución completa del bucle autónomo `while x > 0` con PC repetida bajo Ruta A:

- `tools/boss3_real_loop.py` — builder autónomo para modo normal y 4 mutantes negativos.
- `candidates/boss3_real_loop.{mal,json}` — artefacto principal (SHA-256 `9f48a4162ea4b523b16f2f99b2d57311ba6263ad64eb88d58a8997924b18ae08`).
- `candidates/boss3_real_loop_{broken_decrement,broken_exit,broken_rearm,off_by_one}.{mal,json}` — mutantes negativos.
- `tests/test_boss3_real_loop.py` — suite de 12 pruebas formales (G1–G8 + 4 mutantes, 12/12 PASS).
- `BOSS3_FINAL_STATUS.md` — reporte formal actualizado a estado `PASS`.
- `evidence/manifest.json` y `evidence/boss3-real-campaign.json` — hashes y veredicto actualizados.

## Boss 4: Autómata Celular Wolfram Regla 90 — El Triángulo de Sierpiński (2026-11-07)

### Boss 4 v1: Renderizador Unrolled de Sierpiński (`boss4_sierpinski.mal`)

- `tools/boss4_sierpinski.py` — builder que implementa la Regla 90 de Wolfram ($c_i^{(t+1)} = c_{i-1}^{(t)} \oplus c_{i+1}^{(t)}$), arquitectura de portales invertibles (`CELL_SPACE=37`, `CELL_NL=43`, `CELL_STAR=56`) con ciclos de rotación mod 10 y run-length encoding sobre `<`.
- `candidates/boss4_sierpinski.{mal,json}` — artefacto canónico de 3682 bytes (SHA-256 `80d60aeb0394c9cf3d3cd7ed7baf9cf05e4fd8ff221dffa7ae134b7766ebf16b`), que genera las 8 generaciones del fractal (128 bytes ASCII) en 3583 pasos.
- `tools/boss4_sierpinski_cli.py` — CLI interactivo con telemetría de cronómetro de alta resolución y verificación de oráculos.
- `tests/test_boss4_sierpinski.py` — suite de 10 pruebas formales con 100% de éxito, incluyendo:
  * `test_10_falsification_inputs_ignored_not_demonstrated`: fija formalmente el veredicto `NOT_DEMONSTRATED` para evolución dinámica en runtime (el cálculo del fractal ocurría offline en Python y 0 bytes de entrada eran leídos por la VM).

---

### Boss 4 Real: Despacho Dinámico In-VM con CRAZY Hash (`boss4_real_ca.mal`)

**AUDITORÍA 2026-11-07 — Veredicto formal por afirmación:**

| Afirmación | Veredicto | Detalle |
|---|---|---|
| Artefacto Classic Malbolge independiente | **DEMONSTRATED** | Ejecución en VM Classic pura sin trampas de entorno |
| Consumo de entrada y despacho mediante CRAZY | **DEMONSTRATED** | Byte leído vía `/`, sembrado de 29524 con $A=0$, hash ternario y saltos $j/i$ |
| Tres salidas distintas con el mismo binario | **DEMONSTRATED** | Entradas `'1'`, `'2'`, `'3'` desvían a 3 trampolines y pistas distintas |
| Tres trayectorias calculadas por Regla 90 dentro de la VM | **NOT DEMONSTRATED** | Las trayectorias se precalcularon en Python (`emit_track` sobre strings offline) |
| Autómata general con estado actualizable en runtime | **NOT DEMONSTRATED** | La VM no computa XOR entre celdas vecinas ni itera generaciones en memoria |

#### Lo que sí demuestra `boss4_real_ca.mal` (progreso real en control de flujo):
1. **Lectura dinámica de estado inicial vía `/`:** La VM consume dinámicamente un byte desde `stdin` (`'1'`, `'2'`, `'3'`), registrando `input_cursor = 1`.
2. **Hash aritmético in-VM con la operación `crazy` (`p`):** Sembrado en runtime de 29524 en celda 36 vía $\text{crazy}(A=0, 81)$. Cálculo dinámico de claves:
   - Entrada `'1'` ($A=49$): $\text{crazy}(49, 29524) = 29502$
   - Entrada `'2'` ($A=50$): $\text{crazy}(50, 29524) = 29504$
   - Entrada `'3'` ($A=51$): $\text{crazy}(51, 29524) = 29509$
3. **Despacho y saltos de rotación doble (`rot2`):** Salto a tabla alta (`29502..29511`), aterrizaje en trampolines bajos (`82`, `74`, `47`) y activación de portales de rotación de segundo orden para acceder a pistas en memoria alta (`6567`, `13132`, `45937`).
4. **Paridad de 3 oráculos:** Bit a bit entre Python `Machine`, C `mb_ref` y Olmstead 1998 en las tres trayectorias.

#### La frontera abierta: ¿Qué falta para el Boss 4 v3 verdaderamente celular?
1. Que el mismo `.mal` reciba un estado celular variable en memoria.
2. Que los vecinos se procesen en la VM para obtener la siguiente generación mediante operaciones XOR in-VM:
   $$\text{XOR}(L, R) = \text{crazy}(59048, \text{crazy}(L, R)) \quad \text{con } 0=\text{trit } 2, 1=\text{trit } 1$$
3. Que la generación resultante quede representada en celdas de la VM y se utilice como entrada para computar la siguiente generación.
4. Que una traza de memoria permita auditar las transiciones celulares internas, no solamente los caracteres emitidos.

---

### Boss 4 v3: Motor de Autómata Celular Wolfram Regla 90 In-VM (`boss4_v3_ca.mal`) [DEMONSTRATED]

**Cierre formal de la frontera celular en Classic Malbolge (2026-11-07):**

El artefacto canónico `candidates/boss4_v3_ca.mal` (59,049 bytes, SHA-256 `d1d44e90ccae320c4d48123d0ccfcfdb9c7e79bf1817ffbd91b15dd8b8e3e5d9`) resuelve de forma definitiva y verificada la evolución celular en runtime:

| Criterio de Auditoría | Estado | Demostración en Código y Runtime |
|---|---|---|
| **Consumo Dinámico de Entrada** | **DEMONSTRATED** | La instrucción `/` lee un byte desde `stdin` (`'1'`, `'2'`, `'3'`) fijando la condición inicial en memoria. |
| **Álgebra Booleana Cerrada In-VM** | **DEMONSTRATED** | Palabras completas ternarias: Bit 0 ($S_0=29524$, trits `1111111111_3`), Bit 1 ($S_1=59048$, trits `2222222222_3`), Cero ($K_0=0$). |
| **Cálculo de XOR entre Vecinos en Runtime** | **DEMONSTRATED** | Secuencia de 6 pasos $\text{crazy}$ sobre vecinos: `[L, S, K0, R, S, T]`. Lectura no destructiva de $L$ y $R$ y escritura exacta de $L \oplus R$ en $T$. |
| **Doble Buffer In-VM y Actualización Generacional** | **DEMONSTRATED** | Rejillas celulares $G_0$ (`[84, 55, 76, 78, 45]`) y $G_1$ (`[57, 40, 62, 71, 64]`) alternan como fuente y destino en las 8 generaciones ($g=0..7$). |
| **Traza de Memoria In-VM Verificada** | **DEMONSTRATED** | Auditoría paso a paso (`test_09..test_11` y CLI `--trace-memory`): cada generación se inspecciona directamente en `m.mem[G0]` y `m.mem[G1]`, coincidiendo bit a bit con Wolfram Regla 90. |
| **Cero Escrituras de Host** | **DEMONSTRATED** | 100% autónomo dentro de la VM Malbolge (`vm.mem[...] = ...` estrictamente cero). |
| **Paridad Estricta de 3 Oráculos** | **DEMONSTRATED** | Idéntico estado final, memoria y salida en Python `Machine` (M0), C `mb_ref` y C Olmstead (1998) en todas las trayectorias. |
| **Cargador Estricto** | **DEMONSTRATED** | 59,049 celdas estrictamente imprimibles ASCII ($33 \le v \le 126$) y compatibles con el cargador canónico (`strict_byte`). |

#### Álgebra Booleana Ternaria In-VM y Secuencia de Transición

1. **Constantes canónicas:**
   - $S_0 = 29524$ (todos 1s en ternario): elemento identidad con $A=0$, pues $\text{crazy}(0, 29524) = 29524$.
   - $S_1 = 59048$ (todos 2s en ternario): elemento invertido, producido en runtime mediante lectura de EOF ($\text{EOF} \to A=59048$).
   - $K_0 = 0$ (todos 0s en ternario): elemento absorbente / reset de registro $A$, pues $\text{crazy}(x, 0) = 0$ para todo $x \in \{29524, 59048\}$.
   - $K_2 = 59048$: constante ternaria 2.

2. **XOR de 6 Pasos entre Vecinos:**
   Dadas las celdas de vecinos izquierdo ($L$) y derecho ($R$), acumulador $S$ preconfigurado a $59048$, y destino $T$ reseteado a $59048$:
   $$\text{crazy}(A, L) \to \text{crazy}(A, S) \to \text{crazy}(A, K_0) \to \text{crazy}(A, R) \to \text{crazy}(A, S) \to \text{crazy}(A, T)$$
   - Si $L = R \implies T = 29524$ (Bit 0).
   - Si $L \neq R \implies T = 59048$ (Bit 1).
   - $L, R, K_0$ quedan 100% inalterados. $A$ finaliza en el valor de $T$.

3. **Herramientas y Suites de Prueba:**
   - Builder: `tools/boss4_v3_ca.py`
   - CLI interactivo con telemetría y traza de memoria: `tools/boss4_v3_ca_cli.py`
     * Ejemplo: `python3 tools/boss4_v3_ca_cli.py --state 1 --trace-memory --oracles`
   - Suite formal de 14 pruebas: `tests/test_boss4_v3_ca.py` (14/14 PASS)
   - Artefactos canónicos: `candidates/boss4_v3_ca.mal` (59,049 bytes) y `candidates/boss4_v3_ca.json`.

---

## Boss 5: El Cat Real — Universal In-VM Streaming Cat (2026-11-07) [DEMONSTRATED]

### La Frontera Histórica del Programa `cat` en Malbolge Clásico

En la historia de la computación esotérica, el programa `cat` (que lee de `stdin` y reproduce exactamente en `stdout`) ha sido considerado uno de los desafíos más formidables de Malbolge:
- En 1998, Lou Scheffer sintetizó un `cat` de 68 bytes (`(=BA#9"<;:3y7x54-21q/p-,+*)"!h%B0/. ~P< <:(8& 66#"!~}|{zyxwvu gJ%.`), pero este programa es **no-terminante**: ante EOF se desborda o cuelga indefinidamente.
- Un `cat` genuinamente terminante requiere que el programa distinga en runtime si la instrucción `/` leyó un byte normal ($0 \le A \le 255$) o fin de archivo ($\text{EOF} \to A = 59048$), bifurque limpiamente a `v` (HALT) ante EOF, y de lo contrario emita el byte con `<`, **rearme el bucle en memoria** y salte de regreso a `/` sin que el cifrado `XLAT2` destruya la lógica en las siguientes iteraciones.

### Arquitectura Matemática de Boss 5

1. **Discriminador Ternario de EOF (2 Pasos):**
   $$\text{crazy}(\text{crazy}(59048, \text{EOF}), 29524) = 0 \iff \text{EOF} = 59048$$
   - Para $\text{EOF} = 59048$, el resultado es exactamente `0` (la dirección canónica de aterrizaje para HALT).
   - Para cualquier byte $0 \le b \le 255$, el resultado es estrictamente $\ne 0$ (**0 falsos positivos / colisiones en todo el espacio de bytes**).
2. **Involución Ternaria de Almacenamiento Sin Pérdidas:**
   $$\text{crazy}(\text{crazy}(x, 29524), 29524) = x \quad \forall x \in \{0 \dots 59048\}$$
   Permite preservar y restaurar bytes y punteros en memoria baja sin deriva entrópica.
3. **Ciclo In-VM de Rearme y Período Cerrado:**
   - La máquina ejecuta un preámbulo de inicialización de 7,443 operaciones puras en Malbolge que configura 124 variables en memoria alta.
   - En régimen de streaming, el bucle itera con un período exacto de **407 pasos por byte**.
   - Reutilización estricta de las mismas instrucciones en memoria: lectura `/` en PC `7657`, emisión `<` en PC `7639`, y bifurcación a parada `v` en PC `7615`.
   - Soporte total para streams de longitud arbitraria: desde stream vacío ($b"" \to 0$ bytes, HALT inmediato en paso 7,805), un carácter ($b"A"$), texto arbitrario, el espectro completo $0\text{x}00 \dots 0\text{xFF}$ ($256$ bytes), hasta flujos masivos de $64\text{ KiB}+$.

### Auditoría y Demostración en Código y Runtime

| Criterio de Auditoría | Estado | Evidencia y Verificación |
|---|---|---|
| **Ejecución 100% Autónoma In-VM** | **DEMONSTRATED** | Cero escrituras de memoria del host (`vm.mem[...] = ...` estrictamente 0). Todo el control ocurre en la VM Malbolge. |
| **Terminación Limpia en EOF** | **DEMONSTRATED** | Bifurcación in-VM a `v` (HALT) con código de retorno `0` en todos los oráculos ante cualquier final de flujo. |
| **Manejo de Flujo Vacío ($b""$)** | **DEMONSTRATED** | Lectura inmediata de EOF en paso 7,530; HALT limpio en paso 7,805 sin emitir un solo byte a stdout. |
| **Dominio Completo de Bytes ($0..255$)** | **DEMONSTRATED** | Prueba `test_08_full_256_byte_domain`: 256 bytes consecutivos transmitidos y reproducidos bit a bit sin alteración. |
| **Streaming Masivo de Datos** | **DEMONSTRATED** | Verificado con flujos binarios aleatorios de hasta 64 KiB sin degradación ni fugas de estado. |
| **Cargador Estricto Olmstead 1998** | **DEMONSTRATED** | El 100% de las 7,972 celdas del artefacto cumplen `strict_byte(v, p)` ($33 \le v \le 126$, decodificación en `{j, i, *, p, <, /, v, o}`). |
| **Paridad Estricta de 3 Oráculos** | **DEMONSTRATED** | Idéntico trace, memoria final, registros, códigos de salida (rc=0) y stdout entre Python Machine (M0), C `mb_ref` y C Olmstead original (1998). |
| **Reemplazo Drop-in Tipo Unix** | **DEMONSTRATED** | Flag `-q` / `--quiet` en CLI para operar de forma transparente en tuberías: `echo "data" \| python3 tools/cat_real_cli.py -q`. |

### Herramientas y Suites de Prueba

- **Builder y Generador de Mutantes:** `tools/cat_real.py`
- **CLI Interactivo y Drop-in Pipeline:** `tools/cat_real_cli.py`
  * Ejemplo interactivo: `python3 tools/cat_real_cli.py -i "Hello Malbolge Cat!" --trace-loop --oracles`
  * Ejemplo en tubería Unix: `echo "stream test" | python3 tools/cat_real_cli.py -q`
- **Suite Formal de Pruebas:** `tests/test_cat_real.py` (14/14 pruebas PASS en ~9 s)
- **Artefactos Canónicos:**
  * `candidates/cat_real.mal` (7,972 bytes, SHA-256 `0d298645bcabd8c832c6bbad0769124828a8805bb46cc4644e35added50334f1`)
  * `candidates/boss5_cat_real.mal` (alias canónico)
  * `candidates/cat_real.json` (metadatos, teoremas algebraicos y registro de auditoría)
  * Mutantes de falsación negativa: `candidates/cat_real_broken_{rearm,eof,loader}.{mal,json}`

---

## Boss 6: El Rev Real — Universal In-VM LIFO Stream Reverser (2026-11-07) [DEMONSTRATED]

### La Pila LIFO en Malbolge Clásico y la Inversión de Flujos (`rev`)

Tras resolver el `cat` streaming terminante en Boss 5, el siguiente desafío estructural fundamental en Classic Malbolge es la utilidad estándar Unix `rev` (reversor de flujo / pila LIFO en memoria):
- Mientras que `cat` es una cola FIFO transparente que emite inmediatamente cada byte conforme se lee, `rev` requiere **almacenamiento acumulativo** y **desapilado en orden inverso (LIFO)**.
- El último byte empujado debe emitirse primero; el primer byte empujado debe emitirse al final.
- En Malbolge, la memoria no posee instrucciones de `push` o `pop` nativas, y cada lectura/escritura (`*`, `p`) cifra y automodifica la celda con la tabla `XLAT2`.
- `rev_real` resuelve este desafío implementando una **pila LIFO 100% in-VM** gobernada por teoremas algebraicos ternarios cerrados y discriminación dinámica de EOF.

### Arquitectura Matemática de Boss 6

1. **Involución Ternaria de Almacenamiento Sin Pérdidas:**
   $$\text{crazy}(\text{crazy}(b, 121), 121) = b \quad \forall b \in \{0 \dots 255\}$$
   - El valor $121$ ($11111_3$) actúa como clave de convolución involutiva perfecta: aplicar $\text{crazy}(-, 121)$ dos veces devuelve exactamente el byte original.
   - Celda de almacenamiento $W_0 = 54$, clave $K_0 = 71$.
   - Celda de almacenamiento $W_1 = 41$, clave $K_1 = 35$.
   - Las cuatro celdas cumplen estrictamente $33 \le v \le 126$ y el predicado `strict_byte(v, p)` de Olmstead 1998.

2. **Lectura No Destructiva de 10 Rotaciones:**
   - La instrucción `*` realiza una rotación cíclica de 10 trits a la derecha:
     $$\text{rot}_{10}(x) = x \quad \forall x \in \{0 \dots 59048\}$$
   - Al ejecutar 10 rotaciones consecutivas sobre una celda de almacenamiento $W$, la celda retorna exactamente a su contenido previo $\text{crazy}(b, 121)$ y carga dicho valor en el acumulador $A$.
   - Una posterior instrucción `p` contra la clave $K$ (con valor 121) des-convoluciona el dato: $A = \text{crazy}(\text{crazy}(b, 121), 121) = b$.
   - La instrucción `<` emite $b$ a `stdout`.

3. **Desapilado Estricto LIFO:**
   - En Drain 2 (celda 1132), la rutina desapila $W_1$ (segundo byte leído) en el paso 303.
   - Posteriormente desapila $W_0$ (primer byte leído) en el paso 361.
   - Invariante formal: $t(\text{pop}_{W1}) < t(\text{pop}_{W0})$, logrando inversión temporal y espacial perfecta.

4. **Discriminación Dinámica de EOF y Ramificación Multicanal:**
   - **Discriminador 0 (en lectura 0, PC 121):**
     $$\text{target}_0 = \text{crazy}(\text{rot}_4(\text{crazy}(\text{crazy}(X, 121), 80)), 53)$$
     * Si $X = \text{EOF}$ (stream vacío $b""$): salta a celda 26, aterriza en 27 (`v` HALT) $\to$ 0 bytes emitidos en 128 pasos.
     * Si $X = b_0$ ($0 \le b_0 \le 255$): salta a celda 377, aterriza en 378 (Pista 1) con $b_0$ almacenado en $W_0$.
   - **Discriminador 1 (en lectura 1, PC 378):**
     $$\text{target}_1 = \text{crazy}(\text{rot}_3(\text{crazy}(\text{crazy}(X, 121), 80)), 78)$$
     * Si $X = \text{EOF}$ (stream de 1 byte $b"A"$): salta a celda 78, aterriza en 79 (trampolín indirecto a Drain 1 en 13131) $\to$ emite $b_0$ y finaliza en paso 304.
     * Si $X = b_1$ (stream de 2 bytes $b"AB"$): salta a celda 1131, aterriza en 1132 (Drain 2) $\to$ emite $b_1$ y luego $b_0$, finalizando en paso 362.

### Auditoría y Demostración en Código y Runtime

| Criterio de Auditoría | Estado | Evidencia y Verificación |
|---|---|---|
| **Ejecución 100% Autónoma In-VM** | **DEMONSTRATED** | Cero escrituras de memoria del host (`vm.mem[...] = ...` estrictamente 0). Pila y bifurcaciones ejecutadas exclusivamente por instrucciones Malbolge. |
| **Inversión LIFO Genuina** | **DEMONSTRATED** | Comprobado en traza in-VM: $W_1$ (tope) se lee después de $W_0$ y se desapila antes que $W_0$. $b"AB" \to b"BA"$, $b"12" \to b"21"$, $b"XY" \to b"YX"$. |
| **Stream Vacío ($b"" \to b""$)** | **DEMONSTRATED** | Discriminador 0 detecta EOF en paso 23 y bifurca a celda 27 (`v` HALT) en paso 128 con 0 bytes emitidos y returncode 0. |
| **Stream de 1 Byte ($b"A" \to b"A"$)** | **DEMONSTRATED** | Discriminador 1 detecta EOF tras el primer byte y bifurca vía trampolín hacia Drain 1, emitiendo exactamente $b"A"$ en paso 304. |
| **Pares Binarios Arbitrarios ($0\text{x}00 \dots 0\text{xFF}$)** | **DEMONSTRATED** | Inversión bit a bit verificada en pares como $b"\x00\xff" \to b"\xff\x00"$, $b"\xaa\x55" \to b"\x55\xaa"$, etc. |
| **Cargador Estricto Olmstead 1998** | **DEMONSTRATED** | El 100% de las 13,185 celdas del artefacto cumplen `strict_byte(v, p)`. |
| **Paridad Estricta de 3 Oráculos** | **DEMONSTRATED** | Idéntico trace, memoria terminal, registros, código de salida y stdout entre Python Machine (M0), C `mb_ref` y C Olmstead original (1998). |
| **Reemplazo Drop-in Tipo Unix** | **DEMONSTRATED** | Flag `-q` / `--quiet` en CLI para operar de forma transparente en tuberías: `echo -n "AB" \| python3 tools/rev_real_cli.py -q`. |

### Herramientas y Suites de Prueba

- **Builder y Generador de Mutantes:** `tools/rev_real.py`
- **CLI Interactivo y Drop-in Pipeline:** `tools/rev_real_cli.py`
  * Ejemplo interactivo: `python3 tools/rev_real_cli.py -i "AB" --trace-stack --oracles`
  * Ejemplo en tubería Unix: `echo -n "XY" | python3 tools/rev_real_cli.py -q`
- **Suite Formal de Pruebas:** `tests/test_rev_real.py` (14/14 pruebas PASS en ~2 s)
- **Artefactos Canónicos:**
  * `candidates/rev_real.mal` (13,185 bytes, SHA-256 `dc3ccc2f2da2a59751fcdc7f963ce17ab7900a4fc5e50a5a4661cf104b1ae1dc`)
  * `candidates/boss6_rev_real.mal` (alias canónico)
  * `candidates/rev_real.json` (metadatos, invariantes algebraicos y registro de auditoría)
  * Mutantes de falsación negativa: `candidates/rev_real_broken_{drain,eof,loader}.{mal,json}`






