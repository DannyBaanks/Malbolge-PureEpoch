# Resultados — Pure Epoch M1

## Qué se construyó

Un programa Classic loader-valid de **29,526 bytes** (`candidates/m1c_normal.mal`) que preserva una celda lógica mediante otra celda in-band, calcula un candidato, bifurca según el valor real de la celda, recupera el valor guardado si falla y realiza un segundo intento corregido. Es un experimento finito: dos estados previos × dos operandos candidatos. No se reivindica primacía histórica, recuperación general, protección de memoria o rollback físico de la VM.

La construcción es independiente del código de la Truth Machine: utiliza identidades crazy/rotación y ensamblaje por dirección. M0 sigue siendo un control de ciclo distinto y atribuido a Weird Glyphs.

## M0 reproducido antes de modificar

Los siete archivos originales se leyeron y se ejecutaron 5 tests antes de crear este laboratorio. Una segunda reproducción de la copia preservada quedó en `evidence/m0-tests.txt` y `evidence/report-reproduced.json`. Coinciden hashes de los siete archivos y JSON completo con el baseline: ciclo de 408 instrucciones, 17 unos, cuatro celdas modificadas durante el ciclo; corrupción negativa persistente. Esto es **CYCLE**, no reparación.

## Contrato lógico y mecanismo

Memoria Classic de 59,049 celdas; fuente ASCII estricta; ocho opcodes originales. Target `T=36`, journal `J=52`, cero auxiliar `75`, generador del operando `81`, portal de recuperación `62`. No hay escritura desde el host ni reanudación de snapshots. Cada ejecución comienza en `(a,c,d)=(0,0,0)` con una sola carga del archivo.

Sea `U=29524` (diez trits 1). `crazy(x,U)` permuta los trits 0/1 y conserva 2; esa transformación es una involución. Para los selectores binarios en este dominio:

1. `p` prepara `J=U` y un cero auxiliar dentro de la VM.
2. El primer byte `s∈{1,3}` y una semilla 81 producen `T=U-s`.
3. `p` sobre J guarda `crazy(T,U)=s`, una representación interna reversible del valor previo.
4. Con el cero construido internamente, `p` convierte T en U. El segundo byte `x∈{1,3}` produce el candidato `T=U-x`.
5. `i` en `c=177`, `d=36`, usa **la celda calculada** como destino. T=29523 entra en commit `c=29524`; T=29521 entra en fallo `c=29522`. Es una tabla indirecta para este dominio finito, no un comparador de enteros arbitrarios.
6. La ruta de fallo repone U, lee J mediante diez rotaciones que también lo preservan y ejecuta `p` en `c=19825`: T vuelve a `U-s`.
7. Cuatro rotaciones de la semilla 81 construyen el operando 1. `p` en `c=19856` repite la transición con ese operando; el nuevo T=29523 toma commit. No se pide otro byte al host.

El único output se ejecuta en commit. La conservación del journal es parte del contrato; las lecturas por rotación lo mutan temporalmente y lo devuelven a su valor. No es memoria protegida.

```mermaid
flowchart LR
  S["Guardar T en J"] --> C["Calcular candidato T"]
  C --> D["i: salto según mem 36"]
  D -->|"29523"| O["Commit: S y HALT"]
  D -->|"29521"| R["p en 19825: restaurar desde J"]
  R --> P["p en 19856: segundo intento con operando 1"]
  P --> O
```

## Casos positivos

| stdin hex | T previo | Ruta | Instrucciones incluyendo HALT | T final | J final | stdout |
|---|---:|---|---:|---:|---:|---|
| `0101` | 29523 | commit | 82 | 29523 | 1 | `53` (`S`) |
| `0103` | 29523 | recuperación → retry → commit | 249 | 29523 | 1 | `53` |
| `0301` | 29521 | commit | 82 | 29523 | 3 | `53` |
| `0303` | 29521 | recuperación → retry → commit | 249 | 29523 | 3 | `53` |

