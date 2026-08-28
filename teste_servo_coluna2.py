#!/usr/bin/env pybricks-micropython
"""
teste_servo_coluna2.py - So o seletor, so a coluna 2
====================================================

PARA QUE ESTE ARQUIVO EXISTE: descobrir como PRENDER o seletor direito.
Ele leva o servo de selecao ate a coluna 2 e para por la, para dar tempo
de olhar, apertar, colar, trocar de parafuso - e de mandar de novo para
ver se soltou.

E o passeio pelas 3 colunas do servos_selecionar.py reduzido a UMA
posicao. Nao existe para calibrar angulo nenhum: os ANG_COLUNA_* ja foram
medidos e moram no arduino_servos.ino. Se o seletor parar fora da boca da
coluna 2, o problema e mecanico (horn frouxo, folga no eixo) ou e o
angulo la no sketch - nao ha numero para mexer AQUI.

POR QUE A COLUNA 2: e a do meio, entao um horn que escorregou aparece
para os dois lados; e e para onde o mecanismo tende a voltar quando a
fixacao cede.

COMO USAR:

    1. rode este arquivo (F5). O servo vai para a coluna 2 e fica la.
    2. mexa na fixacao: aperte, cole, troque o parafuso do horn.
    3. FORCE O SELETOR COM A MAO, de leve, para ver se ele volta sozinho
       ou se escorregou.
    4. aperte o botao CENTRAL: o comando da coluna 2 e enviado DE NOVO.
       Se ele voltar para o mesmo lugar de antes, a fixacao esta boa; se
       parar em outro lugar, o horn girou no eixo.
    5. repita quantas vezes quiser. O botao VOLTAR encerra.

O SERVO NAO SOLTA A POSICAO quando o programa termina: quem o alimenta e
o Arduino, e ele segue segurando o ultimo angulo. Para deixar o mecanismo
livre, tire a alimentacao do Nano.

NAO MEXE EM MOTOR NENHUM - nem carrinho, nem garra, nem rodas. Da para
rodar com o robo na bancada, de lado, desmontado.

Se NADA responder (apito e "nao chegou ao Arduino"), o problema e a
conversa e nao a fixacao: rode o teste_arduino.py, que testa so o
barramento.
"""

from pybricks.parameters import Button
from pybricks.tools import wait

import servos_selecionar as sv
from setup import ev3


COLUNA = 2      # a unica posicao deste arquivo


def _esperar_botao():
    """
    Espera um aperto NOVO do botao CENTRAL e devolve True; devolve False
    se o aperto foi em qualquer outro botao (a saida do teste).

    Mesmo cuidado do _esperar_centro do pegar_blocos.py: espera SOLTAR o
    que ja estivesse pressionado antes de escutar o proximo aperto, senao
    um dedo apoiado no botao dispara varios envios seguidos.
    """
    while ev3.buttons.pressed():
        wait(10)
    while not ev3.buttons.pressed():
        wait(10)
    apertados = ev3.buttons.pressed()
    while ev3.buttons.pressed():
        wait(10)
    return Button.CENTER in apertados


def ir_para_coluna_2():
    """
    Manda o seletor para a coluna 2 e diz se ele confirmou.

    False aqui e uma de duas coisas, e o servos_selecionar.py ja imprimiu
    qual: o comando nao chegou ao Arduino (barramento), ou o servo nao
    disse que terminou dentro do cte.SERVO_TIMEOUT_MS - o que, num teste
    de fixacao, costuma ser o servo FORCANDO contra alguma coisa que
    ficou no caminho depois do aperto.
    """
    ok = sv.selecionar_coluna(COLUNA)
    if ok:
        print("coluna", COLUNA, "- servo confirmou. Olhe onde ele parou.")
        ev3.speaker.beep()
    else:
        print("coluna", COLUNA, "- FALHOU (veja a mensagem acima)")
    return ok


if __name__ == "__main__":

    print("=== seletor: so a coluna", COLUNA, "===")
    print("CENTRAL manda de novo   |   VOLTAR encerra")

    ir_para_coluna_2()

    while True:
        print("mexa na fixacao e aperte o CENTRAL para mandar de novo")
        if not _esperar_botao():
            break
        ir_para_coluna_2()

    print("fim - o servo continua segurando a coluna", COLUNA,
          "enquanto o Arduino estiver ligado")
    ev3.speaker.beep()
