# Listados 2.2 y 3.2 del material: MCD por restas y MCD de tres numeros.
# Imprime mcd(84, 36), mcd(17, 5), mcd(9, 9) y mcd3(84, 36, 30), uno por linea.
        .data
potencias: .word 1000000000, 100000000, 10000000, 1000000, 100000, 10000, 1000, 100, 10, 1, 0

        .text
main:   addi $a0, $zero, 84
        addi $a1, $zero, 36
        jal  mcd
        jal  imprimir_resultado      # 12
        addi $a0, $zero, 17
        addi $a1, $zero, 5
        jal  mcd
        jal  imprimir_resultado      # 1
        addi $a0, $zero, 9
        addi $a1, $zero, 9
        jal  mcd
        jal  imprimir_resultado      # 9
        addi $a0, $zero, 84
        addi $a1, $zero, 36
        addi $a2, $zero, 30
        jal  mcd3
        jal  imprimir_resultado      # 6
        addi $v0, $zero, 10
        syscall

# mcd: $v0 <- mcd($a0, $a1), con $a0, $a1 > 0 (procedimiento hoja)
mcd:
mientras:
        beq  $a0, $a1, fin           # si A == B, terminar
        slt  $t0, $a1, $a0           # t0 <- (B < A), es decir, (A > B)
        beq  $t0, $zero, restar      # si A <= B, no intercambiar
        add  $t1, $a0, $zero         # intercambio (A,B) <- (B,A)
        add  $a0, $a1, $zero
        add  $a1, $t1, $zero
restar: sub  $a1, $a1, $a0           # B <- B - A
        j    mientras
fin:    add  $v0, $a0, $zero         # resultado <- A
        jr   $ra

# mcd3: $v0 <- mcd(mcd($a0, $a1), $a2) (procedimiento no hoja)
mcd3:   addi $sp, $sp, -8            # marco de dos palabras
        sw   $ra, 4($sp)             # guardar direccion de retorno
        sw   $s0, 0($sp)             # se usara s0: guardarlo
        add  $s0, $a2, $zero         # s0 <- c (a2 no sobrevive a la llamada)
        jal  mcd                     # v0 <- mcd(a, b)
        add  $a0, $v0, $zero
        add  $a1, $s0, $zero
        jal  mcd                     # v0 <- mcd(mcd(a, b), c)
        lw   $s0, 0($sp)
        lw   $ra, 4($sp)
        addi $sp, $sp, 8
        jr   $ra

# imprime $v0 en decimal y un salto de linea
imprimir_resultado:
        addi $sp, $sp, -4
        sw   $ra, 0($sp)
        add  $a0, $v0, $zero
        jal  imprimir_entero
        addi $a0, $zero, 10
        addi $v0, $zero, 11
        syscall
        lw   $ra, 0($sp)
        addi $sp, $sp, 4
        jr   $ra

imprimir_entero:
        add  $t0, $a0, $zero
        la   $t2, potencias
        add  $t4, $zero, $zero
ie_potencia:
        lw   $t3, 0($t2)
        beq  $t3, $zero, ie_fin
        add  $t5, $zero, $zero
ie_resta:
        slt  $t1, $t0, $t3
        bne  $t1, $zero, ie_digito
        sub  $t0, $t0, $t3
        addi $t5, $t5, 1
        j    ie_resta
ie_digito:
        addi $t1, $zero, 1
        beq  $t3, $t1, ie_imprime
        bne  $t5, $zero, ie_imprime
        beq  $t4, $zero, ie_siguiente
ie_imprime:
        addi $t4, $zero, 1
        addi $a0, $t5, 48
        addi $v0, $zero, 11
        syscall
ie_siguiente:
        addi $t2, $t2, 4
        j    ie_potencia
ie_fin: jr   $ra
