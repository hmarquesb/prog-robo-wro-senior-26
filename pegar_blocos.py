#!/usr/bin/env pybricks-micropython
"""
pegar_blocos.py - Retirada dos blocos do tapete
================================================

O tapete de blocos fica do LADO do robo (o robo fica de lado para os
blocos, nao de frente). O robo so anda RETO e de RE para se alinhar com
a coluna certa; quem alcanca o bloco de lado e o carrinho.

O tapete tem 8 COLUNAS VERTICAIS, 2 por cor, na ordem fixa (nao muda de
partida para partida) a partir de onde o robo comeca:

    branco1, branco2, verde1, verde2, azul1, azul2, amarelo1, amarelo2

Cada coluna vertical tem 3 blocos empilhados de lado, e o carrinho
alcanca OS TRES (perto, meio e fundo). Entao sao 3 blocos por coluna x 2
colunas = 6 BLOCOS ALCANCAVEIS POR COR.

O CICLO DE UM BLOCO - o mesmo do primeiro ao decimo segundo:

    ir_ate_coluna    anda ate a coluna, garra EM CIMA
    pegar_um_bloco   ja parado: carrinho ate a profundidade do bloco,
                     ainda com a garra em cima
    descer a garra   agora sim, parada exatamente em cima do bloco certo.
                     No PRIMEIRO bloco esta descida e o zerar_garra: a
                     unica ida ao batente da rodada
    guardar_bloco    fecha e arremessa DALI MESMO, de onde o carrinho
                     estiver; a garra termina EM CIMA

O CARRINHO ESTENDE ANTES DE A GARRA DESCER, e isso resolve duas coisas de
uma vez: a garra vai EM CIMA dos dois blocos da frente no caminho ate o
do fundo (abaixada, ela ia raspando neles), e a zeragem do primeiro bloco
acontece com o carrinho JA FORA DO BATENTE - que e o que o garra.py exige
para ela chegar no batente de baixo sem bater na estrutura do robo.

QUATRO COISAS QUE O CICLO NAO FAZ MAIS (e fazia):

  * nao zera a garra na largada, e nao anda nada para isso. A zeragem
    acontece la na primeira coluna, com o robo ja parado. A parte2
    termina com dois giros-pivo, e acrescentar meia andada antes da
    primeira coluna so somaria erro de posicao no comeco de tudo.
  * nao recua o carrinho antes do arremesso. O bloco sai de onde o
    carrinho parou. O recuo existia para o bloco nao bater no de tras;
    com a ordem do fundo para a frente (ORDEM_NA_COR) nunca ha bloco
    atras, entao ele virou movimento a toa - 12 vezes por rodada.
  * nao devolve o carrinho para uma "posicao de andar" no fim do bloco.
  * nao recolhe o carrinho para trocar de coluna. O robo anda com ele
    onde estiver, INCLUSIVE TODO ESTENDIDO: o carrinho e impresso em 3D
    agora, nao mais de LEGO, e ficou leve o bastante para isso.

LARGADA (o que a parte2 tem de entregar):

    robo     : de lado para o tapete e ENCOSTADO NA PAREDE. E a posicao 0
               de onde todo o POSICAO_COLUNA foi medido.
    carrinho : ZERADO e FECHADO (no batente).
    garra    : EM CIMA. Ela so desce na primeira coluna.

O CARRINHO SO SE MEXE COM O ROBO PARADO - isso continua valendo (regra 7
do README): quem estende e o pegar_um_bloco, sempre depois de o
ir_ate_coluna ter devolvido. O que mudou e que o robo pode ANDAR com o
carrinho estendido; o proibido e move-lo DURANTE a andada.

APOSTA DA ESTRATEGIA: o mosaico pede 12 blocos e existem 24 alcancaveis
(6 por cor), entao so faltaria bloco se uma cor sozinha fosse pedida
MAIS DE 6 VEZES - metade do mosaico na mesma cor. Ficou improvavel
depois que o terceiro bloco entrou no alcance, mas o robo continua
sabendo se virar: o excedente vira uma cor que ainda tenha bloco
sobrando (ver escolher_cor), de preferencia a mais perto, para nao
gastar percurso.

Quem muda a cada partida e o mosaico lido em leitura_blocos.py, que diz
EM QUE ORDEM os blocos devem ser retirados.

leitura_blocos.py varre o mosaico em zigue-zague (3 colunas de carrinho
x 4 avancos do robo) e devolve uma lista `leituras` com 12 cores nessa
ordem de varredura. COLUNAS_MOSAICO abaixo traduz essa lista de volta
para "4 cores da coluna 1, de cima pra baixo", "4 da coluna 2", etc.

Ordem de retirada exigida: coluna 1, depois coluna 3, depois coluna 2
(do meio) - NAO e a mesma ordem em que o mosaico foi lido.

As distancias/posicoes abaixo sao PLACEHOLDERS - MEDIR COM REGUA /
ajustar no robo real. O teste do fim do arquivo tem um modo so para
conferir POSICAO_COLUNA (ver testar_posicao_coluna).
"""
from pybricks.parameters import Color, Stop, Button
from setup import motor_D, ev3, wait
import movimento as m
import carrinho as c
# As funcoes genericas da garra moram no garra.py, para todo programa
# poder usar. Importadas pelo nome para as chamadas daqui continuarem
# curtas (descer_garra(), e nao g.descer_garra()).
from garra import mover_garra, zerar_garra, descer_garra