La salida constante no es la evidencia de recuperación. Se compara la fase de restore, el journal y la memoria completa entre implementaciones. En este juguete, el resultado final fijo también podría alcanzarse omitiendo restore: el control `no_restore` lo hace y **se rechaza** por incumplir la restauración intermedia. No se afirma que restaurar sea necesario para obtener ese byte; sí que el programa ejecuta la recuperación y que esa fase depende causalmente del valor guardado.

## Primer restore observado

Para `0303`, índice de traza **211** (instrucción ejecutada número **212**):

| Campo | Antes | Después |
|---|---|---|
| Opcode | `p`, residuo 62 | — |
| `(a,c,d,input_cursor)` | `(3,19825,36,2)` | `(29521,19826,37,2)` |
| `mem[36]` | 29524 | **29521** |
| `mem[52]` | 3 | 3 |
| Output emitido | ninguno | ninguno |

En el índice 242, `p` en `19856` cambia T de 29521 a 29523. Commit ocurre en el índice 247; HALT en 248. Véanse `evidence/traces/m1c_normal-0303/{trace.jsonl,python-trace.jsonl,phases.json,state.bin,parity.json}`. El estado final completo C/Python es idéntico.

## Positivos menores y controles

- M1a: `m1a_rot10.mal`, 98 bytes, diez rotaciones de `mem[96]`: 37→19695→…→37 y HALT en 43 instrucciones. Nueve rotaciones dejan 111. Es **REVERSIBLE**, sin journal ni decisión.
- M1b: `m1b_normal.mal`, 308 bytes, entradas `0100`/`0300`, devuelve 29523/29521 leyendo el journal; 210 instrucciones. Su output sí depende del valor recuperado (`S`/`Q`). Es **CHECKPOINT** con recuperación incondicional.
- `m1b_output_impostor`: imprime `S` pero deja T=9841. Gate de memoria lo rechaza.
- M1c `no_save`, `corrupt_journal`, `no_restore`: pueden imprimir `S` y dejar T final válido; el gate de fases/journal los rechaza. No se acepta output ni estado final solos como prueba del protocolo.
- M1c `no_recovery`, `broken_return`, `early_halt`: detienen sin completar recuperación/commit; se rechazan.
- `force_retry_failure`: cambia la construcción del operando corregido, vuelve a generar el candidato inválido y termina en **STALL**, tras 254 fetches. No hubo rescate externo. No existe un manejador autónomo demostrado para fallos repetidos ni agotamiento de intentos.
- Un límite de un paso queda BUDGET y no satisface el contrato; el límite es de observación/prueba, no recuperación.

Todos los `.mal` negativos quedan conservados y pasan el loader estricto; falla la propiedad que pretenden satisfacer. Ver `evidence/measurements.json` y `evidence/failures.md`.

## Oráculos y regresiones

La campaña contiene 19 ejecuciones pequeñas. El C instrumentado y Python coinciden en cada transición, todos los cambios de celda y la memoria final completa. El C estricto **sin cambios** reproduce stdout/stop; el intérprete original Olmstead sin cambios reproduce stdout/HALT de los 18 casos que terminan. El control STALL se compara entre los dos motores acotados; no se ejecuta el histórico sin límite en una condición donde se quedaría esperando.

Instrumentar observación no convierte al observador en restaurador. El C instrumentado usa la operación de la referencia base9; el observador M0 Python calcula por diez trits. Los procesos originales se ejecutan aparte. No se afirma que el histórico sin instrumentar exporte memoria final.

Autobolge: 15 tests pertinentes pasan en el clon fijado, tras compilar los dos probes necesarios. BolgeForge: `make test` pasa con 52 unit tests y sus controles de corpus/compresión/quines/espejo. Logs crudos conservados. El adaptador offline emplea el `char_for` real de Autobolge, reproduce los mismos bytes, exporta anchors **observados** después de restore y valida replay desde cero. No llama a `EpochAnchorV1.restore()` y no guía aún propuestas relacionales.

