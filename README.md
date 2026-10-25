# Pure Epoch — 2026-10-25

**Resultado construido:**
- `candidates/m1c_normal.mal` (29,526 bytes, SHA-256 `17ff6f326c3205fa92bae9eeeba4c8ecf0229a722c55491e2fa5e0cd4d7b7985`): baseline M1 preservado intacto.
- `candidates/m1e_normal.mal` (29,531 bytes, SHA-256 `dc9ed4d81ef7200d5b5e1dc2c3f161bd4b01be39b58ca43bc87db410461e9f53`): M1e con commit dependiente del dato recuperado (`initial=1` → `mem[36]=29526, stdout=V`; `initial=3` → `mem[36]=29522, stdout=R`), rearme in-VM de trampolines, contador interno de intentos (`mem[64]`) y rechazo/HALT explícito ante fallo repetido (`m1e_force_retry_failure.mal`), conservando `STALL` como control negativo separado (`m1e_force_retry_stall.mal`).
- `candidates/m2_normal.mal` (55,770 bytes, SHA-256 `3ec16fd60b5298a83f30dddf340bdc962a6fe981c4a05379c446bcb92a8748d6`): composición M2 de **dos épocas completas en un único proceso Classic Malbolge** (`stdin = [initial, cand_1, cand_2]`), verificada en las 8 combinaciones (`válido/válido`, `inválido/válido`, `válido/inválido`, `inválido/inválido` para `initial ∈ {1, 3}`) y sus controles negativos.
- `candidates/m3_normal.mal` (55,770 bytes, SHA-256 `7f95770a4786132dd148ccbf4af328d6e62be68ed6732754b2f50c5019114689`): composición M3 de **tres épocas completas con Roundtrip + Rollback en un único proceso Classic Malbolge** (`stdin = [initial, cand_1, cand_2, cand_3]`), reutilizando el núcleo de control `1=94` (`0..93`) mediante doble rearme in-VM de trampolines, rotación de portales, enmascaramiento de `EOF = 59048` (`mem[53] = 0` pre-lectura) y validación mediante campaña offline de 64 propuestas acotadas de Autobolge (`evidence/m3-proposals.json`).
- `candidates/quine94_ceiling_probe.mal` (94 bytes, `1=94`) y `evidence/quine-94-analysis.json`: demostración algebraica y empírica de la escalera `4=376`, `2=188`, `1=94` (`XLAT2` sin puntos fijos de periodo 1, bloqueo de `F`/`J` en `78/94` celdas y `0/94` solapamientos bajo el loader estricto, techo acíclico `93 < 94`) y teorema del Punto Fijo Sintético de Periodo-1 (`752/752` pares verificados) vía roundtrip `crazy` de 4 pasos.
- `torus/programs/torus_borrow_e_t2.mal` (677 bytes) y `torus/runs/torus_e_t2_report.json`: demostración constructiva M2 (G-T2 / `E-T2`) de préstamo y devolución controlada en `41 ∈ D \ C \ E` (salvaguarda en `43 ∈ D \ C \ E`), con escritura/lectura para `0x01` y `0x03`, restitución exacta `mem[41] == 121` verificada por salto consumidor y control `no_return` falsado (`INVALID_ENCRYPTION`). Celda 53 intacta (`C=0, R=0, W=0, E=0`).
- `torus/programs/torus_e_t3_normal.mal` (29,842 bytes) y `torus/runs/torus_e_t3_report.json`: demostración constructiva M3 (G-T3 / `E-T3`) de préstamo de journal `J = 42 ∈ D \ C \ E` (pre-préstamo 120), salvaguarda en `L = 44 ∈ D \ C \ E`, estado `S = 40 ∈ D \ C \ E`, checkpoint, bifurcación in-band según candidato, recuperación con rollback, restore y retry, y restitución exacta de `mem[42] == 120` antes del salto del consumidor aguas abajo. Paridad exacta en 5 oráculos (`Python`, `mb_ref`, `observe`, `trace_ref`, `olmstead`) para las 4 combinaciones `(initial, cand) ∈ {1, 3}²`, y los 4 controles negativos (`no_loan_return`, `no_restore`, `corrupt_journal`, `force_retry_failure`) falsados. Celda 53 intacta.

Ver [RESULTS.md](RESULTS.md), [VERDICT.md](VERDICT.md), [NEXT_COMPOSE.md](NEXT_COMPOSE.md) y, por separado, [torus/TORUS_RESULTS.md](torus/TORUS_RESULTS.md).

## Reproducir sin red

Requiere Python 3.10+ y gcc. Los módulos upstream necesarios están copiados sin modificaciones en `vendor/`; no hace falta instalar paquetes Python ni ejecutar una VM modificada.

Desde este directorio:

```bash
python3 -B -m unittest discover -s baseline -v
python3 -B -m unittest discover -s tests -v
python3 -B -m tools.collect_evidence
```

El último comando reconstruye **sólo los candidatos experimentales de este laboratorio**, ejecuta cada caso desde el loader y actualiza `evidence/`. Los baselines y repos originales quedan fuera de sus destinos de escritura. `evidence/collection.txt` conserva la campaña original; `evidence/measurements.json` contiene sus 19 ejecuciones.

Ejecutar el artefacto en el C estricto sin instrumentación:

```bash
gcc -O2 vendor/mb_ref.c -o /tmp/pure-epoch-mb-ref
printf '\003\003' | /tmp/pure-epoch-mb-ref candidates/m1c_normal.mal 5000
```

Imprime un byte `S` y HALT. Las entradas son **bytes 0x01/0x03**, no los caracteres ASCII `1`/`3`. La tabla de entradas admitidas es `01 01`, `01 03`, `03 01`, `03 03`. Primer byte: selector del estado previo; segundo: operando del intento candidato. Las trazas distinguen rutas aunque las cuatro salidas sean `S`.

## Archivos y fronteras

- `baseline/`: los siete archivos M0 originales, byte por byte; Truth Machine de Weird Glyphs, CC BY-SA 4.0. No es un programa original de este experimento.
- `candidates/`: M1a reversible de 98 bytes, M1b checkpoint de 308 bytes, M1c/d condicional de 29,526 bytes y controles negativos. Metadatos adyacentes describen direcciones reales.
- `tools/build_candidates.py`: ensamblaje **offline**. `observe.py`: observación desde cero. `trace_ref.c`: instrumentación aditiva del C, sin writeback. `oracles.py`: procesos independientes.
- `evidence/traces/`: trazas completas C/Python de todos los casos pequeños, memoria final completa u16 little endian, stdout y comparaciones. `step` comienza en cero; `fetched_instructions` incluye HALT.
- `vendor/`: C estricto sin cambios, intérprete original Olmstead sin cambios y módulos Autobolge sin cambios, con avisos de licencia.
- `torus/`: campaña separada del addendum, conjuntos completos de acceso, métricas, fallos, pruebas y cronología muestreada declarada. No es una traza completa de cientos de millones de instrucciones.

La recuperación lógica promete la restauración de `mem[36]` en una fase concreta, conservación del journal y continuación al commit. Código autocifrado, registros, constantes auxiliares y cursores evolucionan legalmente. Un output correcto con una restauración ausente **no** satisface el contrato de fases.

## Upstream inspeccionado

| Fuente | Commit |
|---|---|
| Autobolge local original | `96733704fd54504e6864d1ad733bb1497d53da1f` |
| BolgeForge local original | `454ab61e61ef94745b2e7178205cf0e56f41010c` |
| Autobolge remoto clonado / módulos vendor | `ac0de274cee079ed4c85e4f018754a538c952a9e` |
| BolgeForge remoto clonado / suite de regresión | `eef65c83a2885b6e3d66c26fede9931dfdba5e40` |

Los checkouts originales tenían trabajo no seguido; se registró en `evidence/initial_state.json`. El laboratorio tiene Git propio, rama `codex/pure-epoch-m1`. `sources/` contiene clones de inspección ignorados por Git. El ZIP inicial no estaba disponible en las ubicaciones suministradas; se preservó la carpeta extraída completa ya proporcionada.

Durante la campaña, el checkout original de Autobolge avanzó por trabajo concurrente hasta `dcfcd6fff0e40001ae686432d60a77434834e0b6` y quedó limpio. No se revirtió ni se mezcló ese avance con las revisiones fijadas del experimento. `evidence/final_source_integrity.json` registra la diferencia; BolgeForge original y los siete archivos M0 conservan sus bytes/estado iniciales.

Se ejecutó `make test` en el clon BolgeForge: 52 unit tests, corpus, comprimidos, cinco quines y 236 comparaciones del espejo. En Autobolge se compilaron `bolge.zig` y `trace_probe.zig` y se ejecutaron 15 tests de anchors, trazas y síntesis. No se ejecutó `make test-rebuild` ni la suite completa de Autobolge. Los errores iniciales de preparación/ruta y binario faltante se conservaron, con corridas corregidas separadas.

Para repetir esas regresiones opcionales: clonar los remotos, hacer checkout de los commits fijados, compilar los dos binarios Zig con `zig build-exe <archivo.zig> -O ReleaseFast -femit-bin=<nombre.exe>` desde `Autobolge/zig`, ejecutar `python3 -B -m pytest -p no:cacheprovider tests/test_anchors.py tests/test_trace.py tests/test_synthesizer.py` desde la raíz Autobolge, y `PYTHONDONTWRITEBYTECODE=1 make test` desde BolgeForge.