# =============================================================================
# 1. CONFIGURACAO (medir com regua / calibrar no robo)
# =============================================================================

# --- Distancia (mm) que o robo anda, a partir da PAREDE, ate ficar
# alinhado de lado com cada uma das 8 colunas verticais: [coluna mais
# proxima do inicio, coluna mais distante] de cada cor.
#
# Sao posicoes ABSOLUTAS, nao "ande mais tanto": errar uma nao desloca as
# outras sete. Ver testar_posicao_coluna. ---
POSICAO_COLUNA = {
    Color.WHITE:  [120, 200],
    Color.GREEN:  [295, 385],
    Color.BLUE:   [450, 550],
    Color.YELLOW: [610, 700],
}
 #Color.WHITE:  [105, 175],
 #   Color.GREEN:  [270, 360],
 #   Color.BLUE:   [430, 500],
 #   Color.YELLOW: [610, 655],
# Mesma ordem fisica do tapete. Existe como tupla (e nao so como as
# chaves de POSICAO_COLUNA) porque a ordem de iteracao de um dict no
# MicroPython e arbitraria, e escolher_cor precisa de desempate estavel.
CORES = (Color.WHITE, Color.GREEN, Color.BLUE, Color.YELLOW)

# Parametros do andar() usado para trocar de coluna vertical (ver
# ir_ate_coluna). Separados um por um (em vez de um dict) para poderem
# ser passados como argumento nomeado direto na chamada da funcao.
V_MAX_ANDAR_BLOCOS    = 500
V_MIN_ANDAR_BLOCOS    = 100
ACEL_ANDAR_BLOCOS     = 200
DESACEL_ANDAR_BLOCOS  = 3000
KP_ANDAR_BLOCOS       = 5.5
KD_ANDAR_BLOCOS       = 4

# --- Profundidades do carrinho DENTRO de uma coluna vertical, em mm a
# partir do batente. So as duas da frente estao aqui:
#
#     indice 0 = perto  -> PROFUNDIDADES_CARRINHO[0]
#     indice 1 = meio   -> PROFUNDIDADES_CARRINHO[1]
#     indice 2 = FUNDO  -> NAO TEM NUMERO. E c.estender(), o fim do curso.
#
# O bloco do fundo e o ULTIMO que o carrinho alcanca, entao "ir ate o
# fundo" e "ir ate onde o carrinho consegue" sao a mesma coisa - e pedir
# uma distancia em mm para ele era justamente o que travava o carrinho:
# um numero maior que o curso real faz o motor_A empurrar um fim de curso
# que ele nunca vai "alcancar". Com c.estender() quem manda no limite e o
# CURSO_MM do carrinho.py, num lugar so.
#
# MEDIR OS DOIS COM REGUA. Tem de ficar em ordem crescente e ABAIXO do
# curso do carrinho. ---
PROFUNDIDADES_CARRINHO = [15, 85]

# O mover_carrinho CLAMPA silenciosamente em c.CURSO_MM: uma profundidade
# maior que o curso faz o carrinho parar antes do bloco e a garra fechar
# no vazio, sem erro nenhum. Avisa no import, nao no meio da prova.
if PROFUNDIDADES_CARRINHO[-1] >= c.CURSO_MM:
    print("ATENCAO: profundidade", PROFUNDIDADES_CARRINHO[-1],
          "mm nao cabe no curso do carrinho (", c.CURSO_MM,
          "mm ) - medir CURSO_MM no carrinho.py")

# Rede de seguranca dos movimentos de carrinho (mesmo papel do
# TIMEOUT_GARRA_MS): se ele travar no meio do caminho, o programa PARA DE
# EMPURRAR, apita e SEGUE, em vez de esperar para sempre. O curso inteiro
# a V_CARRINHO_BLOCOS leva bem menos que isso.
#
# E esta rede que impede o travamento de derrubar a rodada: com
# CURSO_MM maior que o curso real, o carrinho encosta no fim e o
# run_target nunca se da por chegado - sem timeout o robo ficaria parado
# ali ate o fim da prova.
TIMEOUT_CARRINHO_MS = 4000

V_CARRINHO_BLOCOS = 1000

# --- Ordem em que os 6 blocos de UMA cor saem, como (coluna, profundidade):
#
#     coluna       : 0 = coluna vertical mais proxima do inicio, 1 = irma
#     profundidade : 0 perto, 1 meio, 2 fundo (ver PROFUNDIDADES_CARRINHO)
#
# Duas decisoes estao escritas aqui, e o resto do programa so le a tabela:
#
# 1. DO FUNDO PARA A FRENTE dentro de cada coluna. E o que garante que
#    nunca haja um bloco ATRAS do que esta sendo arremessado: o do fundo
#    sai quando nao ha nada atras dele, o do meio quando o fundo ja
#    esvaziou, o de perto por ultimo. Era esse choque que o antigo recuo
#    do carrinho existia para evitar - e e por isso que ele pode sumir.
#    Na ordem contraria (perto primeiro) todo arremesso teria um vizinho
#    atras e o recuo teria de voltar.
#
#    De quebra, as tres profundidades saem em ordem DECRESCENTE: o
#    carrinho estende uma vez ate o fim e depois so RECOLHE, dois passos
#    curtos. Estender e o movimento caro; recolher e barato.
#
# 2. UMA COLUNA DE CADA VEZ, esvaziando a primeira antes de ir para a
#    irma. Assim e uma andada so por cor. E termina na coluna irma, mais
#    adiante no tapete, ja perto da cor seguinte.
ORDEM_NA_COR = (
    (0, 2),   # coluna de perto, bloco do FUNDO - onde o robo ja chegou
    (0, 1),   # coluna de perto, bloco do meio  - so recolhe o carrinho
    (0, 0),   # coluna de perto, bloco de perto - idem
    (1, 2),   # coluna irma,     bloco do FUNDO - ANDA ate a coluna irma
    (1, 1),   # coluna irma,     bloco do meio  - nao anda mais
    (1, 0),   # coluna irma,     bloco de perto - termina aqui, adiantado
)
BLOCOS_POR_COR = len(ORDEM_NA_COR)

