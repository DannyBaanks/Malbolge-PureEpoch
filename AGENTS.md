# Malbolge-PureEpoch — Contrato Canónico de Agentes y Autonomía Estricta

> [!IMPORTANT]
> **REGLA FUNDAMENTAL DE AUTONOMÍA EN MALBOLGE (BINDING):**
> **Todo programa en este repositorio DEBE EJECUTARSE SOLO CON PURO LENGUAJE MALBOLGE.**
> **Python, C y demás herramientas externas sirven ÚNICAMENTE como cargadores offline, observadores y oráculos de verificación (test harness), NUNCA como puente en runtime, ni como ayuda, ni para resolver computaciones fuera de la VM.**
> 
> Si la computación, el bucle, el autómata o la transición no ocurren dentro de las 59,049 celdas y los registros de la VM Classic Malbolge durante la ejecución, la afirmación se clasifica obligatoriamente como `NOT_DEMONSTRATED`.

---

## 1. Principios Operativos Inviolables

1. **Cero escrituras del host en runtime:**
   `vm.mem[...] = ...` durante la ejecución está **terminantemente prohibido**. Cualquier modificación de memoria debe provenir de las instrucciones Malbolge (`*`, `p`, cifrado `XLAT2` en `c`).
2. **Sin computación externa disfrazada:**
   Prohibido calcular estados futuros, transiciones de autómatas o contadores de bucle en Python para luego simplemente "dibujarlos" con Malbolge fingiendo ejecución dinámica.
3. **Paridad estricta entre 3 oráculos:**
   Todo artefacto `.mal` debe producir el mismo resultado bit a bit y el mismo estado terminal en:
   - Python `Machine` (`baseline/epoch_probe.py` / `tools/observe.py`)
   - C de referencia (`build/mb_ref`)
   - Binario original de Ben Olmstead de 1998 (`build/olmstead`)
4. **Cumplimiento estricto del cargador de Olmstead 1998:**
   Cada celda $v$ en la posición $p$ del archivo `.mal` debe cumplir `33 <= v <= 126` y `XLAT1[(v - 33 + p) % 94] in VALID`.
5. **Presupuesto de destrucción CERO:**
   No borrar, sobrescribir ni reubicar archivos sin aprobación explícita.
6. **Commits atómicos por ruta:**
   Siempre `git commit -- <rutas>`, nunca `git commit` sin argumentos.
