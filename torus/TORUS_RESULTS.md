# Huella toroidal Classic: ejecución y límites

Fecha: 2026-10-25. Todo lo generado está bajo este directorio. No se modificaron los repositorios originales, los artefactos publicados ni el baseline de PureEpoch. Observación del estado Classic; ninguna restauración o corrupción del estado fue ejecutada por el host.

**Resultado:** se confirman 96/96 solapamientos, con separación de huellas heredada de Lutter. Hay celdas accesibles y modificables desde instrucciones Classic fuera de C, pero no se obtuvo un journal controlado ni recuperación con comparación y retry. La captura recibida no reproduce exactamente las cuentas del script actualmente disponible.

## Gates

| Gate | Veredicto y alcance |
|---|---|
| G-T0 Métrica | **DEMONSTRATED** para el script inspeccionado y las cuentas corregidas. m281 fue ejecutado completo con el script original y con C independiente; coinciden todos los opcodes, pasos, footprints y salida. Lutter completo fue medido con el C independiente, contra salida byte-exact del C estricto separado. La captura antigua queda **NOT_DEMONSTRATED** en sus cuentas de D/unión. |
| G-T1 Separación | **DEMONSTRATED**: C∩D tiene 96 direcciones en m281, Lutter y m284. Se exportan y recomputan mediante sets Python. Cada quine sólo tuvo una colisión simultánea c=d: el primer paso. |
| G-T2 Journal accesible | **DEMONSTRATED**: Conforme a la política de exclusión estricta de la celda 53 (`borrow_windows.py` y `runs/dce_borrow_windows.json`), el experimento constructivo `E-T2` (`torus_borrow_experiments.py` y `runs/torus_e_t2_report.json`) demostró préstamo y devolución controlada en la celda `41 ∈ D \ C \ E` (salvaguarda en `43 ∈ D \ C \ E`). Con entradas `0x01` y `0x03` escribe/lee valores en Classic Malbolge estricto, restituye exactamente el byte pre-préstamo `mem[41] == 121` y completa el salto aguas abajo del consumidor (`mb_ref` exit 0, salida `'y'`). El control negativo `no_return` falla al romper el salto del consumidor sobre `mem[41]`. Celda 53 estrictamente intacta (`C=0, R=0, W=0, E=0`). |
| G-T3 Recuperación | **DEMONSTRATED**: Experimento toroidal constructivo `E-T3` completado en `torus/programs/torus_e_t3_normal.mal` (`runs/torus_e_t3_report.json`). Toma prestada la celda `J = 42 ∈ D \ C \ E` (pre-préstamo 120), salvaguarda en `L = 44 ∈ D \ C \ E`, inicializa `S = 40 ∈ D \ C \ E`, guarda el checkpoint en `J = 42`, bifurca in-band según candidato, corrompe `mem[40]` en ruta de fallo, reconstruye `S` desde `J = 42`, reintenta la transición y devuelve el préstamo `mem[42] == 120` antes del salto del consumidor. Paridad exacta C/Python (`Python`, `mb_ref`, `observe`, `trace_ref`, `olmstead`) para las 4 combinaciones `(initial, cand) ∈ {1, 3}²` con salida `'V'` / `'R'`, y los 4 controles negativos (`no_loan_return`, `no_restore`, `corrupt_journal`, `force_retry_failure`) falsados. Celda 53 intacta (`C=0, R=0, W=0, E=0`). |

## Procedencia y oráculos

Se leyeron completos `/home/danny/.codex/RTK.md`, el addendum, y `/tmp/opencode/torus/mb_fingerprint.py` antes de ejecutarlo. Se copió el script sin cambios a `vendor/mb_fingerprint.py`, SHA256 `de90cfcbba7986341b259e772d2385f4ab36d879f76f5dabc5102350d0749214`.

Fuentes locales: BolgeForge `454ab61e61ef94745b2e7178205cf0e56f41010c`; copia aislada remota `eef65c83a2885b6e3d66c26fede9931dfdba5e40`. Las cuatro fuentes utilizadas tienen el mismo hash en ambas copias. `manifest.json` fija rutas, hashes de fuentes e intérpretes; `binary_hashes.json`, los binarios compilados. No se ejecutó el sintetizador ni se escribió en los repositorios.

`vendor/mb_ref.c` se copió sin cambios y compiló con GCC O3. Es el oráculo Classic estricto: mínimo dos celdas; ASCII33..126, loader-opcodes válidos; memoria de59049; EOF59048; salto cifra el destino; PC o destino de cifrado no imprimible es error. El observador `observe.c` implementa la operación crazy por trits, independientemente de la tabla base9 del oráculo. Los quines m281/Lutter se ejecutaron también en el C estricto separado: salida idéntica a todos los bytes del archivo, incluidos blancos. m284 es byte-exact con el observador estricto; no se gastó una segunda ejecución completa de m284 en mb_ref.