# --- Arremesso (motor_D, motor MEDIO) ---
# Nao existe posicao de armazenagem: a garra fecha em cima do bloco onde
# ele estava e o arremessa DALI MESMO, de onde o carrinho parou, para
# dentro do robo.
#
# E o unico movimento por TEMPO: a velocidade e o tempo DEFINEM EM QUAL
# COLUNA DE ARMAZENAGEM DO ROBO o bloco cai (mais forte / mais tempo =
# mais longe), por isso ha um par (velocidade, tempo) por coluna.
#
# CALIBRAR NAS TRES PROFUNDIDADES. O carrinho esta PARADO durante o
# arremesso (o recuo acabou), mas em profundidades diferentes - e a
# distancia do bloco ate a coluna de armazenagem muda com ela. Se um par
# so nao servir para as tres, e sinal de que V_GARRA_SUBIR /
# TEMPO_GARRA_SUBIR_MS precisam virar tabela de (coluna, profundidade).
V_GARRA_SUBIR = {
    1: 1000,
    2: 800,
    3: 870,
}
# O tempo nao e "quanto tempo a garra gira forte": o run_time sobe do zero
# e volta ao zero DENTRO dele. Para a garra chegar mesmo na velocidade
# pedida, o tempo tem de ser no minimo 2 x velocidade / aceleracao do
# motor_D - abaixo disso ela passa o movimento inteiro acelerando e ja
# freando, e gira um arco pequeno por mais alta que seja a velocidade.
TEMPO_GARRA_SUBIR_MS = {
    1: 850,
    2: 720,
    3: 700,
}
# Como o motor para no fim do arremesso. HOLD: a garra tem de ficar
# parada onde chegou, senao o peso dela mesma a faz escorregar - e
# escorregar depois do arremesso desalinharia a proxima descida.
#
# A DESCIDA NAO SE AJUSTA AQUI: ANGULO_GARRA_ABAIXADA, V_GARRA_DESCER,
# TIMEOUT_GARRA_MS e companhia moram no garra.py e valem para todo
# programa (parte1, leitura_blocos...). Redefinir qualquer um deles aqui
# nao daria erro nenhum - so ignoraria o garra.py neste arquivo.
PARADA_SUBIR = Stop.HOLD

# Indices de `leituras` (a lista de 12 cores devolvida por
# leitura_blocos.py) agrupados por coluna do mosaico, em ordem vertical
# (de cima para baixo). Reflete a varredura em zigue-zague de
# leitura_blocos.py: coluna 3 e lida de baixo pra cima na ida e de cima
# pra baixo na volta, por isso os indices nao sao sequenciais.
COLUNAS_MOSAICO = {
    1: [0, 5, 6, 11],
    2: [1, 4, 7, 10],
    3: [2, 3, 8, 9],
}

ORDEM_RETIRADA = [1, 3, 2]


# =============================================================================
# 2. FUNCOES
# =============================================================================

def coluna_e_profundidade(ja_pegos_desta_cor, ordem=ORDEM_NA_COR):
    """
    A partir de quantos blocos dessa cor ja foram retirados, devolve
    (indice_coluna, indice_profundidade):

        indice_coluna       : 0 = coluna mais proxima, 1 = coluna irma
        indice_profundidade : 0 perto, 1 meio, 2 fundo

    E so uma consulta a ORDEM_NA_COR - a estrategia (esvaziar uma coluna
    de cada vez, do fundo para a frente) esta escrita la, nao aqui, para
    mudar de ideia sem mexer em funcao nenhuma.
    """
    return ordem[ja_pegos_desta_cor]


def escolher_cor(cor_pedida, ja_pegos, posicao_atual_mm,
                  blocos_por_cor=BLOCOS_POR_COR,
                  cores=CORES,
                  posicoes_coluna=POSICAO_COLUNA):
    """
    Decide qual cor o robo vai realmente pegar.

    Normalmente e a propria `cor_pedida`. Mas so ha `blocos_por_cor`
    blocos alcancaveis de cada cor, entao se o mosaico pedir essa cor
    mais vezes do que isso, o excedente e substituido por outra cor que
    ainda tenha bloco sobrando - a MAIS PERTO da posicao atual, para nao
    gastar percurso a toa.

    Devolve None se todas as cores esgotaram (nao deve acontecer: sao 12
    blocos pedidos contra 24 alcancaveis).
    """
    if ja_pegos[cor_pedida] < blocos_por_cor:
        return cor_pedida

    melhor = None
    melhor_distancia = 0
    for cor in cores:
        if ja_pegos[cor] >= blocos_por_cor:
            continue
        indice_coluna, _ = coluna_e_profundidade(ja_pegos[cor])
        distancia = abs(posicoes_coluna[cor][indice_coluna] - posicao_atual_mm)
        if melhor is None or distancia < melhor_distancia:
            melhor = cor
            melhor_distancia = distancia
    return melhor


