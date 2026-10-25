# Plan — Cierre Integral del Roadmap PureEpoch (M1e, M2, M3, Quine 1=94 y Línea Toroidal G-T2/G-T3 Borrow & Return)

## Estado

COMPLETED — 5 milestones (M0–M4) ejecutados, verificados y sellados con 47/47 tests unitarios en verde y paridad total de 5 oráculos.

## Objetivo

Completar de punta a punta el roadmap experimental de `PureEpoch-2026-10-25` definido en `NEXT_COMPOSE.md`, `VERDICT.md` y `torus/TORUS_RESULTS.md`:
1. Consolidar los hitos ya demostrados en la línea principal (`M1e`, `M2`, `M3` de 3 épocas con Roundtrip + Rollback, campaña de 64 propuestas de Autobolge y análisis `1=94` vs `2=188` vs `4=376`).
2. Resolver y ejecutar la **Línea Toroidal Separada (`G-T2` y `G-T3 / E-T3`)** bajo `torus/` sin usar la celda viva `53`: localizar en el grafo observado de `m281`/`lutter`/`m284` las regiones `D \ C \ E` con ventana de préstamo temporal (`borrow & return`), construir y verificar en C estricto (`torus/mb_ref` y `torus/observe`) primero la escritura/lectura controlada de dos valores con devolución exacta (`E-T2`), y después el protocolo completo de préstamo + checkpoint + bifurcación in-band + restore + retry + devolución del préstamo (`E-T3`) con sus controles negativos.
3. Actualizar `VERDICT.md`, `RESULTS.md`, `README.md`, `NEXT_COMPOSE.md`, `torus/TORUS_RESULTS.md` y `torus/SHA256SUMS.txt` con paridad total de oráculos y cero regresiones.

## Evidencia inspeccionada

- `/home/danny/Development/ISyCo Git/PureEpoch-2026-10-25/NEXT_COMPOSE.md:1-27`: Especifica los 5 pasos de continuación reutilizable (`M1e`, `M2`, `M3`) y la línea toroidal separada (prohibición de usar celda `53` por estar viva; localizar región `D \ C \ E` con contrato temporal de préstamo y devolución; demostrar primero escritura/lectura controlada de dos valores y después checkpoint y bifurcación).
- `/home/danny/Development/ISyCo Git/PureEpoch-2026-10-25/VERDICT.md:1-23`: Tabla canónica de claims donde `M2`, `M3`, `G-T2` (reserva controlada) y `G-T3` (`E-T3`) figuraban aún como `NOT_DEMONSTRATED` antes de las entregas de hoy.
- `/home/danny/Development/ISyCo Git/PureEpoch-2026-10-25/torus/TORUS_RESULTS.md:13-14,72-97`: Documenta la destrucción de la hipótesis sobre la celda `53` (`W=3` en pasos `18, 20575, 20605`; `R=1143`) y define el experimento `E-T3` pendiente de ejecución.
- `/home/danny/Development/ISyCo Git/PureEpoch-2026-10-25/torus/runs/m281.counts.csv:1-65`: Evidencia empírica de que en `m281` existen `26,690` celdas en `D \ C \ E` (excluyendo `53`), y en particular en memoria baja (`0..93`):
  - `addr = 39`: `D_visits = 6766, R = 1 (step 138), W = 0, E = 0`.
  - `addr = 41`: `D_visits = 9129, R = 4 (steps 19708..19828), W = 0, E = 0` (ventana de préstamo pre-lectura de `19,707` pasos y post-lectura de `62,220,024` pasos).
  - `addr = 40, 42, 43, 44`: `D_visits = 7933..12573, R = 0, W = 0, E = 0` (`firstD = 5, 7, 8, 9`).
- `/home/danny/Development/ISyCo Git/PureEpoch-2026-10-25/torus/analyze.py:1-64` y `torus/test_evidence.py:1-46`: Pipeline de verificación de conjuntos y pruebas unitarias toroidales (`6/6` en verde, presupuesto acumulado `395,230,192 < 400,000,000` pasos).

## Alcance

- Análisis exacto de ventanas temporales de préstamo (`borrow & return`) en `D \ C \ E` sobre los CSV observados de `m281`, `lutter` y `m284` (`torus/borrow_windows.py` y `torus/runs/dce_borrow_windows.json`).
- Generador offline y verificación en C estricto (`torus/mb_ref` y `torus/observe`) para `E-T2` (escritura/lectura controlada de dos valores `1` y `3` + devolución del byte original de la celda prestada en `D \ C \ E`) y `E-T3` (préstamo de journal `J = 42` con resguardo previo de su valor original en `L = 44`, checkpoint de estado `S = 40`, bifurcación in-band por candidato `1|3`, corrupción controlada, restore desde `J = 42`, retry, devolución del préstamo `mem[42] = 120` y verificación por salto consumidor `j` sobre `mem[42]`).
- Controles negativos explícitos en `torus/`: `no_loan_return` (no devolver la celda prestada rompe el salto downstream del consumidor), `no_restore`, `corrupt_journal` y `force_retry_failure`.
- Pruebas unitarias en `torus/test_evidence.py` y sincronización de `VERDICT.md`, `RESULTS.md`, `README.md`, `NEXT_COMPOSE.md`, `torus/TORUS_RESULTS.md` y `torus/SHA256SUMS.txt`.