Una reproducción mínima expone la diferencia EOF: fuente de dos bytes `uP`, stdin vacío. Classic estricto alcanza HALT con a=59048; Autobolge se detiene en INPUT_UNDERFLOW con a=0. Dos sondas adicionales (`semantic_probes` en `evidence/autobolge-bridge.json`) exponen las divergencias de cifrado post-ejecución (`2750`: `INVALID_ENCRYPTION`/STALL en Classic frente a `TERMINATED` con a=13 en Autobolge) y de loader no-ASCII (`af50`: rechazo del loader Classic frente a `TERMINATED` en Autobolge). No se declara paridad global entre ambas semánticas.

El fixture EOF se ejecutó también en C estricto, C instrumentado y Olmstead original: `evidence/eof-strict/` registra paridad de trazas/estado de los dos motores observados y HALT de los dos originales. Esa ejecución adicional está separada de los 19 casos de candidatos.

La comprobación final detectó progreso concurrente del Autobolge original hasta `dcfcd6fff0e40001ae686432d60a77434834e0b6`; no se escribió ni reseteó ese checkout. El experimento conserva sus fuentes fijadas. BolgeForge original y M0 permanecieron iguales según `evidence/final_source_integrity.json`.

## Addendum toroidal

`torus/` confirma C∩D=96 en m281/Lutter/m284. Las intersecciones se descomponen en 49 direcciones fijas y 47 reubicadas, consistente con la procedencia Lutter. No son tres diseños independientes. El script externo actual coincide con la medición C para m281; algunas cuentas de la captura anterior no se reprodujeron. Se conserva la discrepancia y la falsación del detector original de simetría.

La celda 53 es accesible y modificable, pero ya contiene estado vivo del loop: usarla como reserva intacta queda refutado. G-T3 del quine permanece NOT_DEMONSTRATED. El éxito M1 del programa pequeño no se transfiere a los quines.

## M1e y M2 — Rearme in-VM de trampolines, commit dependiente del dato recuperado, contador de intentos y dos épocas (NEXT_COMPOSE puntos 1–4)

Siguiendo `NEXT_COMPOSE.md` y preservando `candidates/m1c_normal.mal` (`17ff6f326c3205fa92bae9eeeba4c8ecf0229a722c55491e2fa5e0cd4d7b7985`) intacto:

### 1. Bytes reales post-cifrado de trampolines/portales y rearme in-VM (`evidence/trampoline-rearm.json`)

- En Classic Malbolge, el salto indirecto `i` cambia `c = mem[d]` **antes** de aplicar `XLAT2` sobre `mem[c]`, por lo que `i` no se cifra a sí mismo sino que cifra la celda de pre-aterrizaje `mem[mem[d]]`; en cambio, `j` y `<` sí cifran su propia celda `mem[c]` al ejecutarse.
- Para cualquier byte imprimible ASCII `y ∈ [33, 126]` (tanto el byte original como el byte post-`XLAT2`), como `y < 162 = 2·3⁴`, sus trits `2` sólo pueden aparecer en las posiciones `0..3`. Con `80 = 0000002222₃` se cumple la identidad universal:
  `crazy(0, crazy(80, crazy(29524, y))) = 29524` para todo `y ∈ [0, 161]`,
  y `crazy(crazy(B, 29524), 29524) = B` reescribe el byte objetivo `B` dentro de la propia VM, restableciendo además la celda auxiliar `53` mediante `crazy(0, crazy(B, crazy(B, 29524))) = 29524`.

### 2. Candidato M1e (`candidates/m1e_normal.mal`, 29,531 bytes, SHA256 `dc9ed4d81ef7200d5b5e1dc2c3f161bd4b01be39b58ca43bc87db410461e9f53`)

