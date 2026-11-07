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
> **El programa se ejecuta en Malbolge, no en Python.** Python y C construyen, observan y verifican *fuera* de la ejecución. Los checkpoints, saltos, restores y reintentos que se reivindican como demostrados suceden dentro de una **única ejecución de la VM Classic**, sin restaurar snapshots desde el host.
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