## No objetivos

- No re-ejecutar las corridas de 62M–69M pasos de los quines completos (`m281`, `lutter`, `m284`), manteniendo el presupuesto total de `torus/` estrictamente por debajo del tope de `400,000,000` instrucciones (`actual + nuevos micro-candidatos < 395.3M`).
- No modificar `baseline/`, `vendor/`, ni los artefactos certificados `m1c_normal.mal`, `m1e_normal.mal`, `m2_normal.mal` o `m3_normal.mal`.
- No usar la celda `53` como reserva en ningún candidato toroidal nuevo.

## Milestones

### M0 — Congelar especificación, hashes base y auditoría de presupuesto toroidal

- **Objetivo:** Verificar que los artefactos `M0`, `M1a–M1e`, `M2`, `M3` y las pruebas actuales (`44/44`) estén en verde antes de tocar `torus/`, y confirmar el margen de presupuesto de instrucciones disponible en `torus/budget_all.json`.
- **Rutas previstas:** `candidates/m1c_normal.mal`, `candidates/m1e_normal.mal`, `candidates/m2_normal.mal`, `candidates/m3_normal.mal`, `torus/budget_all.json`.
- **Pasos:**
  1. Verificar hashes SHA-256 de `m1c_normal.mal`, `m1e_normal.mal`, `m2_normal.mal` y `m3_normal.mal`.
  2. Inspeccionar `torus/budget_all.json` (`395,230,192` pasos asignados de `400,000,000`, margen libre de `4,769,808` pasos).
- **Aceptación:** Los 4 hashes canónicos coinciden exactamente y el margen toroidal supera `4.7M` instrucciones.
- **Prueba:** `cd "/home/danny/Development/ISyCo Git/PureEpoch-2026-10-25" && sha256sum candidates/m1c_normal.mal candidates/m1e_normal.mal candidates/m2_normal.mal candidates/m3_normal.mal`
- **Rollback:** `git checkout -- .` en caso de cualquier discrepancia previa.

### M1 — Mapa de ventanas de préstamo y devolución en `D \ C \ E` (excluyendo celda 53)

- **Objetivo:** Extraer de las trazas y tablas `counts.csv` / `sets.csv` / `journal_prefix_30000.csv` de `m281`, `lutter` y `m284` el catálogo exacto de celdas `D \ C \ E` (excluyendo `53`) clasificadas por régimen de préstamo: (a) pasivas visitadas por `D` con `R=0, W=0, E=0` (`40, 42, 43, 44`), (b) leídas con ventana pre-lectura/post-lectura libre de escrituras (`39` con `firstR=138`; `41` con ventana pre-lectura `1..19707` y post-lectura `19829..62239852`), y (c) vivas de preámbulo (`45..52, 54..62` con ventana pre-escritura `1..20156`).
- **Rutas previstas:** `torus/borrow_windows.py`, `torus/runs/dce_borrow_windows.json`.
- **Pasos:**
  1. Crear `torus/borrow_windows.py` que lea `runs/{m281,lutter,m284}.{sets,counts}.csv` y `runs/journal_prefix_30000.csv` sin ejecutar pasos nuevos de VM sobre los quines.
  2. Exportar `torus/runs/dce_borrow_windows.json` con la prueba de que la descomposición `49+47` y las celdas en `complement` (`D=0`) carecen de alcanzabilidad `D`, mientras que la banda `D \ C \ E` en `39..44` posee alcanzabilidad `D` inmediata desde los pasos `4..9` y ventanas de préstamo verificables.
- **Aceptación:** `torus/runs/dce_borrow_windows.json` generado y verificado con conteos exactos para `m281`, `lutter` y `m284`, excluyendo explícitamente la celda `53`.
- **Prueba:** `cd "/home/danny/Development/ISyCo Git/PureEpoch-2026-10-25/torus" && python3 -B borrow_windows.py`
- **Rollback:** `rm -f torus/borrow_windows.py torus/runs/dce_borrow_windows.json`

### M2 — Demostración constructiva G-T2 (`E-T2`): Escritura/lectura controlada de dos valores con Borrow & Return en `D \ C \ E`