- Mientras la submatriz `{0,1} × {0,1}` de `TRITS` colapsa el estado previo (`crazy(0, y) = 29524`), la columna `x_trit = 2` (`(0, 2, 1)`) es una involución que separa los tres valores de trit.
- Evaluando el candidato `cand ∈ {1, 3}` a `op = 8` (`0000000022₃`, válido) o `op = 0` (inválido) y aplicando `crazy(op, mem[36])`:
  - Si `cand = 3` (`op = 0`): tanto `initial = 1` (`29523`) como `initial = 3` (`29521`) colapsan a `mem[36] = 29524` (borrando el dato previo en `mem[36]`) y saltan a `failure_route` (`29525`).
  - Si `cand = 1` (o tras recovery + retry con `op = 8`):
    - `initial = 1` (`29523`) → `mem[36] = 29526`, salta a `commit_1` (`29527: <`), emite `V` (`0x56`) y `HALT` (`29528: v`).
    - `initial = 3` (`29521`) → `mem[36] = 29522`, salta a `commit_3` (`29523: <`), emite `R` (`0x52`) y `HALT` (`29524: v`).
- **Control `no_restore` (`m1e_no_restore.mal`):** al omitir `restore`, `mem[36]` permanece en `29524` y el retry produce `crazy(8, 29524) = 29528`, que salta a `no_restore_reject` (`29529: v`) con **stdout vacío (`b""`) y `mem[36] = 29528`**, fallando tanto el resultado final observable como el estado lógico final, además de la fase intermedia.

### 3. Contador interno finito de intentos y rechazo/HALT explícito

- La celda `mem[64]` (`attempt_counter_cell`) inicia en `29524` (`0` intentos), pasa a `29528` (`crazy(8, 29524)`, 1 intento) en el primer intento y a `7` (`crazy(29525, 29528)`, 2 intentos) al entrar en recovery.
- Durante recovery, el portal `mem[62]` rota una segunda vez (`19695 → 6565`, destino `c = 6566` con `v`) y el programa rearma in-VM `29524..29525`.
- En `m1e_force_retry_failure.mal`, el segundo fallo salta por el trampolín rearmado hacia `reject_halt` (`c = 6566`) y termina en **`HALT` explícito** (`stdout = b""`, `mem[36] = 29524`, `mem[64] = 7`, `2,005` fetches).
- El comportamiento `STALL` anterior se conserva por separado en `m1e_force_retry_stall.mal` (`STALL` en `1,741` fetches).

| Candidato M1e | stdin hex | Terminal | Instrucciones incl. HALT | `mem[36]` final | `mem[52]` final | `mem[64]` final | stdout | Contrato |
|---|---|---|---:|---:|---:|---:|---|---|
| `m1e_normal` | `0101` | `HALT` | 1,252 | 29526 | 1 | 29528 | `56` (`V`) | `True` |
| `m1e_normal` | `0103` | `HALT` | 2,042 | 29526 | 1 | 7 | `56` (`V`) | `True` |
| `m1e_normal` | `0301` | `HALT` | 1,252 | 29522 | 3 | 29528 | `52` (`R`) | `True` |
| `m1e_normal` | `0303` | `HALT` | 2,042 | 29522 | 3 | 7 | `52` (`R`) | `True` |
| `m1e_no_restore` | `0103` / `0303` | `HALT` | 2,041 | 29528 | 1 / 3 | 7 | `""` | `False` |
| `m1e_force_retry_failure` | `0103` / `0303` | `HALT` | 2,005 | 29524 | 1 / 3 | 7 | `""` | `False` |
| `m1e_force_retry_stall` | `0103` / `0303` | `STALL` | 1,741 | 29524 | 1 / 3 | 7 | `""` | `False` |

### 4. Composición M2 de dos épocas en un único proceso (`candidates/m2_normal.mal`, 55,770 bytes, SHA256 `3ec16fd60b5298a83f30dddf340bdc962a6fe981c4a05379c446bcb92a8748d6`)

