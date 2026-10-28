#!/usr/bin/env python3
"""Genera circuit/smips.circ: placa con memoria, TTY y un subcircuito CPU vacio.

Fase 1 coloca componentes; Logisim informa donde quedan sus puertos
(Ports.java) y la fase 2 conecta cada puerto a un tunel con su senal.
"""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as E

HERE = Path(__file__).resolve().parent
SALIDA = HERE.parent/'circuit/smips.circ'
JAR = os.environ.get('LOGISIM_JAR', '/snap/logisim-evolution-snapcraft/current/jar/logisim-evolution.jar')
JAVA = os.environ.get('JAVA', 'java')

# Interfaz de la CPU: (nombre, ancho). Entradas a la izquierda, salidas a la derecha.
CPU_ENTRADAS = [('CLK', 1), ('RESET', 1), ('MEM_RDATA', 32)]
CPU_SALIDAS = [('MEM_ADDR', 32), ('MEM_WDATA', 32), ('MEM_BE', 4), ('MEM_WE', 1),
               ('TTY_DATA', 7), ('TTY_WE', 1), ('HALT', 1)]
MEM_ENTRADAS = [('CLK', 1), ('ADDR', 32), ('WDATA', 32), ('BE', 4), ('WE', 1)]
MEM_SALIDAS = [('RDATA', 32)]
BITS_DIRECCION = 12  # 4096 palabras = 16 KiB: el espacio "Compact, Text at Address 0" de MARS

LIBRERIAS = ['#Wiring', '#Gates', '#Plexers', '#Arithmetic', '#FPArithmetic', '#Memory', '#I/O', '#Base']
WIRING, GATES, MEMORY, IO, BASE = '0', '1', '5', '6', '7'
PASO = 40  # separacion entre puertos de los subcircuitos


def comp(circuit, name, xy, lib=None, **attrs):
    data = {'name': name, 'loc': f'({xy[0]},{xy[1]})'}
    if lib is not None:
        data['lib'] = lib
    node = E.SubElement(circuit, 'comp', data)
    for key, value in attrs.items():
        E.SubElement(node, 'a', {'name': key, 'val': str(value)})
    return node


def cable(circuit, a, b):
    if a != b:
        E.SubElement(circuit, 'wire', {'from': f'({a[0]},{a[1]})', 'to': f'({b[0]},{b[1]})'})


def texto(circuit, xy, text, size=14, bold=False):
    comp(circuit, 'Text', xy, BASE, text=text, font=f'SansSerif {"bold" if bold else "plain"} {size}')


