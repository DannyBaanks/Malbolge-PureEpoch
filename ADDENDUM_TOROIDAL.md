# Addendum para Sol — huella toroidal y separación código/datos en quines Classic

Fecha: 2026-10-25
Integrar con `COMPOSE_SOL_AUTOBOLGE_BOLGEFORGE_PURE_EPOCH.md` como investigación adicional, **sin sustituir** los gates de rollback puro.

## Observación recibida

Captura del usuario de un análisis externo (`/tmp/opencode/torus/mb_fingerprint.py`, **script no inspeccionado**). Los siguientes son **datos reportados por ese script**, no verificación independiente de esta huella:

| Propiedad | m=281 | Lutter |
|---|---:|---:|
| steps | 62,239,851 | 69,547,436 |
| unique code positions (visited_c) | 25,553 | 27,292 |
| unique data positions (visited_d) | 26,799 | 29,900 |
| unique union | 52,256 | 57,096 |
| intersection, derived if visited_union is C union D | **96** | **96** |
| unvisited by either pointer, derived (59,049 - union) | **6,793** | **1,953** |
| delta_segments | 26,214,699 | 29,292,515 |
| opcode 4 breaks (jmp / i) | 21,389,393 | 23,901,063 |
| opcode 40 breaks (mov_d / j) | 4,825,305 | 5,391,451 |
| diagonal_fraction (reported rounded) | 0.578812 | 0.578812 |
| shift_symmetry_count (reported) | 0 | 0 |

Las identidades `delta_segments = opcode4_breaks + opcode40_breaks + 1` se cumplen en ambos registros, y `diagonal_fraction` coincide (a seis decimales) con `(steps - opcode4_breaks - opcode40_breaks) / steps`. Esto **sugiere** que la fracción diagonal deriva mecánicamente de los dos recuentos de bifurcaciones, no de una simetría espacial independiente. Verificar la definición leyendo el script.

**Procedencia crucial:** `BolgeForge/synthesize.py` contiene explícitamente `clean_lutter` y deriva la variante m=281 del quine de Lutter mediante reubicaciones y reparación de handoffs. Por tanto, coincidencias de frecuencias/solapamientos **no son evidencia de universales independientes**. Tomar como hipótesis de herencia estructural.

## Hipótesis y mecanismo

Modelar la proyección `(c,d) ∈ (Z/59049Z)^2`: como ambos punteros normalmente avanzan en `+1`, se conserva `delta=(c-d) mod 59049` entre saltos de código y redirecciones de datos. Las instrucciones de salto rompen el tramo diagonal. Esta representación toroidal de **dos coordenadas de la VM** no equivale a demostrar ciclos completos ni auto-reparación del estado de la máquina `(a,c,d,memoria,entrada,salida)`.

Las 96 direcciones compartidas en cada quine sugieren separación estática de huellas de acceso; **no** prueban protección, seguridad o restaurabilidad. Una dirección nunca visitada puede ser inaccesible al programa como journal; una dirección visitada por `d` puede ser modificada por `*`/`p`; cada celda ejecutada por `c` puede cifrarse tras su instrucción. También hay solapamientos *a lo largo del tiempo*, distintos de una colisión simultánea.

## Trabajo concreto solicitado

1. Releer/ejecutar el script de la captura. Fijar su hash, definición exacta de las métricas y el motor/semántica de Malbolge. **No** afirmar resultados revalidados sólo por esta captura.
2. Verificar los dos programas con el mismo oráculo Classic estricto y los artefactos publicados; tomar hashes de fuentes y binarios.
3. Exportar sets `C`, `D`, `C∩D`, `C∪D`, complemento, histograma por opcode, eventos de escritura y cronología de accesos. Confirmar **96/96** por cómputo independiente; distinguir `visited`, `read`, `written`, `executed`, `encrypted`.
4. Representar `(c,d)` módulo 59,049, `delta=(c-d) mod 59049` y sus tramos maximales. Verificar fórmula de `diagonal_fraction`, wraps, saltos, longitud de tramos, retornos y crossings; no deducir simetría de las fracciones. El `shift_symmetry_count=0` sólo significa que el detector *usado* no encontró su tipo de simetría.
5. Añadir control de procedencia: quine Lutter, m281 derivado, otras variantes m, un programa independiente Classic (ej. Cat) y uno corto/aleatorio loader-valid. Comparar las distribuciones y el solapamiento exacto de 96.
6. Buscar regiones `D` accesibles **y no ejecutadas por `C`**, para un checkpoint interno. Localizar transiciones autorizadas hacia/desde la región, sin alterar la VM y sin usar el host para restaurarla. Rechazar candidatas sólo “intactas” que no puedan leerse/escribirse legítimamente desde Malbolge.
7. Señalar fronteras de fase (saltos/redirecciones o estados de handoff) donde se pueda introducir una región journal; diseñar un experimento de escritura → corrupción mediante rama *in-band* → comparación de invariante → restauración *in-band* → retry. Probar y falsar contra oráculo independiente.
8. Si se halla una ruta de acceso al journal, producir candidato `.mal` y traza completa. Si no se halla, preservar grafo de alcanzabilidad y prueba de falsación del candidato.

## Gates

- **G-T0 Métrica**: las cuentas se reproducen, y se conocen sus definiciones; o se documenta exactamente qué falla.
- **G-T1 Separación**: los 96 solapamientos, si se confirman, se explican por conjuntos de posiciones; no se confunden con ausencia de colisiones dinámicas.
- **G-T2 Journal accesible**: una región concreta puede leerse y modificarse *desde la ejecución Classic*, sin host.
- **G-T3 Recuperación**: el programa compara un estado propio con una condición y decide restaurar/reintentar dentro de Malbolge puro. T0–T2 **no** implican T3.

Conservar `DEMONSTRATED`, `INFERRED`, `NOT_DEMONSTRATED`, `DESTROYED` y evidencia negativa. Reportar benchmarks con presupuestos; no correr miles de millones de pasos innecesarios. No editar artefactos publicados ni inventar pruebas.

**Pregunta prioritaria:** ¿la separación de trayectorias que los quines heredan del algoritmo de Lutter es explotable para un journal realmente alcanzable y controlado por instrucciones de Malbolge?
