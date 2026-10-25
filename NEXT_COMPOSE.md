# Próximo compose — de la recuperación finita a una continuación reutilizable

## Base fijada

Trabajar desde este laboratorio y sus hashes. Preservar `m1c_normal.mal` SHA256 `17ff6f326c3205fa92bae9eeeba4c8ecf0229a722c55491e2fa5e0cd4d7b7985`, sus cuatro casos y controles. No sustituir el gate por una salida impresa ni por anchors reanudados desde Python.

M1 actual: una celda lógica T36, journal52, dominio de selectores1/3, bifurcación indirecta finita, restore p19825 y un intento corregido p19856. Hasta249 instrucciones incl.HALT. No hay punto de entrada rearmado, contador de intentos, segunda época ni control del quine.

## Pregunta prioritaria

¿Podemos convertir el protocolo en una subrutina que **restaure su control de continuación** y entre a una segunda época en la misma VM, preservando un dato cuyo valor recuperado influya en el resultado comprometido?

## Experimento siguiente

1. Exportar los bytes reales tras cada cifrado de los trampolines i/j y del portal. Calcular offline qué instrucciones debe ejecutar el programa para rearmar una entrada válida. No modificar esos bytes desde el host.
2. Construir un candidato M1e: dato previo1/3, journal recuperable, commit dependiente del dato recuperado. El control `no_restore` debe fallar también el resultado final observable/estado lógico final, además de la fase intermedia.
3. Agregar un contador interno finito de intentos, con rechazo/HALT explícito si el intento corregido vuelve a fallar. Conservar el actual STALL como control negativo.
4. Sólo con los tres puntos anteriores, componer M2 de exactamente dos épocas en un único proceso. Probar válido/válido, inválido/válido, válido/inválido e inválido/inválido; registrar todas las fases y consumo exacto del journal.
5. Para M3, hacer que un adaptador de `TraceExpander`/proposals de Autobolge proponga únicamente transformaciones de una familia acotada y que BolgeForge valide cada fuente estrictamente. Conservar propuestas rechazadas y discrepancias. La campaña es offline; ningún proceso de observación reescribe la VM.

## Línea toroidal separada [DEMONSTRATED]

Completada y verificada en `torus/`:
1. Celda 53 excluida estrictamente por estar viva (`W=3, R=1143` en `m281`).
2. Ventanas de préstamo y restitución localizadas en `runs/dce_borrow_windows.json` (banda compartida `39..44 ∈ D \ C \ E`).
3. G-T2 (`E-T2`): Demostración constructiva de préstamo/devolución con escritura/lectura controlada de dos valores en celda 41, devuelta exactamente a 121 y verificada por salto aguas abajo del consumidor (`runs/torus_e_t2_report.json`). Control negativo `no_return` falsado.
4. G-T3 (`E-T3`): Checkpoint, bifurcación in-band, corrupción controlada, restore desde journal prestado 42, retry y devolución exacta a 120 antes del salto del consumidor (`runs/torus_e_t3_report.json`). Paridad en 5 oráculos y 4 controles negativos falsados.

## Presupuesto y gates

Máximo128 candidatos de familia, 10,000 instrucciones cada uno al inicio. Positivos, retirar restore, journal corrupto, fallo repetido, retorno roto, output impostor y EOF distinto. Python/C deben coincidir en todas las transiciones y memoria final; el C original separado debe reproducir stdout/HALT. Sin candidato dentro del presupuesto: conservar la mejor falsación y marcar NOT_DEMONSTRATED, sin debilitar Classic.