def ir_ate_coluna(cor, indice_coluna, posicao_atual_mm,
                   posicoes_coluna=POSICAO_COLUNA,
                   v_max=V_MAX_ANDAR_BLOCOS, v_min=V_MIN_ANDAR_BLOCOS,
                   acel=ACEL_ANDAR_BLOCOS, desacel=DESACEL_ANDAR_BLOCOS,
                   kp=KP_ANDAR_BLOCOS, kd=KD_ANDAR_BLOCOS):
    """
    Anda reto (frente ou re) da posicao atual ate a coluna vertical pedida
    daquela cor. Devolve a nova posicao (mm).

    Nao faz NADA se a coluna pedida for a mesma de onde o robo ja esta
    (delta 0) - o caso do 2o e do 3o bloco de cada coluna, que saem so
    recolhendo o carrinho.

    NAO MEXE NO CARRINHO, DE PROPOSITO. O robo anda com ele onde o bloco
    anterior o deixou, inclusive todo estendido: o carrinho e impresso em
    3D e leve o bastante para isso, e recolher so para andar seriam 12
    idas e voltas de graca. A garra chega aqui EM CIMA (o arremesso a
    deixou la), entao nada raspa nos blocos por que o robo passa.

    O que continua proibido e mover o carrinho DURANTE a andada (regra 7
    do README) - por isso nao existe movimento de carrinho aqui dentro.
    """
    destino_mm = posicoes_coluna[cor][indice_coluna]
    delta_mm = destino_mm - posicao_atual_mm
    if delta_mm != 0:
        m.andar(delta_mm, v_max=v_max, v_min=v_min, acel=acel,
                desacel=desacel, kp=kp, kd=kd)
    return destino_mm


def testar_posicao_coluna(posicoes_coluna=POSICAO_COLUNA, cores=CORES):
    """
    Anda ate as 8 colunas verticais, uma de cada vez, na ordem fisica do
    tapete (branco1, branco2, verde1, ... amarelo2). E SO PARA CONFERIR
    POSICAO_COLUNA: nao mexe em carrinho nem em garra.

    Reaproveita o proprio ir_ate_coluna - a mesma funcao que o
    pegar_blocos usa na prova -, entao o que este teste mede e exatamente
    o movimento que vai acontecer na hora de verdade, ganho por ganho.

    Para em cada coluna, apita e ESPERA O BOTAO CENTRAL do EV3: da tempo
    de medir com regua (ou so de olhar se o carrinho ficou alinhado com o
    meio da coluna) antes de seguir para a proxima.

    COMO USAR: ponha o robo na largada de sempre - encostado na parede, a
    mesma posicao que o pegar_blocos espera - e rode este arquivo com F5
    com TESTAR_POSICAO_COLUNA = True la embaixo.

    COMO APLICAR O RESULTADO: o erro em mm se SOMA DIRETO ao numero
    correspondente em POSICAO_COLUNA (positivo se o robo ficou AQUEM da
    coluna, negativo se passou). Como todas as posicoes sao ABSOLUTAS a
    partir da parede, corrigir uma nao desloca as outras sete.

    E O PRIMEIRO DA FILA DE CALIBRACAO, antes de profundidade e de
    arremesso: tudo o mais depende de o robo parar no lugar certo.
    """
    posicao_mm = 0
    for cor in cores:
        for indice_coluna in (0, 1):
            posicao_mm = ir_ate_coluna(cor, indice_coluna, posicao_mm,
                                       posicoes_coluna)
            ev3.speaker.beep()
            print(cor, "- coluna", indice_coluna + 1, "- alvo",
                  posicoes_coluna[cor][indice_coluna], "mm")
            print("  meca e aperte o botao CENTRAL para continuar")
            while Button.CENTER not in ev3.buttons.pressed():
                wait(10)
            while Button.CENTER in ev3.buttons.pressed():
                wait(10)      # solta o botao antes de aceitar o proximo aperto

    print("fim - as 8 colunas foram visitadas")
    ev3.speaker.beep()
    ev3.speaker.beep()


def _esperar_botao(botoes=(Button.LEFT, Button.CENTER, Button.RIGHT,
                            Button.UP, Button.DOWN)):
    """
    Espera um aperto NOVO de um dos `botoes` do EV3 e devolve qual foi.

    Primeiro espera SOLTAR o que ja estivesse pressionado na entrada,
    depois espera um aperto e espera ele soltar antes de devolver - assim
    um dedo segurando o botao nao dispara varios ciclos seguidos.

    O botao fisico VOLTAR nao entra aqui: ele para o programa inteiro, e
    e o jeito de sair da calibracao a qualquer momento.
    """
    while ev3.buttons.pressed():          # solta o que estava preso
        wait(10)
    while True:
        pressionados = ev3.buttons.pressed()
        for b in botoes:
            if b in pressionados:
                while ev3.buttons.pressed():
                    wait(10)
                return b
        wait(10)


