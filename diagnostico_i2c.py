#!/usr/bin/env pybricks-micropython
"""
diagnostico_i2c.py - A conversa EV3 <-> Arduino esta sadia?
===========================================================

ARQUIVO DE APOIO, NAO E PARTE DA PROVA. Rode com F5 quando o servo se
comportar de um jeito estranho e voce nao souber de qual lado esta o
problema: cabo, pull-up, alimentacao, sketch errado ou o servo em si.

O QUE ELE FAZ DE DIFERENTE dos outros dois arquivos de apoio:

    diagnostico.py     descobre QUAL IMPORT quebra o programa
    teste_arduino.py   dois testes de bancada, um passa/falha por vez
    ESTE               mede a conversa e IMPRIME UM RELATORIO inteiro,
                       mesmo quando tudo passa

O relatorio e a razao de existir deste arquivo: ele nao para no primeiro
erro. Roda os 6 exames ate o fim, junta os numeros e imprime um bloco
entre linhas de ==== no Debug Console. COPIE ESSE BLOCO INTEIRO e mande
para quem for ajudar - ele diz sozinho o que esta acontecendo, sem
precisar descrever o sintoma.

DE PROPOSITO nao importa setup.py nem servos.py: o setup.py cria os 4
motores, e na bancada, com so o cabo do Arduino plugado, isso da erro
antes do exame comecar. Por isso as constantes do protocolo estao
repetidas aqui - se mudar o endereco ou os comandos no
arduino_servos.ino, mude no constantes.py E aqui.

ANTES DE RODAR
--------------
  1. Nano ligado (LED de power aceso) com o arduino_servos.ino gravado.
  2. Cabo do EV3 na porta S1 - e o USB do Arduino DESLIGADO. Com os dois
     juntos o Nano esquenta (ver o cabecalho do arduino_servos.ino).
  3. Pull-ups de 82k (valor da documentacao oficial do EV3) ligados ao
     pino 4 do EV3, nao ao 5V do Arduino.
  4. Servo alimentado pela bateria de 4x AA (6V), NAO pelo 5V do Nano.
  5. GND comum entre EV3, Arduino e bateria dos servos. E o erro de
     montagem mais comum, e produz exatamente o sintoma "as vezes
     funciona".

O SERVO VAI SE MEXER. Deixe o mecanismo livre para percorrer o curso
inteiro, ou desacople o servo antes.
"""

from pybricks.hubs import EV3Brick
from pybricks.iodevices import I2CDevice
from pybricks.parameters import Port
from pybricks.tools import wait, StopWatch


# --- tem que bater com o arduino_servos.ino (e com o constantes.py) ---
PORTA_ARDUINO = Port.S1
ENDERECO = 0x04            # 7 bits dos dois lados, sem deslocar

CMD_COLUNA_1 = 0x10
CMD_REPOUSO  = 0x11
CMD_COLUNA_2 = 0x12
CMD_COLUNA_3 = 0x13
CMD_INVALIDO = 0xFF        # nao existe no switch do sketch, de proposito

ASSINATURA = 0x5A          # segundo byte da resposta do sketch v2

COMANDOS = (
    (CMD_REPOUSO,  "repouso  0x11"),
    (CMD_COLUNA_1, "coluna 1 0x10"),
    (CMD_COLUNA_2, "coluna 2 0x12"),
    (CMD_COLUNA_3, "coluna 3 0x13"),
)

# Quantas amostras cada exame tira. Numeros altos demoram; estes dao
# estatistica suficiente para separar "ruim sempre" de "ruim as vezes".
AMOSTRAS_LEITURA = 30
AMOSTRAS_ESCRITA = 30

TIMEOUT = 3000             # ms; se passar disso, o servo nunca "chega"


ev3 = EV3Brick()
arduino = I2CDevice(PORTA_ARDUINO, ENDERECO)


# =============================================================================
# 1. O BARRAMENTO (uma escrita, uma leitura, sem interpretar nada)
# =============================================================================

