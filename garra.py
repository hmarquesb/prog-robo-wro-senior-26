#!/usr/bin/env pybricks-micropython
"""
garra.py - Garra do motor_D
===========================

Hardware vem do setup.py. Os numeros da garra moram AQUI, logo abaixo -
sao dela e de mais ninguem.

    import garra as g

    g.zerar_garra()          # UMA VEZ no inicio: acha o batente de baixo
    g.descer_garra()         # volta para a altura de baixo, aberta
    g.mover_garra(600, 720)  # sobe / arremessa: velocidade e tempo

Dois jeitos de mandar a garra girar, e nada mais mexe no motor_D:

    mover_garra(v, ms)          por TEMPO   - o unico que serve para
                                arremessar, porque a forca do arremesso e
                                (velocidade x tempo)
    mover_garra_ate_angulo(a)   ate um ANGULO absoluto, contado do zero
                                que zerar_garra marcou no batente

zerar_garra e descer_garra sao so combinacoes dessas duas.

POR QUE UM ZERO: o curso da garra termina num batente mecanico. Descer
sempre "por tempo" parece funcionar, mas a sobra de cada descida se
ACUMULA - a subida muda de forca conforme o que ela esta carregando, e o
tempo fixo da descida nunca desfaz exatamente o que a subida fez. Com o
zero marcado uma vez, toda descida vira "va para o angulo X" e para
sempre na mesma altura, do primeiro ao ultimo movimento do programa.

A GARRA SO DESCE O CURSO INTEIRO COM O CARRINHO FORA DO BATENTE. Com o
carrinho todo recolhido ela bate na estrutura do robo antes do fim do
curso. Isso vale para qualquer programa: mande o motor_A tirar o carrinho
do batente ANTES de chamar zerar_garra, senao o zero sai alto e todas as
descidas do programa junto.

A GARRA NAO ESCOLHE A COLUNA DE ARMAZENAGEM. As 3 colunas sao fixas no
topo do robo e quem poe a boca certa debaixo dela e o servo (servos.py).
O arremesso e UM SO para os 12 blocos - o par (velocidade, tempo) fica no
pegar_blocos.py, que e quem arremessa.

Os movimentos podem ser BLOQUEANTES (padrao) ou NAO BLOQUEANTES
(esperar=False), para acionar a garra junto com outro mecanismo:

    g.descer_garra(esperar=False)   # a garra comeca a descer
    m.andar(-100)                   # o robo recua enquanto ela desce
    g.esperar_garra()               # so entao cobra o fim da descida

CUIDADO com esse ultimo caso: na parte1 ele entortava o robo no teste
real, e a descida voltou a ser feita com o robo parado. A garra e mais
leve que o carrinho, mas nao e de graca.
"""

from pybricks.parameters import Stop
from pybricks.tools import wait, StopWatch

from setup import ev3, motor_D


MOTOR_GARRA = motor_D


# =============================================================================
# OS NUMEROS DA GARRA
# =============================================================================

# --- POSICAO ABAIXADA: onde a garra para ao descer ---
# Contada do zero que zerar_garra marca NO BATENTE. NAO e zero: sao alguns
# graus ACIMA do batente, de proposito. Se o alvo caisse em cima dele o
# motor ficaria empurrando sem nunca "chegar", e o robo travaria ali no
# meio da prova. Com a folga ela para no ar, livre.
#
#   ainda encosta no batente ao descer  -> AUMENTE
#   para alta demais para pegar o bloco -> diminua
ANGULO_ABAIXADA = 30

# Velocidade da descida. DEVAGAR DE PROPOSITO: a descida acontece com a
# garra ja em cima do bloco, e descer rapido a faz bater nele e derrubar.
# O sinal so importa em zerar_garra, que gira contra o batente sem saber
# onde a garra esta.
#
# ESTE E OS TEMPOS ANDAM JUNTOS: baixar a velocidade sem subir TIMEOUT_MS
# e TEMPO_ZERAR_MS na mesma proporcao faz a garra ser cortada no meio do
# caminho.
V_DESCER = -800

# Rede de seguranca da descida: se em TIMEOUT_MS a garra nao chegou no
# alvo, o programa desiste do movimento e SEGUE. Tem de caber a descida
# inteira COM FOLGA.
TIMEOUT_MS = 3000

# Como o motor para no fim de cada giro. HOLD: escorregar depois de um
# arremesso desalinharia a proxima descida.
PARADA = Stop.HOLD

# --- ZERAGEM (uma unica vez por programa) ---
# zerar_garra desce POR TEMPO ate o batente e chama aquele ponto de zero.
# Curto demais e o zero fica marcado no meio do curso, e TODA descida do
# programa erra junto - o pior estrago possivel aqui.
#
# Este e o valor com o carrinho POUCO estendido. Quem zera com o carrinho
# todo para fora (o pegar_blocos, em cima da coluna) tem curso livre mais
# longo e passa o seu proprio tempo na chamada.
TEMPO_ZERAR_MS = 1600