def calibrar_garra(profundidade=2,
                    velocidade_carrinho=V_CARRINHO_BLOCOS,
                    velocidades_garra=V_GARRA_SUBIR,
                    tempos_garra_ms=TEMPO_GARRA_SUBIR_MS):
    """
    Calibracao INTERATIVA do grabber (motor_D), pelos botoes do EV3. O
    robo nao anda: fica parado e voce dispara o ciclo de pegar + arremessar
    quantas vezes quiser, escolhendo no botao a coluna de armazenagem de
    destino, e vendo onde o bloco cai antes de mexer nos numeros.

    Cobre os tres pedacos do movimento da garra, na MESMA ORDEM da prova:

        DESCER ATE O BATENTE : a primeira coisa que a funcao faz (e o que
                               o botao UP repete) e zerar a garra - com o
                               carrinho ja estendido, para ela chegar no
                               batente de baixo sem bater na estrutura do
                               robo. Se o zero sair alto, mexa aqui: e
                               esta descida que serve de referencia para
                               todas as outras.
        PEGAR O BLOCO        : cada ciclo estende o carrinho ate a
                               `profundidade` e desce a garra em cima do
                               bloco (descer_garra, o mesmo da prova).
        ENTREGAR NA COLUNA   : arremessa para a coluna escolhida no botao.
                               Ajuste V_GARRA_SUBIR / TEMPO_GARRA_SUBIR_MS
                               daquela coluna ate o bloco cair no lugar.

    BOTOES:

        LEFT   -> arremessa na coluna 1
        CENTER -> arremessa na coluna 2
        RIGHT  -> arremessa na coluna 3
        UP     -> zera a garra de novo (re-conferir a descida ao batente)
        DOWN   -> sai da calibracao
        VOLTAR -> para o programa (funciona a qualquer momento)

    COMO USAR: largada de sempre (encostado na parede), rode este arquivo
    com F5 com CALIBRAR_GARRA = True la embaixo. Ponha um bloco ao alcance
    da garra na profundidade escolhida, escolha a coluna no botao, veja
    onde caiu, corrija o numero e repita. Entre um arremesso e outro o
    carrinho fica onde esta (estendido), igual a prova - so reponha o
    bloco.

    `profundidade` : 0 perto, 1 meio, 2 fundo (fim do curso). Como o bloco
    e arremessado de onde o carrinho parou, calibre nas tres - comece pelo
    fundo, a estendida mais longa. Vem de PROFUNDIDADE_TESTE la embaixo.
    """
    print("=== calibracao da garra - profundidade", profundidade, "===")
    print("LEFT=col1  CENTER=col2  RIGHT=col3  UP=re-zerar  DOWN=sair")

    # DESCER ATE O BATENTE, na ordem da prova: carrinho estende primeiro,
    # so entao a garra desce ao batente. Sem o carrinho fora do batente a
    # garra bate na estrutura antes do fim e o zero sai alto (ver garra.py).
    pegar_um_bloco(profundidade, velocidade_carrinho)
    zerar_garra(tempo_ms=3200)
    print("garra zerada, em", motor_D.angle(), "graus")

    while True:
        botao = _esperar_botao()

        if botao == Button.DOWN:
            print("saindo da calibracao")
            ev3.speaker.beep()
            return

        if botao == Button.UP:
            # re-conferir a descida ao batente, mesma ordem da prova
            pegar_um_bloco(profundidade, velocidade_carrinho)
            zerar_garra(tempo_ms=3200)
            print("garra re-zerada, em", motor_D.angle(), "graus")
            continue

        coluna = {Button.LEFT: 1, Button.CENTER: 2, Button.RIGHT: 3}[botao]
        print("--- coluna", coluna, ":", velocidades_garra[coluna],
              "graus/s por", tempos_garra_ms[coluna], "ms ---")

        # PEGAR O BLOCO: carrinho ate a profundidade (garra em cima), depois
        # a garra desce em cima do bloco. Igual aos passos 2 e 3 da prova.
        pegar_um_bloco(profundidade, velocidade_carrinho)
        descer_garra()
        print("  desceu ate", motor_D.angle(), "graus")

        # ENTREGAR NA COLUNA escolhida
        guardar_bloco(coluna, velocidades_garra, tempos_garra_ms)
        print("  subiu ate", motor_D.angle(), "graus")
        print("  reponha o bloco e escolha a proxima coluna")