`synthesize.py` líneas43..94 toma `clean_lutter`, su prefijo y loop slice, y reubica objetivos mediante `Delta=94*(314-m)`. Por tanto m281/m284/Lutter no constituyen tres diseños independientes. Cat es otro programa Classic del corpus (también atribuido a Lutter), no evidencia de independencia de autor. `short.mal` (`DP`) y `journal_access_candidate.mal` (`(&<N`) fueron construidos aquí y son loader-valid.

## Cuentas completas

Los pasos incluyen la instrucción HALT. C y D son posiciones al inicio de cada instrucción, también HALT. Complemento relativo a las59049 direcciones.

| Programa / entrada | Pasos | C | D | C∩D | C∪D | Complemento |
|---|---:|---:|---:|---:|---:|---:|
| m281 / EOF | 62,239,852 | 25,554 | 26,800 | 96 | 52,258 | 6,791 |
| Lutter / EOF | 69,547,437 | 27,293 | 29,901 | 96 | 57,098 | 1,951 |
| m284 / EOF | 62,902,924 | 24,090 | 27,082 | 96 | 51,076 | 7,973 |
| Cat / `abc\n` | 10,896 | 8,941 | 207 | 15 | 9,133 | 49,916 |
| Cat / EOF | 9,268 | 8,938 | 207 | 14 | 9,131 | 49,918 |
| corto `DP` | 2 | 2 | 2 | 2 | 2 | 59,047 |
| acceso `(&<N` | 4 | 4 | 4 | 1 | 7 | 59,042 |

La captura decía pasos m28162,239,851/Lutter69,547,436: esos números son exactamente los eventos de cifrado. HALT no cifra. También omitía una dirección C, coherente con excluir HALT. **Esto no explica D**: el D de HALT ya se visitó mucho antes. Excluir HALT daría m281 C25,553/D26,800/unión52,257 y Lutter C27,292/D29,901/unión57,097. El D y la unidad restante de unión de la captura siguen sin explicación verificable; no se inventa una versión anterior del script para resolverlo.

Los sets completos `sets/{m281,lutter,m284}/{C,D,R,W,E,intersection,union,complement,D_minus_C}.txt` se derivan del CSV completo, con álgebra de conjuntos independiente del script original. Las intersecciones no son iguales:49 direcciones son fijas y47 se trasladan exactamente por3102 de m281 a Lutter y2820 de m284 a Lutter. Las49 fijas son `{0,99,117..161,59047,59048}`. Esta relación ejecutada respalda **INFERRED: herencia estructural**, no universalidad de96.

## Visitar, leer, escribir, ejecutar, cifrar

R cuenta operandos reales de `i`, `j`, `*`, `p`; no confunde la presencia del registro D durante un NOP con una lectura. C es fetch/ejecución; W son asignaciones de `*`/`p`, incluso si preservan el valor; E son asignaciones del cifrado, incluso si el byte resultante coincide. La inicialización del loader se excluye de W/E.

| Programa | R únicas | W únicas | E únicas | W eventos | E eventos | R∩W fuera de C |
|---|---:|---:|---:|---:|---:|---:|
| m281 | 26,773 | 26,747 | 25,554 | 1,461,006 | 62,239,851 | 26,656 |
| Lutter | 29,868 | 29,848 | 27,293 | 1,633,967 | 69,547,436 | 29,757 |
| m284 | 27,055 | 27,029 | 24,090 | 1,476,376 | 62,902,923 | 26,938 |

**C y E tienen igual cardinalidad en estos quines pero no son el mismo set.** En cada uno hay22 posiciones E\C y22 C\E, porque `i` cifra su destino antes de incrementar C. En m28113 celdas D\C se cifran; sólo26653 de las26656 celdas escritas fuera de C también están fuera de E. Celda53 tiene E=0. Una región sólo fuera de C puede sufrir cifrado indirecto y no es automáticamente un journal.

## Toro, delta, tramos, retornos y simetría

Se observó `(c,d)` módulo59049; delta propio es `(c-d) mod59049`. El script usa el signo contrario `(d-c) mod59049`: no cambia cuándo se rompe un tramo, pero sí las etiquetas. `segments.csv` exporta histograma completo de longitudes en **transiciones**, con un segmento terminal de longitud0. La suma de longitudes por frecuencias es `steps-1`; el número de segmentos es `1+break4+break40`. Los breaks cuentan cambios efectivos de delta, no todas las instrucciones `i/j`.