- En la Época 1, tras emitir el primer byte en `29523: <` o `29527: <`, el puntero `d` avanza de `37` a `38`, por lo que `29524: i` y `29528: i` convergen al mismo portal de continuación `mem[38] = 39397` (`c = 39398, d = 39`).
- Al iniciar la Época 2 en `c = 39398`, el propio programa:
  1. Rearma in-VM la tabla `29523..29528` (instalando `v` en `29524` y `29528` para el cierre de la Época 2).
  2. Rearma el portal `mem[62]` hacia la recuperación de la Época 2 (`49208 → c = 49209`, con rechazo explícito en `55768 → c = 55769`).
  3. Des-compromete `mem[36]` desde el estado comprometido de la Época 1 (`crazy(8, 29526) = 29523` o `crazy(8, 29522) = 29521`) y guarda el journal `mem[52]` de la Época 2 sin releer el selector inicial desde `stdin`.
  4. Ejecuta la Época 2 completa con `cand_2 ∈ {1, 3}`.

| Trayectoria M2 (`m2_normal`) | stdin hex | Rotaciones de journal (E1 + E2) | Instrucciones incl. HALT | `mem[36]` final | `mem[52]` final | `mem[64]` final (E2) | stdout | Contrato |
|---|---|---|---:|---:|---:|---:|---|---|
| válido / válido (`init=1`) | `010101` | `0 + 0 = 0` | 3,916 | 29526 | 1 | 29528 | `5656` (`VV`) | `True` |
| inválido / válido (`init=1`) | `010301` | `10 + 0 = 10` | 4,703 | 29526 | 1 | 29528 | `5656` (`VV`) | `True` |
| válido / inválido (`init=1`) | `010103` | `0 + 10 = 10` | 4,663 | 29526 | 1 | 7 | `5656` (`VV`) | `True` |
| inválido / inválido (`init=1`) | `010303` | `10 + 10 = 20` | 5,450 | 29526 | 1 | 7 | `5656` (`VV`) | `True` |
| válido / válido (`init=3`) | `030101` | `0 + 0 = 0` | 3,916 | 29522 | 3 | 29528 | `5252` (`RR`) | `True` |
| inválido / válido (`init=3`) | `030301` | `10 + 0 = 10` | 4,703 | 29522 | 3 | 29528 | `5252` (`RR`) | `True` |
| válido / inválido (`init=3`) | `030103` | `0 + 10 = 10` | 4,663 | 29522 | 3 | 7 | `5252` (`RR`) | `True` |
| inválido / inválido (`init=3`) | `030303` | `10 + 10 = 20` | 5,450 | 29522 | 3 | 7 | `5252` (`RR`) | `True` |

### 5. Composición M3 de tres épocas con Roundtrip + Rollback y campaña de propuestas acotadas (`candidates/m3_normal.mal`, 55,770 bytes, SHA256 `7f95770a4786132dd148ccbf4af328d6e62be68ed6732754b2f50c5019114689`)

- **Arquitectura de tres épocas en un único proceso Classic Malbolge (`stdin = [initial, cand_1, cand_2, cand_3]`):**
  1. **Época 1 (`c = 98`, recuperación `c = 19696`, rechazo `c = 6566`):** inicializa `mem[36]` desde `initial ∈ {1, 3}`, guarda el journal en `mem[52]`, evalúa `cand_1` (con enmascaramiento de `EOF = 59048` poniendo `mem[53] = 0` antes de `/`, de modo que `crazy(59048, 0) = 0 → op = 0`), recupera desde `mem[52]` si `cand_1 = 3`, emite el primer byte comprometido (`V` o `R`) y salta por `mem[38] = 39397` hacia la Época 2 (`c = 39398`).
  2. **Época 2 (`c = 39398`, recuperación `c = 49209`, rechazo `c = 55769`):** rearma in-VM la tabla de trampolines `29523..29528` conservando `i` en `29524` (`90`) y `29528` (`86`, celda constante `47`), rota una vez `mem[38]` (`39397 → 32815`, preparando `c = 32816` para la Época 3), rearma el portal `mem[62] = 49208`, des-compromete `mem[36]`, guarda el journal `mem[52]` de la Época 2, evalúa `cand_2` (con rollback/retry si `cand_2 = 3`), emite el segundo byte comprometido y salta hacia la Época 3 (`c = 32816`).
  3. **Época 3 (`c = 32816`, recuperación `c = 9816`, rechazo `c = 42638`):** rearma por segunda vez in-VM `29523..29528` (instalando `v` en `29524` y `29528` para el cierre final), resetea `mem[62]` desde `{49208, 55768}` a `29524` mediante `rot^8` + `reset_scratch_cell(62)` y arma el portal de la Época 3 (`mem[62] = 9815 → c = 9816`, rechazo `42637 → c = 42638`), guarda el journal `mem[52]` de la Época 3, evalúa `cand_3` (incluyendo el caso `EOF = 59048` con `stdin` truncado a 3 bytes `010101` / `030101`), emite el tercer byte comprometido (`VVV` o `RRR`) y ejecuta `HALT`.

