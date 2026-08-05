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

Cada coluna vertical tem 3 blocos empilhados de lado, mas o robo so
alcanca OS DOIS PRIMEIROS (perto e meio) - o terceiro, mais profundo,
fica fora do alcance do carrinho por limitacao fisica do robo. Entao
sao 2 blocos por coluna x 2 colunas = 4 BLOCOS ALCANCAVEIS POR COR.

Os 2 blocos de uma coluna saem so com o carrinho, SEM precisar andar de
novo; so quando os 2 acabam e que o robo anda ate a coluna irma daquela
cor (ex.: verde1 -> verde2) para pegar os outros 2. Isso e proposital:
estender o carrinho e mais rapido e preciso do que andar.

APOSTA DA ESTRATEGIA: o mosaico pede 12 blocos e existem 16 alcancaveis
(4 por cor), mas se uma cor sozinha for pedida MAIS DE 4 VEZES nao ha
como atender. Nesse caso o robo substitui o excedente por uma cor que
ainda tenha bloco sobrando (ver escolher_cor) - de preferencia a mais
perto, para nao gastar percurso.

Quem muda a cada partida e o mosaico lido em leitura_blocos.py, que diz
EM QUE ORDEM os blocos devem ser retirados.

leitura_blocos.py varre o mosaico em zigue-zague (3 colunas de carrinho
x 4 avancos do robo) e devolve uma lista `leituras` com 12 cores nessa
ordem de varredura. COLUNAS_MOSAICO abaixo traduz essa lista de volta
para "4 cores da coluna 1, de cima pra baixo", "4 da coluna 2", etc.

Ordem de retirada exigida: coluna 1, depois coluna 3, depois coluna 2
(do meio) - NAO e a mesma ordem em que o mosaico foi lido.

