# Prueba de lw, sw, lb, lbu y sb (little-endian), y de los valores iniciales de $gp y $sp.
        .data
palabra: .word 0x8070f00d
bytes:   .byte 0x11, -23, 0x7f, -128   # 0x11 0xe9 0x7f 0x80
destino: .space 8

        .text
main:   add  $a0, $gp, $zero         # $gp inicial = 0x1800
        jal  imprimir_hex
        add  $a0, $sp, $zero         # $sp inicial = 0x3ffc
        jal  imprimir_hex
        la   $s0, palabra
        lw   $a0, 0($s0)
        jal  imprimir_hex
        lbu  $a0, 0($s0)             # byte de la direccion mas baja = 0x0d
        jal  imprimir_hex
        lbu  $a0, 3($s0)             # 0x80
        jal  imprimir_hex
        jal  nueva_linea

        lb   $a0, 3($s0)             # 0x80 con signo -> 0xffffff80
        jal  imprimir_hex
        lb   $a0, 2($s0)             # 0x70
        jal  imprimir_hex
        lb   $a0, 5($s0)             # bytes[1] = 0xe9 -> 0xffffffe9
        jal  imprimir_hex
        lbu  $a0, 5($s0)             # 0x000000e9
        jal  imprimir_hex
        lw   $a0, 4($s0)             # bytes leidos como palabra: 0x807fe911
        jal  imprimir_hex
        jal  nueva_linea

        # sb en los cuatro carriles: arma 0xddccbbaa byte a byte
        la   $s1, destino
        addi $t6, $zero, 0xaa
        sb   $t6, 0($s1)
        addi $t6, $zero, 0xbb
        sb   $t6, 1($s1)
        addi $t6, $zero, 0xcc
        sb   $t6, 2($s1)
        addi $t6, $zero, 0xdd
        sb   $t6, 3($s1)
        lw   $a0, 0($s1)
        jal  imprimir_hex
        # sb solo cambia un byte de la palabra
        lui  $t6, 0x1234
        ori  $t6, $t6, 0x5678
        sw   $t6, 4($s1)
        addi $t6, $zero, -1          # 0xffffffff: se escribe solo el byte bajo
        sb   $t6, 6($s1)
        lw   $a0, 4($s1)             # 0x12ff5678
        jal  imprimir_hex
        # pila: guardar y recuperar con desplazamiento negativo
        addi $sp, $sp, -8
        sw   $s0, 4($sp)
        sw   $s1, 0($sp)
        lw   $a0, 4($sp)
        jal  imprimir_hex
        lw   $a0, 0($sp)
        jal  imprimir_hex
        addi $sp, $sp, 8
        add  $a0, $sp, $zero
        jal  imprimir_hex
        jal  nueva_linea

        addi $v0, $zero, 10
        syscall

imprimir_hex:
        add  $t0, $a0, $zero
        addi $t1, $zero, 8
ih_bucle:
        srl  $t2, $t0, 28
        slti $t3, $t2, 10
        beq  $t3, $zero, ih_letra
        addi $a0, $t2, 48
        j    ih_imprime
ih_letra:
        addi $a0, $t2, 87
ih_imprime:
        addi $v0, $zero, 11
        syscall
        sll  $t0, $t0, 4
        addi $t1, $t1, -1
        bne  $t1, $zero, ih_bucle
        addi $a0, $zero, 32
        addi $v0, $zero, 11
        syscall
        jr   $ra

nueva_linea:
        addi $a0, $zero, 10
        addi $v0, $zero, 11
        syscall
        jr   $ra
