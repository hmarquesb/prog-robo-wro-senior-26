#!/usr/bin/env pybricks-micropython
"""
teste_arduino.py - Testes de bancada do EV3 <-> Arduino
=======================================================

Dois testes, escolhidos pela variavel TESTE la embaixo:

    TESTE = 1   A CONVERSA. Os dois lados se falam? Nao depende de servo
                montado no mecanismo nem de motor nenhum plugado.
    TESTE = 2   O MOVIMENTO. O servo realmente se mexe quando o comando
                chega, e da para confiar no "espera ate terminar"?

Rode o 1 primeiro. Se ele falhar, o 2 nao tem o que provar.

DE PROPOSITO este arquivo nao importa setup.py nem servos.py: o setup.py
cria os 4 motores, e na bancada, com so o cabo do Arduino plugado, isso
da erro antes do teste comecar. Por isso as constantes do protocolo estao
repetidas aqui - se mudar o endereco ou os comandos no
arduino_servos.ino, mude no constantes.py E aqui.

ANTES DE RODAR
--------------
  1. arduino_servos.ino ja gravado no Nano, e o Nano ligado
     (LED de power aceso).
  2. Cabo do EV3 na porta S1, conferido no multimetro.
  3. Pull-ups de 4,7k ligados ao pino 4 do EV3, nao ao 5V do Arduino.
  4. Servo no pino D9 do Nano, alimentado pela bateria de 4x AA (6V) -
     NAO pelo 5V do Nano.
  5. GND comum entre EV3, Arduino e bateria dos servos. Sem isso o servo
     fica parado ou tremendo, e e o erro mais comum da montagem.

Se o TESTE 1 passar e o servo nao mexer no TESTE 2, o problema e
alimentacao ou GND, nao comunicacao: o Arduino recebeu e respondeu
certinho, so nao teve forca para girar.
"""

from pybricks.hubs import EV3Brick
from pybricks.iodevices import I2CDevice
from pybricks.parameters import Port
from pybricks.tools import wait, StopWatch


# --- tem que bater com o arduino_servos.ino (e com o constantes.py) ---
PORTA_ARDUINO = Port.S1
ENDERECO = 0x04            # 7 bits dos dois lados, sem deslocar

CMD_ACIONA  = 0x10
CMD_REPOUSO = 0x11
CMD_INVALIDO = 0xFF        # nao existe no switch do sketch, de proposito

# TEMPO_CURSO do sketch e 400 ms. Esperamos um pouco mais que isso.
ESPERA_CURSO = 600
TIMEOUT = 2000             # ms; se passar disso, algo travou
CICLOS = 3


ev3 = EV3Brick()
arduino = I2CDevice(PORTA_ARDUINO, ENDERECO)


def msg(*partes):
    """Escreve na tela do brick e no console do VS Code ao mesmo tempo."""
    print(*partes)
    ev3.screen.print(*partes)


def enviar(comando):
    arduino.write(reg=None, data=bytes((comando,)))


def ler_status():
    """Devolve o byte de status, ou None se o Arduino nao respondeu."""
    try:
        return arduino.read(reg=None, length=1)[0]
    except OSError:
        return None


def falhou(texto):
    msg(texto)
    ev3.speaker.beep(frequency=200, duration=800)


def ocupado():
    """True enquanto o Arduino diz que o servo ainda esta se movendo."""
    return ler_status() == 1


def esperar_servo(timeout=TIMEOUT):
    """
    Bloqueia ate o Arduino dizer que terminou.

    Devolve o tempo gasto em ms, ou -1 se estourou o timeout. Esse -1 e
    o que separa "servo lento" de "comunicacao caiu no meio".
    """
    relogio = StopWatch()
    while ocupado():
        if relogio.time() > timeout:
            return -1
        wait(10)
    return relogio.time()


# =============================================================================
# TESTE 1 - a conversa
# =============================================================================