def pegar_um_bloco(indice_profundidade,
                    velocidade_carrinho=V_CARRINHO_BLOCOS,
                    profundidades=PROFUNDIDADES_CARRINHO,
                    timeout_carrinho=TIMEOUT_CARRINHO_MS):
    """
    Leva o carrinho ate a profundidade pedida, parando em cima do bloco.

    COM A GARRA EM CIMA. Ela nao desce aqui - quem desce e o
    descer_garra, DEPOIS, ja com o carrinho parado no lugar certo. Indo
    ate o fundo o carrinho passa por cima dos dois blocos da frente, que
    ainda estao la; abaixada, a garra ia raspando neles e derrubando.

    Duas maneiras, conforme o bloco:

        perto / meio (indices 0 e 1) : posicao em mm de `profundidades`
        FUNDO (indice 2)             : c.estender() - o fim do curso

    O fundo NAO TEM NUMERO PROPRIO de propria vontade. Ele e o ultimo
    bloco que o carrinho alcanca, entao o alvo dele e "ate onde o
    carrinho vai", e nao uma distancia medida - e era pedir uma distancia
    para ele que TRAVAVA O CARRINHO: um numero maior que o curso real faz
    o motor_A empurrar um fim de curso que nunca chega. Assim so existe um
    limite no programa inteiro, o CURSO_MM do carrinho.py.

    O movimento e disparado SEM ESPERAR e a espera fica no relogio
    (esperar_carrinho), igual ao mover_garra_ate_angulo: se o carrinho
    encostar no fim antes de o run_target se dar por chegado, o programa
    PARA DE EMPURRAR, apita e segue a rodada em vez de travar ali. Um
    apito desses e o sinal de que CURSO_MM esta maior que o curso real.

    A posicao e ABSOLUTA (nao "avance mais tanto"), entao nao depende de
    acertar de onde o carrinho veio: erro de posicao morre aqui, em vez de
    se acumular de bloco para bloco.

    Nao mexe na garra: quem desce e o descer_garra, e quem fecha e
    arremessa e o guardar_bloco.
    """
    if indice_profundidade < len(profundidades):
        c.mover_carrinho(profundidades[indice_profundidade],
                         velocidade=velocidade_carrinho, esperar=False)
    else:
        c.estender(velocidade=velocidade_carrinho, esperar=False)

    if not c.esperar_carrinho(timeout_carrinho):
        c.MOTOR_CARRINHO.hold()     # para de forcar o fim de curso
        ev3.speaker.beep(200, 300)
        print("carrinho travou em", c.posicao_carrinho(),
              "mm - conferir CURSO_MM no carrinho.py")


def guardar_bloco(coluna_armazenagem,
                   velocidades_garra=V_GARRA_SUBIR,
                   tempos_garra_ms=TEMPO_GARRA_SUBIR_MS,
                   parada_garra=PARADA_SUBIR):
    """
    Fecha a garra em cima do bloco e o arremessa para dentro do robo, DE
    ONDE O CARRINHO ESTIVER. Um movimento so, e o carrinho nao se mexe.

    `coluna_armazenagem` (1, 2 ou 3) e a coluna DO ROBO em que o bloco
    tem de cair: e ela que escolhe a velocidade e o tempo da subida nos
    dicionarios `velocidades_garra`/`tempos_garra_ms`. Fora esses dois
    numeros o movimento e identico para as tres colunas.

    O CARRINHO NAO RECUA MAIS ANTES DO ARREMESSO. O recuo existia para o
    bloco recem-agarrado nao bater no que estava ATRAS dele na coluna;
    com ORDEM_NA_COR esvaziando de tras para a frente, nunca ha bloco
    atras, entao ele era movimento a toa - 12 vezes por rodada. Os pares
    (velocidade, tempo) tem de ser recalibrados por causa disso: numeros
    medidos com o carrinho em movimento nao valem mais.

    Ao terminar, a garra esta EM CIMA - o estado em que o robo anda ate a
    proxima coluna. Quem chama nao precisa mexer nela.
    """
    mover_garra(velocidades_garra[coluna_armazenagem],
                tempos_garra_ms[coluna_armazenagem],
                parada_garra)