| Trayectoria M3 (`m3_normal`) | stdin hex | Rotaciones de journal (E1+E2+E3) | Instrucciones incl. HALT | `mem[36]` final | `mem[52]` final | `mem[64]` final (E3) | stdout | Contrato |
|---|---|---|---:|---:|---:|---:|---|---|
| limpio 3 épocas (`init=1`) | `01010101` | `0 + 0 + 0 = 0` | 6,763 | 29526 | 1 | 29528 | `565656` (`VVV`) | `True` |
| fallo E1 (`init=1`) | `01030101` | `10 + 0 + 0 = 10` | 7,555 | 29526 | 1 | 29528 | `565656` (`VVV`) | `True` |
| fallo E2 (`init=1`) | `01010301` | `0 + 10 + 0 = 10` | 7,431 | 29526 | 1 | 29528 | `565656` (`VVV`) | `True` |
| fallo E3 (`init=1`) | `01010103` | `0 + 0 + 10 = 10` | 7,510 | 29526 | 1 | 7 | `565656` (`VVV`) | `True` |
| triple rollback E1+E2+E3 (`init=1`) | `01030303` | `10 + 10 + 10 = 30` | 8,970 | 29526 | 1 | 7 | `565656` (`VVV`) | `True` |
| triple rollback E1+E2+E3 (`init=3`) | `03030303` | `10 + 10 + 10 = 30` | 8,970 | 29522 | 3 | 7 | `525252` (`RRR`) | `True` |
| `EOF` en E3 recuperado (`init=1`) | `010101` | `0 + 0 + 10 = 10` | 7,510 | 29526 | 1 | 7 | `565656` (`VVV`) | `True` |
| `EOF` en E3 recuperado (`init=3`) | `030101` | `0 + 0 + 10 = 10` | 7,510 | 29522 | 3 | 7 | `525252` (`RRR`) | `True` |
| `m3_force_retry_failure` | `01030303` / `03030303` | `10 + 10 + 10 = 30` | 8,940 | 29524 | 1 / 3 | 7 | `VV` / `RR` | `False` |
| `m3_eof_unmasked` | `010101` / `030101` | `0 + 0 + 0 = 0` | 6,732 (`STALL`) | 29526 / 29522 | 1 / 3 | 29528 | `VVV` / `RRR` | `False` |

- **Campaña offline de propuestas acotadas (`evidence/m3-proposals.json`, `tools/autobolge_adapter.py`):**
  - Se evaluaron **64 candidatos** (`<= 128` de presupuesto, `<= 10,000` instrucciones por corrida) generados sobre 8 familias de slots (`epoch3_save`, `epoch3_restore`, `epoch3_retry_dispatch`, `epoch3_eof_mask`, `epoch3_damage_journal`, `epoch3_retry_const_op`, `epoch3_post_output_op`, `strict_loader_boundary`) usando el codificador `char_for` y `TraceExpander` de Autobolge.
  - **Resultado:** `8` propuestas aceptadas (las 8 convergen exactamente al fuente canónico `m3_normal.mal` SHA256 `7f95770a4786…`) y `56` propuestas rechazadas y conservadas con su gate exacto (`strict_loader_gate`: 7, `no_save_or_checkpoint_gate`: 7, `no_restore_gate`: 7, `broken_return_gate`: 7, `corrupt_journal_gate`: 7, `repeated_failure_gate`: 7, `output_impostor_gate`: 7, `distinct_eof_gate`: 1 + 6 fallos previos en positivo).
  - **Discrepancias registradas:**
    1. `TraceExpander._valid_extensions` propone extensiones en `len(anchor.program)` mientras `EpochAnchorV1.restore()` reanuda el snapshot mutado en memoria sin recargar desde cero.
    2. En el payload `EOF` de 3 bytes (`010101`), Classic estricto lee `59048`, lo enmascara a `op = 0`, ejecuta rollback en `epoch3_restore` y compromete `VVV` (`HALT` en `7,510` fetches), mientras `ClassicDebugger` de Autobolge detiene la ejecución en `read_candidate_3` con `StopReason.INPUT_UNDERFLOW` y salida truncada `VV`.