As distancias/posicoes abaixo sao PLACEHOLDERS - MEDIR COM REGUA /
ajustar no robo real.
"""
from setup import sensor_esq, sensor_dir, motor_A, motor_B, motor_C, motor_D, ev3, wait
from pybricks.parameters import Color
import setup as s
import movimento as m
import linha as lin
import carrinho as c


# =============================================================================
# 1. CONFIGURACAO (medir com regua / calibrar no robo)
# =============================================================================

# --- Distancia (mm) que o robo anda, a partir de onde comeca, ate ficar
# alinhado de lado com cada uma das 8 colunas verticais: [coluna mais
# proxima do inicio, coluna mais distante] de cada cor. ---
POSICAO_COLUNA = {
    Color.WHITE:  [130, 210],
    Color.GREEN:  [290, 370],
    Color.BLUE:   [450, 530],
    Color.YELLOW: [610, 690],
}

# Mesma ordem fisica do tapete. Existe como tupla (e nao so como as
# chaves de POSICAO_COLUNA) porque a ordem de iteracao de um dict no
# MicroPython e arbitraria, e escolher_cor precisa de desempate estavel.
CORES = (Color.WHITE, Color.GREEN, Color.BLUE, Color.YELLOW)

# Parametros do andar() usado para trocar de coluna vertical (ver
# ir_ate_coluna). Separados um por um (em vez de um dict) para poderem
# ser passados como argumento nomeado direto na chamada da funcao.
V_MAX_ANDAR_BLOCOS    = 300
V_MIN_ANDAR_BLOCOS    = 200
ACEL_ANDAR_BLOCOS     = 2000
DESACEL_ANDAR_BLOCOS  = 3000
KP_ANDAR_BLOCOS       = 1.8
KD_ANDAR_BLOCOS       = 3.5

# --- Profundidades do carrinho (mm) dentro de UMA coluna vertical.
# A coluna tem 3 blocos, mas so os 2 primeiros (perto e meio) estao ao
# alcance - o 3o, mais profundo, o robo nao consegue pegar. Por isso a
# lista tem 2 posicoes, e nao 3.
# 2 profundidades x 2 colunas = BLOCOS_POR_COR blocos por cor. ---
PROFUNDIDADES_CARRINHO = [30, 100]
BLOCOS_POR_COLUNA = 2
BLOCOS_POR_COR = BLOCOS_POR_COLUNA * 2   # 2 colunas verticais por cor

# --- Partida: o robo comeca ENCOSTADO NA PAREDE. Anda este tanto para
# frente antes de abaixar a garra pela primeira vez, para ela nao abrir
# contra a parede. Depois disso `posicao_mm` ja conta a partir daqui. ---
DISTANCIA_INICIAL_MM = 50

# --- Garra (motor_D, motor MEDIO) ---
# Nao existe posicao de armazenagem: o bloco e jogado para cima na MESMA
# posicao do carrinho em que foi pego, entao entre pegar e soltar o
# carrinho nao se mexe.
#
# Nenhum dos dois movimentos e por GRAUS: o curso termina num batente
# mecanico, entao nao precisa acertar um numero de graus. O SINAL da
# velocidade e que define o sentido.
#
#   DESCER : abaixa e abre a garra ate o batente, pronta para fechar.
#            E SEMPRE IGUAL: termina no batente, entao nao depende de
#            para onde o bloco vai depois. Acontece sempre na posicao de
#            carrinho de onde o bloco anterior acabou de sair (que esta
#            vazia), ou com o carrinho recolhido no comeco do programa.
#   SUBIR  : fecha em cima do bloco e o arremessa para cima. Aqui a
#            velocidade e o tempo DEFINEM EM QUAL COLUNA DE ARMAZENAGEM
#            DO ROBO o bloco cai (mais forte/mais tempo = mais longe),
#            por isso subir tem um par (velocidade, tempo) por coluna e
#            descer nao.
V_GARRA_DESCER        = -700

# EM TESTE: descer parando por TRAVAMENTO (run_until_stalled) em vez de
# por tempo. O motor roda ate travar no batente e para exatamente ali,
# nao importa quanto tempo leve - mais confiavel que cronometrar, SE
# funcionar: o motor_D e MEDIO, e run_until_stalled e conhecido por so
# ser confiavel nos motores GRANDES (esta na lista de armadilhas do
# README). Se a garra nao parar no batente, ou travar sozinha no meio do
# curso, volte para False: ai vale o run_time de TEMPO_GARRA_DESCER_MS.
DESCER_POR_TRAVAMENTO = False
FORCA_GARRA_DESCER    = 40    # duty_limit em %: baixo o bastante para nao
                              # forcar o batente, alto o bastante para o
                              # motor nao se dar por travado no meio do curso
TEMPO_GARRA_DESCER_MS = 820   # so usado com DESCER_POR_TRAVAMENTO = False;
                              # longo o bastante para chegar no batente

# Arremesso, por COLUNA DE ARMAZENAGEM do robo (as mesmas colunas 1/2/3
# de ORDEM_RETIRADA / COLUNAS_MOSAICO). Sao os UNICOS numeros que mudam
# de uma coluna para outra - todo o resto do ciclo e identico.
#
# Comecam todos com o mesmo valor ja testado; diferenciar medindo no
# robo, uma coluna de cada vez (ver o teste no fim do arquivo).
V_GARRA_SUBIR = {
    1: 690,
    2: 835,
    3: 1000,
}
TEMPO_GARRA_SUBIR_MS = {
    1: 1000,
    2: 700,
    3: 500,
}

# Como o motor para no fim de cada giro: COAST
PARADA_DESCER = s.Stop.COAST
PARADA_SUBIR  = s.Stop.COAST

V_CARRINHO_BLOCOS = 400

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
def mover_garra(velocidade, tempo_ms, parada=s.Stop.HOLD):
    """
    Gira o motor_D por TEMPO (nao por graus): `velocidade` em graus/s,
    com o sinal definindo o sentido, durante `tempo_ms` milissegundos.
    Bloqueia ate terminar.

    Por tempo, e nao por graus, porque o curso termina num batente
    mecanico: basta girar tempo suficiente que a garra encosta nele.

    `tempo_ms` nao tem valor padrao de proposito: descer e subir usam
    tempos diferentes, e a subida ainda muda conforme a coluna de
    armazenagem - quem chama sempre sabe qual dos dois quer.

    Junto com mover_garra_ate_travar, sao as unicas funcoes que mexem na
    garra - descer_garra e guardar_bloco so chamam elas.
    """
    motor_D.run_time(velocidade, tempo_ms, then=parada)


def mover_garra_ate_travar(velocidade, forca=FORCA_GARRA_DESCER,
                            parada=s.Stop.COAST):
    """
    Gira o motor_D ate ele TRAVAR - isto e, ate a garra encostar no
    batente e nao conseguir mais girar - e para ali. Bloqueia ate travar.

    `forca` e o duty_limit em %, igual ao do zerar_carrinho: e o quanto o
    motor pode empurrar antes de se dar por travado. Muito alto forca o
    batente; muito baixo faz ele parar sozinho no meio do curso.

    Devolve o angulo em que travou. Serve para conferir no teste se o
    curso foi o esperado ou se o motor desistiu no meio do caminho.
    """
    return motor_D.run_until_stalled(velocidade, then=parada, duty_limit=forca)


def coluna_e_profundidade(ja_pegos_desta_cor, blocos_por_coluna=BLOCOS_POR_COLUNA):
    """
    A partir de quantos blocos dessa cor ja foram retirados, devolve
    (indice_coluna, indice_profundidade):

        indice_coluna       : 0 = coluna mais proxima, 1 = coluna irma
        indice_profundidade : 0 perto, 1 meio (o 3o, mais fundo, esta
                              fora do alcance e nao entra na conta)

    Os `blocos_por_coluna` primeiros (0,1) ficam na coluna 0, so mudando
    de profundidade; dai em diante (2,3) vem da coluna 1.
    """
    return ja_pegos_desta_cor // blocos_por_coluna, ja_pegos_desta_cor % blocos_por_coluna


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
    blocos pedidos contra 16 alcancaveis).
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
    (delta 0) - e assim que os 2 blocos alcancaveis de uma coluna saem so
    com o carrinho, direto de uma profundidade para a outra.

    NAO mexe no carrinho: o robo anda com ele onde estiver, estendido ou
    nao. Isso vale porque a garra sempre desce ate o batente depois do
    arremesso anterior, e abaixada assim ela passa livre pelos blocos do
    tapete durante o percurso.

    Nao recolha o carrinho aqui: recolher e estender de novo so gastaria
    tempo, e quem precisar de outra profundidade ja a pede por posicao
    ABSOLUTA em pegar_um_bloco - inclusive VOLTANDO, que e o caso de
    acabar de pegar o bloco do meio de uma coluna (carrinho fundo) e ir
    pegar o bloco de perto de outra coluna (carrinho volta sozinho).
    """
    destino_mm = posicoes_coluna[cor][indice_coluna]
    delta_mm = destino_mm - posicao_atual_mm
    if delta_mm != 0:
        m.andar(delta_mm, v_max=v_max, v_min=v_min, acel=acel, desacel=desacel, kp=kp, kd=kd)
    return destino_mm


