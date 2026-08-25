#!/usr/bin/env pybricks-micropython
"""
teste_escrita_i2c.py - Que forma de conversa chega ao Arduino?
===============================================================

ARQUIVO DE APOIO, NAO E PARTE DA PROVA. Existe para responder UMA
pergunta, e depois que ela for respondida pode ser apagado.

O SINTOMA QUE ELE INVESTIGA. O diagnostico_i2c.py mostrou um barramento
perfeito - presenca 5/5, 30 leituras limpas, 0 escritas recusadas - e
mesmo assim NENHUM comando deixou o Arduino ocupado. Leitura funciona,
escrita nao. Duas explicacoes cabem nesse quadro:

    A) A FORMA da conversa. O I2CDevice do Pybricks chama o driver SMBus
       do Linux, e o driver do EV3 (i2c-legoev3) nasceu para o protocolo
       do NXT, que e sempre "escreve registrador, le dado". Nem toda
       combinacao de reg/data existe la - e a que o servos.py usa pode
       estar virando uma transacao que manda so o endereco: o Arduino
       ACKa (por isso nenhuma escrita falha), o aoReceber() dispara com
       zero byte, e nada acontece.

    B) A FIACAO. Com o SDA em curto para o GND, toda leitura devolve
       0x00 e toda escrita "ACKa" porque a linha ja esta baixa - os
       exames 1, 2 e 3 do diagnostico dariam o mesmo resultado com o
       Arduino nem participando da conversa.

O TESTE 0 tenta separar as duas falando com um endereco VAZIO - mas so
e conclusivo quando ele da erro; um 0 de volta cabe nas duas (ver a
docstring dele). O TESTE 1 procura uma forma de LER 2 bytes. O sketch v2
responde [status, 0x5A]; um barramento em curto responde [0, 0]. De
quebra ele mostra quais formas de leitura o driver do EV3 aceita.

O TESTE 2 so faz sentido se o 1 disser que o Arduino esta mesmo
respondendo. Ele tenta cinco formas de mandar um comando e diz qual faz
o status virar 1.

O QUE FAZER COM A RESPOSTA: a forma vencedora vai para a funcao enviar()
do servos.py. Nao mude o arduino_servos.ino por causa disto - o problema
esta em como o EV3 poe o byte no fio.

DUAS EXCECOES DIFERENTES. O driver levanta OSError quando a conversa
falha no fio, e ValueError quando a COMBINACAO pedida nem existe (foi o
que derrubou a primeira versao deste arquivo: read(reg=None, length=2)
nao e uma operacao valida). Os dois casos sao capturados em todo lugar
aqui, porque os dois sao resposta - so que respostas diferentes.

DE PROPOSITO nao importa setup.py nem servos.py, pelo mesmo motivo do
teste_arduino.py: na bancada, com so o cabo do Arduino plugado, criar os
4 motores daria erro antes do teste comecar.

O SERVO NAO PRECISA ESTAR LIGADO. O byte de status sai de millis(), nao
do servo - se o servo estiver conectado ele vai se mexer, so isso.
"""

from pybricks.hubs import EV3Brick
from pybricks.iodevices import I2CDevice
from pybricks.parameters import Port
from pybricks.tools import wait


# --- tem que bater com o arduino_servos.ino (e com o constantes.py) ---
PORTA_ARDUINO = Port.S1
ENDERECO = 0x04

CMD_COLUNA_1 = 0x10
CMD_REPOUSO  = 0x11

ASSINATURA = 0x5A          # segundo byte da resposta do sketch v2


ev3 = EV3Brick()
arduino = I2CDevice(PORTA_ARDUINO, ENDERECO)


def msg(*partes):
    """Escreve na tela do brick e no console do VS Code ao mesmo tempo."""
    print(*partes)
    ev3.screen.print(*partes)


def tentar(funcao):
    """
    Roda a funcao e devolve (resultado, erro).

    O erro e uma string curta - "OSError" (a conversa falhou no fio) ou
    "ValueError" (essa combinacao nem existe no driver). Nenhuma das
    duas para o teste: o objetivo E descobrir quais formas falham.
    """
    try:
        return funcao(), None
    except OSError:
        return None, "OSError"
    except ValueError:
        return None, "ValueError"


def status():
    """O byte de status, pela unica forma de leitura que ja sabemos boa."""
    resposta, _ = tentar(lambda: arduino.read(reg=None, length=1))
    return None if resposta is None else resposta[0]


# =============================================================================
# TESTE 0 - o barramento enderecca, ou esta preso em zero?
# =============================================================================

# Um endereco onde NAO existe nada. Se o SDA estiver em curto com o GND,
# a linha ja esta baixa e o mestre le "ACK" de qualquer endereco - este
# aqui inclusive. Com o barramento sadio, ninguem ACKa e da OSError.
#
# E o unico exame que nao depende de UMA LINHA do sketch: ele testa o
# fio, nao o Arduino. Por isso vem antes de tudo.
ENDERECO_FANTASMA = 0x77


