# COMPOSE PARA SOL — AUTOBOLGE × BOLGEFORGE
## Pure Epoch / Recuperación autónoma en Malbolge Classic
**Fecha:** 2026-10-25  
**Tipo:** experimento de investigación y construcción incremental  
**Prioridad:** evidencia reproducible > narrativa > velocidad  
**Entrada:** ZIP `Autobolge_BolgeForge_PureEpoch_M0.zip` adjunto + repositorios `DannyBaanks/Autobolge` y `DannyBaanks/BolgeForge`.

### 0. Misión

Sol: lleva este experimento lo más lejos posible **sin fingir que hemos demostrado algo que no hemos demostrado**. Quiero investigar si un programa escrito en **Malbolge Classic puro** puede:

1. conservar internamente un estado útil;
2. ejecutar una modificación de ese estado;
3. identificar por sí mismo una condición inválida;
4. restaurar el estado necesario y reintentar una transición;
5. eventualmente usar ese mecanismo para encadenar *épocas* de ejecución con continuidad lógica.

La ambición posterior es acoplar el sintetizador de Autobolge con las técnicas constructivas de BolgeForge. **No confundas el objetivo experimental de rollback puro con la propuesta híbrida de JIT de Argon**: una VM que guarda y restaura memoria desde Zig/Python es otro resultado, útil como control, pero **no demuestra autonomía interna de Malbolge**.

Trabaja sobre las reglas originales del lenguaje; no inventes opcodes, no cambies el intérprete para favorecer el resultado, no uses un proceso padre que reescriba el estado en caliente ni sustituyas la salida de Malbolge por la de un emulador.

### 1. Material real y arranque

Abre primero el ZIP y lee **todos** estos archivos:
- `README.md`
- `COMPOSE_M1.md`
- `ATTRIBUTION.md`
- `report.json`
- `epoch_probe.py`
- `test_epoch_probe.py`
- `truth_machine_classic_90b.mal`

Verifica el baseline exacto, desde el directorio `malbolge_epoch_lab/`:

```bash
python3 -m unittest -v test_epoch_probe.py
python3 epoch_probe.py truth_machine_classic_90b.mal > report-reproduced.json
```

**Baseline local reproducido antes de enviarte este compose:** 5/5 tests PASS; la Truth Machine de 90 bytes muestra un ciclo de 408 instrucciones entre los pasos 1000 y 1408, con 17 bytes `1` por ciclo y coincidencia del estado `(a,c,d,memoria completa,input_cursor)`. En la observación aparecen 59 celdas tocadas, 4 modificadas en el ciclo que regresan a sus valores anteriores y una región observada intacta de 58,960 celdas. Un control negativo inyectó una corrupción en una copia de prueba y **Malbolge no la reparó**.

**Eso demuestra repetición del estado, no checkpoint ni rollback condicional.** La memoria no tocada **no** equivale a memoria protegida.

Verifica las implementaciones actuales de ambos repositorios (no confíes ciegamente en un README si el código o el árbol han cambiado):

- `Autobolge/ROADMAP.md`, `AUTOBOLGE_PROVENANCE.md`, `relational/anchors.py`, `relational/classic.py`, `relational/trace.py`, `relational/synthesizer.py`, `zig/vm.zig`, tests de anchors y síntesis.
- `BolgeForge/README.md`, `GUIA.md`, `docs/CLAIMS.md`, `oracle/mb_ref.c`, `tools/prove_truth_machine.py`, `tools/verify_handoff_state.py`, su suite de pruebas y los artefactos Classic publicados.

`Autobolge` ya documenta `EpochAnchorV1`, traza, replay, memoria causal y oráculos v2: **son infraestructura de observación/continuación externa**, no una implementación de recuperación autónoma dentro de Malbolge. `BolgeForge` dispone de oráculos estrictos y programas certificados que sirven como controles.

Respeta diferencias de semántica y EOF entre la VM Classic de Autobolge y los oráculos estrictos de BolgeForge. Fija el commit de cada fuente y declara cuál es el oráculo para cada afirmación. Si las semánticas no coinciden, no falsifiques la paridad: informa exactamente dónde difieren.

**Procedencia:** la Truth Machine de 90 bytes es obra de *Weird Glyphs*, CC BY-SA 4.0; no la atribuyas a nuestro laboratorio ni la relices sin avisos.

### 2. Frontera no negociable: MALBOLGE PURO

