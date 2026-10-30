# Compose — Boss 3 real: bucle `while x > 0` con PC repetida en Classic Malbolge

**Para:** agente OpenCode (sesión limpia)
**Escrito por:** Claude Code, 2026-10-27, tras auditar los Bosses
**Estado al entregar:** auditoría aplicada en el árbol de trabajo, **sin commit** sobre `b434ebd`

---

## 0. Antes de empezar

1. `git status --short`. Si la auditoría sigue sin commit, tus cambios deben ir en un commit **separado**. Usa siempre `git commit -- <rutas>`.
2. `python3 -m pytest -q -p no:cacheprovider tests baseline torus/test_evidence.py` debe dar **70 passed, 59 subtests passed**. Si da otra cosa, detente y repórtalo antes de tocar nada.
3. Lee `VERDICT.md` (filas Boss 2 y Boss 3) y la sección 07 del `README.md`. Ahí está el estado corregido.

## 1. Base fijada (no modificar)

| Archivo | SHA-256 | Regla |
|---|---|---|
| `candidates/boss3_autonomous_loop.mal` | `d2d6b91d5f4df1f64890174cbe22599e71b37041aeb3677d2845f95ae01263bc` | Evidencia del intento fallido. **No borrar, no sobrescribir, no renombrar.** |
| `candidates/boss3_dynamic_loop.mal` | `f59cf283414251ee23d35f98beffaf634f7b69ef9f8cb23e259fdb7c5329d1d2` | Intento previo, asistido por el host. Igual. |
| `candidates/boss1_byzantine.mal` | `63802e3cf211e733c33b075703681757f0ba2a3f637f95c138b8ef67cbdfe8dd` | No tocar. |
| `candidates/boss2_brainfuck.mal` | `ac46c907fc219724e0bd60694a7549dc04995df75879f568d9a15b720e1cc8db` | No tocar. |
| `vendor/mb_ref.c` | `a8ce19c2dc93e36f8c9c24a271c4187d68f922b9455262c7199a009763fe3ad3` | Oráculo; no modificar. |
| `vendor/olmstead_original.c` | `05abd38e78b266050c5a5e8cc5b36584daa5bbdeb404bfb351de7ea6fa26b510` | Oráculo histórico; no modificar. |

`tools/observe.py`, `tools/oracles.py` y `baseline/epoch_probe.py` son la VM y los oráculos de referencia. **No los cambies para que un candidato pase.**

## 2. Lo que encontró la auditoría (por qué existe este compose)

`boss3_autonomous_loop.mal` se declaró `DEMONSTRATED` como «bucle autónomo», pero:

- **Ninguna PC se ejecuta dos veces** con ninguna entrada. No hay iteración.
- Cada N soportado salta a un bloque propio con N instrucciones `<` escritas a mano: 1 en `9853..`, 2 en `49219..`, 3 en `29538..` y 7 en `112..118`. No hay contador ni decremento.
- Fuera de la tabla {EOF, 0, 1, 2, 3, 7} la salida es basura: `4`→`\xeb`, `5`→`\xeb\xeb`, `6`/`9`→vacío, `8`→`\xe1\xe1`.
- Los tests originales solo comprobaban los 6 casos para los que se construyó el artefacto, así que lo «validaban» por construcción.

Esto ya está fijado en `tests/test_boss3_dynamic_loop.py::test_09` y `::test_10`. **Esos tests deben seguir pasando**: describen el artefacto viejo, no el tuyo.

## 3. Objetivo

Un artefacto **nuevo**, `candidates/boss3_real_loop.mal`, construido por un builder nuevo, `tools/boss3_real_loop.py`, que implemente:

```
x = stdin_byte - '0'
while x > 0:
    print('1')
    x = x - 1
halt
```

dentro de **una única ejecución de la VM Classic**, sin que el host escriba en memoria.

### Hito mínimo aceptable

Dominio `x ∈ {0..9}`, leído como un dígito ASCII. EOF y bytes fuera de `'0'..'9'` deben dar un comportamiento **documentado y testeado**: lo más simple es salida vacía y HALT. Un N sin límite queda como frontera abierta y no hace falta para este hito.

## 4. Contrato de aceptación (todos obligatorios)

Escríbelo **primero**, como `tests/test_boss3_real_loop.py`, y verifica que falla (rojo) antes de que exista el artefacto. Guarda esa salida en `evidence/boss3-real-red.txt`.

| Gate | Qué se comprueba | Por qué |
|---|---|---|
| G1 Iteración real | Existe al menos una PC del cuerpo del bucle cuyo conteo en la traza es **exactamente N** para cada `N ∈ {1..9}`, y es la **misma PC** para todos los N. | Es justo lo que le faltaba al artefacto viejo. |
| G2 Sin tablas por N | El número de instrucciones `<` **distintas** (por PC) ejecutadas es constante e independiente de N; no crece con N. | Prohíbe bloques desenrollados por caso. |
| G3 Salida exacta | Para **cada** entrada `'0'..'9'` la salida es exactamente `b'1' * N` y `terminal == 'HALT'`. Los 10 casos, no una muestra. | Prohíbe validar solo los casos de construcción. |
| G4 Fuera de dominio | EOF y al menos `b'/'`, `b':'`, `b'A'` y `b'\x00'` producen el comportamiento documentado en §3 y terminan (HALT o terminal documentado) dentro del presupuesto. | Comportamiento definido fuera del dominio. |
| G5 Cero escrituras del host | El test ejecuta solo con `tools.observe.run` / `oracles.verify` sobre los bytes del archivo. Prohibido en builder, CLI y tests: `Machine(...).mem[...] =`, `vm.mem[...] =`, snapshots reanudados, cambiar `c`/`d` a mitad de corrida. | El fallo del intento asistido por el host. |
| G6 Paridad 3 oráculos | `validate_parity(verify(img, payload, budget))` es True para las 10 entradas y para las de G4, con `reference_returncode == 0` y `original_returncode == 0` en los casos HALT. | Igual que M1–M3. |
| G7 Artefacto inmutable | El SHA-256 de `candidates/boss3_real_loop.mal` coincide con `candidates/boss3_real_loop.json["sha256"]`, y reconstruirlo con el builder da los mismos bytes. | Reproducibilidad. |
| G8 Loader estricto | Cada byte del archivo cumple `strict_byte(v, pos)` (`tools/build_candidates.py`). | Classic estricto, sin loader relajado. |

