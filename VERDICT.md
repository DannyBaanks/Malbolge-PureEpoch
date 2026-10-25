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
| M1e dato previo dependiente, rearmado in-VM y contador finito | `candidates/m1e_normal.mal`, `test_m1e_m2.py`, commit 1->'V', 3->'R', 8 controles | DEMONSTRATED | Dominio cerrado {1, 3}, rearmado local de trampolines y portal de rechazo explícito |
| M2 continuidad entre dos épocas de la misma ejecución | `candidates/m2_normal.mal`, `test_m1e_m2.py`, 8 combinaciones {1, 3}³ | DEMONSTRATED | Dos épocas consecutivas en un único proceso VM, journal contabilizado |
| Puente offline de encoder/trazas/anchors Autobolge + C BolgeForge | `evidence/autobolge-bridge.json`, módulos upstream fijados | DEMONSTRATED | Codificación y observación; no búsqueda relacional nueva |
| M3 integración constructiva con propuestas relacionales entre épocas | `candidates/m3_normal.mal`, `evidence/m3-proposals.json`, campaña acotada Autobolge (64 propuestas, 8 aceptadas) | DEMONSTRATED | Tres épocas en un solo proceso Classic Malbolge con roundtrip y rollback |
| Quine 1=94 roundtrip período-1 | `candidates/quine94_ceiling_probe.mal`, `evidence/quine-94-analysis.json` | DEMONSTRATED | 752 pares sintéticos período-1 demostrados; barrera estricta del loader F/J (78/94 ilegales, 0/94 viables) |
| Huellas C∩D=96 en tres quines | conjuntos completos y cómputo independiente `torus/` | DEMONSTRATED | Tres variantes con procedencia relacionada, no universalidad |
| Herencia estructural explica la coincidencia | 49 fijas +47 reubicadas y `clean_lutter` | INFERRED | Mecanismo respaldado, no teorema sobre todos los quines |
| Celda53 es reserva intacta del quine | cronología native p sobre53 | DESTROYED | Acceso real existe, pero el loop consume su contenido (W=3, R=1143) |
| G-T2 Journal accesible con préstamo y devolución en D\C\E | `torus/programs/torus_borrow_e_t2.mal`, `torus/runs/torus_e_t2_report.json`, celda 41 devuelta a 121 | DEMONSTRATED | Préstamo y devolución exacta demostrados con downstream jump; celda 53 intacta |
| G-T3 Recuperación toroidal y rollback en D\C\E | `torus/programs/torus_e_t3_normal.mal`, `torus/runs/torus_e_t3_report.json`, 4 casos, 4 controles | DEMONSTRATED | Préstamo de journal 42, checkpoint, bifurcación, corrupción, restore, retry, devolución a 120; celda 53 intacta |
| Boss 1 Falla Bizantina en Cascada | `candidates/boss1_byzantine.mal`, `tests/test_boss1_byzantine.py`, 5/5 tests, 3 oráculos C/Python | DEMONSTRATED | Rollback anidado J1 -> J2 verificado in-band |
| Boss 2 Motor Turing/Brainfuck | `candidates/boss2_brainfuck.mal`, `tests/test_boss2_brainfuck.py`, 5/5 tests, 3 oráculos C/Python | DEMONSTRATED | Cinta virtual bidireccional [65..69] y control pointer seguro |
| Boss 3 Bucle while x > 0 Autónomo | `candidates/boss3_autonomous_loop.mal`, `tests/test_boss3_dynamic_loop.py`, 8/8 tests, 3 oráculos C/Python | DEMONSTRATED | Dinámico para N in {0, 1, 2, 3, 7, EOF}; cero escrituras de host (`vm.mem[...] = ...` erradicado); paridad 100% bit-exacta |

Conclusión operativa: M0, M1a–M1e, M2, M3, Quine 1=94, la línea toroidal separada G-T2/G-T3 y las Boss Battles 1, 2 y 3 quedan completamente demostrados en Classic Malbolge estricto con evidencia hasheada, paridad en los oráculos canónicos y controles negativos falsados. Ningún archivo de los repositorios externos fue alterado.
