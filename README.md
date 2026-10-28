# S-MIPS: layout para implementar la CPU

Placa de Logisim Evolution 5.0.0 lista para que se implemente dentro una CPU **multiciclo** de S-MIPS. La placa (memoria, terminal, reloj, reset y halt) ya está resuelta; el subcircuito `CPU` está vacío, solo con su interfaz.

```text
SMIPS-Layout/
├── docs/guide.pdf          Orientación y especificación completa del proyecto (fuente: guide.tex)
├── circuit/smips.circ      Circuitos Board, CPU (vacío) y Memory
├── programs/               Programas .asm: ejemplos (hello, array_sum, gcd, multiply) y pruebas de instrucciones (arithmetic, memory, branches)
├── tests/                  (la crea el estudiante) programas de prueba propios: sección 7 de guide.pdf
├── images/                 Imágenes de memoria generadas desde los .asm
├── open.sh                 Abre el circuito en Logisim (con Questa si la CPU usa VHDL)
└── tools/                  assemble.py (MARS → imagen), run_tests.py (compara con MARS), build.py
```

**La especificación del proyecto está en [`docs/guide.pdf`](docs/guide.pdf).** Este archivo solo resume la placa y el flujo de trabajo.

## 1. Circuitos

| Circuito | Contenido | ¿Se modifica? |
|---|---|---|
| `Board` (principal) | Reloj, botón Reset, CPU, Memory, TTY y LED Halt, conectados por túneles | No |
| `CPU` | Solo los pines de la interfaz | **Sí: aquí se implementa la CPU** |
| `Memory` | RAM nativa de 4096 × 32 bits con habilitación por bytes | No |

No se requiere Questa para usar la placa: todo es nativo de Logisim.

## 2. Interfaz de la CPU

| Pin | Dir. | Ancho | Significado |
|---|---|---|---|
| `CLK` | entrada | 1 | Reloj de la placa. Memoria y TTY actúan en el flanco de subida. |
| `RESET` | entrada | 1 | Botón Reset (1 mientras está pulsado). |
| `MEM_RDATA` | entrada | 32 | Palabra alineada que contiene la dirección `MEM_ADDR`. Llega en el **mismo ciclo** (lectura combinacional). |
| `MEM_ADDR` | salida | 32 | Dirección de byte. La memoria ignora los bits 1..0 y lee/escribe la palabra alineada. |
| `MEM_WDATA` | salida | 32 | Dato a escribir, ya colocado en su carril de byte. |
| `MEM_BE` | salida | 4 | Habilitación por byte: el bit *k* escribe `MEM_WDATA[8k+7..8k]`. `sw` → `1111`; `sb` → un solo bit, según `MEM_ADDR[1..0]`. |
| `MEM_WE` | salida | 1 | Con 1, la memoria escribe en el próximo flanco de subida de `CLK`. |
| `TTY_DATA` | salida | 7 | Código ASCII del carácter a imprimir. |
| `TTY_WE` | salida | 1 | Con 1, el TTY imprime `TTY_DATA` en el próximo flanco de subida. Debe durar **un ciclo** por carácter. |
| `HALT` | salida | 1 | Enciende el LED Halt (`syscall` 10). |

La memoria es *little-endian*: el byte de la dirección `4n + k` es `MEM_RDATA[8k+7..8k]` al leer la palabra `4n`. Por tanto, `lb`/`lbu` deben seleccionar el byte con `MEM_ADDR[1..0]` y extenderlo, y `sb` debe replicar o desplazar el byte al carril correcto. Ese trabajo es de la CPU.

## 3. Mapa de memoria

Corresponde a la configuración **«Compact, Text at Address 0»** de MARS (*Settings → Memory Configuration*):

| Región | Dirección |
|---|---|
| `.text` (PC inicial) | `0x0000` |
| `$gp` inicial | `0x1800` |
| `.data` | `0x2000` |
| `$sp` inicial | `0x3FFC` |

La memoria tiene 16 KiB (`0x0000`–`0x3FFF`). Las direcciones superiores se repiten cada 16 KiB. Al hacer reset, la CPU debe poner PC = 0, `$sp` = `0x3FFC`, `$gp` = `0x1800` y el resto de registros a 0, como hace MARS. El botón Reset no borra la memoria.

## 4. Servicios `syscall`

| `$v0` | Servicio | Efecto en la placa |
|---|---|---|
| 11 | imprimir carácter | `TTY_DATA ← $a0[6..0]`, `TTY_WE = 1` durante un ciclo |
| 10 | terminar | `HALT = 1`; la CPU deja de avanzar |
| otro | — | sin efecto: continúa con la instrucción siguiente |

Una instrucción ilegal detiene la CPU igual que `syscall` 10. Los detalles están en `docs/guide.pdf`.

## 5. Ejecutar un programa

1. Ensamblar (requiere Java y MARS 4.5; ruta configurable con `MARS_JAR`):
   ```bash
   python3 tools/assemble.py programs/hello.asm
   ```
   Genera `images/hello.hex` con `.text` desde `0x0000` y `.data` desde `0x2000`. Avisa si el código contiene instrucciones fuera de S-MIPS.
2. Abrir `circuit/smips.circ` en Logisim Evolution 5.0.0.
3. Entrar en `Memory` desde la simulación (pestaña **Simulate** del panel izquierdo → `Board` → `Memory`, o clic derecho sobre el bloque en la placa → **View Memory**), hacer clic derecho en la RAM → **Load Image…** y elegir `images/hello.hex`. No abrirla desde la lista de la pestaña **Design**: así se edita una copia aislada y la placa no ve la imagen.
4. Volver a `Board`, pulsar **Reset** con la herramienta de la mano y activar los ticks del reloj.

## 6. Regenerar el circuito

`python3 tools/build.py` reconstruye `circuit/smips.circ` desde cero (necesita Java 21 y el JAR de Logisim 5.0.0 en `LOGISIM_JAR`). **Sobrescribe el archivo**: no lo ejecutes sobre una copia en la que ya se haya implementado la CPU.

## 7. Comprobar la CPU

```bash
bash open.sh                                     # abre circuit/smips.circ (activa la simulación VHDL si hace falta)
python3 tools/run_tests.py                       # programs/*.asm y tests/*.asm: TTY comparado con MARS
python3 tools/run_tests.py programs/memory.asm # un solo programa
```

`run_tests.py` ensambla cada programa, obtiene la salida esperada con MARS, lo ejecuta en la placa y compara el texto del TTY. Requiere Java 21, MARS y Logisim 5.0.0 (`LOGISIM_JAR`, `MARS_JAR`); si la CPU tiene entidades VHDL, también Questa con licencia (`QUESTA_BIN`, `SALT_LICENSE_SERVER`), y entonces la simulación es más lenta.