| Programa | breaks i | breaks j | Segmentos | Mayor tramo / transiciones | delta distintos | fracción diagonal |
|---|---:|---:|---:|---:|---:|---:|
| m281 | 21,389,393 | 4,825,305 | 26,214,699 | 24 | 32,034 | .578811675195 |
| Lutter | 23,901,063 | 5,391,451 | 29,292,515 | 22 | 35,519 | .578812444231 |
| m284 | 21,617,925 | 4,876,504 | 26,494,430 | 24 | 32,073 | .578804476561 |

La fórmula exacta para estas ejecuciones con HALT es `(steps-1-break4-break40)/steps`: HALT no aporta transición diagonal. La fórmula recibida sin `-1` sólo coincide al redondear a seis decimales. Tampoco basta restar todos los opcodes j: m281 ejecuta5,934,693 j, pero sólo4,825,305 cambian delta. La coincidencia de seis decimales m281/Lutter es descriptiva y dependiente de procedencia.

Wraps del incremento C/D: m281528280/3, Lutter590320/3, m284533920/3. No cuentan un salto como wrap aritmético. Crossings exactos c=d:1/1/1. Pares proyectados distintos:132515/146662/132179; revisitas del par:62107337/69400775/62770745. Se computaron con bitmap exacto de59049² bits, no sólo sampling. **Un par repetido no implica repetición de a, memoria, entrada o salida**; no se verificó ciclo de estado completo ni autorreparación.

El detector original de traslación es defectuoso: convierte un vector de59049 **bytes** en un entero y luego lo rota/enmascara como si tuviera59049 **bits**. Cuando hay un C≥7382, el entero contiene bits fuera de la máscara y `(sh & V)==V` es imposible. Los tres quines visitan C59048, por lo que ese cero es forzoso. Un test con nueve posiciones todas visitadas reproduce falso cero, aunque sus ocho desplazamientos no nulos son simetrías. El detector corregido busca el período cíclico mínimo entre los divisores3^k de59049: período59049 y cero desplazamientos no triviales en los footprints C reales. Este resultado corregido sólo concierne al set C unidimensional; no prueba simetría/ausencia de simetría del camino bidimensional completo.

## Acceso al journal y falsación

Celda53 en m281 está fuera de C y E durante la ejecución completa. D la visita13330 veces, R1143 y W3. La cronología Python independiente completa de30000 pasos coincide bit a bit con el hash de transición C del mismo prefijo: `329c54ba64fcca289b0d95e8e496072f2b6e82251ac561f69a44b0bfdcfd9baa`.

Eventos nativos sobre53 en ese prefijo:

| Paso | C | Instrucción | Antes → después |
|---|---:|---|---|
| 18 | 132 | p | 81 → 29524 |
| 20575 | 20689 | p | 29524 → 29524 |
| 20605 | 20719 | p | 29524 → 26318 |

Entrada inicial secuencial: después del paso17 C132/D53; salida después del18 C133/D54. En la ejecución completa hay278 aristas observadas de redirección j hacia D53, exportadas en `journal53_reachability.json`; la salida j desde53 va a26319,1140 veces, empezando en56439 con C26310. Esto muestra alcanzabilidad real. También revela uso existente:53 almacena una dirección viva del loop. La hipótesis **“53 es una reserva intacta aprovechable sin cambiar el contrato” queda DESTROYED** por las escrituras, especialmente20605. No se afirma que sea imposible reasignarla en otro programa.

Después del paso1358 se observó el handoff `(a,c,d)=(29524,1473,149)`. Los saltos/redirecciones y las entradas/salidas de53 son fronteras concretas para investigar una futura síntesis. El complemento incluye celdas3..22 al inicio, pero no se observó acceso D a ellas: su mera falta de visitas no aporta una ruta nativa para un journal. Hay21 celdas D-only leídas sin W/E en m281; eso demuestra lectura, no escritura controlada.

Se produjo `programs/journal_access_candidate.mal`, exactamente cuatro bytes `(&<N`, validado por el C estricto separado y por el observador. Su **traza completa de cuatro instrucciones** está en `runs/journal_access_candidate.samples.csv`:

1. j en C0 cambia D a41 y cifra C0.
2. * en C1/D41 modifica78→26, a=26; después D42.
3. p en C2/D42 modifica29545→29543; después D43.
4. v en C3/D43 termina.

41/42 están fuera de C y E. Esto satisface el umbral literal de leer/modificar desde Classic sin host; no implementa almacenamiento de un checkpoint arbitrario, comparación ni restore.