def descer_garra(velocidade_garra=V_GARRA_DESCER,
                  por_travamento=DESCER_POR_TRAVAMENTO,
                  forca_garra=FORCA_GARRA_DESCER,
                  tempo_garra_ms=TEMPO_GARRA_DESCER_MS,
                  parada_garra=PARADA_DESCER):
    """
    Abaixa a garra ate o batente, deixando-a ABERTA e pronta para fechar
    em cima do proximo bloco.

    E SEMPRE IGUAL, para qualquer bloco e qualquer coluna de armazenagem:
    termina no batente mecanico, entao nao ha o que variar aqui. Quem
    muda por coluna e so a subida (guardar_bloco).

    `por_travamento` escolhe COMO ela sabe que chegou no batente:

        True  : run_until_stalled - para no instante em que trava, sem
                depender de tempo. E o que esta em teste (motor MEDIO).
        False : run_time por `tempo_garra_ms`, o jeito antigo.

    Devolve o angulo de travamento quando `por_travamento`, senao None.

    Nao exige carrinho recolhido: acontece na posicao de onde o bloco
    anterior acabou de sair, que esta vazia. O que nao pode e abrir a
    garra em cima de um bloco que ainda esta la.
    """
    if por_travamento:
        return mover_garra_ate_travar(velocidade_garra, forca_garra, parada_garra)
    mover_garra(velocidade_garra, tempo_garra_ms, parada_garra)
    return None


def pegar_um_bloco(indice_profundidade,
                    velocidade_carrinho=V_CARRINHO_BLOCOS,
                    profundidades=PROFUNDIDADES_CARRINHO):
    """
    Leva o carrinho ate a profundidade pedida (perto/meio), encaixando a
    garra - que ja veio aberta do descer_garra - em volta do bloco.

    A posicao e ABSOLUTA, entao serve para qualquer posicao de onde o
    carrinho venha - avancando ou RECUANDO, tanto faz: a garra encaixa
    igual vindo da frente ou de tras do bloco. Recuar e o caso de acabar
    de pegar o bloco do meio de uma coluna e a coluna nova pedir o de
    perto; e aqui o unico lugar onde o carrinho volta, ja que
    ir_ate_coluna nao o recolhe.

    Nao mexe na garra: quem fecha e sobe e o guardar_bloco.
    """
    c.mover_carrinho(profundidades[indice_profundidade], velocidade=velocidade_carrinho)


