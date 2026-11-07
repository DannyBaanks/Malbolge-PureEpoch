# Auditoría del diagnóstico previo de Boss 3 (Nemotron)

**Fecha:** 2026-11-06
**Alcance:** verificar/refutar las afirmaciones del diagnóstico anterior (Nemotron)
sobre el bloqueo de Boss 3, contra el intérprete real (`baseline/epoch_probe.py`),
el loader estricto (`tools/observe.load`), los artefactos del repo y la suite de tests.
**Método:** cada afirmación se somete a un experimento ejecutable. Sin afirmaciones
por narrativa.

**Repositorio:** `/home/danny/Development/ISyCo Git/Malbolge-PureEpoch`
**HEAD:** `d09a42f` · **árbol de trabajo:** 13 archivos modificados + 28 untracked

---

## Veredicto global

`NOT_DEMONSTRATED` para Boss 3 (correcto), pero **el diagnóstico del bloqueo es
mayoritariamente FALSO**. De 11 afirmaciones auditadas, **7 son refutadas por
experimentos**, 2 quedan refutadas en su forma fuerte y 2 se confirman. La
interpretación previa se quedó corta en tres puntos que cambian la ruta de trabajo:

1. El "quantum jump de celdas 0–107 y 3312–3316 que aterriza en c=3315, d=121"
   **no existe en el artefacto**. El artefacto real tiene un quantum jump de una
   sola instrucción (celda 0 = `i`) que aterriza en pc=99, d=1. Las celdas
   3312–3316 existen pero **nunca se ejecutan** (son padding `o`).
2. `trip_to_trampoline` **no** exige `d > 29522`. La precondición real es la
   opuesta: `seek(54)` solo dirige el tablero 1..97, así que se usa desde
   memoria **baja** (d≈63, el patrón M1e/M2/M3) y **falla** desde d=29501.
3. "Ningún parcheo puede satisfacer G8" es **falso**: la cadena de derivación
   depende solo de los **dos últimos** bytes fuente. Parchear cualquier byte
   fuente anterior a esos dos **no altera ninguna celda derivada** y el loader
   estricto acepta el resultado.

---

## A. Afirmaciones auditadas

| ID | Afirmación | Veredicto | Evidencia |
|----|------------|-----------|-----------|
| C1 | Quantum jump en celdas 0–107/3312–3316, aterriza c=3315 d=121 | **REFUTADA** | celda 0 = `i` (byte 98) → pc=99, d=1; celdas 3312–3316 = `o`, nunca ejecutadas |
| C2 | Dispatcher `rot(crazy(input,67))` con salto `i` en 99–107 | **DEMOSTRADA** | ops 99–107 = `/ j p j * j i o o`; input `1` → target 9853; input `2` → 49219 |
| C3 | `j` solo alcanza d=byte+1 (máx 127); destinos altos imposibles | **REFUTADA** | input `2` ejecuta PCs 49219–49226; celdas 67/68 guardan valores rotados; `i` (c=mem[d]) salta a 49219 |
| C4 | `trip_to_trampoline` solo funciona con d>29522 | **REFUTADA (invertida)** | d=29501 → `low-memory steering budget exhausted`; d=63 (patrón M1e/M2/M3) → OK |
| C5 | Ningún parcheo puede satisfacer G8 (cadena de derivación) | **REFUTADA** | parche de 1 byte fuente en pos 0/1000/49997: loader=OK, **0** celdas derivadas cambian; solo pos n−2/n−1 lasalteran |
| C6 | Las celdas solo pueden contener 33–126 | **REFUTADA** | solo los **bytes fuente** (0..49999) están acotados; las derivadas (50000+) contienen valores como 29526, 29559 |
| C7 | Una celda fuente no puede contener una dirección alta | **DEMOSTRADA (con matiz)** | 29509 no cabe en un byte fuente, pero celdas derivadas o escritas en runtime (`p`) sí lo contienen |
| C8 | El entregable `boss3_real_loop.mal` cumple G7 | **REFUTADA** | builder produce 3317 bytes sha `75ece58c…`; disco tiene 102 bytes sha `f59cf283…` → **G7 rebuild falla** |
| C9 | El entregable produce `b'1'*N` y repite PCs (G1/G3) | **REFUTADA** | input `1` → 833 unos, `terminal=BUDGET` (ciclo infinito); input `3` → `b'3'` |
| C10 | El builder `tools/boss3_real_loop.py` es loader-estricto válido (G8) | **DEMOSTRADA** | 3317 bytes, 0 offsets inválidos, pero es un **placeholder** (`STRUCTURAL_PLACEHOLDER`, HALT inmediato) |
| C11 | La ruta 1 puede usar las constantes de quantum jump de `build_candidates.py` | **REFUTADA** | `{0:98,1:93,74:72,…}` decodifican a `'5','&','#',…` — **no son opcodes válidos** |

