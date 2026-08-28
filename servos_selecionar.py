#!/usr/bin/env pybricks-micropython
"""
servos_selecionar.py - Servo seletor das colunas de armazenagem
==============================================================

ANGULOS JA MEDIDOS NO ROBO: o passeio pelas 3 colunas (teste no fim deste
arquivo) para na boca de cada uma. Os ANG_COLUNA_* do arduino_servos.ino
sao os valores bons - nao sao mais placeholder. O outro servo, o que
segura e libera os blocos, mora no servos_segurar.py.

Hardware vem do setup.py, protocolo vem do constantes.py (secao 5).
Mesmo papel do garra.py, so que para o servo: qualquer programa que
precise escolher uma coluna importa daqui em vez de escrever bytes no
barramento na mao.

    import servos_selecionar as sv

    sv.selecionar_coluna(2)    # poe o seletor na boca da coluna 2
    sv.repouso()               # tira o seletor do caminho

O QUE ELE FAZ NA PROVA. As 3 colunas de armazenagem sao FIXAS no topo do
robo. A garra arremessa todos os blocos com a MESMA forca, sempre, e o
carrinho para na mesma profundidade - quem decide em qual coluna cada
bloco cai e este servo, chamado uma vez por bloco, antes do arremesso.

O SERVO NAO E LIGADO NO EV3. Ele e comandado por um Arduino Nano
(arduino_servos.ino), e o EV3 conversa com o Nano por I2C na porta S1. O
protocolo tem dois lados:

    ESCRITA  1 byte de comando  (cte.SERVO_CMD_*)
    LEITURA  1 byte de status   (1 = ainda movendo, 0 = terminou)

O status e o que permite ESPERAR o servo em vez de chutar um wait(): o
Arduino so devolve 0 quando o curso acabou. E o mesmo padrao do
esperar_garra - dispara, espera no relogio, e desiste com apito se
estourar o timeout, em vez de travar a rodada.

O SKETCH CONHECE OS QUATRO COMANDOS (0x10, 0x12, 0x13 e 0x11), um angulo
para cada. Se um byte cair no default de la, o sketch segura o status em
"ocupado" ate estourar o SERVO_TIMEOUT_MS - o apito do esperar_servo e o
sinal de que os dois lados sairam do contrato. O robo perde a selecao
daquele bloco, mas termina a rodada.

FALHA DE I2C NAO PARA A PROVA. Cabo solto, pull-up ruim ou Nano
reiniciando levantam OSError no meio do barramento. Aqui isso vira um
apito e um False, nunca um traceback: um bloco na coluna errada custa
pontos, um programa morto custa a rodada inteira.
"""

from pybricks.tools import wait, StopWatch

import constantes as cte
from setup import ev3, arduino


# =============================================================================
# 1. PROTOCOLO (o que fala com o barramento)
# =============================================================================

def enviar(comando):
    """
    Escreve UM byte de comando no Arduino.

    Devolve True se o barramento aceitou. Um OSError aqui e cabo/pull-up/
    endereco - nao e o servo. Tenta cte.SERVO_TENTATIVAS vezes antes de
    desistir, porque a primeira escrita depois de ligar as vezes se perde
    (o mesmo motivo pelo qual o teste_arduino.py tenta tres vezes).
    """
    for _ in range(cte.SERVO_TENTATIVAS):
        try:
            arduino.write(reg=None, data=bytes((comando,)))
            return True
        except OSError:
            wait(10)
    return False


def ler_status():
    """
    Devolve o byte de status do Arduino, ou None se ele nao respondeu.

        1     o servo ainda esta se movendo
        0     terminou o curso
        None  o barramento nao respondeu (cabo, pull-up, endereco)

    O None e diferente do 0 de proposito: "nao respondeu" e "respondeu
    que terminou" pedem reacoes diferentes de quem chama.
    """
    for _ in range(cte.SERVO_TENTATIVAS):
        try:
            return arduino.read(reg=None, length=1)[0]
        except OSError:
            wait(10)
    return None


def ocupado():
    """True enquanto o Arduino disser que o servo ainda esta se movendo."""
    return ler_status() == 1


