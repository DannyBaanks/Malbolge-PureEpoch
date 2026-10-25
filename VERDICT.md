# Veredicto por afirmación

| CLAIM | EVIDENCE | VERDICT | LIMIT |
|---|---|---|---|
| M0 reproduce el ciclo 408/17 | `evidence/report-reproduced.json`, cinco tests M0 | DEMONSTRATED | CYCLE, no reparación |
| M0 repara una corrupción ajena al ciclo | control negativo preservado | DESTROYED | La celda alterada no vuelve al valor original |
| M1a mutación reversible | `m1a_rot10.mal`, traza completa y C independiente | DEMONSTRATED | Una celda, diez rotaciones; sin checkpoint |
| M1b checkpoint interno recuperable | `m1b_normal.mal`, dos entradas, journal alterado/quitar save | DEMONSTRATED | Una celda lógica; recuperación incondicional |
| M1c decisión interna y restore ante candidato inválido | `m1c_normal.mal`, cuatro casos, i177 y p19825 | DEMONSTRATED | Dominio cerrado de dos valores candidatos; no comparador general |
| M1d segundo intento corregido in-band | p19856, operando1 construido con rotaciones, commit posterior | DEMONSTRATED | Una repetición de la transición; máximo dos intentos en el dominio probado; no bucle general reutilizable |
| La restauración usa el journal | dos valores previos y controles no_save/corrupt_journal | DEMONSTRATED | Dependencia de la fase intermedia; output final constante no requiere restore |
| Output correcto basta para demostrar estado/protocolo | impostores output correcto / target o fase incorrectos | DESTROYED | El gate exige memoria y trazas de fase |
| Rollback exacto del estado físico completo | código cifrado y auxiliares evolucionan | NOT_DEMONSTRATED | No forma parte del contrato de una celda lógica |
| Gestión autónoma de fallos repetidos/agotamiento | force_retry_failure produce STALL, presupuesto negativo | NOT_DEMONSTRATED | No se proclama handler interno ni disponibilidad |
| M2 continuidad entre dos épocas de la misma ejecución | diseño siguiente en NEXT_COMPOSE | NOT_DEMONSTRATED | El control auto-modificado no se ha vuelto a armar para reutilización |
| Puente offline de encoder/trazas/anchors Autobolge + C BolgeForge | `evidence/autobolge-bridge.json`, módulos upstream fijados | DEMONSTRATED | Codificación y observación; no búsqueda relacional nueva |
| M3 integración constructiva con propuestas relacionales entre épocas | adaptador mínimo actual | NOT_DEMONSTRATED | Sin selector/proposals ni M2; no JIT/runtime synthesis |
| Huellas C∩D=96 en tres quines | conjuntos completos y cómputo independiente `torus/` | DEMONSTRATED | Tres variantes con procedencia relacionada, no universalidad |
| Herencia estructural explica la coincidencia | 49 fijas +47 reubicadas y `clean_lutter` | INFERRED | Mecanismo respaldado, no teorema sobre todos los quines |
| Celda53 es reserva intacta del quine | cronología native p sobre53 | DESTROYED | Acceso real existe, pero el loop consume su contenido |
| G-T3 recuperación/retry dentro del quine | ninguna modificación del quine construida | NOT_DEMONSTRATED | El programa pequeño no demuestra ese resultado |

Conclusión operativa: M1a–M1d demostrados en el alcance finito explicitado. M2/M3 completos y recuperación del quine siguen abiertos. Los outputs y artefactos certificados de los repos originales no se modificaron.