def guardar_bloco(coluna_armazenagem,
                   velocidades_garra=V_GARRA_SUBIR,
                   tempos_garra_ms=TEMPO_GARRA_SUBIR_MS,
                   parada_garra=PARADA_SUBIR):
    """
    Fecha a garra no bloco e sobe, arremessando-o para cima na MESMA
    posicao de carrinho em que ele foi pego.

    `coluna_armazenagem` (1, 2 ou 3) e a coluna DO ROBO em que o bloco
    tem de cair: e ela que escolhe a velocidade e o tempo da subida nos
    dicionarios `velocidades_garra`/`tempos_garra_ms`. Fora esses dois
    numeros o movimento e identico para as tres colunas.

    NAO mexe no carrinho - nem para pegar o bloco, nem depois de solta-lo:
    o carrinho fica onde esta ate pegar_um_bloco pedir a profundidade do
    proximo bloco, que pode ser mais fundo (outro bloco da mesma coluna) ou
    mais perto (primeiro bloco de uma coluna nova). A garra e presa na
    estrutura e acompanha o carrinho.
    """
    mover_garra(velocidades_garra[coluna_armazenagem],
                tempos_garra_ms[coluna_armazenagem],
                parada_garra)


def pegar_blocos(leituras,
                  velocidade_carrinho=V_CARRINHO_BLOCOS,
                  colunas_mosaico=COLUNAS_MOSAICO,
                  ordem_retirada=ORDEM_RETIRADA,
                  blocos_por_coluna=BLOCOS_POR_COLUNA,
                  blocos_por_cor=BLOCOS_POR_COR,
                  cores=CORES,
                  distancia_inicial_mm=DISTANCIA_INICIAL_MM):
    """
    Retira do tapete os blocos na ordem que o mosaico determinou e joga
    cada um para cima, na propria posicao em que ele foi pego.

    `leituras` : lista de 12 cores devolvida por leitura_blocos.py, na
                 ordem de varredura em zigue-zague (ver colunas_mosaico).

    Pressupoe o robo parado de lado com o tapete e ENCOSTADO NA PAREDE
    (a posicao 0 de POSICAO_COLUNA), com o carrinho ja zerado e levado
    para a primeira profundidade (PROFUNDIDADES_CARRINHO[0]) - dali ele
    nao volta mais ao batente. A primeira coisa que faz e sair da parede e
    abaixar a garra.

    A garra e sempre abaixada/aberta ANTES de o robo ir ate a coluna, e
    nunca em cima de um bloco que ainda esta la. Por bloco, entao:

        descer_garra -> ir_ate_coluna -> pegar_um_bloco (leva o carrinho
        ate a profundidade) -> guardar_bloco (fecha, sobe, arremessa)

    O carrinho NUNCA volta ao batente durante a retirada - nem para andar
    de uma coluna vertical para outra. Ele vai sempre direto de uma
    profundidade para a proxima (pegar_um_bloco, posicao absoluta), seja
    para frente (bloco do meio da mesma coluna) ou para tras (bloco de
    perto de uma coluna nova). A garra desce na posicao de onde o bloco
    anterior acabou de sair, que esta vazia, e e abaixada assim que ela
    passa pelos blocos do tapete enquanto o robo anda.

    Desse ciclo, o UNICO passo que muda de uma coluna de armazenagem
    para outra e a subida do guardar_bloco (velocidade e tempo do
    arremesso, em V_GARRA_SUBIR / TEMPO_GARRA_SUBIR_MS); descer, andar e
    mover o carrinho sao iguais para os 12 blocos.

    Percorre as colunas do MOSAICO na ordem de `ordem_retirada` (1, 3, 2
    por padrao: primeira, terceira, meio) - diferente da ordem em que
    foram lidas. Dentro de cada coluna, os 4 blocos saem na mesma ordem
    vertical em que foram lidos, e todos com o mesmo arremesso, ja que
    caem todos naquela mesma coluna do robo.

    Se o mosaico pedir uma cor mais de `blocos_por_cor` vezes, o
    excedente e trocado por outra cor ainda disponivel (escolher_cor).
    """
    ja_pegos = {}
    for cor in cores:
        ja_pegos[cor] = 0

    # Sai da parede antes de mexer na garra, senao ela abriria contra a
    # parede. A partir daqui posicao_mm acompanha POSICAO_COLUNA.

    m.andar(distancia_inicial_mm,
            v_max=V_MAX_ANDAR_BLOCOS, v_min=V_MIN_ANDAR_BLOCOS,
            acel=ACEL_ANDAR_BLOCOS, desacel=DESACEL_ANDAR_BLOCOS,
            kp=KP_ANDAR_BLOCOS, kd=KD_ANDAR_BLOCOS)
    posicao_mm = distancia_inicial_mm

    descer_garra()      # abre a garra antes de ir ao primeiro bloco

    for coluna_armazenagem in ordem_retirada:
        for indice in colunas_mosaico[coluna_armazenagem]:
            cor = escolher_cor(leituras[indice], ja_pegos, posicao_mm,
                               blocos_por_cor, cores)
            if cor is None:
                return          # acabaram os blocos alcancaveis de todas as cores
            if cor != leituras[indice]:
                print("cor", leituras[indice], "esgotada, trocando por", cor)
            indice_coluna, indice_profundidade = coluna_e_profundidade(
                ja_pegos[cor], blocos_por_coluna)
            # so anda se for mesmo trocar de coluna vertical
            posicao_mm = ir_ate_coluna(cor, indice_coluna, posicao_mm)
            pegar_um_bloco(indice_profundidade, velocidade_carrinho)
            ja_pegos[cor] += 1
            # a subida muda com a coluna de armazenagem; a descida nao
            guardar_bloco(coluna_armazenagem)
            descer_garra()   # ja deixa aberta para o proximo bloco