**Permitido fuera del runtime:** ensamblar y sintetizar programas `.mal`, buscar candidatos, compilar oráculos, comparar trazas, mirar memoria, medir, hashear, generar pruebas, calcular resultados esperados.

**Prohibido como evidencia de recuperación autónoma:** parchear memoria desde el host, restaurar snapshots con Python/Zig/C, reiniciar el proceso a mitad de una época, inyectar un programa nuevo después del arranque, ofrecer instrucciones privilegiadas, sobrescribir outputs para simular éxito.

El resultado principal debe ser **un archivo `.mal` que el loader Classic estricto acepte y que, ejecutado desde cero, lleve a cabo la transición y la recuperación mediante instrucciones Malbolge**.

Distinciones explícitas:
- `CYCLE`: estado periódico exacto sin gestión de errores.
- `REVERSIBLE`: deshacer una mutación predecible, sin detección de fallo.
- `CHECKPOINT`: guardar dentro de la cinta un valor/estado para recuperarlo después.
- `ROLLBACK`: ante condición fallida, un branch interno recupera la condición previa relevante.
- `RETRY`: tras rollback, el programa prueba otra transición y alcanza un estado válido.
- `EPOCH`: múltiples fases con invariantes demostrables y continuidad causal.
- `JIT/HYBRID`: el host sintetiza algo durante la ejecución; etiquetar aparte, **no** como Pure Malbolge.

### 3. Experimentos escalonados

**M1a — Mutación reversible mínima.** Produce un `.mal` estricto que modifique una celda seleccionada y la devuelva a su valor anterior mientras continúa el flujo. Inspecciona dirección, valor antes/después, instrucciones reales y dependencia de `c`, `d`, `a`. Que una transformación coincida periódicamente no implica que el programa decidiera reparar algo. Si lo único logrado es un ciclo, etiquétalo `CYCLE`, no `ROLLBACK`.

**M1b — Estado guardado *dentro* del programa.** Construye una rutina que preserve el valor anterior de una celda útil en otra representación in-band antes de modificarla. Demuestra con trazas que la restauración usa esa representación y no una coincidencia accidental del ciclo o una constante escrita por el constructor. Usa valores de prueba distintos cuando sea viable.

**M1c — Detección y recuperación condicional.** Introduce por entrada ordinaria o elección interna un caso válido y otro inválido. El programa debe tomar dos rutas distintas: `commit` cuando cumpla una invariante definida; `restore` cuando falle. Muestra dónde y cómo toma la decisión con opcodes Classic reales. Si la única distinción está en un script Python, FAIL.

**M1d — Reintento real.** Después de `restore`, consigue que cambie una condición pertinente y vuelva a ejecutar la transición sin quedar atrapado en el mismo fallo. Acota intentos; documenta qué ocurre si se agota el presupuesto. No llames `RETRY` a volver a imprimir el mismo byte.

**M2 — Continuidad entre dos épocas.** Sólo si M1c/M1d tienen PASS sólido. Construye una secuencia completa dentro de **una sola ejecución Classic**, con estado lógico preservado entre épocas y una transición defectuosa recuperable. Mide memoria reservada realmente usada, journal, caminos de control y coste. Compara contra la alternativa externa/híbrida usando la misma tarea, sin mezclar claims.

**M3 — Integración Autobolge × BolgeForge.** Usa Autobolge para proponer o guiar candidatos mediante trazas/anchors y BolgeForge para montaje y verificación estricta. La síntesis **puede ser offline** para producir el `.mal` autónomo. Conecta por adaptadores mínimos; no reescribas los núcleos ni rompas artefactos publicados. Un ciclo `Synth → Verify → Artifact` offline **no prueba** JIT ni autosíntesis runtime.

No es obligatorio terminar todos los hitos. Prioriza una demostración pequeña e incontestable sobre un sistema ambicioso que sólo funciona bajo un intérprete permisivo.

### 4. Pruebas que pueden destruir la hipótesis