def subcircuito(root, name, entradas, salidas, titulo):
    """Crea el circuito con sus pines y una apariencia con un puerto cada PASO px."""
    circuit = E.SubElement(root, 'circuit', {'name': name})
    E.SubElement(circuit, 'a', {'name': 'appearance', 'val': 'custom'})
    filas = max(len(entradas), len(salidas))
    ancho, alto = 220, PASO*filas
    # Un pin de entrada se dibuja a la izquierda de su punto de conexion (hasta 8 bits por fila, 10 px cada uno)
    # y su etiqueta a la izquierda del cuerpo: la columna se aleja del borde lo que ocupe la etiqueta mas larga.
    entrada_x = 60 + max(10*min(w, 8) + 10 + 8*len(n) for n, w in entradas)
    entrada_x = -(-entrada_x//10)*10
    appear = E.SubElement(circuit, 'appear')
    E.SubElement(appear, 'rect', {'fill': 'none', 'height': str(alto), 'stroke': '#000000', 'stroke-width': '2',
                                  'width': str(ancho), 'x': '50', 'y': '50'})
    E.SubElement(appear, 'text', {'dominant-baseline': 'central', 'font-family': 'SansSerif', 'font-size': '16',
                                  'font-weight': 'bold', 'text-anchor': 'middle',
                                  'x': str(50 + ancho//2), 'y': str(50 + alto//2)}).text = titulo
    for lado, pines in (('in', entradas), ('out', salidas)):
        pin_y = 140
        for index, (pin_name, width) in enumerate(pines):
            y = 50 + PASO//2 + PASO*index
            x = 50 if lado == 'in' else 50 + ancho
            # Dentro del circuito, los pines de bus son altos: se separan segun su ancho.
            pin_xy = (entrada_x if lado == 'in' else 900, pin_y)
            pin_y += 100 if width > 8 else 50
            attrs = dict(label=pin_name, width=width, appearance='classic', labelfont='SansSerif plain 12')
            if lado == 'out':
                attrs.update(type='output', facing='west', labelloc='east')
            comp(circuit, 'Pin', pin_xy, WIRING, **attrs)
            E.SubElement(appear, 'text', {'dominant-baseline': 'central', 'font-family': 'SansSerif', 'font-size': '11',
                                          'text-anchor': 'start' if lado == 'in' else 'end',
                                          'x': str(x + 5 if lado == 'in' else x - 5), 'y': str(y)}).text = pin_name
            E.SubElement(appear, 'circ-port', {'dir': lado, 'pin': f'{pin_xy[0]},{pin_xy[1]}', 'x': str(x), 'y': str(y)})
    E.SubElement(appear, 'circ-anchor', {'facing': 'east', 'x': '50', 'y': '50'})
    return circuit


def herramientas(root):
    """Raton y barra de herramientas de la plantilla por defecto de Logisim (default.templ).
    Sin <mappings> el clic derecho no abre el menu (Load Image...) y sin <toolbar> no hay mano ni flecha."""
    mappings = E.SubElement(root, 'mappings')
    for name, boton in (('Poke Tool', 'Button2'), ('Menu Tool', 'Button3'), ('Menu Tool', 'Ctrl Button1')):
        E.SubElement(mappings, 'tool', {'lib': BASE, 'map': boton, 'name': name})
    toolbar = E.SubElement(root, 'toolbar')
    for item in [(BASE, 'Poke Tool', {}), (BASE, 'Edit Tool', {}), (BASE, 'Wiring Tool', {}),
                 (BASE, 'Text Tool', {}), None,
                 (WIRING, 'Pin', {}), (WIRING, 'Pin', {'facing': 'west', 'type': 'output'}), None,
                 (GATES, 'NOT Gate', {}), (GATES, 'AND Gate', {}), (GATES, 'OR Gate', {}),
                 (GATES, 'XOR Gate', {}), (GATES, 'NAND Gate', {}), (GATES, 'NOR Gate', {}), None,
                 (MEMORY, 'D Flip-Flop', {}), (MEMORY, 'Register', {})]:
        if item is None:
            E.SubElement(toolbar, 'sep')
            continue
        lib, name, attrs = item
        tool = E.SubElement(toolbar, 'tool', {'lib': lib, 'name': name})
        for key, value in attrs.items():
            E.SubElement(tool, 'a', {'name': key, 'val': value})


def fase1():
    root = E.Element('project', {'source': '5.0.0', 'version': '1.0'})
    root.text = '\n  This file is intended to be loaded by Logisim-evolution v5.0.0(https://github.com/logisim-evolution/).\n\n  '
    for index, desc in enumerate(LIBRERIAS):
        E.SubElement(root, 'lib', {'desc': desc, 'name': str(index)})
    E.SubElement(root, 'main', {'name': 'Board'})
    options = E.SubElement(root, 'options')
    for key, value in (('gateUndefined', 'ignore'), ('simlimit', '1000'), ('simrand', '0')):
        E.SubElement(options, 'a', {'name': key, 'val': value})
    herramientas(root)

    placa = E.SubElement(root, 'circuit', {'name': 'Board'})
    texto(placa, (560, 40), 'S-MIPS | Board', 22, bold=True)
    texto(placa, (560, 70), 'No modificar: la CPU se implementa dentro del subcircuito CPU.', 13)
    comp(placa, 'Clock', (120, 160), WIRING, label='Reloj', facing='east')
    comp(placa, 'Button', (120, 240), IO, label='Reset', facing='east')
    comp(placa, 'CPU', (400, 140))
    comp(placa, 'Memory', (960, 140))
    comp(placa, 'TTY', (420, 620), IO, rows=12, cols=48)
    comp(placa, 'LED', (1020, 500), IO, label='Halt', facing='west')

    cpu = subcircuito(root, 'CPU', CPU_ENTRADAS, CPU_SALIDAS, 'CPU')
    texto(cpu, (500, 40), 'CPU S-MIPS: implementar aqui', 20, bold=True)
    texto(cpu, (500, 65), 'No cambiar nombres, anchos ni sentido de los pines: la placa depende de ellos.', 12)

    memoria = subcircuito(root, 'Memory', MEM_ENTRADAS, MEM_SALIDAS, 'Memory')
    texto(memoria, (480, 30), f'Memoria unificada: {2**BITS_DIRECCION} palabras de 32 bits (16 KiB), little-endian', 14, bold=True)
    texto(memoria, (480, 52), 'Lectura combinacional; escritura en el flanco de subida de CLK con WE=1, solo en los bytes con BE=1.', 12)
    texto(memoria, (480, 72), 'Se usan los bits 13..2 de ADDR; los demas se ignoran (el espacio se repite cada 16 KiB).', 12)
    split = {f'bit{i}': ('0' if 2 <= i < 2 + BITS_DIRECCION else 'none') for i in range(32)}
    comp(memoria, 'Splitter', (280, 520), WIRING, incoming=32, fanout=1, appear='center', **split)
    comp(memoria, 'Splitter', (280, 640), WIRING, incoming=4, fanout=4, appear='center', spacing=3)
    comp(memoria, 'Constant', (280, 860), WIRING)
    comp(memoria, 'RAM', (740, 300), MEMORY, addrWidth=BITS_DIRECCION, dataWidth=32, databus='bibus',
         byteenables='byteEnables', asyncread='true', appearance='classic', label='Main_Memory', type='nonvolatile')
    return root


def puertos(root):
    with tempfile.TemporaryDirectory(prefix='smips-layout-') as directory:
        stage = Path(directory)/'fase1.circ'
        E.ElementTree(root).write(stage, encoding='UTF-8', xml_declaration=True)
        result = subprocess.run([JAVA, '-Djava.awt.headless=true', f'-Djava.util.prefs.userRoot={directory}/prefs',
                                 '--class-path', JAR, str(HERE/'Ports.java'), str(stage)],
                                capture_output=True, text=True, timeout=120)
    if result.returncode:
        sys.exit(result.stdout + result.stderr)
    rows = []
    for line in result.stdout.splitlines():
        fields = line.split('\t')
        if len(fields) == 9:
            circuit, kind, loc, index, tip, xy, width, _, bounds = fields
            x, y = map(int, xy.split(','))
            rows.append(dict(circuit=circuit, kind=kind, loc=loc, index=int(index), tip=tip, x=x, y=y,
                             width=int(width), bounds=tuple(map(int, bounds.split(',')))))
    return rows


def lado(port):
    if port['kind'] == 'Splitter':
        return 'west' if port['index'] == 0 else 'east'
    bx, by, bw, bh = port['bounds']
    distancias = {'west': port['x'] - bx, 'east': bx + bw - port['x'],
                  'north': port['y'] - by, 'south': by + bh - port['y']}
    return min(distancias, key=distancias.get)


def tunel(circuit, xy, label, width, facing):
    comp(circuit, 'Tunnel', xy, WIRING, label=label, width=width, facing=facing, labelfont='SansSerif plain 12')


def tunel_directo(circuit, port, label, length=30):
    dx, dy, facing = {'west': (-1, 0, 'east'), 'east': (1, 0, 'west'),
                      'north': (0, -1, 'south'), 'south': (0, 1, 'north')}[lado(port)]
    end = (port['x'] + dx*length, port['y'] + dy*length)
    cable(circuit, (port['x'], port['y']), end)
    tunel(circuit, end, label, port['width'], facing)


def escalera_oeste(circuit, ports):
    """Saca hacia la izquierda puertos muy juntos: codos anidados que no se cruzan,
    con los tuneles separados PASO px por debajo del ultimo puerto."""
    ports = sorted(ports, key=lambda p: p['y'])
    n, x = len(ports), ports[0]['x']
    fondo, extremo = ports[-1]['y'] + 30, x - 30 - 10*n - 40
    for k, port in enumerate(ports):
        codo, destino = x - 20 - 10*(n - 1 - k), fondo + PASO*k
        ruta = [(x, port['y']), (codo, port['y']), (codo, destino), (extremo, destino)]
        for a, b in zip(ruta, ruta[1:]):
            cable(circuit, a, b)
        tunel(circuit, (extremo, destino), port['label'], port['width'], 'east')


def etiqueta_ram(tip):
    clave = tip.split(':')[0].strip().lower()
    if clave.startswith('byte enable for byte'):
        return 'BE' + clave[-1]
    return {'address': 'A', 'data': 'RDATA', 'input': 'WDATA', 'load': 'UNO',
            'store': 'WE', 'clock': 'CLK'}[clave]


def fase2(root, rows):
    circuitos = {c.get('name'): c for c in root.findall('circuit')}
    placa_memoria = {'CLK': 'CLK', 'ADDR': 'MEM_ADDR', 'WDATA': 'MEM_WDATA', 'BE': 'MEM_BE',
                     'WE': 'MEM_WE', 'RDATA': 'MEM_RDATA'}
    tty = {'clear': 'RESET', 'clock': 'CLK', 'write enable': 'TTY_WE', 'data': 'TTY_DATA'}
    ram_oeste, tty_puertos = [], []
    for port in rows:
        circuit, kind, index = port['circuit'], port['kind'], port['index']
        if circuit == 'CPU':
            continue
        label = None
        if circuit == 'Board':
            if kind == 'CPU': label = port['tip']
            elif kind == 'Memory': label = placa_memoria[port['tip']]
            elif kind == 'Clock': label = 'CLK'
            elif kind == 'Button': label = 'RESET'
            elif kind == 'LED': label = 'HALT'
            elif kind == 'TTY':
                tty_puertos.append(dict(port, label=tty[port['tip'].split(':')[0].strip().lower()]))
                continue
        elif circuit == 'Memory':
            if kind == 'Pin': label = port['tip']
            elif kind == 'Splitter' and port['width'] in (32, BITS_DIRECCION): label = 'ADDR' if index == 0 else 'A'
            elif kind == 'Splitter': label = 'BE' if index == 0 else f'BE{index - 1}'
            elif kind == 'Constant': label = 'UNO'
            elif kind == 'RAM':
                label = etiqueta_ram(port['tip'])
                if lado(port) == 'west':
                    ram_oeste.append(dict(port, label=label))
                    continue
        if label is None:
            raise ValueError(f'Puerto sin conectar: {port}')
        tunel_directo(circuitos[circuit], port, label)
    escalera_oeste(circuitos['Memory'], ram_oeste)
    # El TTY tiene dos puertos al oeste y dos al sur, a 10 px: se reparten hacia la izquierda.
    placa = circuitos['Board']
    x0 = min(p['x'] for p in tty_puertos) - 40
    for port in (p for p in tty_puertos if lado(p) == 'west'):
        if port['label'] == 'TTY_DATA':
            tunel_directo(placa, port, 'TTY_DATA', 40)
        else:
            ruta = [(port['x'], port['y']), (port['x'] - 10, port['y']), (port['x'] - 10, port['y'] + 50),
                    (x0, port['y'] + 50)]
            for a, b in zip(ruta, ruta[1:]):
                cable(placa, a, b)
            tunel(placa, ruta[-1], port['label'], 1, 'east')
    sur = sorted((p for p in tty_puertos if lado(p) == 'south'), key=lambda p: p['x'])
    for k, port in enumerate(sur):
        destino = port['y'] + 70 + PASO*k
        cable(placa, (port['x'], port['y']), (port['x'], destino))
        cable(placa, (port['x'], destino), (x0, destino))
        tunel(placa, (x0, destino), port['label'], 1, 'east')


def main():
    root = fase1()
    rows = puertos(root)
    if '--puertos' in sys.argv:
        for row in rows: print(row)
        return
    fase2(root, rows)
    E.indent(root, space='  ')
    E.ElementTree(root).write(SALIDA, encoding='UTF-8', xml_declaration=True)
    print(f'OK: {SALIDA}')


if __name__ == '__main__':
    main()