# --- LEVANTAR ---
# A garra nao tem "angulo levantado": ela sobe por TEMPO, e o par
# (velocidade, tempo) e que define ate onde vai. Por isso cada subida da
# prova leva o seu par escrito na propria chamada; estes dois sao so o
# default do teste no fim deste arquivo.
LEVANTAR_V  = 500
LEVANTAR_MS = 720


# =============================================================================
# 1. MOVIMENTOS BASICOS
# =============================================================================

def mover_garra(velocidade, tempo_ms, parada=PARADA, esperar=True):
    """
    Gira o motor_D por TEMPO (nao por graus): `velocidade` em graus/s,
    com o sinal definindo o sentido, durante `tempo_ms` milissegundos.

    E o unico jeito de ARREMESSAR: a forca do arremesso e o par
    (velocidade, tempo), e e ele que decide o quanto o bloco viaja. Por
    isso `tempo_ms` nao tem valor padrao - quem chama sempre sabe quanto
    quer.

    O ARREMESSO E UM SO PARA OS 12 BLOCOS. Ele nao escolhe a coluna de
    armazenagem: as colunas sao fixas no topo do robo e quem poe a boca
    certa debaixo da garra e o servo (servos.py).

    Cuidado com tempos curtos: o run_time sobe do zero e volta ao zero
    DENTRO do tempo pedido. Para a garra chegar mesmo na velocidade
    pedida, o tempo tem de ser no minimo 2 x velocidade / aceleracao do
    motor_D (motor_D.control.limits()[1]) - abaixo disso ela passa o
    movimento inteiro acelerando e ja freando, e gira um arco pequeno por
    mais alta que seja a velocidade.

    esperar=True  -> so devolve o controle quando a garra terminar
    esperar=False -> dispara e volta na hora. Quem usa fica responsavel
                     por esperar (esperar_garra).
    """
    MOTOR_GARRA.run_time(velocidade, tempo_ms, then=parada, wait=esperar)


def mover_garra_ate_angulo(angulo, velocidade=V_DESCER, parada=PARADA,
                           timeout=TIMEOUT_MS, esperar=True):
    """
    Leva o motor_D ate um angulo ABSOLUTO, contado do zero marcado por
    zerar_garra. Bloqueia ate chegar - ou ate estourar o `timeout`.

    Por angulo, e nao por tempo, e o que garante que a garra pare sempre
    na MESMA altura: nao importa quanto a subida anterior girou, daqui
    ela volta exatamente para o ponto pedido, sem sobra para acumular.

    O TIMEOUT existe porque um alvo por angulo pode ser inalcancavel: se
    a garra encostar no batente antes da conta fechar, o motor empurra o
    batente e nunca se da por "chegado" - com o run_target esperando
    (wait=True) o programa ficaria parado ali para sempre, no meio da
    prova. Por isso o movimento e SEMPRE disparado sem esperar, e a
    espera fica por conta do esperar_garra, no relogio.

    Estourando o timeout, para de empurrar (`parada`), apita e devolve
    False - o robo perde aquele movimento, mas CONTINUA a rodada. Se isso
    acontecer, o alvo esta caindo em cima do batente: aumente
    ANGULO_ABAIXADA (mais folga) ou rode zerar_garra de novo.

    `velocidade` e so o modulo (graus/s) - quem decide o sentido e o
    angulo de destino, entao um valor negativo aqui nao inverteria nada.

    esperar=True  -> devolve True/False conforme tenha chegado no alvo
    esperar=False -> dispara e volta na hora, devolvendo None: ainda nao
                     ha resultado. Quem chama fica responsavel por
                     esperar (esperar_garra).
    """
    MOTOR_GARRA.run_target(abs(velocidade), angulo, then=parada, wait=False)
    if not esperar:
        return None
    return esperar_garra(timeout, parada)


def garra_chegou():
    """True quando a garra terminou o ultimo movimento."""
    return MOTOR_GARRA.control.done()


def esperar_garra(timeout=TIMEOUT_MS, parada=PARADA):
    """
    Bloqueia ate a garra terminar. Devolve False se estourar o timeout.

    Serve para o padrao "garra + outro mecanismo ao mesmo tempo": dispara
    os dois com esperar=False e espera os dois no fim.

    Estourando o timeout, PARA DE EMPURRAR (`parada`), apita e avisa no
    print - um movimento que nao terminou no prazo e a garra travada em
    cima de alguma coisa, e deixar o motor forcando ali so esquenta o
    motor e atrapalha o proximo movimento. Com Stop.HOLD ela para mas
    segura a altura onde chegou; com COAST solta.

    O robo CONTINUA a rodada de qualquer jeito - quem chama decide se o
    False importa.
    """
    relogio = StopWatch()
    while not garra_chegou():
        if relogio.time() > timeout:
            if parada == Stop.HOLD:
                MOTOR_GARRA.hold()   # para de empurrar, mas segura a altura
            else:
                MOTOR_GARRA.stop()
            ev3.speaker.beep(200, 300)
            print("garra nao terminou o movimento - parou em",
                  MOTOR_GARRA.angle(), "graus")
            return False
        wait(10)
    return True


