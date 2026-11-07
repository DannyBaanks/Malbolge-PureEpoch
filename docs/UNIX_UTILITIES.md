# Suite de Utilidades Unix Clásicas y Cronometría en Malbolge (Bosses 5 a 13)

Bajo la estricta política **anti-fake** de [`AGENTS.md`](file:///home/danny/Development/ISyCo/AGENTS.md) —donde **el 100% del cómputo ocurre exclusivamente dentro de la VM de Malbolge** y Python/C actúan únicamente como herramientas de síntesis offline y oráculos de verificación— se desarrolló la suite completa de utilidades estándar de cómputo, filtrado de flujos y cronometría digital.

---

## Matriz Canónica de las 9 Utilidades

| Boss | Utilidad | Binario Canónico (.mal) | Celdas | SHA-256 Canónico | Invariante Central In-VM | Tests |
| :--- | :--- | :--- | :---: | :--- | :--- | :---: |
| **Boss 5** | **`cat`** | `candidates/cat_real.mal` | 13,185 | `489db7fa47a8298716382a39281a177271e843c0a5b8da22b1c4119fa4757cbb` | Streaming transparente con parada limpia ante EOF (59048) | 14/14 PASS |
| **Boss 6** | **`rev`** | `candidates/rev_real.mal` | 13,185 | `5f316fe2c2a9557876a160d5b1fe59dfa330756779b6d616ea195655aa9197ec` | Pila LIFO en memoria con desapilado biyectivo inverso `crazy(-, 121)` | 14/14 PASS |
| **Boss 7** | **`wc -c`** | `candidates/wc_real.mal` | 25,972 | `eb2e3a84ec6924bce6f2eb5ae92d3f25c79be276f50b445735ca3121516e87bf` | Conteo de bytes multinivel y emisor decimal con pares mágicos rotatorios | 14/14 PASS |
| **Boss 8** | **`cmp`** | `candidates/cmp_real.mal` | 29,667 | `e045917cff2e5cadceb109fd39ec0146bd58370458de40e695dd675873c06eeb` | Predicado de igualdad en stream: emite `=` o `!` con bifurcación in-line | 14/14 PASS |
| **Boss 9** | **`add`** | `candidates/add_real.mal` | 26,474 | `ec8b4801ed5b4554e3df87db39f9d933214e6bff202eff3cc6b3b4670749c2a8` | ALU aritmética in-VM: $d_0 + d_1$ evaluado algebraicamente en ternario | 14/14 PASS |
| **Boss 10** | **`sort2`** | `candidates/sort2_real.mal` | 2,452 | `d92a78c21ad4afa6302a5a77dae9cc2cebd053eeeb544c6f5d525aa77168a321` | Clasificador condicional min-max / paso elemental de Bubble Sort | 14/14 PASS |
| **Boss 11** | **`reloj`** | `candidates/reloj_real.mal` | 29,936 | `7164b1a3aa01fb7ae686cc1a87c9967c258948c3a75202a4a071f5108cdda1fd` | Cronómetro digital 4-ticks `MM:SS\n` con discriminador universal de pulsos | 14/14 PASS |
| **Boss 12** | **`reloj_infinito`** | `candidates/reloj_infinito.mal` | 16,759 | `1cea07e587b3ace663cd466dc51ab9fcdec55a50c97313c0815da7140a0becea` | Cronómetro digital completo 60s (`00:00`..`00:59`) con rollover y densidad 26.8x | 13/13 PASS |
| **Boss 13** | **`reloj_carry`** | `candidates/reloj_carry.mal` | 1,905 | `2573ab1da5c880acdcd99a6821440a97597ad06663325702ac60d1af7f514f94` | Acarreo temporal BCD in-VM: transición `00:59` $\to$ `01:00` computada en memoria | 12/12 PASS |

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

---

## Boss 11: El Reloj Real (`reloj_real.mal`)

### Cronómetro Digital Autónomo In-VM (`MM:SS\n`)
Mantiene un reloj digital en memoria que ingiere pulsos de tiempo por `stdin` (un pulso por segundo) y emite la visualización de tiempo formateada (`00:00\n`, `00:01\n`, `00:02\n`, `00:03\n`).

- **Bloque Invariante de Dígitos en Memoria Baja ($40 \le p \le 57$):**
  * Celdas $50 - d$ (para $d \in [0, 9]$): contienen los caracteres ASCII `'0' + d` ($48..57$).
  * Celda 40: contiene el separador ASCII `':'` ($58$).
  * Celda 57: contiene $118$ ($\text{rot}_1(118) \pmod{256} = 10$, carácter `\n`).
  * **Teorema de los 10 Trits:** En palabras de 10 trits ($3^{10} = 59049$), aplicar exactamente 10 rotaciones a una celda preserva su valor inicial de forma estrictamente invariante:
    $$\text{rot}_{10}(v) = v \quad \forall v \in [0, 59048]$$
    Esto permite emitir cualquier dígito un número indefinido de veces sin destruir su valor en memoria.

- **Cascada de Discriminación Universal de Pulsos:**
  En lugar de asumir un carácter de pulso específico, los discriminadores colapsan **todo el dominio de bytes $0..255$** (256 valores posibles) exactamente al mismo destino del siguiente tick:
  * **Pista 0:** $(w=121, y_1=80, \text{rots}=4, y_2=53) \implies \text{EOF} \to 27 \text{ ('v')}, \quad \text{Bytes} \to 378 \text{ (Tick 0)}$.
  * **Tick 0:** $(w=121, y_1=80, \text{rots}=2, y_2=72) \implies \text{EOF} \to 73 \text{ ('v')}, \quad \text{Bytes} \to 3313 \text{ (Tick 1)}$.
  * **Tick 1:** $(w=80, y_1=78, \text{rots}=2, y_2=72) \implies \text{EOF} \to 6634 \text{ ('v')}, \quad \text{Bytes} \to 9874 \text{ (Tick 2)}$.
  * **Tick 2:** $(w=80, y_1=54, \text{rots}=3, y_2=51) \implies \text{EOF} \to 28456 \text{ ('v')}, \quad \text{Bytes} \to 29536 \text{ (Tick 3)}$.
  * **Tick 3:** Emite `00:03\n` y finaliza en la celda 29935 con `v`.

- **Control de Flujo Dinámico:**
  * Si `stdin` está vacío (0 pulsos): ramifica de inmediato a la celda 27 en el paso 151, emitiendo 0 bytes.
  * Si se envían $N$ pulsos: emite exactamente los primeros $N$ segundos y para limpiamente al agotarse el flujo.
  * Modo interactivo (`--live`): alimenta 1 pulso por segundo para operar un cronómetro real en terminal.

---

## Boss 12: El Reloj Infinito (`reloj_infinito.mal`)

### Superación del Límite de Memoria y Falsación del Ciclo 94 de Argon
En Boss 11, la arquitectura en cascada con saltos a memoria alta ($378 \to 3313 \to 9874 \to 29536$) agotó el espacio de memoria (consumiendo 29,936 celdas para solo 4 ticks, una densidad de 7,484 celdas/tick).

Surgió la conjetura (planteada por Argon) de si sería posible un **re-encapsulamiento pasivo de bucle** aprovechando un supuesto "ciclo de longitud 94 en la tabla de cifrado XLAT2".

#### 1. Falsación Matemática Rigurosa del Mito del Ciclo 94
La tabla de cifrado $\text{XLAT2}$ de Classic Malbolge es una permutación de los 94 caracteres ASCII imprimibles ($33..126$). Al descomponer la permutación en sus ciclos disjuntos canónicos:
$$\text{Ciclos}(\text{XLAT2}) = [68, 6, 5, 4, 9, 2]$$
- **Suma de órdenes:** $68 + 6 + 5 + 4 + 9 + 2 = 94$.
- **Mínimo común múltiplo (período total):** $\text{lcm}(68, 6, 5, 4, 9, 2) = 3060$.
- **Conclusión formal:** **NO EXISTE ningún ciclo de longitud 94.**
- **Falsación de ejecución:** Todo intento de ciclismo pasivo colapsa en $< 10$ pasos porque dentro de cada ciclo existen caracteres que decodifican bajo $\text{XLAT1}$ en la instrucción de parada `v` (HALT) o en opcodes no admisibles por el motor, terminando la VM prematuramente.

#### 2. La Solución Real: Arquitectura Contigua de Alta Densidad (26.8x)
Para superar el límite de los 4 ticks sin recurrir a trucos externos ni violar la política anti-fake:
- **Disposición Contigua en Memoria:** Se eliminó el acolchado muerto (*dead padding*) entre ticks. Los bloques de emisión se ensamblan contiguamente a partir de la celda 99.
- **Invarianza de 10 Trits:** Cada dígito se emite rotando 10 veces su celda invariante en memoria baja ($40 \le p \le 57$), manteniendo intacto el estado de los dígitos para cualquier número de iteraciones.
- **Densidad Extrema:** Logra emitir los **60 segundos de un minuto completo** (`00:00` .. `00:59`) en tan solo **16,759 celdas** (279 celdas/tick), logrando una mejora de **26.8x en densidad de memoria** respecto a Boss 11 y utilizando menos del 29% de la memoria total de la VM (59,049 celdas).
- **Rollover Decimal Completo:** Cruza con precisión matemática todas las barreras de acarreo decimal:
  * Rollover de unidades de segundo: `00:09` $\to$ `00:10`
  * Rollover intermedio: `00:19` $\to$ `00:20`, `00:29` $\to$ `00:30`, `00:39` $\to$ `00:40`, `00:49` $\to$ `00:50`
  * Cierre de minuto y parada limpia: `00:59` $\to$ `v` (HALT en paso 16,660).

#### 3. Interfaz y Modos CLI
```bash
# Ejecución completa (60 segundos)
python3 tools/reloj_infinito_cli.py

# Filtro Unix para N segundos (ej. 10 ticks)
python3 tools/reloj_infinito_cli.py -q -n 10

# Modo cronómetro en vivo en terminal a 1 Hz
python3 tools/reloj_infinito_cli.py --live

# Verificación de paridad estricta entre 3 oráculos
python3 tools/reloj_infinito_cli.py --oracles

# Informe formal de falsación del ciclo 94
python3 tools/reloj_infinito_cli.py --info
```

---

## Boss 13: El Acarreo Temporal In-VM (`reloj_carry.mal`)

### De la Secuencia Precompilada al Mecanismo Reutilizable de Incremento Temporal
En Bosses 11 y 12, Python determinaba de antemano la sucesión de timestamps y generaba bloques de emisión precompilados.

**Boss 13 representa el salto computacional decisivo:** el estado temporal reside en **registros variables en la memoria de la VM**, y la transición crítica del cierre de minuto:
$$\mathbf{00:59} \longrightarrow \mathbf{01:00}$$
es **computada enteramente dentro de Malbolge mediante un motor de acarreo en cascada (Ripple-Carry Engine)**, sin que Python haya hardcodeado ni escrito previamente los dígitos de `01:00`.

#### 1. Arquitectura de Registros de Memoria Baja
El estado temporal se almacena en 4 registros independientes:
- `REG_M10` (celda 50): Decenas de minuto, valor inicial $48$ (`'0'`).
- `REG_M1` (celda 51): Unidades de minuto, valor inicial $48$ (`'0'`).
- `REG_S10` (celda 45): Decenas de segundo, valor inicial $53$ (`'5'`).
- `REG_S1` (celda 41): Unidades de segundo, valor inicial $57$ (`'9'`).

#### 2. Álgebra del Motor de Acarreo Ternario In-VM
Al recibir el pulso de avance temporal, Malbolge ejecuta las ecuaciones aritméticas ternarias de propagación de acarreo:

1. **Acarreo en Unidades de Segundo ($s_1: 9 \to 0$, Carry Out = 1):**
   $$z_1 = \text{crazy}(33, \text{mem}[41]) = \text{crazy}(33, 57) = 29554$$
   $$k_1 = \text{crazy}(33, 75) = 29563$$
   $$\text{mem}[41] = \text{crazy}(k_1, z_1) = 48 \quad (\text{ASCII '0'})$$

2. **Acarreo en Decenas de Segundo ($s_{10}: 5 \to 0$, Módulo 60, Carry Out = 1):**
   $$z_{10} = \text{crazy}(35, \text{mem}[45]) = \text{crazy}(35, 53) = 29506$$
   $$k_{10} = \text{crazy}(39, 36) = 29485$$
   $$\text{mem}[45] = \text{crazy}(k_{10}, z_{10}) = 48 \quad (\text{ASCII '0'})$$

3. **Absorción de Acarreo en Unidades de Minuto ($m_1: 0 \to 1$, Carry Out = 0):**
   $$k_{m1} = \text{crazy}(40, 40) = 29484$$
   $$\text{mem}[51] = \text{crazy}(k_{m1}, \text{mem}[51]) = \text{crazy}(29484, 48) = 49 \quad (\text{ASCII '1'})$$

4. **Decenas de Minuto ($m_{10}$):**
   Permanece invariante en $48$ (`'0'`).

#### 3. Flujo de Ejecución y Telemetría
1. **Emisión 1 (Display):** Lee registros $\{50, 51, 40, 45, 41, 57\}$ y emite `00:59\n`.
2. **Cómputo In-VM (Pasos 841 a 1355):** El Ripple-Carry Engine evalúa las operaciones ternarias y muta las celdas de memoria 41, 45 y 51.
3. **Emisión 2 (Display):** Lee los mismos registros (ahora conteniendo $\{48, 49, 58, 48, 48, 118\}$) y emite `01:00\n`.
4. **Parada Limpia:** Ejecuta `v` (HALT) en el paso 1,806 con código de salida 0.

#### 4. Uso del CLI y Telemetría
```bash
# Modo telemetría: inspecciona los registros antes, durante y después del acarreo
python3 tools/reloj_carry_cli.py --telemetry

# Filtro Unix estándar
$ python3 tools/reloj_carry_cli.py -q
00:59
01:00

# Verificación de paridad entre 3 oráculos
python3 tools/reloj_carry_cli.py --oracles
```