### 6. Análisis de la escalera Mod-94 (`4=376`, `2=188`, `1=94`) y Punto Fijo Sintético de Periodo-1 (`evidence/quine-94-analysis.json`)

- **Por qué existen `4 = 376` y `2 = 188`, pero NO una quine Classic autónoma de `1 = 94` bytes bajo loader estricto (`tools/quine_94_probe.py`):**
  1. **Descomposición de ciclos de `XLAT2`:** los 94 caracteres ASCII imprimibles se particionan en 6 ciclos disjuntos de longitudes `[68, 9, 6, 5, 4, 2]` (`68+9+6+5+4+2 = 94`). No existe **ningún punto fijo de longitud 1** (`fixed_points_period_1 = []`); el ciclo mínimo tiene longitud **2** (`'F' (70) ↔ 'J' (74)`), razón por la cual los anillos estáticos de dos y cuatro tiempos requieren múltiplos de `2 × 94 = 188` o `4 × 94 = 376` (y la quine de Lutter usa dos mitades `2C = 2 × 94 × m = 188 × m`).
  2. **Muro del loader Classic estricto en `0..93` (`1 = 94`):** en un bloque único de 94 celdas, `'F'` sólo es legal en 8 posiciones y `'J'` en 8 posiciones (`16` posiciones únicas de 94, con **0 posiciones donde ambos sean simultáneamente legales**); en **78 de las 94 posiciones (`82.98%`)** ni `'F'` ni `'J'` son aceptados por el loader estricto.
  3. **Techo acíclico (`93 < 94`):** sin un salto hacia atrás (`i`), un programa de 94 celdas que termina en `v` ejecuta a lo sumo 93 instrucciones antes de `HALT`, por lo que puede emitir como máximo 93 bytes (`< 94`, y a lo sumo 47 transiciones distintas de `A`). Se verificó empíricamente en los 3 oráculos el programa `candidates/quine94_ceiling_probe.mal` de exactamente `94` bytes (`SHA256 717f0cd4…`), que ejecuta un roundtrip de 10 rotaciones sobre `mem[81] = 81` dentro de `0..93`.
- **Teorema del Punto Fijo Sintético de Periodo-1 (`1 = 94`) vía Roundtrip:**
  - Aunque `XLAT2` no tiene puntos fijos nativos de periodo 1, la secuencia in-VM de 4 pasos `crazy(x_const, crazy(0, crazy(80, crazy(29524, XLAT2(pre))))) == pre` restaura exactamente el byte pre-`XLAT2` en la **misma dirección módulo 94** (verificado exhaustivamente en los `94 × 8 = 752` pares `(pos, opcode)`).
  - Gracias a este punto fijo sintético de periodo 1, `M3` mantiene todo su núcleo de despacho y estado (`17` trampolines en `2..77` + celdas lógicas, portales, journal, contador y constantes en `36..84`) dentro del **primer bloque `1 = 94` (`0..93`)**, reutilizándolo a lo largo de 3 épocas completas sin duplicar anillos de `188` o `376` celdas.

Las **89 ejecuciones** de la campaña completa (`19` de M1a/b/c + `22` de M1e + `20` de M2 + `28` de M3) tienen paridad exacta entre Python, `trace_ref`, `mb_ref` y `olmstead` (en todos los casos `HALT`).
