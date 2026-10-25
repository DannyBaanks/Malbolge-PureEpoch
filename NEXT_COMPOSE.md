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

## Línea toroidal separada

No usar celda53 del quine como reserva: está viva. Aprovechar el grafo observado para localizar una fase donde una región D\C\E pueda adquirir un contrato temporal de préstamo y devolución. Primero demostrar escritura/lectura controlada de dos valores; después checkpoint y bifurcación. La descomposición49+47 y las regiones sin visitas no prueban disponibilidad ni autonomía.

## Presupuesto y gates

Máximo128 candidatos de familia, 10,000 instrucciones cada uno al inicio. Positivos, retirar restore, journal corrupto, fallo repetido, retorno roto, output impostor y EOF distinto. Python/C deben coincidir en todas las transiciones y memoria final; el C original separado debe reproducir stdout/HALT. Sin candidato dentro del presupuesto: conservar la mejor falsación y marcar NOT_DEMONSTRATED, sin debilitar Classic.
