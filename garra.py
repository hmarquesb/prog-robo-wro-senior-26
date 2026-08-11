#!/usr/bin/env pybricks-micropython
"""
garra.py - Garra do motor_D
===========================

Hardware vem do setup.py. Mesmo papel do carrinho.py, so que para a
garra: qualquer programa que precise mexer no motor_D importa daqui em
vez de chamar motor_D.run_time() na mao.

    import garra as g

    g.zerar_garra()          # UMA VEZ no inicio: acha o batente de baixo
    g.descer_garra()         # volta para a altura de baixo, aberta
    g.mover_garra(700, 800)  # arremesso (velocidade, tempo) - so quem
                             # chama sabe a forca que quer

Tres jeitos de mandar a garra girar, e nada mais mexe no motor_D:

    mover_garra(v, ms)          por TEMPO   - o unico que serve para
                                arremessar, porque a forca do arremesso e
                                (velocidade x tempo)
    mover_garra_ate_travar(v)   ate ENCOSTAR no batente, sem cronometro
    mover_garra_ate_angulo(a,v) ate um ANGULO absoluto, contado do zero
                                que zerar_garra marcou no batente

zerar_garra e descer_garra sao so combinacoes dessas tres.

POR QUE UM ZERO: o curso da garra termina num batente mecanico. Descer
sempre "por tempo" parece funcionar, mas a sobra de cada descida se
ACUMULA - a subida muda de forca conforme o que ela esta carregando, e o
tempo fixo da descida nunca desfaz exatamente o que a subida fez. Com o
zero marcado uma vez, toda descida vira "va para o angulo X" e para
sempre na mesma altura, do primeiro ao ultimo movimento do programa.

A GARRA SO DESCE O CURSO INTEIRO COM O CARRINHO FORA DO BATENTE. Com o
carrinho todo recolhido ela bate na estrutura do robo antes do fim do
curso. Isso vale para qualquer programa: leve o carrinho para fora ANTES
de chamar zerar_garra, senao o zero sai alto e todas as descidas do
programa junto (ver carrinho.py).

Os movimentos podem ser BLOQUEANTES (padrao) ou NAO BLOQUEANTES
(esperar=False), igual ao carrinho.py, para acionar a garra junto com
outro mecanismo:

    g.descer_garra(esperar=False)   # a garra comeca a descer
    m.andar(-100)                   # o robo recua enquanto ela desce
    g.esperar_garra()               # so entao cobra o fim da descida

A regra do carrinho - nao mover enquanto o robo anda - nasceu do
deslocamento de MASSA dele, que destoa o PD de sincronismo das rodas no
meio do percurso. A garra e bem mais leve, entao o caso acima e viavel,
mas e teste no robo real: se o robo so sair torto nos trechos em que a
garra se mexe, volte a fazer um de cada vez.
"""

from pybricks.parameters import Stop
from pybricks.tools import wait, StopWatch

from setup import ev3, motor_D


# =============================================================================
# 1. CONFIGURACAO
# =============================================================================

MOTOR_GARRA = motor_D

# Altura em que a garra para ao descer, contada do zero que zerar_garra
# marca NO BATENTE. NAO e zero: e uns graus ACIMA do batente, de proposito.
#
# Descer por angulo so e seguro se o alvo estiver ANTES do batente. Se o
# alvo caisse em cima dele (ou depois), o motor ficaria empurrando o
# batente sem nunca "chegar", e o run_target esperaria para sempre - o
# robo travava ali no meio da prova. Com a folga ele para no ar, livre.
#
# Suba este valor se a garra ainda encostar no batente ao descer; abaixe
# se ela estiver parando alta demais para abracar o objeto.
ANGULO_GARRA_ABAIXADA = 30

# Velocidade da descida (graus/s). O SINAL so importa em zerar_garra, que
# gira contra o batente sem saber onde a garra esta; descer_garra vai
# para um angulo, entao usa so o modulo.
#
# DEVAGAR DE PROPOSITO. A descida acontece com a garra ja em cima do
# bloco, e descer rapido a faz bater nele e derrubar em vez de abracar.
# Era -500; foi para metade disso.
#
# ESTES TRES ANDAM JUNTOS: baixar a velocidade sem subir TIMEOUT_GARRA_MS
# e TEMPO_GARRA_DESCER_MS na mesma proporcao faz a garra ser cortada no
# meio do caminho - ela nao chega no alvo dentro do prazo e o programa
# desiste do movimento. Mexeu em um, refaca a conta dos outros dois.
V_GARRA_DESCER = -600

# Rede de seguranca da descida (ver mover_garra_ate_angulo): se em
# TIMEOUT_GARRA_MS a garra nao chegou no alvo - travou, ou ficou
# oscilando em volta dele -, o programa desiste do movimento e SEGUE, em
# vez de esperar para sempre.
#
# Tem de caber a descida inteira COM FOLGA: uns 600 graus a 250 graus/s
# ja dao 2,4 s. Dobrou junto com a queda da velocidade (era 1700).
TIMEOUT_GARRA_MS = 3400