### Hallazgos adicionales (no estaban en el diagnóstico previo)

| ID | Hallazgo | Veredicto | Evidencia |
|----|----------|-----------|-----------|
| H1 | **M2/M3 ya repiten PCs** (la premisa "ningún artefacto repite PCs" era falsa) | **DEMOSTRADA** | M2: PCs 29525–29528 repetidas 2×; M3: repetidas 3×, dentro de una sola corrida |
| H2 | El conteo de M2/M3 es **fijo** (3 épocas), no dependiente del dato | **DEMOSTRADA** | 3 payloads distintos → mismo `max_repeticiones_de_una_PC=3` |
| H3 | El artefacto `boss3_dynamic_loop.mal` **sí contiene un cuerpo de bucle real** [64,65,88,89] | **DEMOSTRADA** | sin host: input `1` → PC 64 repetida 6651×, pc 88 ×3325, `terminal=BUDGET` (nunca sale solo) |
| H4 | La salida de ese bucle depende del host (`vm.mem[47]=99`) | **DEMOSTRADA** | `tools/boss3_dynamic_loop.py:161` escribe `vm.mem[47] = 99` desde Python |
| H5 | El camino de salida **existe como camino de programa** | **DEMOSTRADA** | celda 47 = `j`, celda 99 = `o` (prelanding), celda 100 = `v` (HALT); inyectar `mem[47]=99` → `terminal=HALT` |
| H6 | **El entregable está contaminado**: `boss3_real_loop.mal` es **byte-idéntico** a `boss3_dynamic_loop.mal` | **CONFIRMADO** | `cmp` → idénticos; sha `f59cf283…` en ambos; COMPOSE §1 declara el dynamic_loop como "intento previo, **asistido por el host**" |
| H7 | El JSON del entregable declara `"host_intervention_required": true` | **CONFIRMADO** | el propio metadato confiesa la dependencia del host |
| H8 | `test_review_regressions` falla por **timeout de infraestructura** (90 s), no por regresión lógica | **CONFIRMADO** | aislado tarda 58.5 s y pasa con `returncode=0`; bajo la suite completa excede 90 s (la suite spends ~155 s) |
| H9 | No existe `goal_judge` en el monorepo ni en el repo | **CONFIRMADO** | `grep -rl goal_judge` sobre todo ISyCo → vacío. Los 5 errores del juez previos **no** son reproducibles aquí: no hay juez que invocar |
| H10 | El contrato de tests tiene gates débiles | **CONFIRMADO** | G5 = `assertTrue(True)` (placeholder, no verifica nada); los 4 mutantes = `assertTrue(False)` fijos (no falsifican por construcción) |

---

## B. Qué restricciones matemáticas están realmente demostradas

1. **Bytes fuente acotados a 33–126 y decodificables** (`strict_byte`). Los bytes
   fuente son también el valor de la celda → una celda fuente **no** puede
   contener una dirección >126. **DEMOSTRADA.**
2. **La cadena de derivación depende solo de los 2 últimos bytes fuente.** Un
   parche en cualquier posición anterior **no** propaga. **DEMOSTRADA.**
3. **Celdas derivadas (≥ len(source)) y celdas escritas en runtime contienen
   cualquier valor 0–59048**, incluidos 29526, 29559 y direcciones de destino.
   **DEMOSTRADA.** (C6 del diagnóstico previo era falsa.)
4. **`c = mem[d]` (`i`) alcanza cualquier dirección**, siempre que `mem[d]` la
   contenga. **DEMOSTRADA** (C3 del diagnóstico previo era falsa).
5. **`trip_to_trampoline` exige `d` en el tablero 1..97** (memoria baja), no
   memoria alta. **DEMOSTRADA** (C4 del diagnóstico previo era invertida).
6. **`i` nunca se encripta**: `c = mem[d]` se evalúa antes del paso XLAT2 de la
   celda destino, así que una celda `i` puede reentrar el cuerpo indefinidamente.
   **DEMOSTRADA** por H3 (6651 reentradas a PC 64).
7. **Repetir PCs es posible en Classic Malbolge.** **DEMOSTRADA** (H1, H3).
8. **Un cuerpo de bucle puede salir por un portal propio** (celda 47 `j` →
   celda 99 `o` → celda 100 `v`). **DEMOSTRADA** (H5).

### Lo que NO está demostrado (y sigue abierto)
- Que el **número** de iteraciones pueda depender del **dígito leído** (0..9).
  M2/M3 repiten PCs con conteo **fijo**; el dynamic_loop repite pero **no sale**.
  Este es el hueco **real** y **acotado**, no "imposibilidad general".

---

## C. Qué construcción falsaría la hipótesis de bloqueo