def angulo_garra():
    """Angulo atual da garra, contado do zero que zerar_garra marcou."""
    return MOTOR_GARRA.angle()


# =============================================================================
# 2. MOVIMENTOS DA PROVA
# =============================================================================

def zerar_garra(velocidade=V_DESCER, tempo_ms=TEMPO_ZERAR_MS, parada=PARADA,
                angulo_abaixada=ANGULO_ABAIXADA, apitar=True):
    """
    Abaixa a garra ate o batente de baixo, deixando-a ABERTA, chama
    aquele ponto de zero e sobe a folga de `angulo_abaixada` para sair de
    cima dele.

    CHAME UMA VEZ NO INICIO DE TODO PROGRAMA que va mexer na garra. Esta e
    a UNICA vez em que a garra encosta no batente: dali em diante
    descer_garra volta a esta mesma altura por angulo, parando um pouco
    antes do fim do curso.

    E a unica que pode ir ao batente porque nao depende do encoder -
    empurra POR TEMPO e so entao define a referencia. Uma descida por
    angulo que empurrasse o batente ficaria esperando para sempre; esta
    aqui nao espera "chegar", so cronometra.

    `tempo_ms` TEM DE CHEGAR AO BATENTE COM FOLGA. Curto demais e o zero
    fica marcado no meio do caminho, e TODA descida do programa erra
    junto. O default vale para o carrinho pouco estendido; quem zera com
    ele todo para fora passa um tempo maior na chamada.

    EXIGE O CARRINHO JA FORA DO BATENTE. Com ele todo recolhido a garra
    bate na estrutura do robo antes do fim do curso, e o zero marcado
    aqui - a referencia de TODAS as descidas do programa - sairia alto.
    Mande o motor_A tirar o carrinho do batente primeiro, sempre.

    O que tambem nao pode e abrir a garra em cima de um objeto que ainda
    esta la, ou contra a parede.

    `apitar` avisa que a zeragem terminou. Desligue se o programa ja usa
    apitos para outra coisa naquele momento.
    """
    mover_garra(velocidade, tempo_ms, parada)
    MOTOR_GARRA.reset_angle(0)       # aqui, encostado, e o zero de tudo
    mover_garra_ate_angulo(angulo_abaixada, velocidade, parada)
    if apitar:
        ev3.speaker.beep()


def descer_garra(velocidade=V_DESCER, angulo_abaixada=ANGULO_ABAIXADA,
                 parada=PARADA, esperar=True):
    """
    Volta a garra para a altura de baixo - aberta e pronta para fechar em
    cima do proximo objeto -, isto e, para `angulo_abaixada`, logo acima
    do zero que zerar_garra marcou no batente.

    Desce EXATAMENTE o que a subida anterior subiu, ao contrario, seja
    qual for a forca daquela subida: como o destino e um angulo absoluto,
    nao ha sobra de um movimento para se somar a do proximo. Era
    justamente isso que acontecia quando a descida era por tempo fixo - a
    garra ia parando cada vez mais embaixo.

    NAO encosta no batente - para na folga antes dele. Se encostasse, o
    motor ficaria empurrando sem nunca chegar no alvo e o programa
    esperaria ali para sempre; e por isso que o alvo nao e o zero, e por
    isso que mover_garra_ate_angulo ainda tem timeout por cima.

    Devolve False se nao chegou (ver mover_garra_ate_angulo), para quem
    chama poder avisar. O robo segue de qualquer jeito.

    esperar=False dispara a descida e volta na hora, para descer a garra
    AO MESMO TEMPO que outra coisa acontece. Devolve None e quem chama
    espera com esperar_garra().

    Precisa que zerar_garra ja tenha rodado; sem isso o zero nao tem
    referencia nenhuma. E, como ele, precisa do carrinho fora do batente
    para ter curso livre.
    """
    return mover_garra_ate_angulo(angulo_abaixada, velocidade, parada,
                                  esperar=esperar)


# =============================================================================
# 3. TESTE
# =============================================================================

if __name__ == "__main__":

    from setup import motor_A

    # O CARRINHO PRIMEIRO, sempre: com ele no batente a garra bate na
    # estrutura do robo e nao desce o curso todo. Ajuste os graus abaixo
    # ate o carrinho sair o suficiente para a garra ter curso livre.
    motor_A.run_angle(1000, 120)

    zerar_garra()
    print("depois de zerar, a garra esta em", angulo_garra(), "graus")
    wait(1000)

    # Sobe e desce algumas vezes. "voltou a" tem de dar sempre
    # ANGULO_ABAIXADA, igual nas tres voltas - se for baixando, a garra
    # esta escorregando no mecanismo e nao e problema de programa.
    # Nenhum "garra nao terminou" (o apito longo): se aparecer, o alvo
    # esta batendo no batente e ANGULO_ABAIXADA tem de subir.
    for volta in range(3):
        mover_garra(LEVANTAR_V, LEVANTAR_MS)
        print("volta", volta + 1, "- subiu ate", angulo_garra(), "graus")
        wait(500)
        descer_garra()
        print("           voltou a", angulo_garra(), "graus")
        wait(500)

    ev3.speaker.beep()
