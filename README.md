# Pure Epoch — 2026-10-25

**Resultado construido:** `candidates/m1c_normal.mal`, 29,526 bytes, ejecuta un checkpoint de una celda lógica, selecciona commit o recuperación mediante un salto Classic sobre el valor calculado, restaura desde el journal y realiza un intento corregido. El mismo archivo cubre cuatro entradas binarias. No restaura el estado físico completo ni implementa dos épocas reutilizables.

SHA-256: `17ff6f326c3205fa92bae9eeeba4c8ecf0229a722c55491e2fa5e0cd4d7b7985`.

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

Se ejecutó `make test` en el clon BolgeForge: 52 unit tests, corpus, comprimidos, cinco quines y 236 comparaciones del espejo. En Autobolge se compilaron `bolge.zig` y `trace_probe.zig` y se ejecutaron 15 tests de anchors, trazas y síntesis. No se ejecutó `make test-rebuild` ni la suite completa de Autobolge. Los errores iniciales de preparación/ruta y binario faltante se conservaron, con corridas corregidas separadas.

Para repetir esas regresiones opcionales: clonar los remotos, hacer checkout de los commits fijados, compilar los dos binarios Zig con `zig build-exe <archivo.zig> -O ReleaseFast -femit-bin=<nombre.exe>` desde `Autobolge/zig`, ejecutar `python3 -B -m pytest -p no:cacheprovider tests/test_anchors.py tests/test_trace.py tests/test_synthesizer.py` desde la raíz Autobolge, y `PYTHONDONTWRITEBYTECODE=1 make test` desde BolgeForge.