# Como o motor para no fim de cada giro. HOLD: a garra tem de ficar
# parada onde chegou, senao o peso dela mesma a faz escorregar - e
# escorregar depois de um arremesso desalinharia a proxima descida.
PARADA_DESCER = Stop.HOLD

# --- So para o zerar_garra (uma unica vez por programa) ---
# EM TESTE: achar o batente por TRAVAMENTO (run_until_stalled) em vez de
# por tempo. O motor roda ate travar no batente e para exatamente ali,
# nao importa quanto tempo leve - mais confiavel que cronometrar, SE
# funcionar: o motor_D e MEDIO, e run_until_stalled e conhecido por so
# ser confiavel nos motores GRANDES (esta na lista de armadilhas do
# README). Se a garra nao parar no batente, ou travar sozinha no meio do
# curso, volte para False: ai vale o run_time de TEMPO_GARRA_DESCER_MS.
DESCER_POR_TRAVAMENTO = False
FORCA_GARRA_DESCER    = 55    # duty_limit em %: baixo o bastante para nao
                              # forcar o batente, alto o bastante para o
                              # motor nao se dar por travado no meio do curso
TEMPO_GARRA_DESCER_MS = 1700  # so usado com DESCER_POR_TRAVAMENTO = False;
                              # longo o bastante para chegar no batente.
                              # E TEMPO, entao anda com V_GARRA_DESCER: a
                              # velocidade caiu pela metade e este dobrou
                              # (era 850) para percorrer o mesmo curso.
                              # Curto demais e o zero fica marcado no meio
                              # do caminho, e TODA descida do programa erra
                              # junto - e o pior estrago possivel aqui.


# =============================================================================
# 2. FUNCOES
# =============================================================================

def mover_garra(velocidade, tempo_ms, parada=Stop.HOLD, esperar=True):
    """
    Gira o motor_D por TEMPO (nao por graus): `velocidade` em graus/s,
    com o sinal definindo o sentido, durante `tempo_ms` milissegundos.

    E o unico jeito de ARREMESSAR: a forca do arremesso e o par
    (velocidade, tempo), e e ele que decide onde o objeto vai cair. Por
    isso `tempo_ms` nao tem valor padrao - quem chama sempre sabe quanto
    quer.

    Cuidado com tempos curtos: o run_time sobe do zero e volta ao zero
    DENTRO do tempo pedido. Para a garra chegar mesmo na velocidade
    pedida, o tempo tem de ser no minimo 2 x velocidade / aceleracao do
    motor_D (motor_D.control.limits()[1]) - abaixo disso ela passa o
    movimento inteiro acelerando e ja freando, e gira um arco pequeno por
    mais alta que seja a velocidade.

    esperar=True  -> so devolve o controle quando a garra terminar
    esperar=False -> dispara e volta na hora, igual ao mover_carrinho.
                     Quem usa fica responsavel por esperar (esperar_garra).
    """
    MOTOR_GARRA.run_time(velocidade, tempo_ms, then=parada, wait=esperar)


def mover_garra_ate_travar(velocidade=V_GARRA_DESCER,
                            forca=FORCA_GARRA_DESCER,
                            parada=Stop.COAST):
    """
    Gira o motor_D ate ele TRAVAR - isto e, ate a garra encostar no
    batente e nao conseguir mais girar - e para ali. Bloqueia ate travar.

    `forca` e o duty_limit em %, igual ao do zerar_carrinho: e o quanto o
    motor pode empurrar antes de se dar por travado. Muito alto forca o
    batente; muito baixo faz ele parar sozinho no meio do curso.

    Devolve o angulo em que travou. Serve para conferir no teste se o
    curso foi o esperado ou se o motor desistiu no meio do caminho.
    """
    return MOTOR_GARRA.run_until_stalled(velocidade, then=parada,
                                         duty_limit=forca)