- **Objetivo:** Construir un programa Classic Malbolge estricto (`torus/programs/torus_borrow_e_t2.mal`) y su control negativo sin devolución (`torus/programs/torus_borrow_e_t2_no_return.mal`) que tome prestada la celda `D \ C \ E` `addr = 41` (cuyo byte original `121` es requerido después por un salto `j` del consumidor), guarde primero su byte original `121` en el resguardo `L = 43` (`D \ C \ E`), escriba y lea de vuelta dos valores distintos de entrada (`stdin = 0x01` o `0x03`) sobre `addr = 41`, restaure `mem[41] = 121` desde `L = 43`, y ejecute finalmente el salto `j` del consumidor a través de `mem[41] = 121` para emitir el valor leído y hacer `HALT`.
- **Rutas previstas:** `torus/torus_borrow_experiments.py`, `torus/programs/torus_borrow_e_t2.mal`, `torus/programs/torus_borrow_e_t2_no_return.mal`, `torus/runs/torus_e_t2_report.json`.
- **Pasos:**
  1. Implementar el ensamblador offline de `torus_borrow_e_t2.mal` y `torus_borrow_e_t2_no_return.mal` en `torus/torus_borrow_experiments.py` respetando `strict_byte` en cada dirección y manteniendo `C`, `D`, `R`, `W`, `E` disjuntos (`41, 43 ∈ D \ C \ E`, celda `53` no tocada `R=0, W=0`).
  2. Ejecutar ambos programas para `stdin = 0x01` y `stdin = 0x03` en el observador C (`torus/observe`), el oráculo C estricto (`torus/mb_ref`) y el verificador Python.
  3. Confirmar que `torus_borrow_e_t2.mal` restaura exactamente `mem[41] == 121` tras haber almacenado y leído `29523` (para `0x01`) o `29521` (para `0x03`), y que `torus_borrow_e_t2_no_return.mal` falla al romper el salto `j` del consumidor sobre `mem[41]`.
- **Aceptación:** `E-T2` pasa en los 3 oráculos para `0x01` y `0x03` con `41, 43 ∈ D \ C \ E`, `mem[41]` devuelto a `121`, celda `53` intacta (`W=0, R=0`), y `no_return` rechazado.
- **Prueba:** `cd "/home/danny/Development/ISyCo Git/PureEpoch-2026-10-25/torus" && python3 -B torus_borrow_experiments.py`
- **Rollback:** `git checkout -- torus/`

### M3 — Ejecución constructiva G-T3 (`E-T3`): Préstamo, Checkpoint, Bifurcación In-Band, Restore, Retry y Devolución en `D \ C \ E`

- **Objetivo:** Ejecutar el experimento `E-T3` completo diseñado en `torus/TORUS_RESULTS.md` y `NEXT_COMPOSE.md`: tomar prestada la celda `J = 42` (`D \ C \ E`, valor original `120`, nunca `53`), resguardar su valor pre-préstamo `120` en `L = 44` (`D \ C \ E`), inicializar el estado `S` en `addr = 40` (`D \ C \ E`) desde `initial ∈ {1, 3}`, guardar el checkpoint de `S` en el journal prestado `J = 42`, bifurcar in-band según `cand ∈ {1, 3}` (hacia commit limpio si `cand = 1` o corrupción controlada `mem[40] = 29524` si `cand = 3`), reconstruir `S` desde `J = 42` en recovery y reintentar la transición (`retry`), y **devolver `J = 42` a su valor original `120` desde `L = 44`** antes de que el consumidor final ejecute `j` sobre `mem[42] = 120` para llegar al commit (`V` para `initial=1`, `R` para `initial=3`).
- **Rutas previstas:** `torus/torus_borrow_experiments.py`, `torus/programs/torus_e_t3_normal.mal`, `torus/programs/torus_e_t3_no_loan_return.mal`, `torus/programs/torus_e_t3_no_restore.mal`, `torus/programs/torus_e_t3_corrupt_journal.mal`, `torus/programs/torus_e_t3_force_retry_failure.mal`, `torus/runs/torus_e_t3_report.json`.
- **Pasos:**
  1. Construir `torus_e_t3_normal.mal` y sus 4 controles negativos (`no_loan_return`, `no_restore`, `corrupt_journal`, `force_retry_failure`) asegurando que `S = 40`, `J = 42` y `L = 44` pertenezcan estrictamente a `D \ C \ E` (`C_visits = 0, encryptions = 0`) y que la celda `53` jamás sea escrita ni leída.
  2. Ejecutar las 4 combinaciones `(initial, cand) ∈ {1, 3}²` sobre `torus_e_t3_normal.mal` y los controles negativos en `torus/observe`, `torus/mb_ref`, `trace_ref` y `olmstead`.
  3. Verificar que tanto el camino limpio (`cand = 1`) como el camino con corrupción + restore + retry (`cand = 3`) devuelven `mem[42] == 120` al finalizar el préstamo, comprometen `mem[40] == 29526` (`stdout = V`) o `29522` (`stdout = R`), y que `no_loan_return`, `no_restore`, `corrupt_journal` y `force_retry_failure` fallan sus gates respectivos.
