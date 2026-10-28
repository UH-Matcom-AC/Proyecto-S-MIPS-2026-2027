# Prueba de las instrucciones aritmeticas, logicas y con inmediato de S-MIPS.
# Imprime cada resultado en hexadecimal; run_tests.py compara la salida con MARS.
        .text
main:   addi $s0, $zero, 1000        # s0 = 0x000003e8
        addi $s1, $zero, -7          # s1 = 0xfffffff9 (addi extiende con signo)

        add  $a0, $s0, $s1           # 993
        jal  imprimir_hex
        sub  $a0, $s0, $s1           # 1007
        jal  imprimir_hex
        sub  $a0, $s1, $s0           # -1007
        jal  imprimir_hex
        and  $a0, $s0, $s1
        jal  imprimir_hex
        or   $a0, $s0, $s1
        jal  imprimir_hex
        jal  nueva_linea

        slt  $a0, $s1, $s0           # -7 < 1000 -> 1 (con signo)
        jal  imprimir_hex
        slt  $a0, $s0, $s1           # 0
        jal  imprimir_hex
        sll  $a0, $s1, 4
        jal  imprimir_hex
        srl  $a0, $s1, 4             # logico: entran ceros
        jal  imprimir_hex
        srl  $a0, $s1, 31
        jal  imprimir_hex
        jal  nueva_linea

        addi $a0, $s1, 100           # 93
        jal  imprimir_hex
        slti $a0, $s1, -6            # -7 < -6 -> 1
        jal  imprimir_hex
        slti $a0, $s0, -1            # 0
        jal  imprimir_hex
        andi $a0, $s1, 0xff0f        # andi extiende con ceros -> 0x0000ff09
        jal  imprimir_hex
        ori  $a0, $zero, 0x8000      # 0x00008000, no 0xffff8000
        jal  imprimir_hex
        jal  nueva_linea

        lui  $a0, 0x8001             # 0x80010000
        jal  imprimir_hex
        lui  $t5, 0x1234
        ori  $a0, $t5, 0x5678        # 0x12345678
        jal  imprimir_hex
        li   $a0, -5                 # MARS genera addiu
        jal  imprimir_hex
        move $a0, $s1                # MARS genera addu
        jal  imprimir_hex
        add  $zero, $s0, $s0         # escribir en $zero no tiene efecto
        nop
        add  $a0, $zero, $zero
        jal  imprimir_hex
        jal  nueva_linea

        addi $v0, $zero, 10          # terminar
        syscall

# imprime $a0 en hexadecimal (8 digitos) seguido de un espacio
imprimir_hex:
        add  $t0, $a0, $zero
        addi $t1, $zero, 8
ih_bucle:
        srl  $t2, $t0, 28            # digito mas significativo
        slti $t3, $t2, 10
        beq  $t3, $zero, ih_letra
        addi $a0, $t2, 48            # '0' + d
        j    ih_imprime
ih_letra:
        addi $a0, $t2, 87            # 'a' + d - 10
ih_imprime:
        addi $v0, $zero, 11
        syscall
        sll  $t0, $t0, 4
        addi $t1, $t1, -1
        bne  $t1, $zero, ih_bucle
        addi $a0, $zero, 32          # espacio
        addi $v0, $zero, 11
        syscall
        jr   $ra

nueva_linea:
        addi $a0, $zero, 10
        addi $v0, $zero, 11
        syscall
        jr   $ra