def _teste_0_barramento():
    """
    Devolve sempre True - este exame INFORMA, nao decide.

        OSError no fantasma   OTIMO, e conclusivo: o barramento distingue
                              enderecos, entao o que vem do 0x04 e mesmo
                              o Arduino respondendo.
        fantasma responde 0   INCONCLUSIVO. Ou a linha esta presa em
                              zero, ou o driver do EV3 simplesmente
                              devolve 0x00 para quem nao ACKou. Os dois
                              dao exatamente esta saida, e nenhum teste
                              em Python separa um do outro - so o
                              multimetro e o Serial Monitor.
    """
    msg("Barramento:")

    fantasma, erro = tentar(lambda: I2CDevice(PORTA_ARDUINO,
                                              ENDERECO_FANTASMA))
    if erro:
        # Nem deu para criar o objeto - nao da para concluir nada, mas
        # tambem nao e motivo para parar.
        msg("fantasma:", erro)
        msg("inconclusivo")
        return True

    resposta, erro = tentar(lambda: fantasma.read(reg=None, length=1))

    if erro:
        msg("0x77 mudo -", erro)
        msg("barramento OK")
        return True

    # NAO da para concluir "curto" daqui. O proprio exemplo da LEGO na
    # documentacao do I2CDevice confere o VALOR lido para saber se o
    # sensor esta conectado, em vez de esperar uma excecao - ou seja, no
    # EV3 uma leitura sem resposta devolve 0x00 em vez de falhar. Entao
    # o fantasma responder 0 pode ser:
    #
    #     o SDA em curto com o GND (linha presa em zero), ou
    #     o driver devolvendo 0x00 porque ninguem ACKou - normal.
    #
    # Quem separa isso nao e software: e o multimetro (A4 e A5 devem
    # medir ~5V em repouso, puxados pelo pull-up) e o Serial Monitor do
    # Arduino, que mostra se ha recepcao. Aqui so registramos e seguimos.
    msg("0x77 respondeu", list(resposta))
    msg("inconclusivo - ver")
    msg("multimetro/serial")
    return True


# =============================================================================
# TESTE 1 - quem responde, e por qual forma de leitura
# =============================================================================

# CUIDADO: as formas com reg=X ESCREVEM o byte X antes de ler. Por isso
# aqui o registrador usado e o CMD_REPOUSO - se essa escrita chegar ao
# Arduino, o unico efeito e mandar o servo para o repouso, que e onde ele
# ja deveria estar.

LEITURAS = (
    ("L1 reg=None len=1", lambda: arduino.read(reg=None, length=1)),
    ("L2 reg=None len=2", lambda: arduino.read(reg=None, length=2)),
    ("L3 reg=0x11 len=1", lambda: arduino.read(reg=CMD_REPOUSO, length=1)),
    ("L4 reg=0x11 len=2", lambda: arduino.read(reg=CMD_REPOUSO, length=2)),
)


def _teste_1_assinatura():
    """
    O sketch v2 responde [status, ASSINATURA]. As conclusoes:

        2 bytes com 0x5A no fim   e o Arduino. A leitura esta sadia, e o
                                  problema e a FORMA - siga para o 2.
        2 bytes [0, 0]            ninguem responde: SDA em curto com o
                                  GND, ou no pino errado. Conserte a
                                  fiacao; software nao resolve.
        2 bytes [0xFF, 0xFF]      linha solta, sem escravo nenhum.
        nenhuma forma de 2 bytes  o driver so faz leitura de 1 byte -
                                  inconclusivo, va pelo Serial Monitor.
    """
    msg("Leituras:")

    dois_bytes = None

    for nome, leitura in LEITURAS:
        resposta, erro = tentar(leitura)

        if erro:
            msg(nome, erro)
            continue

        valores = list(resposta)
        msg(nome, valores)

        if dois_bytes is None and len(valores) >= 2:
            dois_bytes = valores

        wait(200)

    if dois_bytes is None:
        msg("sem leitura de 2 bytes")
        msg("inconclusivo - siga")
        # Nao da para provar quem respondeu, mas tambem nao da para
        # descartar o Arduino. O teste 2 ainda vale a pena.
        return True

    if dois_bytes[1] == ASSINATURA:
        msg("assinatura OK - v2")
        return True

    # ATENCAO A ESTA LEITURA. Um segundo byte 0 NAO prova curto no fio:
    # um sketch que escreve UM byte so no onRequest tambem devolve
    # [status, 0] quando o mestre pede dois, porque a biblioteca Wire
    # completa com o que estiver no buffer. Ou seja, [0, 0] quer dizer
    # "nao e o v2", e as duas explicacoes possiveis sao:
    #
    #     o sketch gravado e o v1 (sem assinatura)  -> regrave
    #     nada esta respondendo, linha presa em 0   -> fiacao
    #
    # Quem separa as duas NAO e este arquivo: o teste 0 so separa quando
    # o fantasma da erro. Se ele respondeu 0, a resposta esta no Serial
    # Monitor do Arduino (aparece "arduino_servos v2 pronto" no boot?) e
    # no multimetro (A4 e A5 medem ~5V em repouso?).
    if dois_bytes[1] == 0:
        msg("sem assinatura")
        msg("sketch v1? regrave")
    elif dois_bytes[1] == 0xFF:
        msg("linha solta")
    else:
        msg("assinatura errada")
        msg("regrave o sketch")

    # Segue mesmo assim: descobrir QUAL forma de escrita chega vale
    # tanto com o v1 quanto com o v2, e o teste 2 usa so o 0x10, que os
    # dois tratam.
    return True