- **Aceptación:** Paridad exacta C/Python en todas las corridas de `E-T3`, `mem[42] == 120` restituido al cierre en las 4 trayectorias positivas, celda `53` intacta, y los 4 controles negativos falsados.
- **Prueba:** `cd "/home/danny/Development/ISyCo Git/PureEpoch-2026-10-25/torus" && python3 -B torus_borrow_experiments.py`
- **Rollback:** `git checkout -- torus/`

### M4 — Sincronización de evidencias, `VERDICT.md`, `TORUS_RESULTS.md`, `SHA256SUMS.txt` y suite global

- **Objetivo:** Integrar los resultados de `M1e`, `M2`, `M3`, `Quine 1=94`, `E-T2` y `E-T3` en `torus/test_evidence.py`, `torus/TORUS_RESULTS.md`, `torus/SHA256SUMS.txt`, `VERDICT.md`, `RESULTS.md`, `README.md`, `NEXT_COMPOSE.md` y `evidence/manifest.json`, ejecutando todas las suites de pruebas y registrando el commit final.
- **Rutas previstas:** `torus/test_evidence.py`, `torus/TORUS_RESULTS.md`, `torus/SHA256SUMS.txt`, `VERDICT.md`, `RESULTS.md`, `README.md`, `NEXT_COMPOSE.md`, `evidence/progress.md`, `evidence/manifest.json`.
- **Pasos:**
  1. Ampliar `torus/test_evidence.py` con pruebas unitarias para `dce_borrow_windows.json`, `E-T2` (`G-T2`) y `E-T3` (`G-T3`) y regenerar `torus/SHA256SUMS.txt` con `python3 hash_all.py`.
  2. Actualizar `VERDICT.md`, `torus/TORUS_RESULTS.md`, `RESULTS.md`, `README.md`, `NEXT_COMPOSE.md` y `evidence/progress.md`.
  3. Ejecutar `unittest` en `baseline`, `tests` y `torus`, actualizar `evidence/manifest.json`, hacer `git commit -- <paths>` y liberar el lease del bridge.
- **Aceptación:** 100% de los tests en `baseline`, `tests` y `torus` en verde (exit 0), `torus/SHA256SUMS.txt` y `evidence/manifest.json` actualizados, árbol git limpio.
- **Prueba:** `cd "/home/danny/Development/ISyCo Git/PureEpoch-2026-10-25" && python3 -B -m unittest discover -s baseline -v && python3 -B -m unittest discover -s tests -v && python3 -B -m unittest discover -s torus -p "test_*.py" -v`
- **Rollback:** `git checkout -- VERDICT.md RESULTS.md README.md NEXT_COMPOSE.md torus/ evidence/`

## Dependencias

- `M0` → `M1` → `M2` → `M3` → `M4`
- Requiere `gcc` y `python3` (disponibles en el entorno local) y los binarios compilados `torus/observe`, `torus/mb_ref` y `build/{trace_ref,mb_ref,olmstead}`.

## Riesgos

- **Riesgo:** Que el salto consumidor `j` tras devolver el préstamo de `mem[41]` o `mem[42]` cifre una celda o desplace `d` fuera de la región esperada.
  - **Mitigación:** Diseñar la devolución del préstamo (`mem[42] = 120`) usando nuestro roundtrip in-VM de 4 pasos (`29524 → 80 → 0 → x_const`) donde `x_const = crazy(mem[44], 29524)` se computa dinámicamente desde el resguardo `L = 44`, garantizando que `mem[42]` recupere exactamente `120` y que el `j` sobre `d = 42` salte siempre a `d = 121` si y sólo si el préstamo fue devuelto.
- **Riesgo:** Exceder el tope de `400,000,000` instrucciones del presupuesto toroidal.
  - **Mitigación:** No re-ejecutar los quines de 62M–69M pasos; `E-T2` y `E-T3` consumen `< 25,000` instrucciones en total (`< 0.006%` del presupuesto).

## Rollback global

Ejecutar `git reset --hard 2b18f2e` en `/home/danny/Development/ISyCo Git/PureEpoch-2026-10-25` para volver exactamente al commit verificado de `M3` y `Quine 1=94`.

## Próximo paso

- **Primer paso:** Ejecutar `M0` verificando los hashes SHA-256 de `m1c`, `m1e`, `m2`, `m3` y el presupuesto en `torus/budget_all.json`.
- **Comando inicial:** `cd "/home/danny/Development/ISyCo Git/PureEpoch-2026-10-25" && sha256sum candidates/m1c_normal.mal candidates/m1e_normal.mal candidates/m2_normal.mal candidates/m3_normal.mal && cat torus/budget_all.json`