**Experimento constructivo E-T3 (ejecutado y verificado):** Siguiendo las directrices de `NEXT_COMPOSE.md` y excluyendo estrictamente la celda 53, se implementó y ejecutó `torus/torus_borrow_experiments.py` con los artefactos `torus/programs/torus_e_t3_{normal,no_loan_return,no_restore,corrupt_journal,force_retry_failure}.mal`. El programa toma prestada la celda `J = 42 ∈ D \ C \ E` (pre-préstamo 120), salvaguarda en `L = 44 ∈ D \ C \ E`, checkpoint de `S = 40 ∈ D \ C \ E`, bifurcación in-band sobre celda 38, corrupción controlada de `S`, restauración de `S` desde `J = 42`, reintento de transición a estado de commit (`mem[40]=29526`/'V' o `29522`/'R') y restitución exacta de `mem[42] == 120` antes del salto del consumidor. Los cuatro caminos positivos pasan con paridad exacta en cinco oráculos (`Python`, `mb_ref`, `observe`, `trace_ref`, `olmstead`) y los cuatro controles negativos son rechazados. Reporte completo en `runs/torus_e_t3_report.json`.

## Evidencia, ejecución y límites

`runs/*.sets.csv` cubre todas las59049 direcciones; `counts.csv` da cuentas y primeros/últimos pasos; `d_edges.csv` conserva todas las aristas distintas observadas de j y sus frecuencias; `delta.csv` e histogramas por opcode son completos. `first_events.csv` conserva las primeras dos lecturas y primeras dos escrituras de cada dirección. No es una cronología completa de millones de escrituras. `samples.csv` conserva primeros256 pasos, cada100000 y HALT. Los eventos de todos los pasos se incorporan a SHA256 sin almacenar el stream gigante. El prefijo independiente de30000 instrucciones y el fixture de cuatro instrucciones sí tienen cronología completa. Los hashes no reemplazan una traza completa recuperable: permiten reejecutar y comparar exactamente las observaciones declaradas.

Encoding de hash: por instrucción un registro little-endian `<Q12H`,32 bytes: paso1-based; a anterior, c anterior, d anterior, celda de código, opcode numérico, operando mem[d] anterior, valor tras escritura directa, dirección de cifrado, byte antes de cifrar, byte después, c siguiente, d siguiente.65535 indica campo ausente. HALT conserva c/d. `event_sha256` está en cada JSON. No se almacenan snapshots de memoria completa ni se afirma un hash completo del estado VM.

El script original no es un oráculo estricto: carece de validación del loader, aplica op numérica aunque el PC no sea imprimible, omite cifrado inválido y usa a=-1 para EOF. Los quines no leen entrada, así que esa diferencia no afectó m281. Cat se comparó también con EOF en ambos motores; las cuentas de esa entrada coinciden, aunque la representación de a para EOF difiere. No extrapolar conformidad general del script a programas distintos. No se ejecutó el script Python original sobre Lutter completo: sus70M pasos adicionales excederían el presupuesto conjunto. Su huella se verificó mediante el observador C independiente y su salida con el C estricto separado.

Reproducción desde este directorio:

```bash
python3 run.py
python3 journal_replay.py > runs/journal_replay.stdout 2> runs/journal_replay.stderr
python3 analyze.py > runs/analysis.stdout 2> runs/analysis.stderr
python3 -m unittest -v test_evidence.py > runs/tests.stdout 2> runs/tests.stderr
python3 hash_all.py
```

`run.py` conserva resultados existentes: para una repetición nueva usar una copia nueva de este directorio sin sus `*.command.json`; cada comando generado incluye presupuesto explícito y timeout120s. El inventario `SHA256SUMS.txt` debe generarse al final. No lanzar de nuevo los largos intérpretes sólo para verificar hashes.

Presupuesto total asignado, incluidos prefijos y fallo inicial: **395,230,192 pasos**, por debajo de400M; instrucciones completadas contabilizadas388,829,050. `budget_all.json` da el total; `budget.json` cubre las órdenes del runner. Ningún comando hijo excedió120s; el más largo, Python original m281,22.315s de pared. Observadores quines2.16–2.38s; C estricto separado0.14–0.16s en este host; no se presenta como benchmark portátil.

Se conservan dos fallos: una primera implementación Python omitió la entrada crazy(0,1), falló tras2082 transiciones y fue corregida antes de aceptar evidencia; source/traza fallidos están en `vendor/journal_replay_failed_v1.py` y `runs/journal_prefix_failed_v1.csv`. La hipótesis falsa de que HALT agregaba también un D nuevo provocó una aserción de análisis y un test dependiente sin archivo, preservados en `runs/analysis_failed_v1.json` y `runs/tests_failed_v1.stderr`. Las correcciones pasan seis tests, incluida la tabla crazy completa por posición ternaria, hash completo del fixture, destino de cifrado de saltos y falso cero del detector original. El compilador emitió advertencias de indentación del observador, preservadas; no hubo error de compilación.