def esperar_servo(timeout=cte.SERVO_TIMEOUT_MS):
    """
    Bloqueia ate o Arduino dizer que o movimento acabou.

    Devolve True se terminou dentro do prazo, False se estourou o
    `timeout` - e ai apita e imprime, igual ao esperar_garra. O robo
    CONTINUA a rodada de qualquer jeito; quem chama decide se o False
    importa.

    Um timeout aqui e uma de duas coisas, e vale conferir qual:
      - o servo esta forcando contra um batente e nunca "chega" (ajustar
        o angulo no arduino_servos.ino);
      - a conversa caiu no meio (cabo/alimentacao), e ai o ler_status ja
        vinha devolvendo None.
    """
    relogio = StopWatch()
    while ocupado():
        if relogio.time() > timeout:
            ev3.speaker.beep(200, 300)
            print("servo nao terminou o movimento em", timeout, "ms")
            return False
        wait(10)
    return True


# =============================================================================
# 2. MOVIMENTOS DA PROVA
# =============================================================================

def selecionar_coluna(coluna, esperar=True):
    """
    Poe o seletor na boca da coluna de armazenagem `coluna` (1, 2 ou 3),
    de modo que o proximo bloco arremessado caia nela.

    CHAME ANTES DO ARREMESSO, com o robo parado. E a unica coisa que
    diferencia um bloco do outro na hora de guardar - a garra arremessa
    os 12 com a mesma forca.

    Devolve True se o servo confirmou o movimento. False significa que o
    comando nao chegou ou que o servo nao terminou no prazo: o bloco
    daquele ciclo provavelmente vai cair na coluna anterior. Apita nos
    dois casos, e o robo segue.

    esperar=True  -> so devolve o controle quando o servo terminar
    esperar=False -> dispara e volta na hora, devolvendo None. Quem chama
                     fica responsavel por esperar (esperar_servo). Serve
                     para acionar o servo JUNTO com o carrinho, com o
                     robo parado - sao dois atuadores independentes.
    """
    comando = cte.SERVO_CMD.get(coluna)
    if comando is None:
        print("selecionar_coluna: coluna", coluna, "nao existe (use 1, 2 ou 3)")
        return False

    if not enviar(comando):
        ev3.speaker.beep(200, 300)
        print("servo: comando da coluna", coluna, "nao chegou ao Arduino")
        return False

    if not esperar:
        return None
    return esperar_servo()


def repouso(esperar=True):
    """
    Manda o seletor para a posicao de repouso, fora do caminho.

    Nao e usado no meio da retirada - la o seletor vai direto de uma
    coluna para a outra. Serve para deixar o mecanismo num estado
    conhecido no comeco e no fim de um programa, e para os testes.
    """
    if not enviar(cte.SERVO_CMD_REPOUSO):
        ev3.speaker.beep(200, 300)
        print("servo: comando de repouso nao chegou ao Arduino")
        return False

    if not esperar:
        return None
    return esperar_servo()


# =============================================================================
# 3. TESTE
# =============================================================================

if __name__ == "__main__":

    # Passeia pelas 3 colunas e volta ao repouso, parando em cada uma
    # para dar tempo de olhar onde o seletor parou.
    #
    # O QUE CONFERIR:
    #   1. as tres paradas caem na BOCA de cada coluna. Se o servo parar
    #      entre duas, o angulo esta errado - ajuste no
    #      arduino_servos.ino, nao aqui;
    #   2. nenhum "servo nao terminou" (apito longo). Se aparecer, ou o
    #      servo esta forcando um batente, ou o comando daquela coluna
    #      ainda nao existe no sketch;
    #   3. o servo nao fica zumbindo parado - zumbido e servo empurrando
    #      o fim do curso.
    #
    # Se NADA responder, o problema e a conversa e nao o servo: rode o
    # teste_arduino.py, que testa so o barramento.
    print("=== passeio pelas 3 colunas ===")

    repouso()
    wait(500)

    for volta in range(2):
        for coluna_teste in (1, 2, 3):
            ok = selecionar_coluna(coluna_teste)
            print("volta", volta + 1, "- coluna", coluna_teste,
                  "->", "OK" if ok else "FALHOU")
            wait(800)

    repouso()
    ev3.speaker.beep()
