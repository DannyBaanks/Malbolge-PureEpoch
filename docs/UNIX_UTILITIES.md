# Suite de Utilidades Unix Clásicas en Malbolge (Bosses 5 a 10)

Bajo la estricta política **anti-fake** de [`AGENTS.md`](file:///home/danny/Development/ISyCo/AGENTS.md) —donde **el 100% del cómputo ocurre exclusivamente dentro de la VM de Malbolge** y Python/C actúan únicamente como herramientas de síntesis offline y oráculos de verificación— se desarrolló la suite completa de utilidades estándar de cómputo y filtrado de flujos.

---

## Matriz Canónica de las 6 Utilidades

| Boss | Utilidad | Binario Canónico (.mal) | Celdas | SHA-256 Canónico | Invariante Central In-VM | Tests |
| :--- | :--- | :--- | :---: | :--- | :--- | :---: |
| **Boss 5** | **`cat`** | `candidates/cat_real.mal` | 13,185 | `489db7fa47a8298716382a39281a177271e843c0a5b8da22b1c4119fa4757cbb` | Streaming transparente con parada limpia ante EOF (59048) | 14/14 PASS |
| **Boss 6** | **`rev`** | `candidates/rev_real.mal` | 13,185 | `5f316fe2c2a9557876a160d5b1fe59dfa330756779b6d616ea195655aa9197ec` | Pila LIFO en memoria con desapilado biyectivo inverso `crazy(-, 121)` | 14/14 PASS |
| **Boss 7** | **`wc -c`** | `candidates/wc_real.mal` | 25,972 | `eb2e3a84ec6924bce6f2eb5ae92d3f25c79be276f50b445735ca3121516e87bf` | Conteo de bytes multinivel y emisor decimal con pares mágicos rotatorios | 14/14 PASS |
| **Boss 8** | **`cmp`** | `candidates/cmp_real.mal` | 29,667 | `e045917cff2e5cadceb109fd39ec0146bd58370458de40e695dd675873c06eeb` | Predicado de igualdad en stream: emite `=` o `!` con bifurcación in-line | 14/14 PASS |
| **Boss 9** | **`add`** | `candidates/add_real.mal` | 26,474 | `ec8b4801ed5b4554e3df87db39f9d933214e6bff202eff3cc6b3b4670749c2a8` | ALU aritmética in-VM: $d_0 + d_1$ evaluado algebraicamente en ternario | 14/14 PASS |
| **Boss 10** | **`sort2`** | `candidates/sort2_real.mal` | 2,452 | `d92a78c21ad4afa6302a5a77dae9cc2cebd053eeeb544c6f5d525aa77168a321` | Clasificador condicional min-max / paso elemental de Bubble Sort | 14/14 PASS |

---

## Boss 5: El Cat Real (`cat_real.mal`)

### La Frontera Histórica del `cat` en Malbolge
En 1998, Lou Scheffer sintetizó un `cat` de 68 bytes, pero era **no-terminante**: ante EOF entraba en un bucle indefinido de fallos. Un `cat` real requiere:
1. Ingestión byte a byte mediante `/`.
2. Detección inmediata del valor de fin de archivo de Malbolge ($59048 \equiv 3^{10} - 1$).
3. Bifurcación condicional in-VM hacia parada limpia `v` cuando $A = 59048$, o hacia emisión `<` cuando $A \in [0, 255]$.

### Álgebra del Discriminador EOF
Mediante operaciones ternarias se construye la función discriminadora:
$$\text{target} = \text{crazy}(\text{rot}_4(\text{crazy}(\text{crazy}(A, 121), 80)), 53) + 1$$
- Para $A = 59048$ (EOF): $\text{target} = 27$ (`HALT_PC_DRAIN0`, instrucción `v`).
- Para cualquier byte $A \in [0, 255]$: $\text{target} = 378$ (Pista de emisión y lectura subsecuente).

---

## Boss 6: El Rev Real (`rev_real.mal`)

### Pila LIFO en Memoria de la VM
A diferencia de `cat`, `rev` requiere acumular los bytes leídos y emitirlos en orden inverso (LIFO).
- **Almacenamiento biyectivo:** Cada byte $b_i$ se almacena cifrado en una celda $W_i$ mediante $\text{crazy}(b_i, 121)$.
- **Teorema de Involución en 121:** Para todo $b \in [0, 255]$:
  $$\text{crazy}(\text{crazy}(b, 121), 121) = b$$
- **Desapilado:** En el drenaje final, la VM rota 10 veces $W_i$ (identidad de 10 trits) para cargarlo en $A$, evalúa $\text{crazy}(A, 121)$ sobre una clave fija, y emite el byte original con `<` en orden estrictamente inverso.

---

## Boss 7: El Wc Real (`wc_real.mal`)

### Conteo Helicoidal y Emisión Decimal
`wc -c` cuenta el número de bytes presentes en el flujo de entrada (hasta 99 bytes en el espacio canónico) y emite la representación ASCII de la cuenta decimal.
- **Discriminadores en Cascada:** Cada posición de lectura bifurca a la siguiente etapa de conteo o al drenaje terminal según la presencia o ausencia de EOF.
- **Pares Mágicos de Rotación Rápida:** Para evitar bucles de emisión lentos que crucen celdas contiguas, se desarrollaron pares mágicos $(V, P)$ tales que rotar $V$ dos o tres veces genera exactamente el carácter ASCII del dígito (`'0'` a `'9'`).

---

## Boss 8: El Cmp Real (`cmp_real.mal`)

### Predicado de Igualdad en Flujo (`cmp` / `eq`)
Compara dos tokens leídos de `stdin` y emite `=` si son idénticos, o `!` si son desiguales.
- **Discriminador de Igualdad:** Tras desapilar $b_0$ y $b_1$, calcula:
  $$d = \text{crazy}(\text{crazy}(b_1, b_0), 80)$$
  * Para bytes iguales: $d = 80$.
  * Para bytes desiguales: $d = 53$.
- **Bifurcación Geométrica sin Trampolines:** Tras 9 rotaciones y evaluación contra $K=97$ en celda 59:
  * Tokens iguales: salta a la celda 29588 (`Drain Equal`, emite `=`).
  * Tokens desiguales: salta a la celda 29426 (`Drain Unequal`, emite `!`).

---

## Boss 9: El Add Real (`add_real.mal`)

### Unidad Aritmética Lógica (ALU) In-VM
Evalúa la suma de dos dígitos decimales / ternarios en memoria de la VM.
- **Fórmula Aritmética Ternaria:**
  $$r = \text{crazy}(\text{crazy}(50, d_0), \text{crazy}(50, \text{crazy}(d_1, d_0)))$$
  * Para $0 + 0 = 0$: produce $50$.
  * Para $0 + 1 = 1$ y $1 + 0 = 1$: produce $49$ (simetría garantizada).
  * Para $1 + 1 = 2$: produce $48$.
- **Drenajes de Emisión Rápida:**
  * Suma 1: salta a 26288 (emite `'1'`).
  * Suma 2: salta a 26369 (emite `'2'`).
  * Suma 0: salta a 26450 (emite `'0'`).

---

## Boss 10: El Sort2 Real (`sort2_real.mal`)

### Clasificador Condicional Min-Max / Bubble Sorter
Toma dos elementos de entrada y los emite en orden ordenado ascendente (FIFO si ya están ordenados, LIFO si estaban invertidos).
- **Discriminador de Orden Ternario:**
  $$r = \text{crazy}(33, \text{crazy}(\text{crazy}(50, d_0), \text{crazy}(d_1, d_0)))$$
  * Para pares ordenados ($d_0 \le d_1$): $r = 29500$.
  * Para pares invertidos ($d_0 > d_1$): $r = 29501$.
- **Salto Condicional In-Line:**
  Tras 6 rotaciones ternarias y evaluación con $K=97$ en celda 59:
  * Ordenado: aterriza en 2194 (`DRAIN_SORTED_FIFO`: emite $d_0$ luego $d_1$).
  * Invertido: aterriza en 2356 (`DRAIN_INVERTED_LIFO`: emite $d_1$ luego $d_0$).
- **Optimización de Claves:** Requiere únicamente 2,452 celdas en total, logrando la implementación más compacta y eficiente de la serie.