def _teste_1_conversa():
    """
      1 - o Arduino responde?          (fiacao / endereco)
      2 - ele entendeu um comando?     (le 1 = "estou movendo")
      3 - ele terminou o movimento?    (le 0 depois de esperar)
      4 - ele sabe recusar lixo?       (comando invalido = continua 0)

    Passar nos 4 significa que os dois sentidos da conversa funcionam e
    que o valor lido e resposta de verdade, nao ruido do barramento.
    """
    msg("Teste I2C S1")

    # A primeira leitura depois de ligar as vezes sai vazia, entao
    # tentamos tres vezes antes de dizer que esta mudo.
    status = None
    for _ in range(3):
        status = ler_status()
        if status is not None:
            break
        wait(100)

    if status is None:
        falhou("1 FALHOU: mudo")
        msg("ver cabo/pullup/end")
        return

    msg("1 ok: resp =", status)

    # Comando valido faz o sketch marcar fim_movimento, entao o status
    # tem que virar 1 (ocupado) na hora.
    enviar(CMD_ACIONA)
    wait(20)
    status = ler_status()

    if status != 1:
        falhou("2 FALHOU: leu " + str(status))
        msg("escrita nao chegou")
        enviar(CMD_REPOUSO)
        return

    msg("2 ok: ocupado=1")

    wait(ESPERA_CURSO)
    status = ler_status()

    if status != 0:
        falhou("3 FALHOU: leu " + str(status))
        msg("nao terminou curso")
        enviar(CMD_REPOUSO)
        return

    msg("3 ok: livre=0")

    # Comando que nao existe cai no default do sketch, que NAO mexe em
    # fim_movimento. Se mesmo assim vier 1, o que estamos lendo nao e
    # resposta de verdade.
    enviar(CMD_INVALIDO)
    wait(20)
    status = ler_status()

    if status != 0:
        falhou("4 FALHOU: leu " + str(status))
        msg("resposta suspeita")
    else:
        msg("4 ok")
        msg("I2C FUNCIONA")
        ev3.speaker.beep()

    # Deixa o servo no repouso, aconteca o que acontecer.
    enviar(CMD_REPOUSO)


# =============================================================================
# TESTE 2 - o movimento
# =============================================================================

def _mover(comando, nome):
    """Manda o comando, espera terminar e conta o que aconteceu."""
    enviar(comando)
    gasto = esperar_servo()

    if gasto < 0:
        msg(nome, "TRAVOU")
        ev3.speaker.beep(frequency=200, duration=800)
        return False

    msg(nome, gasto, "ms")
    return True


def _teste_2_movimento():
    """
    O QUE OBSERVAR
      - O curso e o angulo certo? Se nao, ajustar ANG_ACIONADO no
        arduino_servos.ino (o 90 mecanico quase nunca e o 90 do servo).
      - O servo fica zumbindo parado no fim do curso? E o servo forcando
        contra o batente - ANG_ACIONADO passou do ponto.

    O tempo impresso e o TEMPO_CURSO declarado no sketch (400 ms), nao o
    tempo real do servo. Para calibrar de verdade: cronometrar o servo no
    olho e ajustar TEMPO_CURSO no arduino_servos.ino.
    """
    msg("Servo:", CICLOS, "ciclos")

    # Comeca de um estado conhecido, senao o primeiro ciclo pode ser um
    # movimento de lugar nenhum para lugar nenhum.
    enviar(CMD_REPOUSO)
    esperar_servo()
    wait(500)

    for _ in range(CICLOS):
        if not _mover(CMD_ACIONA, "aciona"):
            return
        wait(700)          # tempo de olhar o servo parado no fim do curso

        if not _mover(CMD_REPOUSO, "repouso"):
            return
        wait(700)

    msg("FIM OK")
    ev3.speaker.beep()


if __name__ == "__main__":

    TESTE = 1

    ev3.screen.clear()

    if TESTE == 1:
        _teste_1_conversa()
    else:
        _teste_2_movimento()

    wait(5000)
