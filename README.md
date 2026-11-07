<div align="center">

# Malbolge-PureEpoch

**Recuperación Multi-Época, Control de Flujo y Computación 100% Autónoma en Classic Malbolge**

[![Tests](https://img.shields.io/badge/Unit%20Tests-123%2F123%20PASS-brightgreen.svg)]()
[![Oracles](https://img.shields.io/badge/3--Oracle%20Parity-100%25%20Bit--Identical-blue.svg)]()
[![Loader](https://img.shields.io/badge/Olmstead%201998-Strict%20Compliant-success.svg)]()
[![Autonomy](https://img.shields.io/badge/Host%20Memory%20Writes-ZERO%20(100%25%20In--VM)-orange.svg)]()

*“State is not a screenshot. Recovery is not a replay.”*

---

</div>

## 01 / ¿Qué es Malbolge-PureEpoch?

Malbolge es legendario por automutar y cifrar cada instrucción inmediatamente después de ejecutarla mediante la tabla `XLAT2`. Históricamente, se asumió que cualquier intento de recuperación, repetición de instrucciones o cómputo complejo en Malbolge requería emulación externa o inyecciones de memoria desde el host.

**PureEpoch demuestra lo contrario:** es posible ejecutar bucles con repetición de direcciones físicas (`PC`), recuperarse de fallas bizantinas mediante journals toroidales, calcular autómatas celulares y ejecutar utilidades estándar de flujos (Unix utilities) **de forma 100% autónoma en memoria dentro de la VM original de Ben Olmstead (1998)**, sin una sola escritura externa del host durante el runtime.

---

## 02 / La Campaña de los 13 Hitos (The 13 Boss Battles)

La investigación se articuló en 13 hitos computacionales adversariales, todos completamente demostrados y verificados:

| Hito | Nombre / Utilidad | Tipo de Cómputo In-VM | Celdas (.mal) | Verificación |
| :--- | :--- | :--- | :--- | :---: |
| **Boss 1** | **Falla Bizantina** | Rollback anidado en cascada $J_1 \to J_2$ con Safe-Mode | 29,540 | 8/8 PASS |
| **Boss 2** | **Compilador BF** | Compilador lineal Brainfuck $\to$ Malbolge en línea recta | 1,348 | 7/7 PASS |
| **Boss 3** | **Bucle Autónomo** | Bucle `while x > 0` con **PC repetida** y rearmado dinámico | 30,500 | 12/12 PASS |
| **Boss 4** | **Autómata Wolfram** | Triángulo de Sierpiński in-VM (Regla 90 con XOR ternario) | 28,829 | 10/10 PASS |
| **Boss 5** | **`cat` Real** | Streaming universal transparente y terminación limpia en EOF | 13,185 | 14/14 PASS |
| **Boss 6** | **`rev` Real** | Pila LIFO en memoria con desapilado biyectivo inverso | 13,185 | 14/14 PASS |
| **Boss 7** | **`wc -c` Real** | Contador de longitud de flujo y emisor decimal rotatorio | 25,972 | 14/14 PASS |
| **Boss 8** | **`cmp` Real** | Predicado de igualdad en stream (`=` o `!`) con salto in-line | 29,667 | 14/14 PASS |
| **Boss 9** | **`add` Real** | ALU aritmética in-VM: evaluador de suma de un dígito | 26,474 | 14/14 PASS |
| **Boss 10** | **`sort2` Real** | Clasificador condicional min-max / Bubble Sort elemental | 2,452 | 14/14 PASS |
| **Boss 11** | **`reloj` Real** | Cronómetro digital 4-ticks `MM:SS\n` con discriminador universal | 29,936 | 14/14 PASS |
| **Boss 12** | **`reloj_infinito`** | Cronómetro digital 60s (`00:00`..`00:59`), rollover y densidad 26.8x | 16,759 | 13/13 PASS |
| **Boss 13** | **`reloj_carry`** | Acarreo BCD in-VM: transición `00:59` $\to$ `01:00` en memoria | 1,905 | 12/12 PASS |

---

## 03 / Suite de Utilidades Unix Clásicas

Cada utilidad opera como un binario `.mal` independiente o mediante CLI interactivo con soporte de tuberías Unix (`|`):

```bash
# Invertir texto en flujo (Boss 6: Rev Real)
$ echo -n "MALBOLGE" | python3 tools/rev_real_cli.py -q
EGLOBLAM

# Sumar dígitos en la ALU in-VM (Boss 9: Add Real)
$ echo -n "11" | python3 tools/add_real_cli.py -q
2

# Evaluar igualdad de tokens (Boss 8: Cmp Real)
$ echo -n "==" | python3 tools/cmp_real_cli.py -q
=

# Clasificar y ordenar elementos (Boss 10: Sort2 Real)
$ echo -n "10" | python3 tools/sort2_real_cli.py -q
01

# Cronómetro digital in-VM 4-ticks (Boss 11: Reloj Real)
$ echo -n "PPP" | python3 tools/reloj_real_cli.py -q
00:00
00:01
00:02

# Cronómetro digital completo 60 segundos in-VM (Boss 12: Reloj Infinito)
$ python3 tools/reloj_infinito_cli.py -q -n 4
00:00
00:01
00:02
00:03

# Acarreo temporal BCD in-VM 00:59 -> 01:00 (Boss 13: Reloj Carry)
$ python3 tools/reloj_carry_cli.py -q
00:59
01:00

# Composición en tubería Unix pura:
$ echo -n "21" | python3 tools/sort2_real_cli.py -q | python3 tools/rev_real_cli.py -q
21
```

---

## 04 / Documentación Técnica Modular

Para mantener este README conciso y accesible, el detalle matemático exhaustivo y la evidencia histórica se encuentran organizados en documentos modulares:

- 🏛️ **[Arquitectura Técnica](docs/ARCHITECTURE.md):** El problema de las 94 celdas, la mecánica de las tres épocas, el journaling toroidal sin memoria protegida y la VM reflexiva **BolgePiton** (el Ciclo Ouroboros).
- ⚔️ **[Boss Battles 1 a 4](docs/BOSS_BATTLES_1_4.md):** Falla bizantina en cascada, compilador Brainfuck lineal, resolución formal del bucle con PC repetida (**Boss 3 Ruta A**) y el autómata celular Wolfram Regla 90 (**Boss 4 Sierpiński**).
- 🛠️ **[Utilidades Unix y Cronometría](docs/UNIX_UTILITIES.md):** Análisis algebraico profundo, involuciones biyectivas en 121, discriminadores EOF, geometría de drenajes, cronómetros digitales y el motor de acarreo BCD in-VM de los Bosses 5 a 13 (`cat`, `rev`, `wc`, `cmp`, `add`, `sort2`, `reloj`, `reloj_infinito`, `reloj_carry`) con la falsación del ciclo 94.
- 🔬 **[Guía de Reproducibilidad y Oráculos](docs/REPRODUCIBILITY.md):** Protocolo de verificación sin conexión, triple paridad de oráculos (Python Machine M0, C `mb_ref`, Olmstead 1998 nativo) y controles negativos mutantes.

---

## 05 / Reproducción Rápida

Todo el laboratorio se ejecuta de forma determinista y offline utilizando únicamente la biblioteca estándar de Python 3.10+ y GCC:

```bash
# Clonar el laboratorio
git clone https://github.com/DannyBaanks/Malbolge-PureEpoch.git
cd Malbolge-PureEpoch

# Ejecutar la suite completa de las 9 utilidades Unix y Cronómetros (123/123 PASS)
python3 -m unittest \
  tests/test_cat_real.py \
  tests/test_rev_real.py \
  tests/test_wc_real.py \
  tests/test_cmp_real.py \
  tests/test_add_real.py \
  tests/test_sort2_real.py \
  tests/test_reloj_real.py \
  tests/test_reloj_infinito.py \
  tests/test_reloj_carry.py

# Ejecutar las Boss Battles 1 a 4 (35/35 PASS)
python3 -m unittest \
  tests/test_boss1_byzantine.py \
  tests/test_boss2_brainfuck.py \
  tests/test_boss3_real_loop.py \
  tests/test_boss4_v3_ca.py

# Verificar paridad estricta contra el ejecutable original de Ben Olmstead de 1998
python3 tools/reloj_carry_cli.py --oracles
```

---

## 06 / Política Anti-Fake y Frontera Honesta

Siguiendo el contrato de rigor científico de [`AGENTS.md`](file:///home/danny/Development/ISyCo/AGENTS.md):
- **Cero escrituras del host:** Prohibido inyectar valores en memoria de la VM (`vm.mem[...] = ...`) durante la ejecución de cualquier candidato.
- **Fail-Closed:** Cada programa cuenta con tres mutantes (`broken_drain`, `broken_eof`, `broken_loader`) que verifican que los fallos detienen el sistema de inmediato.
- **Lo que NO está demostrado:** PureEpoch **no** afirma haber construido una Máquina de Turing con memoria infinita ni un compilador universal arbitrario. Todas las afirmaciones se limitan estrictamente al espacio de estados y flujos acotados verificados empíricamente.

---

## 07 / Procedencia y Créditos

- **Autor de la arquitectura PureEpoch, BolgePiton y los 13 Bosses:** Danny Baanks & Antigravity (2026).
- **Especificación canónica de Malbolge e intérprete de referencia (1998):** Ben Olmstead.
- **Análisis criptográfico pionero de Malbolge (1998):** Lou Scheffer.
- **Ecosistema de investigación:** Ecosistema ISyCo Monorepo.