### Controles negativos (deben FALLAR el contrato de forma específica)

Genera los mutantes con el builder (`mode=...`). Cada uno tiene que hacer fallar **su** gate:

| Mutante | Debe romper |
|---|---|
| `broken_decrement`: el contador no baja | G3 (no termina con N≥1 dentro del presupuesto, o la salida ≠ N unos) |
| `broken_exit`: sin salida a HALT con x = 0 | G3/G4 (terminal ≠ HALT) |
| `broken_rearm`: el cuerpo no se reconstruye entre iteraciones | G1 o G3 con N ≥ 2 (con N=1 puede pasar; documéntalo) |
| `off_by_one`: condición `x >= 0` | G3 (N+1 unos) |

Si un mutante **no** rompe su gate, el gate es débil: arréglalo antes de declarar nada.

## 5. Punto de partida en el propio repo

No hace falta inventar desde cero. Ya hay mecanismos demostrados que reconstruyen control dentro de la VM:

- `tools/build_candidates.py`: `Layout`, `seek`, `strict_byte`, `_emit_helpers` (`load_const`, `rearm_trampoline_cell`, `trip_to_trampoline`).
- M1e/M2/M3 (`candidates/m1e_normal.mal`, `m2_normal.mal`, `m3_normal.mal`, `evidence/trampoline-rearm.json`): rearme de trampolines y portales en la VM entre épocas.
- `tools/boss1_byzantine.py`: despacho por valor calculado y portales.

Lo que **ningún** artefacto existente hace todavía: volver a ejecutar las **mismas** direcciones del cuerpo un número de veces que depende de un dato. Ese es todo el reto.

## 6. Presupuesto y regla de parada

- Máximo **128 candidatos** y **20,000 instrucciones** por ejecución en el hito 0..9.
- Registra cada candidato rechazado y el gate que lo rechazó en `evidence/boss3-real-campaign.json`.
- Si se acaba el presupuesto sin pasar G1–G8: **no** debilites gates ni oráculos. Conserva el mejor candidato y la falsación, y marca `NOT_DEMONSTRATED` con la frontera exacta (por ejemplo: «G1 pasa hasta N=3; G3 falla en N=4 porque…»).

## 7. Prohibido

- Escribir en la memoria de la VM desde Python o C durante la ejecución, aunque sea «solo para inicializar».
- Un bloque de código por valor de N, o cualquier estructura cuyo tamaño de código ejecutado crezca con N sin repetir PCs (G1/G2 lo detectan).
- Modificar `tools/observe.py`, `tools/oracles.py`, `baseline/epoch_probe.py` o `vendor/*`.
- Borrar, sobrescribir o renombrar cualquier `.mal` existente.
- Cambiar los tests de la auditoría (`test_boss3_dynamic_loop.py::test_09/10`, `test_boss2_brainfuck.py::test_06/07`, `test_boss1_byzantine.py::test_06`).
- Poner `DEMONSTRATED` en `VERDICT.md` o el README sin que G1–G8 y los 4 mutantes estén verdes **y** guardados en `evidence/`.

## 8. Entregables

1. `tools/boss3_real_loop.py` (builder con los modos `normal` + 4 mutantes).
2. `candidates/boss3_real_loop.mal` + `.json` (sha256, longitud, dominio, PCs del cuerpo, conteos por N).
3. `tests/test_boss3_real_loop.py` (G1–G8 + mutantes).
4. Evidencia: `evidence/boss3-real-red.txt`, `evidence/boss3-real-green.txt` (salida completa de pytest), `evidence/boss3-real-campaign.json` y un directorio `evidence/boss3_real/<payload>/` por cada entrada `'0'..'9'` generado con `verify(..., evidence=...)`.
5. Una fila **nueva** en `VERDICT.md` («Boss 3 real: bucle con PC repetida») con el veredicto que resulte, `DEMONSTRATED` o `NOT_DEMONSTRATED` con su frontera. **No edites** las filas de Boss 3 que puso la auditoría.
6. En el README §07, solo cambia el nodo B3 del diagrama y añade una subsección «Boss 3 real», sin borrar el veredicto de auditoría.
7. La suite completa en verde: `70 + tus tests`.
8. Commit propio: `git commit -- <solo tus rutas>`, con un mensaje que diga el veredicto real.

## 9. Formato del reporte final

```
VEREDICTO: DEMONSTRATED | NOT_DEMONSTRATED
Dominio probado: ...
PC(s) del cuerpo y conteos por N: {1: k, 2: k, ...}
Gates: G1..G8 = PASS/FAIL cada uno
Mutantes: cada uno con el gate que rompió
SHA-256 del artefacto: ...
Pytest: N passed (pega la última línea literal)
Lo que NO se demostró: ...
```
