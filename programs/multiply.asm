# Listado 3.1 del material: multiplicacion por desplazamiento y suma,
# usada por un factorial recursivo (ejercicio 3.15.2). Imprime 5! = 120 y 12 * 13 = 156.
        .data
potencias: .word 1000000000, 100000000, 10000000, 1000000, 100000, 10000, 1000, 100, 10, 1, 0

        .text
main:   addi $a0, $zero, 5
        jal  factorial
        add  $a0, $v0, $zero
        jal  imprimir_entero         # 120
        addi $a0, $zero, 32
        addi $v0, $zero, 11
        syscall
        addi $a0, $zero, 12
        addi $a1, $zero, 13
        jal  multiplicar
        add  $a0, $v0, $zero
        jal  imprimir_entero         # 156
        addi $v0, $zero, 10
        syscall

# factorial(n) = n * factorial(n - 1), factorial(0) = 1
factorial:
        addi $sp, $sp, -8
        sw   $ra, 4($sp)
        sw   $a0, 0($sp)
        bne  $a0, $zero, fact_rec
        addi $v0, $zero, 1
        addi $sp, $sp, 8
        jr   $ra
fact_rec:
        addi $a0, $a0, -1
        jal  factorial               # v0 <- (n - 1)!
        lw   $a0, 0($sp)             # a0 <- n
        add  $a1, $v0, $zero
        jal  multiplicar             # v0 <- n * (n - 1)!
        lw   $ra, 4($sp)
        addi $sp, $sp, 8
        jr   $ra

# multiplicar: $v0 <- $a0 * $a1 (sin signo, procedimiento hoja)
multiplicar:
        add  $v0, $zero, $zero       # producto <- 0
mult_bucle:
        beq  $a1, $zero, mult_fin    # sin bits restantes: terminar
        andi $t0, $a1, 1             # t0 <- bit menos significativo
        beq  $t0, $zero, mult_sig
        add  $v0, $v0, $a0           # si el bit es 1, acumular
mult_sig:
        sll  $a0, $a0, 1             # multiplicando <- 2*multiplicando
        srl  $a1, $a1, 1             # pasar al siguiente bit
        j    mult_bucle
mult_fin:
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
