# Especificación Canónica de la ABI de Malbolge-PureEpoch (v1.0)

Este documento fija la especificación formal e inmutable de la máquina virtual Malbolge (Olmstead 1998) bajo el contrato canónico de **PureEpoch**, resolviendo todas las ambigüedades entre emuladores históricos, el compilador C de referencia, el runtime nativo en Zig y el observador en Python.

---

## 1. Espacio de Memoria y Representación

* **Capacidad:** La memoria consta de exactamente $3^{10} = 59,049$ palabras de 10 trits (rango entero $0 \le w \le 59,048$).
* **Registros:**
  * $A$ (Acumulador): 10 trits ($0 \le A \le 59,048$).
  * $C$ (Code Pointer): Dirección de la instrucción actual ($0 \le C \le 59,048$).
  * $D$ (Data Pointer): Dirección del operando actual ($0 \le D \le 59,048$).
* **Inicialización:**
  * Los primeros $N$ bytes del archivo fuente (ignorando espacios en blanco ASCII `\t`, `\n`, `\v`, `\f`, `\r`, `' '`) se cargan en `mem[0..N-1]`.
  * Todo byte fuente debe cumplir $33 \le b \le 126$ y su instrucción descifrada inicial debe pertenecer al conjunto válido:
    $$\text{VALID\_INIT} = \{'j', 'i', '*', 'p', '<', '/', 'v', 'o'\}$$
  * Las celdas restantes $N \le i < 59,049$ se completan determinísticamente mediante la operación crazy:
    $$\text{mem}[i] = \text{crazy}(\text{mem}[i-1], \text{mem}[i-2])$$
    *(Nota crítica de orden de operandos: `mem[i-1]` actúa sobre `mem[i-2]`, equivalente a `o[y/p9[j]%9][x/p9[j]%9]` en C)*.

---

## 2. Ciclo de Instrucción Canónico

En cada paso $S_t$:

1. **Validación de PC imprimible:**
   Si $\text{mem}[C] < 33$ o $\text{mem}[C] > 126$, la VM aborta inmediatamente con estado **`STALL`** (código de salida 3 en CLI).

2. **Decodificación de Instrucción:**
   $$\text{instr} = \text{XLAT1}[(\text{mem}[C] - 33 + C) \pmod{94}]$$

3. **Ejecución Semántica:**
   * **`'j'` (Jump):**
     $$D = \text{mem}[D]$$
   * **`'i'` (Indirect Jump):**
     $$C = \text{mem}[D]$$
   * **`'*'` (Rotate Trit Right):**
     $$\text{rotated} = \lfloor \text{mem}[D] / 3 \rfloor + (\text{mem}[D] \pmod 3) \times 19,683$$
     $$\text{mem}[D] = \text{rotated}, \quad A = \text{rotated}$$
   * **`'p'` (Crazy Tritwise):**
     $$\text{res} = \text{crazy}(A, \text{mem}[D])$$
     $$\text{mem}[D] = \text{res}, \quad A = \text{res}$$
   * **`'<'` (Output Character):**
     Emite a stdout el byte truncado $A \ \& \ 255$. El registro $A$ preserva su valor completo de 10 trits.
   * **`'/'` (Input Character):**
     Lee un byte de stdin. Si se alcanza EOF, $A = 59,048$ ($3^{10}-1$). En caso contrario, $A = \text{byte}$.
   * **`'v'` (Halt):**
     La máquina detiene la ejecución inmediatamente con estado **`HALT`** (código de salida 0 en CLI). No se ejecuta la fase de cifrado ni el incremento de punteros.
   * **Cualquier otro caracter (`'o'` o caracter no-operador en $33..126$):**
     Se ejecuta como **NOP estricto**. No modifica $A$, $D$ ni el estado interno. Continúa hacia la fase de cifrado.

4. **Cifrado Post-Ejecución (`XLAT2`):**
   Si $\text{mem}[C] < 33$ o $\text{mem}[C] > 126$, la VM aborta con **`STALL`**.
   En caso contrario:
   $$\text{mem}[C] = \text{XLAT2}[\text{mem}[C] - 33]$$

5. **Avance de Punteros:**
   $$C = (C + 1) \pmod{59,049}$$
   $$D = (D + 1) \pmod{59,049}$$
   $$\text{steps} = \text{steps} + 1$$

---

## 3. Invariantes de No-Interferencia de PureEpoch

* **Distancia Mínima de Punteros:**
  Para evitar que la cabeza lectora de código $C$ altere las celdas apuntadas por la cabeza de datos $D$, los generadores garantizan:
  $$\min(|C - D|, 59,049 - |C - D|) \ge 42$$
* **Zona de Journal Toroidal:**
  El área de journal reside en un anillo de memoria desacoplado topológicamente de los buffers de datos y de la zona de emisión.
* **Cero Inyecciones desde el Host:**
  El host jamás modifica celdas de memoria durante el ciclo de vida de la VM. Todo cálculo, acarreo y reparación es 100% in-VM.
