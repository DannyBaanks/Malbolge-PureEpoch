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
| Boss 1 Falla Bizantina en Cascada | `candidates/boss1_byzantine.mal`, `tests/test_boss1_byzantine.py`, 6/6 tests, 3 oráculos C/Python, control de corrupción de J2 | DEMONSTRATED | Rollback anidado J1 -> J2 verificado in-band; el restore de nivel 2 sigue al contenido de J2. Dos intentos fijos, dominio {1,3}. La doble falla emite el byte restaurado (`\x01`/`\x03`), no `'F'` |
| Boss 2 compilador Brainfuck sin bucles -> Malbolge en línea recta | `candidates/boss2_brainfuck.mal`, `tests/test_boss2_brainfuck.py`, 7/7 tests, 3 oráculos C/Python | DEMONSTRATED | Subconjunto `> < + - . !`, valores 0..3, 5 celdas [65..69]; puntero y cinta resueltos en Python al compilar |
| Boss 2 VM Brainfuck / cinta de Turing en Malbolge | auditoría 2026-10-27: sin `[ ]`, `,` guardaba `crazy(byte, celda)`, ninguna PC se repite | NOT_DEMONSTRATED | No hay intérprete en tiempo de ejecución; `,` `[` `]` ahora se rechazan con `NotImplementedError` |
| Boss 3 Bucle while x > 0 Autónomo | auditoría 2026-10-27, `tests/test_boss3_dynamic_loop.py` test_09/test_10 | NOT_DEMONSTRATED | El artefacto es una tabla de despacho por entrada con salidas desenrolladas: ninguna PC se repite, no hay contador ni decremento; `4`->`\xeb`, `5`->`\xeb\xeb`, `6`/`9`->vacío, `8`->`\xe1\xe1` |
| Boss 3 despacho por entrada sin escrituras del host | `candidates/boss3_autonomous_loop.mal`, test_01..test_08, 3 oráculos C/Python | DEMONSTRATED | Tabla cerrada {EOF, 0, 1, 2, 3, 7}; cero `vm.mem[...] = ...` del host; paridad bit-exacta en esos 6 casos |
| Boss 3 real: bucle con PC repetida | `candidates/boss3_real_loop.mal`, `tests/test_boss3_real_loop.py` G1–G8 | NOT_DEMONSTRATED | Campaña de 1 candidato placeholder; G3 falla, sin iteración real ni PC repetida; frontera documentada en `evidence/boss3-real-campaign.json` |

Conclusión operativa: M0, M1a–M1e, M2, M3, Quine 1=94, la línea toroidal separada G-T2/G-T3 y Boss 1 quedan demostrados en Classic Malbolge estricto con evidencia hasheada, paridad en los oráculos canónicos y controles negativos falsados. Boss 2 queda demostrado solo como compilador en línea recta; la VM Brainfuck y el bucle autónomo de Boss 3 son `NOT_DEMONSTRATED` (corrección de auditoría 2026-10-27, que bajó los veredictos de `b434ebd` y `7075b6c`). Ningún archivo de los repositorios externos fue alterado.
