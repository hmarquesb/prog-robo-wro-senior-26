#!/usr/bin/env pybricks-micropython
"""
servos_segurar.py - Servo que SEGURA e LIBERA os blocos
=======================================================

O SEGUNDO servo do Arduino (sinal no D10). O primeiro, o seletor de
coluna, mora no servos_selecionar.py - e e de la que este arquivo importa
o protocolo (enviar / esperar_servo), porque os dois servos falam com o
MESMO Arduino, no MESMO barramento, com o MESMO byte de status. So muda o
byte de comando.

    import servos_segurar as sg

    sg.segurar()    # prende o bloco
    sg.liberar()    # solta o bloco

O QUE ELE FAZ. O seletor escolhe a coluna; este aqui e o que prende o
bloco enquanto o robo se move e o solta na hora certa. Enquanto os
angulos nao estiverem medidos, ele so tem duas posicoes, e este arquivo
existe justamente para descobrir quais sao elas antes de o servo entrar
no programa principal.

QUAL POSICAO SEGURA E MECANICA, NAO PROGRAMA. Se o teste mostrar as duas
trocadas, inverta ANG_SERVO2_ACIONADO e ANG_SERVO2_REPOUSO no
arduino_servos.ino - nao os bytes do constantes.py, e nao aqui. E a mesma
regra 11 do README, aplicada ao outro servo.

FALHA DE I2C NAO PARA A PROVA, igual ao seletor: OSError no barramento
vira apito e False, nunca traceback.
"""

from pybricks.tools import wait

import constantes as cte
from setup import ev3

# O protocolo (1 byte de comando, 1 byte de status, tentativas, timeout) e
# um so para os dois servos - esta escrito no servos_selecionar.py e nao
# se repete aqui.
from servos_selecionar import enviar, esperar_servo, ler_status, ocupado


# =============================================================================
# 1. MOVIMENTOS
# =============================================================================

def _comandar(comando, nome, esperar):
    """
    Manda um dos dois comandos deste servo e espera (ou nao).

    Devolve True se o servo confirmou, False se o comando nao chegou ou se
    estourou o cte.SERVO_TIMEOUT_MS, e None quando esperar=False (quem
    chama fica responsavel pelo esperar_servo).
    """
    if not enviar(comando):
        ev3.speaker.beep(200, 300)
        print("servo dos blocos: comando de", nome, "nao chegou ao Arduino")
        return False

    if not esperar:
        return None
    return esperar_servo()


def segurar(esperar=True):
    """
    Fecha o servo sobre o bloco, para o robo poder se mover com ele.

    esperar=False dispara e volta na hora - serve para acionar este servo
    JUNTO com outro mecanismo parado (regra 5 do README: nunca com o robo
    andando).
    """
    return _comandar(cte.SERVO_CMD_SEGURAR, "segurar", esperar)


def liberar(esperar=True):
    """
    Abre o servo e solta o bloco.

    E tambem a posicao em que o mecanismo deve ficar no comeco e no fim de
    um programa, para nao segurar nada por engano.
    """
    return _comandar(cte.SERVO_CMD_LIBERAR, "liberar", esperar)


# =============================================================================
# 2. TESTE
# =============================================================================

if __name__ == "__main__":

    # TESTE 1  vai e volta sozinho, para achar as duas posicoes
    # TESTE 2  espera um toque no botao entre cada movimento, para dar
    #          tempo de por o bloco na mao e sentir se ele fica preso
    TESTE = 1

    ESPERA_MS = 1500     # quanto olhar cada posicao no TESTE 1
    VOLTAS = 3

    # O QUE CONFERIR NOS DOIS:
    #   1. "segurar" realmente prende o bloco, e "liberar" o deixa cair
    #      sozinho. Se estiver ao contrario, troque os DOIS angulos no
    #      arduino_servos.ino (ANG_SERVO2_ACIONADO / ANG_SERVO2_REPOUSO);
    #   2. nenhum apito de "servo nao terminou". Se apitar, ou o servo
    #      esta forcando um batente (angulo passou do curso mecanico), ou
    #      o comando nao existe no sketch;
    #   3. o servo nao fica zumbindo parado - zumbido e servo empurrando
    #      o fim do curso, e isso e o mesmo stall que ja fritou um Nano
    #      aqui. Desligue e corrija o angulo antes de continuar;
    #   4. o bloco nao escorrega com o robo andando: se escorregar, o
    #      angulo de segurar precisa fechar mais.
    #
    # Se NADA responder, o problema e a conversa e nao o servo: rode o
    # teste_arduino.py, que testa so o barramento.

    if TESTE == 1:
        print("=== servo dos blocos: vai e volta ===")

        print("status inicial do Arduino:", ler_status())

        liberar()
        wait(ESPERA_MS)

        for volta in range(VOLTAS):
            ok = segurar()
            print("volta", volta + 1, "- segurar ->", "OK" if ok else "FALHOU")
            wait(ESPERA_MS)

            ok = liberar()
            print("volta", volta + 1, "- liberar ->", "OK" if ok else "FALHOU")
            wait(ESPERA_MS)

        ev3.speaker.beep()

    elif TESTE == 2:
        print("=== servo dos blocos: passo a passo ===")
        print("aperte o botao central do EV3 para cada movimento")

        passos = (
            ("liberar", liberar),
            ("segurar", segurar),
            ("liberar", liberar),
        )

        for nome, funcao in passos:
            while not ev3.buttons.pressed():
                wait(20)
            while ev3.buttons.pressed():     # espera soltar o botao
                wait(20)

            ok = funcao()
            print(nome, "->", "OK" if ok else "FALHOU",
                  "| ocupado agora:", ocupado())

        ev3.speaker.beep()