def escrever(comando):
    """Escreve 1 byte. Devolve True, ou False se o barramento recusou."""
    try:
        arduino.write(reg=None, data=bytes((comando,)))
        return True
    except (OSError, ValueError):
        return False


def ler():
    """Devolve o byte de status, ou None se o Arduino nao respondeu."""
    try:
        return arduino.read(reg=None, length=1)[0]
    except (OSError, ValueError):
        return None


def esperar_livre(timeout=TIMEOUT):
    """
    Espera o status virar 0. Devolve o tempo gasto em ms, ou -1 se
    estourou o timeout.

    Esse -1 e o que separa "servo lento" de "o Arduino nunca disse que
    terminou" - e o segundo caso e comunicacao, nao mecanica.
    """
    relogio = StopWatch()
    while True:
        if ler() == 0:
            return relogio.time()
        if relogio.time() > timeout:
            return -1
        wait(10)


# =============================================================================
# 2. O RELATORIO (so acumula linhas; nada e impresso antes do fim)
# =============================================================================

linhas = []
problemas = []

# Quantos comandos validos o Arduino ignorou no exame 4. O exame 6 le
# este numero: com nenhuma escrita chegando, o byte invalido dele
# tambem nao chegou, e o veredito sobre a versao do sketch nao vale.
comandos_ignorados = 0


def anotar(*partes):
    """Uma linha do relatorio."""
    linhas.append(" ".join([str(p) for p in partes]))


def problema(texto):
    """Um sintoma, para a lista do fim. Nao interrompe o exame."""
    problemas.append(texto)


# =============================================================================
# 3. OS EXAMES
# =============================================================================

def exame_1_presenca():
    """
    O Arduino esta ai? Le algumas vezes e conta quantas responderam.

    A primeira leitura depois de ligar as vezes sai vazia - por isso o
    que interessa e a CONTAGEM, nao a primeira resposta.
    """
    anotar("[1] PRESENCA")

    ok = 0
    for _ in range(5):
        if ler() is not None:
            ok += 1
        wait(50)

    anotar("    respondeu", ok, "de 5")

    if ok == 0:
        problema("MUDO: nada respondeu no endereco 0x04 da porta S1.")
        problema("  -> cabo, pull-up de 82k, ou Nano sem alimentacao.")
        return False

    if ok < 5:
        problema("INTERMITENTE: o Arduino respondeu so as vezes.")
        problema("  -> pull-up fraco/ausente, GND nao comum, ou cabo ruim.")

    # Le 2 bytes: o sketch responde [status, ASSINATURA]. Isto separa
    # "o Arduino respondeu 0" de "o SDA esta em curto com o GND", que
    # dao leituras identicas quando se pede um byte so.
    try:
        resposta = list(arduino.read(reg=None, length=2))
    except (OSError, ValueError):
        # ValueError = essa combinacao nem existe no driver do EV3.
        # Com reg=None ele so sabe ler UM byte, entao a assinatura fica
        # sem confirmacao - inconclusivo, nao um problema.
        resposta = None

    anotar("    2 bytes =", resposta)

    if resposta is None or len(resposta) < 2:
        anotar("    (sem assinatura - nao da para confirmar quem respondeu)")
    elif resposta[1] == ASSINATURA:
        anotar("    assinatura ok - e o sketch v2")
    elif resposta[1] == 0:
        problema("LINHA EM CURTO: tudo devolve 0, nem a assinatura chega.")
        problema("  -> SDA encostado no GND ou no pino errado. Nao e software.")
    elif resposta[1] == 0xFF:
        problema("LINHA SOLTA: tudo devolve 0xFF, nao ha escravo respondendo.")
    else:
        anotar("    assinatura diferente - sketch antigo ou outro dispositivo")

    return True