# =============================================================================
# 3. TESTE
# =============================================================================

if __name__ == "__main__":

    # Calibracao do arremesso, uma coluna de cada vez: ponha aqui o
    # numero da coluna de armazenagem (1, 2 ou 3), deixe um bloco ao
    # alcance da garra ja abaixada/aberta e rode - so fecha e arremessa,
    # sem andar. Veja em que coluna caiu e mexa em V_GARRA_SUBIR /
    # TEMPO_GARRA_SUBIR_MS daquele numero.
    #
    # Deixe None para rodar a retirada completa (o teste normal).
    COLUNA_TESTE = None

    # Lista de exemplo so para testar a logica de ordem sem depender de
    # uma leitura real do mosaico (rodar leitura_blocos.py para obter a
    # lista de verdade).
    #
    # Este exemplo tem AMARELO 5 vezes (indices 0, 3, 7, 9, 11), um a
    # mais que os 4 alcancaveis: o 5o pedido cai no escolher_cor e sai
    # como outra cor. Trocar por uma lista com no maximo 4 de cada para
    # testar o caminho normal, sem substituicao.
    leituras_teste = [
        Color.YELLOW, Color.GREEN, Color.BLUE,
        Color.YELLOW, Color.GREEN, Color.WHITE,
        Color.BLUE, Color.YELLOW, Color.GREEN,
        Color.YELLOW, Color.BLUE, Color.YELLOW,
    ]

    if COLUNA_TESTE is None:
        c.zerar_carrinho(velocidade=800, forca=90)
        # unica ida ao batente: dali em diante o carrinho so troca de
        # profundidade, nunca recolhe (ver ir_ate_coluna)
        c.mover_carrinho(PROFUNDIDADES_CARRINHO[0], velocidade=500)
        pegar_blocos(leituras_teste)
    else:
        print("arremesso da coluna", COLUNA_TESTE,
              ":", V_GARRA_SUBIR[COLUNA_TESTE], "graus/s por",
              TEMPO_GARRA_SUBIR_MS[COLUNA_TESTE], "ms")
        mover_garra(V_GARRA_SUBIR[COLUNA_TESTE],
                    TEMPO_GARRA_SUBIR_MS[COLUNA_TESTE],
                    PARADA_SUBIR)
        wait(1000)

        # Volta a garra para o batente, aberta. Com
        # DESCER_POR_TRAVAMENTO = True, o angulo impresso e onde ela
        # travou: repita o teste algumas vezes e veja se o valor se
        # repete. Variando muito (ou parando longe do batente), o motor
        # medio nao esta dando conta do run_until_stalled - mexa em
        # FORCA_GARRA_DESCER ou volte para o modo por tempo.
        angulo = descer_garra()
        if angulo is not None:
            print("travou em", angulo, "graus")
    ev3.speaker.beep()
