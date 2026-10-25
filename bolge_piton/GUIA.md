# GUIA.md — Guía de Operación Humana de BolgePiton

**BolgePiton** es la demostración del ciclo inverso de **Pibolge**: una Máquina Virtual en **Malbolge puro** (`.mal`) capaz de interpretar y ejecutar programas en **Micro-Pitón** (sintaxis en español de Pitón).

---

## 1. El Bucle Ouroboros (Pitón $\to$ Malbolge $\to$ Pitón)

El sistema demuestra una jerarquía de ejecución reflexiva de tres niveles con paridad exacta:

```
[ Nivel 0: Host Python 3.12 ]
          │
          ▼
[ Nivel 1: pibolge.piton ]  (Intérprete canónico de Malbolge escrito en Pitón)
          │
          ▼
[ Nivel 2: bolge_piton_vm.mal ]  (VM en Malbolge sintetizada con PureEpoch)
          │
          ▼
[ Nivel 3: script en Micro-Pitón ]  (Código en español: imprimir_texto, cargar, locura)
```

---

## 2. Comandos Rápidos

### A. Demostración CLI con Ouroboros
Ejecuta el ejemplo interactivo que corre el script en C y luego a través de Pibolge:

```bash
python3 workspace/labs/bolge_piton/bolge_piton_cli.py
```

### B. Ejecutar un Texto Personalizado
```bash
python3 workspace/labs/bolge_piton/bolge_piton_cli.py --texto 'imprimir_texto "Hola Danny!"'
```

### C. Correr la Suite de Pruebas Unitaria (4/4 PASS)
```bash
python3 workspace/labs/bolge_piton/ouroboros_test.py -v
```

---

## 3. Sintaxis Soportada de Micro-Pitón

| Comando en Español | Descripción |
|---|---|
| `imprimir_texto "..."` | Emite la cadena de caracteres a stdout. |
| `emitir <byte>` | Emite un byte ASCII o número directo a stdout. |
| `cargar <n>` | Carga el valor `<n>` en el acumulador virtual de la VM (`mem[75]`). |
| `locura <m>` | Aplica la involución ternaria de Malbolge `crazy(m, acc)`. |
| `imprimir` | Emite el valor del acumulador a stdout. |
| `parar` / `alto` | Detiene la máquina virtual limpiamente (`HALT`). |