def exame_2_ruido_de_leitura():
    """
    Com o servo parado, o status TEM de ser 0 em todas as leituras.

    Um 1 solto aqui e o Arduino ocupado com outra coisa; qualquer valor
    que nao seja 0 nem 1 nao e resposta - e ruido do barramento, e ai
    nada do que os outros exames medirem vale.
    """
    anotar("[2] LEITURA EM REPOUSO")

    escrever(CMD_REPOUSO)
    esperar_livre()
    wait(300)

    zeros = 0
    uns = 0
    mudos = 0
    lixo = []

    for _ in range(AMOSTRAS_LEITURA):
        valor = ler()
        if valor is None:
            mudos += 1
        elif valor == 0:
            zeros += 1
        elif valor == 1:
            uns += 1
        else:
            lixo.append(valor)
        wait(20)

    anotar("    0 =", zeros, " 1 =", uns,
           " mudo =", mudos, " lixo =", len(lixo))
    if lixo:
        anotar("    valores estranhos:", lixo[:8])

    if lixo:
        problema("RUIDO: vieram bytes que nao sao 0 nem 1.")
        problema("  -> pull-up errado, cabo longo demais, ou GND nao comum.")
    if mudos:
        problema("PERDA: " + str(mudos) + " de " + str(AMOSTRAS_LEITURA) +
                 " leituras nao responderam.")
    if uns:
        problema("OCUPADO PARADO: diz estar movendo com o servo em repouso.")
        problema("  -> servo forcando batente, ou tempo de curso longo demais.")


def exame_3_confiabilidade_da_escrita():
    """
    Escreve muitas vezes seguidas e conta as recusas.

    Uma escrita perdida no meio da prova e um bloco na coluna errada. A
    taxa aqui e o que diz se vale confiar em uma escrita so ou se a
    montagem precisa de conserto.
    """
    anotar("[3] ESCRITA REPETIDA")

    falhas = 0
    for _ in range(AMOSTRAS_ESCRITA):
        if not escrever(CMD_REPOUSO):
            falhas += 1
        wait(20)

    anotar("    falhou", falhas, "de", AMOSTRAS_ESCRITA)

    if falhas:
        problema("ESCRITA PERDIDA: " + str(falhas) + " de " +
                 str(AMOSTRAS_ESCRITA) + " escritas foram recusadas.")
        problema("  -> mesmo diagnostico do ruido: pull-up, GND, cabo.")


def exame_4_eco_do_comando():
    """
    Cada comando valido tem de deixar o Arduino OCUPADO na hora.

    E o unico jeito de saber que a escrita CHEGOU: se o status nao muda
    para 1 depois de escrever, o byte se perdeu ou o sketch nao trata
    aquele comando.
    """
    global comandos_ignorados

    anotar("[4] O COMANDO CHEGA?")

    escrever(CMD_REPOUSO)
    esperar_livre()
    wait(300)

    for comando, nome in COMANDOS[1:]:
        escrever(comando)
        wait(20)
        status = ler()
        anotar("   ", nome, "-> status", status)

        if status != 1:
            comandos_ignorados += 1
            problema("COMANDO IGNORADO: " + nome + " nao deixou o Arduino ocupado.")
            problema("  -> ou a escrita nao chega, ou o sketch nao trata esse byte.")

        esperar_livre()
        wait(400)

    escrever(CMD_REPOUSO)
    esperar_livre()


def exame_5_tempo_de_curso():
    """
    Quanto tempo o Arduino diz que cada salto leva.

    O numero e o que o SKETCH calcula, nao o servo real - serve para
    conferir se o TEMPO_POR_GRAU esta coerente com o curso e para
    flagrar um salto que nunca termina.
    """
    anotar("[5] TEMPO DE CURSO (o que o sketch declara)")

    escrever(CMD_REPOUSO)
    esperar_livre()
    wait(300)

    for comando, nome in COMANDOS[1:]:
        escrever(comando)
        gasto = esperar_livre()
        anotar("   ", nome, "->", gasto, "ms")

        if gasto < 0:
            problema("NUNCA TERMINA: " + nome + " nao voltou a 0 em " +
                     str(TIMEOUT) + " ms.")
            problema("  -> servo travado no batente, ou a conversa caiu no meio.")

        wait(400)

    escrever(CMD_REPOUSO)
    esperar_livre()