def pegar_blocos(leituras,
                  velocidade_carrinho=V_CARRINHO_BLOCOS,
                  colunas_mosaico=COLUNAS_MOSAICO,
                  ordem_retirada=ORDEM_RETIRADA,
                  ordem_na_cor=ORDEM_NA_COR,
                  blocos_por_cor=BLOCOS_POR_COR,
                  cores=CORES):
    """
    Retira do tapete os blocos na ordem que o mosaico determinou e joga
    cada um para cima, na propria posicao em que ele foi pego.

    `leituras` : lista de 12 cores devolvida por leitura_blocos.py, na
                 ordem de varredura em zigue-zague (ver colunas_mosaico).

    LARGADA ESPERADA (quem entrega e a parte2):

        robo     : de lado para o tapete, ENCOSTADO NA PAREDE - a posicao
                   0 de POSICAO_COLUNA
        carrinho : ZERADO e FECHADO
        garra    : EM CIMA

    Esta funcao NAO anda nada antes da primeira coluna e NAO mexe na
    garra antes de chegar la. O primeiro movimento da rodada e o
    ir_ate_coluna do primeiro bloco.

    O CICLO, igual para os 12 blocos:

        1. ir_ate_coluna     anda ate a coluna, garra EM CIMA
        2. pegar_um_bloco    ja parado: carrinho ate a profundidade do
                             bloco, ainda com a garra em cima
        3. descer a garra    agora sim, em cima do bloco certo. No
                             PRIMEIRO bloco e o zerar_garra; nos outros
                             11, descer_garra
        4. guardar_bloco     arremessa dali mesmo; a garra volta a ficar
                             EM CIMA

    A ORDEM DOS PASSOS 2 E 3 E LOAD-BEARING: o carrinho estende PRIMEIRO,
    e so entao a garra desce. Ela precisa ir em cima dos dois blocos da
    frente no caminho ate o do fundo - abaixada, ia raspando neles - e,
    no primeiro bloco, precisa do carrinho ja fora do batente para ter
    curso livre ate o batente de baixo (ver garra.py).

    A GARRA E ZERADA UMA VEZ SO, no primeiro bloco (passo 3 da primeira
    volta), e ja com o robo parado na coluna e o carrinho estendido. E a
    unica vez em que ela encosta no batente; dali em diante toda descida
    e uma volta ao mesmo angulo absoluto, um pouco antes do batente. Por
    isso a altura de pegar nao muda do primeiro para o decimo segundo
    bloco e o motor nunca fica empurrando o fim do curso.

    O ROBO ANDA COM O CARRINHO ONDE ELE ESTIVER, inclusive todo
    estendido: nao ha recolhimento entre um bloco e outro nem para trocar
    de coluna. O que continua proibido e move-lo enquanto o robo anda -
    o carrinho so se mexe no passo 3, com o robo parado.

    Dentro de cada cor a ordem e a de `ordem_na_cor`: esvazia a primeira
    coluna vertical inteira - fundo, meio, perto -, anda ate a coluna
    irma e esvazia ela do mesmo jeito. Uma andada por cor, nunca um bloco
    atras do que esta sendo arremessado, e o carrinho estendendo uma vez
    por coluna e so recolhendo depois.

    Percorre as colunas do MOSAICO na ordem de `ordem_retirada` (1, 3, 2
    por padrao: primeira, terceira, meio) - diferente da ordem em que
    foram lidas, e diferente tambem da ordem em que serao ENTREGUES (ver
    entregar_blocos.py). Dentro de cada coluna, os 4 blocos saem na mesma
    ordem vertical em que foram lidos, e todos com o mesmo arremesso, ja
    que caem todos naquela mesma coluna do robo.

    Se o mosaico pedir uma cor mais de `blocos_por_cor` vezes, o
    excedente e trocado por outra cor ainda disponivel (escolher_cor).
    """
    ja_pegos = {}
    for cor in cores:
        ja_pegos[cor] = 0

    posicao_mm = 0          # encostado na parede: o zero de POSICAO_COLUNA
    garra_zerada = False

    for coluna_armazenagem in ordem_retirada:
        for indice in colunas_mosaico[coluna_armazenagem]:
            cor = escolher_cor(leituras[indice], ja_pegos, posicao_mm,
                               blocos_por_cor, cores)
            if cor is None:
                return      # acabaram os blocos alcancaveis de todas as cores
            if cor != leituras[indice]:
                print("cor", leituras[indice], "esgotada, trocando por", cor)

            indice_coluna, indice_profundidade = coluna_e_profundidade(
                ja_pegos[cor], ordem_na_cor)

            # 1. anda ate a coluna, garra em cima e carrinho onde estiver
            posicao_mm = ir_ate_coluna(cor, indice_coluna, posicao_mm)

            # 2. ja parado na coluna: o carrinho estende ate o bloco
            #    (fundo = fim do curso) COM A GARRA EM CIMA
            pegar_um_bloco(indice_profundidade, velocidade_carrinho)

            # 3. so agora, parada em cima do bloco certo e com o carrinho
            #    ja fora do batente, a garra desce. A primeira descida da
            #    rodada e a zeragem, e e a unica que vai ao batente.
            if garra_zerada:
                descer_garra()
            else:
                # tempo_ms acompanha o V_GARRA_DESCER do garra.py: curto
                # demais e o zero fica marcado no meio do curso.
                zerar_garra(tempo_ms=3200)
                garra_zerada = True

            # 4. arremessa dali mesmo; a garra termina em cima
            guardar_bloco(coluna_armazenagem)
            ja_pegos[cor] += 1


# =============================================================================
# 3. TESTE
# =============================================================================

