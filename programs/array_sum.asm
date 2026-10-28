# Listado 2.1 del material: suma de los elementos de un arreglo.
# La placa solo ofrece los servicios 10 y 11, asi que imprimir cadena (4) e
# imprimir entero (1) se hacen en software con imprimir_cadena e imprimir_entero.
        .data
arreglo: .word 5, -2, 7, 10, 3
n:       .word 5
mensaje: .asciiz "Suma: "
potencias: .word 1000000000, 100000000, 10000000, 1000000, 100000, 10000, 1000, 100, 10, 1, 0

        .text
main:   la   $s0, arreglo            # s0 <- direccion base
        la   $t0, n
        lw   $s1, 0($t0)             # s1 <- n
        add  $s2, $zero, $zero       # suma <- 0
        add  $t0, $zero, $zero       # i <- 0
bucle:  slt  $t1, $t0, $s1           # t1 <- (i < n)
        beq  $t1, $zero, fin_bucle
        sll  $t2, $t0, 2             # t2 <- 4*i
        add  $t2, $s0, $t2           # t2 <- direccion de A[i]
        lw   $t3, 0($t2)             # t3 <- A[i]
        add  $s2, $s2, $t3           # suma <- suma + A[i]
        addi $t0, $t0, 1             # i <- i + 1
        j    bucle
fin_bucle:
        la   $a0, mensaje
        jal  imprimir_cadena         # "Suma: "
        add  $a0, $s2, $zero
        jal  imprimir_entero         # 23
        addi $v0, $zero, 10          # terminar
        syscall

# imprime la cadena terminada en nulo que empieza en $a0
imprimir_cadena:
        add  $t0, $a0, $zero
ic_bucle:
        lbu  $a0, 0($t0)
        beq  $a0, $zero, ic_fin
        addi $v0, $zero, 11
        syscall
        addi $t0, $t0, 1
        j    ic_bucle
ic_fin: jr   $ra

# imprime $a0 en decimal: para cada potencia de 10 cuenta cuantas veces se puede restar
imprimir_entero:
        add  $t0, $a0, $zero
        slt  $t1, $t0, $zero
        beq  $t1, $zero, ie_positivo
        addi $a0, $zero, 45          # '-'
        addi $v0, $zero, 11
        syscall
        sub  $t0, $zero, $t0
ie_positivo:
        la   $t2, potencias
        add  $t4, $zero, $zero       # t4 = 1 cuando ya se imprimio un digito
ie_potencia:
        lw   $t3, 0($t2)
        beq  $t3, $zero, ie_fin
        add  $t5, $zero, $zero       # digito
ie_resta:
        slt  $t1, $t0, $t3
        bne  $t1, $zero, ie_digito
        sub  $t0, $t0, $t3
        addi $t5, $t5, 1
        j    ie_resta
ie_digito:
        addi $t1, $zero, 1
        beq  $t3, $t1, ie_imprime    # las unidades siempre se imprimen
        bne  $t5, $zero, ie_imprime
        beq  $t4, $zero, ie_siguiente # ceros a la izquierda: no
ie_imprime:
        addi $t4, $zero, 1
        addi $a0, $t5, 48
        addi $v0, $zero, 11
        syscall
ie_siguiente:
        addi $t2, $t2, 4
        j    ie_potencia
ie_fin: jr   $ra