def exame_6_versao_do_sketch():
    """
    Um byte que nao existe no switch distingue as duas versoes do sketch:

        status 1  o sketch NOVO segura "ocupado" de proposito, para o
                  EV3 apitar o timeout em vez de achar que deu certo
        status 0  o sketch ANTIGO responde "terminei" para lixo - e ai
                  as colunas 2 e 3 falham em silencio

    Vale mais que qualquer outro exame quando "gravei e nao mudou nada":
    diz se o Nano esta rodando a versao que voce acha que gravou.
    """
    anotar("[6] VERSAO DO SKETCH")

    escrever(CMD_REPOUSO)
    esperar_livre()
    wait(300)

    escrever(CMD_INVALIDO)
    wait(20)
    status = ler()
    anotar("    byte invalido 0xFF -> status", status)

    if status == 1:
        anotar("    sketch NOVO (4 comandos)")
    elif status == 0:
        # SO da para culpar a versao do sketch se as escritas estiverem
        # chegando. Com o exame 4 acusando todos os comandos ignorados, o
        # byte invalido tambem nao chegou - e o 0 aqui nao diz nada sobre
        # qual sketch esta gravado.
        if comandos_ignorados:
            anotar("    INCONCLUSIVO - nenhuma escrita chega")
        else:
            anotar("    sketch ANTIGO")
            problema("SKETCH DESATUALIZADO: o Nano responde 0 a byte invalido.")
            problema("  -> regrave o arduino_servos.ino; as colunas 2 e 3 nao existem la.")
    else:
        problema("Sem resposta ao byte invalido - ver exames 1 e 2.")

    # Tira o Arduino do "ocupado" artificial e deixa o servo em repouso.
    escrever(CMD_REPOUSO)
    esperar_livre()


# =============================================================================
# 4. PROGRAMA
# =============================================================================

if __name__ == "__main__":

    ev3.screen.clear()
    ev3.screen.print("Diagnostico I2C")
    ev3.screen.print("aguarde...")

    anotar("==== DIAGNOSTICO I2C EV3 <-> ARDUINO ====")
    anotar("porta S1, endereco 0x04")
    anotar("")

    # O exame 1 e o unico que interrompe: sem ninguem do outro lado, os
    # cinco seguintes so produziriam paginas de "mudo".
    vivo = exame_1_presenca()
    anotar("")

    if vivo:
        for exame in (exame_2_ruido_de_leitura,
                      exame_3_confiabilidade_da_escrita,
                      exame_4_eco_do_comando,
                      exame_5_tempo_de_curso,
                      exame_6_versao_do_sketch):
            exame()
            anotar("")

    anotar("---- CONCLUSAO ----")
    if problemas:
        for p in problemas:
            anotar(p)
    else:
        anotar("Nada estranho. A conversa esta sadia.")
        anotar("Se o servo ainda erra a coluna, e ANGULO, nao comunicacao:")
        anotar("ajuste ANG_COLUNA_* no arduino_servos.ino.")
    anotar("==== FIM (copie deste bloco inteiro) ====")

    for linha in linhas:
        print(linha)

    # A tela do brick nao cabe o relatorio - so o veredito, para quem
    # estiver longe do computador.
    ev3.screen.clear()
    if not vivo:
        ev3.screen.print("MUDO")
        ev3.speaker.beep(frequency=200, duration=800)
    elif problemas:
        ev3.screen.print(len(problemas), "problemas")
        ev3.screen.print("ver o console")
        ev3.speaker.beep(frequency=200, duration=800)
    else:
        ev3.screen.print("TUDO OK")
        ev3.speaker.beep()

    wait(10000)