Ejecuta, según aplique:
1. Mismo archivo `.mal`, misma entrada, misma traza e invariantes en oráculos independientes.
2. Caso válido vs caso inválido con **ramas internas distintas**.
3. Desactivar/alterar el branch de restauración: el control debe fallar de una forma interpretable.
4. Alterar el journal interno o valor guardado: comprobar si la restauración depende causalmente de él.
5. Dos valores iniciales diferentes: detectar si la «restauración» estaba hardcodeada.
6. Falta de ruta de retorno, reintento agotado, límite de pasos y HALT prematuro.
7. Comparar el estado relevante de la máquina; no aceptar sólo igualdad de salida. La igualdad completa de memoria es necesaria únicamente si el claim exige *rollback exacto del estado físico completo*: una recuperación **lógica** puede dejar mutaciones legítimas en código, journal y controles, pero debe demostrar explícitamente su contrato de equivalencia.
8. Salida y otros efectos: los bytes ya emitidos no se des-emiten. No reclamar transacción atómica si no hay barrera de commit o protocolo interno que la respalde.

**Control de falsación importante:** intenta construir un candidato que emita el output correcto pero tenga un estado final incorrecto; el verificador debe rechazarlo para cualquier claim de estado.

### 5. Calidad, presupuesto y seguridad del trabajo

- Desarrolla en una rama aislada o laboratorio nuevo. No sobreescribas `master/main`, artefactos certificados ni reportes históricos.
- Registra estado inicial (`git status`, commits, versiones, hashes); detecta cambios ajenos antes de editar.
- No uses `--force`, no borres trabajos previos; reporta comandos destructivos antes de ejecutarlos.
- Primero reproducciones pequeñas y presupuestos cerrados. Evita búsquedas exhaustivas multimillonarias sin evidencia de que son necesarias.
- Ejecuta los tests pertinentes de ambos repos y controla regresiones. Nunca describas un test que no corriste como PASS.
- Si no puedes demostrar el siguiente gate en un presupuesto razonable, detén esa rama de exploración, conserva el mejor contraejemplo y registra el límite. Sigue con un subproblema menor sólo si ofrece información nueva.
- Ante divergencia de EOF, loader o VM, produce reproducción mínima: bytes fuente, entrada, pasos, estado divergente y versión exacta.

### 6. Entregables obligatorios

Deja un directorio fechado o rama de experimento que contenga:

```text
pure_epoch/
  README.md                  # ejecución + alcance exacto
  baseline/                  # M0, hashes y procedencia sin alterarlos
  candidates/                # fuentes .mal y procedencia de cada una
  tools/                     # sólo ensamblaje y observación
  tests/                     # positivos, negativos, oráculos
  evidence/
    manifest.json            # commits, semántica, hashes, entorno
    traces/                  # trazas reproducibles
    measurements.json        # memoria, tiempo, pasos, outputs
    failures.md              # hipótesis fallidas y límites
  RESULTS.md                 # hechos separados de interpretaciones
  VERDICT.md                 # clasificación por claim
  NEXT_COMPOSE.md            # siguiente experimento si procede
```

Estructura sugerida; adáptala al repositorio existente, sin inventar rutas ni reportarlas como creadas antes de crearlas.

Clasifica **cada afirmación** como `DEMONSTRATED`, `INFERRED`, `NOT_DEMONSTRATED` o `DESTROYED` (puedes mapear los estados `REFUTED/RETIRED` de BolgeForge sin modificar su significado). Un gate fallido vale como resultado científico: deja el artefacto y los datos crudos.

En tu informe final quiero ver:
- Qué se construyó realmente y en qué repo/rama/commit.
- Comandos exactos ejecutados y resultados de prueba.
- Una tabla `CLAIM | EVIDENCE | VERDICT | LIMIT`.
- Primer opcode y punto de traza donde aparece la restauración, si existe.
- Qué dependió de herramientas externas y qué ocurrió en Malbolge puro.
- Próximo experimento que más información aportaría, incluso si M1 no pasa.
- Si procede, PR en borrador con trazabilidad; **no hagas merge automático**.

### 7. Criterio de éxito real

**Éxito mínimo:** una rutina *Malbolge puro* con estado interno conservado y una reparación condicionada por un fallo controlado, verificada contra controles negativos y un oráculo estricto independiente.

**Éxito extendido:** recuperación + retry + continuidad por dos épocas dentro de un único proceso.

**No éxito:** sólo un snapshot externo, un ciclo conocido de Truth Machine, una nueva impresión de texto, un output correcto con memoria causal distinta, un emulador permisivo, o una VDF/criptografía reclamada sin pruebas específicas.

Trabaja hasta el mejor hito demostrable que consigas sin relajar la frontera. Si fracasa, explica **por qué** y deja una falsación reproducible.

**No me vendas milagros: enséñame el `.mal`, el opcode, la traza y el control negativo.**

— Danny / ISyCo