La hipótesis de bloqueo ("no se puede repetir un PC / el quantum jump no deja
llegar a donde sea") queda falsada por H1+H3+H5. La hipótesis **reducida** que
sigue en pie es:

> *El conteo de iteraciones no puede depender de un dígito leído de stdin.*

**Falsificador concreto (un experimento):** construir un `.mal` donde
- el cuerpo del bucle sea **uno solo**, en celdas fijas (p. ej. 64,65,88,89),
- la salida por el portal 99/100 sea **in-band** (escrita por la propia VM),
- y el **número de vueltas** sea el valor del dígito leído.

Si ese `.mal` produce `b'1'*N` con `terminal=HALT` para N=0..9 y **la misma PC
de salida repetida exactamente N veces**, la hipótesis queda falsada y Boss 3
queda `DEMONSTRATED`. Si falla, el contraejemplo localiza la restricción real
(zero-test en banda / decremento en banda) en vez de "imposibilidad".

---

## D. La prueba mínima ejecutable más cercana a un bucle real

**Estado real medido:** el artefacto `boss3_dynamic_loop.mal` **ya tiene** el
cuerpo de bucle real [64,65,88,89] y el portal de salida [47,99,100]. Faltan dos
cosas, y solo dos:

**(D-1) La salida debe ser in-band.** Hoy `tools/boss3_dynamic_loop.py:161`
escribe `vm.mem[47] = 99` desde Python. La salida limpia ya existe como camino
de programa (celda 47 `j` → 99 `o` → 100 `v`); lo que falta es que **la propia
VM** escriba el valor 99 en la celda 47 cuando el contador llega a 0.
→ Prueba mínima: un `.mal` donde la celda 47 se rearma en banda con `p`/trampoline
(sin `vm.mem[...] =` desde Python) y el programa termina en HALT por sí solo.

**(D-2) El conteo debe depender del dígito.** El contador debe decrementarse en
banda. Ya existen las primitivas algebraicas:
- `DECREMENT_TABLE[v]` = x con `crazy(x, v) = v−1` para v ∈ {1,2,4,5,7,8}
- `DOUBLE_DECREMENT` para v ∈ {3,6,9}
- `rearm_trampoline_cell` (probado en M1e/M2/M3) para rearmar celdas en banda

→ Prueba mínima: decrementar un contador en celda fija y saltar a HALT cuando
llegue a 0, sin.host.

**Nota crítica de disciplina (H6):** el `boss3_real_loop.mal` actual es una
**copia byte-idéntica** del artefacto **asistido por el host**, prohibido por
COMPOSE §1. Debe reemplazarse por un artefacto nuevo, no parchearse ni
reutilizarse. Y el builder actual no reproduce su propio archivo (G7 falla:
3317 bytes generados vs 102 en disco), así que **G7 nunca pasó**.

---

## E. Clasificación

| Elemento | Clasificación |
|----------|----------------|
| Boss 3 (bucle con PC repetida y N dependiente del dígito) | `NOT_DEMONSTRATED` |
| Diagnóstico previo "imposible / requiere ruta 1 con ~120 celdas" | `REFUTED` (7/11 afirmaciones) |
| "Ningún parcheo puede satisfacer G8" | `REFUTED` |
| "trip_to_trampoline exige memoria alta" | `REFUTED` (precondición invertida) |
| "quantum jump en 0–107/3312–3316 con aterrizaje c=3315,d=121" | `REFUTED` (no describe este artefacto) |
| Entregable `boss3_real_loop.mal` | `BLOCKED_BY_TOOLING` — es una copia del artefacto asistido por host; G5 y G7 fallan |
| `test_review_regressions` | `BLOCKED_BY_INFRASTRUCTURE` — timeout de 90 s; aislado pasa en 58.5 s |
| Juez `goal_judge` (5 errores deepseek previos) | `BLOCKED_BY_INFRASTRUCTURE` — **no existe en este monorepo**; no hay juez que invocar ni diagnóstico que hacer |

## F. Archivos de evidencia generados

| Archivo | Contenido |
|---------|-----------|
| `evidence/boss3-nemotron-audit.json` | 11 afirmaciones con veredicto y evidencia |
| `evidence/boss3-nemotron-audit-round2.json` | Alcance de la cadena de derivación + PCs repetidas en M2/M3 |
| `evidence/boss3-nemotron-audit-round3.json` | Bucle real del dynamic_loop sin host (G1 evaluado) |
| `evidence/boss3-nemotron-audit-round4.json` | Probe del camino de salida (instrumentación, no solución) |
| `tools/audit_nemotron_claims.py` | Auditor reproducible de C1–C11 |
| `tools/audit_round2.py` | Cadena de derivación + M2/M3 |
| `tools/audit_round3.py` | Bucle sin host |
| `tools/audit_round4.py` | Probe del portal de salida |