# =============================================================================
# TESTE 2 - qual forma faz o comando chegar?
# =============================================================================

# As quatro primeiras sao as combinacoes documentadas em iodevices.html,
# "Advanced I2C Commands". A quinta nao e uma escrita: e uma LEITURA com
# registrador, que no protocolo do NXT poe o byte do registrador no fio
# antes de ler - se o driver do EV3 so sabe conversar assim, ela e a
# unica que entrega o comando ao Arduino.

def _forma_1(comando):
    """reg=None, data=1 byte - a que o servos.py usa hoje."""
    arduino.write(reg=None, data=bytes((comando,)))


def _forma_2(comando):
    """reg=comando, data=None - so o registrador, sem dado."""
    arduino.write(reg=comando, data=None)


def _forma_3(comando):
    """reg=comando, data=1 byte de enchimento."""
    arduino.write(reg=comando, data=b"\x00")


def _forma_4(comando):
    """reg=0, data=1 byte - registrador fixo, comando no dado."""
    arduino.write(reg=0x00, data=bytes((comando,)))


def _forma_5(comando):
    """
    Leitura com registrador. O byte devolvido nao interessa - o que
    importa e que o registrador vai para o fio como escrita.

    ATENCAO se esta for a vencedora: o byte que ela devolve e o status
    ANTIGO, nao o novo. A biblioteca Wire do Arduino so entrega o
    recebimento ao aoReceber() quando chega o STOP, e numa leitura com
    registrador o onRequest acontece ANTES disso. Ou seja: mande o
    comando com esta forma e leia o status DEPOIS, em outra chamada.
    """
    arduino.read(reg=comando, length=1)


FORMAS = (
    ("F1 reg=None+dado", _forma_1),
    ("F2 reg=cmd s/dado", _forma_2),
    ("F3 reg=cmd+enche", _forma_3),
    ("F4 reg=0+dado", _forma_4),
    ("F5 leitura c/ reg", _forma_5),
)


def _repousar():
    """
    Volta o servo ao repouso entre as tentativas, por todas as formas.
    As que nao funcionam nao fazem nada - e tudo bem, porque nesse caso
    o servo tambem nao saiu do lugar.
    """
    for _, forma in FORMAS:
        tentar(lambda: forma(CMD_REPOUSO))
    wait(600)


def _teste_2_formas():
    """
    Para cada forma: manda o comando da coluna 1 e le o status.

        status 1     O COMANDO CHEGOU. Esta e a forma boa.
        status 0     o byte nao chegou, ou chegou vazio.
        OSError      a conversa falhou no fio.
        ValueError   essa combinacao nem existe no driver do EV3.

    Se NENHUMA das cinco funcionar, a serial do Arduino conta o resto: as
    linhas "rx" dizem se ele esta recebendo alguma coisa, e sem nenhuma
    "rx" nao e a forma - e o fio do SDA.

    MAS NAO LIGUE O USB JUNTO COM O CABO DO EV3 (ver o cabecalho do
    arduino_servos.ino): com os dois o Nano esquenta. Rode este teste com
    o cabo do EV3 sozinho, anote o resultado, e so entao troque para o
    USB sozinho para ler a serial.
    """
    msg("5 formas:")

    vencedoras = []

    for nome, forma in FORMAS:
        _repousar()

        _, erro = tentar(lambda: forma(CMD_COLUNA_1))

        if erro:
            msg(nome, erro)
            continue

        wait(20)
        lido = status()

        if lido == 1:
            msg(nome, "CHEGOU")
            vencedoras.append(nome)
        else:
            msg(nome, "nao", lido)

        wait(800)

    _repousar()

    if vencedoras:
        msg("USE:", vencedoras[0])
        msg("no enviar() do servos")
        ev3.speaker.beep()
    else:
        msg("NENHUMA chegou")
        msg("ver Serial Monitor")
        ev3.speaker.beep(frequency=200, duration=800)


if __name__ == "__main__":

    ev3.screen.clear()

    # A ordem e do fio para cima: primeiro o barramento enderecca, depois
    # quem responde, so entao qual forma de escrita chega. Nenhum dos
    # tres interrompe por conta propria: cada um so estreita a duvida, e
    # rodar os seguintes com o barramento suspeito ainda informa.
    if _teste_0_barramento():
        wait(1500)
        ev3.screen.clear()

        if _teste_1_assinatura():
            wait(1500)
            ev3.screen.clear()
            _teste_2_formas()

    wait(15000)