if __name__ == "__main__":

    # --- MODO 1: conferir POSICAO_COLUNA (ver testar_posicao_coluna) ---
    # True anda ate as 8 colunas verticais, parando em cada uma para voce
    # medir com regua. IGNORA COLUNA_TESTE e as leituras abaixo. E o
    # PRIMEIRO da fila de calibracao: profundidade e arremesso so fazem
    # sentido depois que o robo para no lugar certo.
    TESTAR_POSICAO_COLUNA = False

    # --- MODO 1b: calibrar a garra pelos BOTOES (ver calibrar_garra) ---
    # True fica parado e voce dispara pegar+arremessar quantas vezes
    # quiser, escolhendo a coluna no botao (LEFT/CENTER/RIGHT = 1/2/3),
    # re-zerando com UP e saindo com DOWN. Usa PROFUNDIDADE_TESTE. IGNORA
    # COLUNA_TESTE e as leituras. E o jeito rapido de acertar a descida ao
    # batente e os arremessos sem editar constante nem reiniciar o
    # programa a cada tentativa.
    CALIBRAR_GARRA = True

    # --- MODO 2: calibrar o arremesso, uma coluna de cada vez ---
    # Ponha aqui o numero da coluna de ARMAZENAGEM (1, 2 ou 3), ponha um
    # bloco na profundidade PROFUNDIDADE_TESTE e rode - o robo nao anda,
    # so estende o carrinho, desce a garra, arremessa e repete. Veja em
    # que coluna o bloco caiu e mexa em V_GARRA_SUBIR /
    # TEMPO_GARRA_SUBIR_MS daquele numero.
    #
    # Deixe None para rodar a retirada completa (MODO 3).
    COLUNA_TESTE = None

    # Qual profundidade usar no MODO 2 (0 perto, 1 meio, 2 FUNDO = fim do
    # curso do carrinho). REPETIR A CALIBRACAO NAS TRES: agora o bloco e
    # arremessado de onde o carrinho parou, e a distancia ate a coluna de
    # armazenagem muda com a profundidade.
    #
    # Comece pelo 2: e a estendida mais longa, e a unica que passa por
    # cima dos dois blocos da frente.
    PROFUNDIDADE_TESTE = 2

    # Lista de exemplo so para testar a logica de ordem sem depender de
    # uma leitura real do mosaico (rodar leitura_blocos.py para obter a
    # lista de verdade).
    #
    # Este exemplo tem AMARELO 5 vezes (indices 0, 3, 7, 9, 11). Com 6
    # blocos alcancaveis por cor isso NAO aciona o escolher_cor - as 5
    # saem como amarelo mesmo. Para testar a substituicao, ponha uma cor
    # 7 vezes ou mais.
    leituras_teste = [
        Color.YELLOW, Color.GREEN, Color.BLUE,
        Color.YELLOW, Color.GREEN, Color.WHITE,
        Color.BLUE, Color.YELLOW, Color.GREEN,
        Color.YELLOW, Color.BLUE, Color.YELLOW,
    ]

    if TESTAR_POSICAO_COLUNA:
        # Mesma largada da prova, mas este teste nem chega a mexer no
        # carrinho depois de zerar - so anda.
        c.zerar_carrinho(velocidade=800, forca=90)
        testar_posicao_coluna()

    elif CALIBRAR_GARRA:
        # Robo parado: so o carrinho e a garra se mexem. O carrinho tem de
        # comecar zerado, igual a prova - o resto e pelos botoes.
        c.zerar_carrinho(velocidade=800, forca=90)
        calibrar_garra(PROFUNDIDADE_TESTE)

    elif COLUNA_TESTE is None:
        # --- MODO 3: retirada completa ---
        # Largada da prova: carrinho ZERADO e FECHADO, garra EM CIMA. O
        # pegar_blocos nao precisa de mais nada - ele sai andando direto
        # para a primeira coluna e zera a garra la.
        c.zerar_carrinho(velocidade=800, forca=90)
        pegar_blocos(leituras_teste)

    else:
        # Largada igual a da prova: carrinho fechado no batente.
        c.zerar_carrinho(velocidade=800, forca=90)

        # (velocidade, aceleracao, atuacao) do motor_D. A ACELERACAO e o
        # que decide se o tempo desta coluna da para a garra chegar na
        # velocidade pedida: o minimo e 2 x velocidade / aceleracao.
        limites = motor_D.control.limits()
        print("limites do motor_D:", limites)
        print("tempo minimo para", V_GARRA_SUBIR[COLUNA_TESTE], "graus/s:",
              2000 * V_GARRA_SUBIR[COLUNA_TESTE] // limites[1], "ms")
        wait(500)

        # Repete o ciclo estender / descer / arremessar, na MESMA ORDEM da
        # prova (menos o andar): o carrinho estende com a garra em cima e
        # ela so desce depois, ja em cima do bloco. Ponha outro bloco no
        # lugar entre as voltas. Confira cinco coisas:
        #
        #   1. A ZERAGEM DA PRIMEIRA VOLTA. Ela acontece com o carrinho ja
        #      estendido, igual a da prova: a garra tem de chegar no
        #      batente de baixo sem bater na estrutura do robo. Se bater,
        #      o zero sai alto e toda descida da rodada erra junto - e o
        #      pior estrago possivel aqui.
        #   2. "desceu ate" tem de dar sempre ANGULO_GARRA_ABAIXADA, igual
        #      nas 4 voltas. Se for baixando, a garra esta escorregando no
        #      mecanismo e nao e problema de programa.
        #   3. nenhum "garra nao chegou" (o apito longo). Se aparecer, ou
        #      o alvo esta batendo no batente (aumente
        #      ANGULO_GARRA_ABAIXADA) ou a descida ficou lenta demais para
        #      o prazo (aumente TIMEOUT_GARRA_MS) - os dois no garra.py.
        #   4. nenhum "carrinho travou". Se aparecer com PROFUNDIDADE_TESTE
        #      = 2, o CURSO_MM do carrinho.py esta maior que o curso real:
        #      meca com regua e corrija LA.
        #   5. OS BLOCOS DA FRENTE TEM DE FICAR PARADOS na ida ate o
        #      fundo. Com a garra em cima isso e de graca; se algum ainda
        #      se mexer, ela nao esta subindo o bastante no arremesso.
        for volta in range(4):
            print("volta", volta + 1, "- arremesso da coluna", COLUNA_TESTE,
                  ":", V_GARRA_SUBIR[COLUNA_TESTE], "graus/s por",
                  TEMPO_GARRA_SUBIR_MS[COLUNA_TESTE], "ms")

            pegar_um_bloco(PROFUNDIDADE_TESTE)      # estende, garra em cima
            print("  carrinho em", c.posicao_carrinho(), "mm")

            if volta == 0:
                zerar_garra(tempo_ms=3200)          # a zeragem da prova
            else:
                descer_garra()
            print("  desceu ate", motor_D.angle(), "graus")

            guardar_bloco(COLUNA_TESTE)
            print("  subiu ate", motor_D.angle(), "graus")

            # SO NO TESTE: devolve o carrinho para a profundidade de
            # perto, que e de onde ele sai para o bloco do fundo na prova
            # (o ultimo bloco de uma coluna deixa ele ali). Na prova nao
            # existe este movimento.
            c.mover_carrinho(PROFUNDIDADES_CARRINHO[0],
                             velocidade=V_CARRINHO_BLOCOS)
            wait(1000)

    ev3.speaker.beep()
