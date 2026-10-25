# Fallos, controles y límites preservados

## Hipótesis destruidas por controles ejecutados

- M0 como reparación: corrupción negativa persiste; `baseline/report.json` y reproducción.
- Nueve rotaciones restauran el dato37: `m1a_rot9_negative` deja111.
- Checkpoint sin save: M1b deja T0/J29524, con HALT; no es recuperación.
- Checkpoint con journal rotado: M1b deja T9841/J19683; dependencia causal confirmada.
- Output prueba memoria: impostor M1b emite S y deja T9841.
- Output y T final prueban fase restore: M1c no_restore emite S y deja T29523/J3; el gate lo rechaza porque no restauró el previo29521.
- Journal innecesario para la fase: M1c no_save/corrupt_journal llegan a commit, pero el journal y el restore no satisfacen el contrato. El byte S no aporta ese dato.
- Recuperación sin rama/retorno: controles HALT prematuros dejan T29521 y no hacen commit.
- El retry siempre se recupera de cualquier segundo fallo: force_retry_failure deja T29521 y STALL, sin intervención de rescate; traza254 fetches.

Fuentes `.mal`, metadatos, traces C/Python, stdout y memoria final están en `candidates/` y `evidence/traces/`. Todos los controles pequeños se verificaron contra C estricto. No se borra un candidato por fallar.

## Preparación y corridas corregidas

- El primer guardado de un log M0 usó una ruta relativa fuera del directorio correcto; no ejecutó esa reproducción y no se contó como PASS. La corrida desde baseline está en m0-tests.txt y report-reproduced.json.
- El primer comando de pytest Autobolge se ejecutó desde zig/, causando tres errores de importación: `autobolge-remote-tests-initial-cwd.txt`.
- La siguiente corrida tuvo14 PASS/1 FAIL porque faltaba trace_probe.exe: `autobolge-remote-tests-before-trace-build.txt`. Se compiló desde el source fijado y la corrida final es15/15: `autobolge-remote-tests.txt`.
- El primer red de adapter se intentó guardar desde el clon con una ruta inexistente. No se contó como RED; la corrida real con2 fallos de funcionalidad ausente está en tdd-adapter-red.txt.
- Los RED iniciales de builder, oráculos, condicional y adaptador están preservados separadamente. Las suites posteriores GREEN quedan en sus logs.

## Límites que no constituyen una imposibilidad general

- No se construyó M2 ni un motor general de intentos agotados.
- El segundo intento del candidato positivo usa otra dirección p, la misma transición crazy con operando corregido; no es un retorno a la misma instrucción física ni un loop reutilizable.
- El resultado final fijo puede obtenerse sin restore. La afirmación demostrada exige que la restauración intermedia ocurra y sea journal-dependiente, y no que sea necesaria para imprimir S.
- No hay nuevo buscador relacional ni JIT; el adaptador M3 sólo codifica/observa.
- La huella quine y sus falsaciones pertenecen a torus/TORUS_RESULTS.md. Los fallos de esa campaña se conservaron allí. No se reclasifican como recuperación por el éxito del candidato independiente.
