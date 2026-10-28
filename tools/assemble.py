#!/usr/bin/env python3
"""Ensambla un .asm con MARS ("Compact, Text at Address 0") y genera la imagen de la RAM.

La imagen (formato "v3.0 hex words addressed" de Logisim) contiene .text desde 0x0000
y .data desde 0x2000. Se carga con clic derecho sobre la RAM > Cargar imagen.
Uso: python3 tools/assemble.py programs/hello.asm [-o images/hello.hex]
"""
from pathlib import Path
import argparse
import os
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
MARS = os.environ.get('MARS_JAR', str(Path.home()/'Apps/mars/Mars4_5.jar'))
JAVA = os.environ.get('JAVA', 'java')
INICIO_DATOS = 0x2000

# Codificaciones de S-MIPS (Tabla A.3 del material); el resto se avisa.
# addiu y addu no son de S-MIPS, pero MARS las genera para li y move: la CPU las trata como addi y add.
OPCODES = {0x02: 'j', 0x03: 'jal', 0x04: 'beq', 0x05: 'bne', 0x08: 'addi', 0x09: 'addiu', 0x0A: 'slti', 0x0C: 'andi',
           0x0D: 'ori', 0x0F: 'lui', 0x20: 'lb', 0x23: 'lw', 0x24: 'lbu', 0x28: 'sb', 0x2B: 'sw'}
FUNCTS = {0x00: 'sll', 0x02: 'srl', 0x08: 'jr', 0x0C: 'syscall', 0x20: 'add', 0x21: 'addu', 0x22: 'sub',
          0x24: 'and', 0x25: 'or', 0x2A: 'slt'}


def palabras(path):
    return [int(line, 16) for line in path.read_text().split()]


def fuera_de_smips(texto):
    avisos = []
    for index, word in enumerate(texto):
        op, fn = word >> 26, word & 0x3F
        if (op == 0 and fn not in FUNCTS) or (op != 0 and op not in OPCODES):
            avisos.append(f'  0x{4*index:04x}: 0x{word:08x} (op=0x{op:02x}' + (f', funct=0x{fn:02x})' if op == 0 else ')'))
    return avisos


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('fuente', type=Path)
    parser.add_argument('-o', '--salida', type=Path)
    args = parser.parse_args()
    salida = args.salida or ROOT/'images'/(args.fuente.stem + '.hex')
    with tempfile.TemporaryDirectory(prefix='smips-mars-') as directory:
        texto_hex, datos_hex = Path(directory)/'text.hex', Path(directory)/'data.hex'
        result = subprocess.run([JAVA, '-jar', MARS, 'nc', 'mc', 'CompactTextAtZero', 'a',
                                 'dump', '.text', 'HexText', str(texto_hex),
                                 'dump', '.data', 'HexText', str(datos_hex), str(args.fuente)],
                                capture_output=True, text=True)
        if result.returncode or not texto_hex.exists():
            sys.exit(f'MARS no pudo ensamblar {args.fuente}:\n{result.stdout}{result.stderr}')
        texto = palabras(texto_hex)
        datos = palabras(datos_hex) if datos_hex.exists() else []
    avisos = fuera_de_smips(texto)
    if avisos:
        print('Aviso: instrucciones fuera de S-MIPS (la CPU las tratara como ilegales y se detendra):', *avisos, sep='\n')
    lineas = ['v3.0 hex words addressed']
    for base, bloque in ((0, texto), (INICIO_DATOS//4, datos)):
        for i in range(0, len(bloque), 8):
            lineas.append(f'{base + i:03x}: ' + ' '.join(f'{w:08x}' for w in bloque[i:i + 8]))
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text('\n'.join(lineas) + '\n')
    print(f'OK: {salida} ({len(texto)} instrucciones, {len(datos)} palabras de datos)')


if __name__ == '__main__':
    main()
