# Prueba de beq, bne, j, jal y jr: saltos tomados y no tomados, hacia delante
# y hacia atras, llamadas anidadas con pila y salto a una direccion calculada.
# Cada comprobacion imprime una letra; un '!' indica un salto equivocado.
        .text
main:   addi $s0, $zero, 5
        addi $s1, $zero, 5
        addi $s2, $zero, 6

        beq  $s0, $s1, b1            # tomado
        jal  error
b1:     addi $a0, $zero, 65          # 'A'
        jal  letra
        beq  $s0, $s2, error_b       # no tomado
        addi $a0, $zero, 66          # 'B'
        jal  letra
        bne  $s0, $s2, b2            # tomado
        jal  error
b2:     addi $a0, $zero, 67          # 'C'
        jal  letra
        bne  $s0, $s1, error_b       # no tomado
        addi $a0, $zero, 68          # 'D'
        jal  letra

        # bucle hacia atras: imprime 0123
        add  $t4, $zero, $zero
bucle:  addi $a0, $t4, 48
        jal  letra
        addi $t4, $t4, 1
        slti $t5, $t4, 4
        bne  $t5, $zero, bucle

        j    salto_j                 # j hacia delante
        jal  error
salto_j:
        addi $a0, $zero, 69          # 'E'
        jal  letra

        # jr a una direccion calculada (la de 'destino')
        la   $t6, destino
        jr   $t6
        jal  error
destino:
        addi $a0, $zero, 70          # 'F'
        jal  letra

        # recursion: suma(10) = 55, impreso en decimal (decenas por restas)
        addi $a0, $zero, 10
        jal  suma
        add  $s3, $v0, $zero
        addi $a0, $zero, 32
        jal  letra
        add  $t4, $zero, $zero       # decenas
decenas:
        slti $t5, $s3, 10
        bne  $t5, $zero, unidades
        addi $s3, $s3, -10
        addi $t4, $t4, 1
        j    decenas
unidades:
        addi $a0, $t4, 48
        jal  letra
        addi $a0, $s3, 48
        jal  letra
        addi $a0, $zero, 10
        jal  letra

        addi $v0, $zero, 10
        syscall

error_b:
        addi $a0, $zero, 33          # '!'
        jal  letra
        addi $v0, $zero, 10
        syscall

error:  addi $a0, $zero, 33          # '!'
        addi $v0, $zero, 11
        syscall
        jr   $ra

letra:  addi $v0, $zero, 11
        syscall
        jr   $ra

# suma(n) = n + suma(n - 1), suma(0) = 0 (Listado 3.3 del material)
suma:   addi $sp, $sp, -8
        sw   $ra, 4($sp)
        sw   $a0, 0($sp)
        bne  $a0, $zero, suma_rec
        add  $v0, $zero, $zero
        addi $sp, $sp, 8
        jr   $ra
suma_rec:
        addi $a0, $a0, -1
        jal  suma
        lw   $a0, 0($sp)
        lw   $ra, 4($sp)
        addi $sp, $sp, 8
        add  $v0, $v0, $a0
        jr   $ra