def mover_garra_ate_angulo(angulo, velocidade=V_GARRA_DESCER,
                            parada=Stop.HOLD, timeout=TIMEOUT_GARRA_MS,
                            esperar=True):
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
    espera fica por conta do esperar_garra, no relogio - exatamente como
    o esperar_carrinho.

    Estourando o timeout, para de empurrar (`parada`), apita e devolve
    False - o robo perde aquele movimento, mas CONTINUA a rodada. Se isso
    acontecer, o alvo esta caindo em cima do batente: aumente
    ANGULO_GARRA_ABAIXADA (mais folga) ou rode zerar_garra de novo.

    `velocidade` e so o modulo (graus/s) - quem decide o sentido e o
    angulo de destino, entao um valor negativo aqui nao inverteria nada.

    esperar=True  -> devolve True/False conforme tenha chegado no alvo
    esperar=False -> dispara e volta na hora, devolvendo None: ainda nao
                     ha resultado. Quem chama fica responsavel por
                     esperar (esperar_garra), igual ao mover_carrinho.
    """
    MOTOR_GARRA.run_target(abs(velocidade), angulo, then=parada, wait=False)
    if not esperar:
        return None
    return esperar_garra(timeout, parada)


def garra_chegou():
    """True quando a garra terminou o ultimo movimento."""
    return MOTOR_GARRA.control.done()


def esperar_garra(timeout=TIMEOUT_GARRA_MS, parada=PARADA_DESCER):
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


def zerar_garra(velocidade=V_GARRA_DESCER,
                 por_travamento=DESCER_POR_TRAVAMENTO,
                 forca=FORCA_GARRA_DESCER,
                 tempo_ms=TEMPO_GARRA_DESCER_MS,
                 parada=PARADA_DESCER,
                 angulo_abaixada=ANGULO_GARRA_ABAIXADA,
                 apitar=True):
    """
    Abaixa a garra ate o batente de baixo, deixando-a ABERTA, chama
    aquele ponto de zero e sobe a folga de `angulo_abaixada` para sair de
    cima dele.

    CHAME UMA VEZ NO INICIO DE TODO PROGRAMA que va mexer na garra -
    mesmo papel do zerar_carrinho. Esta e a UNICA vez em que a garra
    encosta no batente: dali em diante descer_garra volta a esta mesma
    altura por angulo, parando um pouco antes do fim do curso.

    E a unica que pode ir ao batente porque nao depende do encoder -
    empurra ate travar (ou por tempo) e so entao define a referencia. Uma
    descida por angulo que empurrasse o batente ficaria esperando para
    sempre; esta aqui nao espera "chegar", espera travar.

    `por_travamento` escolhe COMO ela sabe que chegou no batente:

        True  : run_until_stalled - para no instante em que trava, sem
                depender de tempo. E o que esta em teste (motor MEDIO).
        False : run_time por `tempo_ms`, o jeito antigo.

    Devolve o angulo de travamento quando `por_travamento`, senao None.
    (E o angulo de ANTES da zeragem - depois dela o batente vale zero.)

    EXIGE O CARRINHO JA FORA DO BATENTE. Com ele todo recolhido a garra
    bate na estrutura do robo antes do fim do curso, e o zero marcado
    aqui - a referencia de TODAS as descidas do programa - sairia alto.
    Rode o carrinho primeiro, sempre.

    O que tambem nao pode e abrir a garra em cima de um objeto que ainda
    esta la, ou contra a parede.

    `apitar` avisa que a zeragem terminou. Desligue se o programa ja usa
    apitos para outra coisa naquele momento.
    """
    angulo = None
    if por_travamento:
        angulo = mover_garra_ate_travar(velocidade, forca, parada)
    else:
        mover_garra(velocidade, tempo_ms, parada)
    MOTOR_GARRA.reset_angle(0)       # aqui, encostado, e o zero de tudo
    mover_garra_ate_angulo(angulo_abaixada, velocidade, parada)
    if apitar:
        ev3.speaker.beep()
    return angulo


def descer_garra(velocidade=V_GARRA_DESCER,
                  angulo_abaixada=ANGULO_GARRA_ABAIXADA,
                  parada=PARADA_DESCER,
                  esperar=True):
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
    AO MESMO TEMPO que outra coisa acontece. Devolve None (ainda nao ha
    resultado) e quem chama espera com esperar_garra():

        g.descer_garra(esperar=False)   # a garra comeca a descer
        m.andar(-100)                   # o robo recua enquanto ela desce
        g.esperar_garra()               # so entao cobra o fim da descida

    Precisa que zerar_garra ja tenha rodado; sem isso o zero nao tem
    referencia nenhuma (igual ao carrinho sem zerar_carrinho). E, como
    ele, precisa do carrinho fora do batente para ter curso livre.
    """
    return mover_garra_ate_angulo(angulo_abaixada, velocidade, parada,
                                  esperar=esperar)


# =============================================================================
# 3. TESTE
# =============================================================================

if __name__ == "__main__":

    import carrinho as c

    # O CARRINHO PRIMEIRO, sempre: com ele no batente a garra bate na
    # estrutura do robo e nao desce o curso todo.
    c.zerar_carrinho(velocidade=800, forca=90)
    c.mover_carrinho(20, velocidade=800)

    # Com DESCER_POR_TRAVAMENTO = True o angulo impresso e onde ela
    # travou: repita o teste algumas vezes e veja se o valor se repete.
    # Variando muito (ou parando longe do batente), o motor medio nao
    # esta dando conta do run_until_stalled - mexa em FORCA_GARRA_DESCER
    # ou volte para o modo por tempo.
    angulo = zerar_garra()
    if angulo is not None:
        print("travou em", angulo, "graus")
    print("depois de zerar, a garra esta em", angulo_garra(), "graus")
    wait(1000)

    # Sobe e desce algumas vezes. "voltou a" tem de dar sempre
    # ANGULO_GARRA_ABAIXADA, igual nas tres voltas - se for baixando, a
    # garra esta escorregando no mecanismo e nao e problema de programa.
    # Nenhum "garra nao chegou" (o apito longo): se aparecer, o alvo esta
    # batendo no batente e ANGULO_GARRA_ABAIXADA tem de subir.
    for volta in range(3):
        mover_garra(700, 800)
        print("volta", volta + 1, "- subiu ate", angulo_garra(), "graus")
        wait(500)
        descer_garra()
        print("           voltou a", angulo_garra(), "graus")
        wait(500)

    ev3.speaker.beep()
