#!/usr/bin/env python3
"""Ejecuta programas en la CPU de circuit/smips.circ y compara la salida del TTY con la de MARS.

Uso: python3 tools/run_tests.py [--circuito archivo.circ] [fuente.asm ...]
Sin fuentes prueba programs/*.asm y tests/*.asm. Necesita Java 21, MARS (MARS_JAR),
Logisim Evolution 5.0.0 (LOGISIM_JAR) y, solo si la CPU tiene entidades VHDL, Questa con licencia
(QUESTA_BIN, SALT_LICENSE_SERVER).
"""
from pathlib import Path
import argparse
import os
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
HERE = ROOT/'tools'
JAR = os.environ.get('LOGISIM_JAR', '/snap/logisim-evolution-snapcraft/current/jar/logisim-evolution.jar')
MARS = os.environ.get('MARS_JAR', str(Path.home()/'Apps/mars/Mars4_5.jar'))
JAVA = os.environ.get('JAVA', 'java')
CICLOS_MAX = 60000  # con 4-5 ciclos por instruccion, el programa mas largo usa unos 8000


def normalizar(texto):
    lineas = [linea.rstrip() for linea in texto.split('\n')]
    while lineas and not lineas[-1]:
        lineas.pop()
    return '\n'.join(lineas)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--circuito', type=Path, default=ROOT/'circuit/smips.circ')
    parser.add_argument('fuentes', type=Path, nargs='*')
    args = parser.parse_args()
    fuentes = args.fuentes or sorted((ROOT/'programs').glob('*.asm')) + sorted((ROOT/'tests').glob('*.asm'))
    with tempfile.TemporaryDirectory(prefix='smips-probar-') as directorio:
        directorio = Path(directorio)
        imagenes, esperado = {}, {}
        for fuente in fuentes:
            imagen = directorio/(fuente.stem + '.hex')
            subprocess.run([sys.executable, str(HERE/'assemble.py'), str(fuente), '-o', str(imagen)],
                           check=True, capture_output=True, text=True)
            mars = subprocess.run([JAVA, '-jar', MARS, 'nc', 'mc', 'CompactTextAtZero', str(fuente)],
                                  capture_output=True, text=True, check=True)
            imagenes[str(imagen)] = fuente
            esperado[fuente] = normalizar(mars.stdout)
        print(f'Ejecutando {len(fuentes)} programas en la placa...', flush=True)
        orden = [JAVA, f'-Djava.util.prefs.userRoot={directorio}/prefs', '--class-path', JAR,
                 str(HERE/'Run.java'), str(args.circuito.resolve()), str(CICLOS_MAX), '0', *imagenes]
        # Cada programa se informa en cuanto termina (la cosimulacion es lenta).
        proceso = subprocess.Popen(orden, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        resultados, fallos = [], 0
        for linea in proceso.stdout:
            if not linea.startswith('RESULTADO'):
                continue
            _, imagen, detenido, ciclos, pc, tty = linea.rstrip('\n').split('\t')
            resultados.append(imagen)
            fuente = imagenes[imagen]
            salida = normalizar(bytes.fromhex(tty).decode())
            ok = detenido == 'true' and salida == esperado[fuente]
            fallos += not ok
            print(f'{"OK   " if ok else "FALLO"} {os.path.relpath(fuente)}  ({ciclos} ciclos)', flush=True)
            if not ok:
                print(f'  detenido={detenido} (MEM_ADDR final 0x{pc})\n  esperado (MARS):\n    ' + esperado[fuente].replace('\n', '\n    ') +
                      '\n  obtenido (TTY):\n    ' + salida.replace('\n', '\n    '), flush=True)
        error = proceso.stderr.read()
        if proceso.wait() or len(resultados) != len(fuentes):
            sys.exit(f'Fallo la ejecucion:\n{error[-4000:]}')
    print(f'\n{len(resultados) - fallos}/{len(resultados)} correctos')
    sys.exit(1 if fallos else 0)


if __name__ == '__main__':
    main()
