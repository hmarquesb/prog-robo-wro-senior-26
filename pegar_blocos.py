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
alcanca OS TRES (perto, meio e fundo - as tres PROFUNDIDADES abaixo).
Entao sao 3 blocos por coluna x 2 colunas = 6 BLOCOS ALCANCAVEIS POR COR.

O CICLO DE UM BLOCO - o mesmo do primeiro ao decimo segundo:

    1. anda ate a coluna         (ir_ate_coluna)
    2. estende o carrinho ate a profundidade do bloco
       (motor_A.run_target, escrito no proprio laco)
    3. guarda                    (guardar_bloco: servo -> arremesso ->
                                  garra desce de volta)

QUEM ESCOLHE A COLUNA DE ARMAZENAGEM E O SERVO. As 3 colunas sao FIXAS no
topo do robo, e um servo montado nelas poe a boca certa debaixo do
arremesso (servos.py). A garra arremessa os 12 blocos com a MESMA forca,
e o carrinho para na MESMA profundidade nominal - nao ha ajuste por
coluna em lugar nenhum.

O CARRINHO E COMANDADO DIRETO, sem modulo no meio: as tres profundidades
sao graus do motor_A, listadas logo abaixo, e o laco chama
motor_A.run_target() com elas. Para mudar o alcance de uma profundidade,
mude o numero na lista - o efeito esta a uma linha de distancia.

A GARRA DESCE LOGO DEPOIS DO ARREMESSO, dentro do proprio guardar_bloco,
e nao no comeco do bloco seguinte. Ou seja: fora o instante do arremesso
a garra fica SEMPRE EMBAIXO, pronta para fechar. Quem chama nao precisa
descer a garra em lugar nenhum.

A UNICA EXCECAO E O PRIMEIRO BLOCO: ali a garra ainda chega EM CIMA (a
parte3 a entrega assim) e a descida e o zerar_garra - a unica ida ao
batente da rodada. Ela acontece depois de o carrinho ja ter estendido,
que e o que o garra.py exige para a garra chegar no batente de baixo sem
bater na estrutura do robo.

PARA CONFERIR NO ROBO: com a garra embaixo desde o primeiro arremesso, os
dois blocos da frente de uma coluna passam por BAIXO dela toda vez que o
carrinho estende ate o fundo de uma coluna nova (7 das 8 colunas - a
primeira ainda pega a garra levantada). Dentro de uma mesma coluna nao ha
risco: ali o carrinho so RECOLHE, por cima de posicoes ja esvaziadas.

LARGADA (o que a parte3 tem de entregar):

    robo     : de lado para o tapete e ENCOSTADO NA PAREDE. E a posicao 0
               de onde todo o POSICAO_COLUNA foi medido.
    carrinho : RECOLHIDO, encostado no batente de casa.
    garra    : EM CIMA. Ela so desce na primeira coluna.

O CARRINHO SO SE MEXE COM O ROBO PARADO (README, regra 8). O robo PODE
andar com o carrinho estendido - desde que ele virou peca impressa em 3D
ficou leve o bastante -, o proibido e move-lo DURANTE a andada. Por isso
nao ha recolhimento entre um bloco e outro nem para trocar de coluna.

APOSTA DA ESTRATEGIA: o mosaico pede 12 blocos e existem 24 alcancaveis
(6 por cor), entao so faltaria bloco se uma cor sozinha fosse pedida
MAIS DE 6 VEZES - metade do mosaico na mesma cor. Se acontecer, o
excedente vira uma cor que ainda tenha bloco sobrando, de preferencia a
mais perto, para nao gastar percurso (ver escolher_cor).
"""

from pybricks.parameters import Button, Stop
from pybricks.tools import wait

import constantes as cte
import movimento as m
import servos as sv
import garra as g
from setup import ev3, motor_A


# =============================================================================
# OS NUMEROS DESTA ETAPA
# =============================================================================

# --- AS 3 PROFUNDIDADES DO CARRINHO, em GRAUS do motor_A ---
# Contadas do zero que a zeragem do inicio de pegar_blocos() marca no
# batente de casa. Sao as posicoes dos 3 blocos empilhados dentro de uma
# coluna do tapete:
#
#     indice 0 = perto  : o bloco da frente
#     indice 1 = meio   : o do meio
#     indice 2 = fundo  : o ultimo que o carrinho alcanca
#
# OS PASSOS TEM DE SER IGUAIS entre si: os blocos sao igualmente
# espacados no tapete. Se o primeiro estiver certo e o terceiro errado,
# o passo esta errado - nao mexa so no terceiro.
#
# PLACEHOLDER - MEDIR NO ROBO (TESTE 2 no fim deste arquivo). O carrinho
# passou a ser comandado em GRAUS do motor, e nao mais em mm de correia,
# entao os valores antigos em milimetro nao servem de referencia.
PROFUNDIDADES = (100, 260, 420)

V_CARRINHO = 1000     # graus/s do motor_A ao trocar de profundidade

# --- Zeragem do carrinho contra o batente de casa ---
# Gira ate travar e chama aquele ponto de zero. As PROFUNDIDADES acima
# sao contadas dali, entao isto roda uma vez antes do primeiro bloco.
#
# Se o carrinho for para o lado ERRADO, inverta o sinal da velocidade
# aqui (ou o Direction do motor_A no setup.py).
#
#   trava antes de chegar no batente        -> aumente a FORCA
#   estala / range ao bater                 -> diminua a VELOCIDADE, e so
#                                              depois a forca
V_ZERAR     = -400    # graus/s, negativo = recolhe
FORCA_ZERAR = 60      # duty_limit em %

# --- ARREMESSO: UM par (velocidade, tempo) para os 12 blocos ---
# A garra fecha em cima do bloco e o arremessa para dentro do robo DE
# ONDE O CARRINHO ESTIVER. Nao ha par por coluna: quem escolhe a coluna e
# o servo.
#
# O tempo nao e "quanto tempo a garra gira forte": o run_time sobe do zero
# e volta ao zero DENTRO dele. Para a garra chegar mesmo na velocidade
# pedida o tempo tem de ser no minimo 2 x velocidade / aceleracao do
# motor_D - abaixo disso ela passa o movimento inteiro acelerando e ja
# freando, e gira um arco pequeno por mais alta que seja a velocidade.
#
# CALIBRAR NAS TRES PROFUNDIDADES (TESTE 3): o bloco e lancado de onde o
# carrinho parou, e a distancia ate a boca das colunas muda com ela. O
# par tem de servir as tres.
ARREMESSO_V  = 600
ARREMESSO_MS = 720

# Tempo da zeragem da garra AQUI, com o carrinho todo estendido em cima
# da coluna: o curso livre e mais longo que o do garra.py, entao o tempo
# e outro.
TEMPO_ZERAR_GARRA_MS = 1200

# Troca de coluna no tapete: o robo anda de lado para os blocos, muitas
# vezes com o carrinho estendido.
ANDAR_BLOCOS = dict(v_max=500, v_min=100, acel=200, desacel=3000,
                    kp=6, kd=4)


# =============================================================================
# 1. ESCOLHA DO BLOCO
# =============================================================================

def coluna_e_profundidade(ja_pegos_desta_cor):
    """
    A partir de quantos blocos dessa cor ja foram retirados, devolve
    (indice_coluna, indice_profundidade):

        indice_coluna       : 0 = coluna mais proxima, 1 = coluna irma
        indice_profundidade : 0 perto, 1 meio, 2 fundo

    E so uma consulta a cte.ORDEM_NA_COR - a estrategia (esvaziar uma
    coluna de cada vez, do fundo para a frente) esta escrita la, nao
    aqui, para mudar de ideia sem mexer em funcao nenhuma.
    """
    return cte.ORDEM_NA_COR[ja_pegos_desta_cor]


def escolher_cor(cor_pedida, ja_pegos, posicao_atual_mm):
    """
    Decide qual cor o robo vai realmente pegar.

    Normalmente e a propria `cor_pedida`. Mas so ha BLOCOS_POR_COR blocos
    alcancaveis de cada cor, entao se o mosaico pedir essa cor mais vezes
    do que isso, o excedente e substituido por outra cor que ainda tenha
    bloco sobrando - a MAIS PERTO da posicao atual, para nao gastar
    percurso a toa.

    Devolve None se todas as cores esgotaram (nao deve acontecer: sao 12
    blocos pedidos contra 24 alcancaveis).
    """
    if ja_pegos[cor_pedida] < cte.BLOCOS_POR_COR:
        return cor_pedida

    melhor = None
    melhor_distancia = 0
    for cor in cte.CORES:
        if ja_pegos[cor] >= cte.BLOCOS_POR_COR:
            continue
        indice_coluna, _ = coluna_e_profundidade(ja_pegos[cor])
        distancia = abs(cte.POSICAO_COLUNA[cor][indice_coluna]
                        - posicao_atual_mm)
        if melhor is None or distancia < melhor_distancia:
            melhor = cor
            melhor_distancia = distancia
    return melhor


# =============================================================================
# 2. PASSOS DO CICLO
# =============================================================================

def zerar_carrinho():
    """
    Encosta o carrinho no batente de casa e chama aquele ponto de zero.

    E o que da sentido as PROFUNDIDADES: elas sao graus contados DAQUI.
    Roda uma vez, antes do primeiro bloco.

    Nao e um atalho para mover o carrinho - e a referencia. Todo movimento
    de carrinho desta etapa e um motor_A.run_target() escrito na linha
    onde acontece.
    """
    motor_A.run_until_stalled(V_ZERAR, then=Stop.HOLD, duty_limit=FORCA_ZERAR)
    motor_A.reset_angle(0)


def ir_ate_coluna(cor, indice_coluna, posicao_atual_mm):
    """
    Anda reto (frente ou re) da posicao atual ate a coluna vertical pedida
    daquela cor. Devolve a nova posicao (mm).

    Nao faz NADA se a coluna pedida for a mesma de onde o robo ja esta
    (delta 0) - o caso do 2o e do 3o bloco de cada coluna, que saem so
    recolhendo o carrinho.

    NAO MEXE NO CARRINHO NEM NA GARRA, DE PROPOSITO. O robo anda com o
    carrinho onde o bloco anterior o deixou, inclusive todo estendido;
    recolher so para andar seriam 12 idas e voltas de graca. A garra
    chega aqui EMBAIXO, porque o guardar_bloco anterior ja a desceu -
    fora o primeiro bloco da rodada, em que ela ainda vem levantada.
    """
    destino_mm = cte.POSICAO_COLUNA[cor][indice_coluna]
    delta_mm = destino_mm - posicao_atual_mm
    if delta_mm != 0:
        m.andar(delta_mm, **ANDAR_BLOCOS)
    return destino_mm


def guardar_bloco(coluna_armazenagem):
    """
    Poe o SERVO na coluna de armazenagem pedida, arremessa o bloco para
    dentro do robo DE ONDE O CARRINHO ESTIVER e JA DESCE A GARRA DE
    VOLTA. O carrinho nao se mexe em momento nenhum.

    `coluna_armazenagem` (1, 2 ou 3) e a coluna DO ROBO em que o bloco
    tem de cair, e ela vai INTEIRA para o servo. O arremesso em si e
    identico nas tres: ARREMESSO_V / ARREMESSO_MS, um par so.

    SE O SERVO FALHAR o bloco e arremessado assim mesmo, para a coluna em
    que o seletor tiver ficado. O servos.py ja apitou e imprimiu; parar a
    rodada por causa de um bloco custaria os outros onze.

    A DESCIDA FAZ PARTE DO GUARDAR. Ela nao fica para o comeco do proximo
    bloco: assim que o bloco e solto na coluna de armazenagem a garra
    volta para g.ANGULO_ABAIXADA e fica la. Quem chama recebe a garra
    pronta para fechar no proximo bloco.

    Como a volta e para um ANGULO ABSOLUTO, ela tambem reafirma a altura
    da garra depois de cada arremesso - a forca da subida nao deixa sobra
    para se acumular de um bloco para o outro.

    Devolve o angulo em que a garra chegou NO TOPO, antes de descer. Na
    prova ninguem usa; serve para o TESTE 3 mostrar ate onde o arremesso
    levou a garra.
    """
    sv.selecionar_coluna(coluna_armazenagem)
    g.mover_garra(ARREMESSO_V, ARREMESSO_MS)
    topo = g.angulo_garra()
    g.descer_garra()
    return topo


# =============================================================================
# 3. ROTINA COMPLETA
# =============================================================================

def pegar_blocos(leituras):
    """
    Retira do tapete os blocos na ordem que o mosaico determinou e joga
    cada um para dentro do robo, da propria posicao em que ele foi pego.

    `leituras` : lista de 12 cores devolvida pela leitura (parte 2), na
                 ordem de varredura em zigue-zague (ver COLUNAS_MOSAICO
                 no constantes.py).

    LARGADA ESPERADA (quem entrega e a parte3):

        robo     : de lado para o tapete, ENCOSTADO NA PAREDE - a
                   posicao 0 de POSICAO_COLUNA
        carrinho : RECOLHIDO
        garra    : EM CIMA

    O primeiro movimento e a zeragem do carrinho; o segundo ja e o
    ir_ate_coluna do primeiro bloco.

    A GARRA E ZERADA UMA VEZ SO, no primeiro bloco, e essa e a unica
    descida que este laco faz por conta propria - porque so ali a garra
    ainda esta levantada (a parte3 a entrega assim). A zeragem acontece
    DEPOIS de o carrinho estender, com o robo parado na coluna, que e o
    que o garra.py exige para ela ter curso livre ate o batente de baixo.

    E a unica vez em que a garra encosta no batente; dali em diante toda
    descida e uma volta ao mesmo angulo absoluto, um pouco antes dele.
    Por isso a altura de pegar nao muda do primeiro para o decimo segundo
    bloco e o motor nunca fica empurrando o fim do curso.

    Percorre as colunas do MOSAICO na ordem de cte.ORDEM_RETIRADA (1, 3,
    2: primeira, terceira, meio) - diferente da ordem em que foram lidas,
    e diferente tambem da ordem em que serao ENTREGUES (ver
    entregar_blocos.py). Dentro de cada coluna, os 4 blocos saem na mesma
    ordem vertical em que foram lidos, e todos com o mesmo arremesso, ja
    que caem todos naquela mesma coluna do robo.
    """
    zerar_carrinho()

    ja_pegos = {}
    for cor in cte.CORES:
        ja_pegos[cor] = 0

    posicao_mm = 0          # encostado na parede: o zero de POSICAO_COLUNA
    garra_zerada = False

    for coluna_armazenagem in cte.ORDEM_RETIRADA:
        for indice in cte.COLUNAS_MOSAICO[coluna_armazenagem]:
            cor = escolher_cor(leituras[indice], ja_pegos, posicao_mm)
            if cor is None:
                return      # acabaram os blocos alcancaveis de todas as cores
            if cor != leituras[indice]:
                print("cor", leituras[indice], "esgotada, trocando por", cor)

            indice_coluna, indice_profundidade = coluna_e_profundidade(
                ja_pegos[cor])

            # 1. anda ate a coluna, com o carrinho onde estiver
            posicao_mm = ir_ate_coluna(cor, indice_coluna, posicao_mm)

            # 2. ja parado na coluna: o carrinho vai ate a profundidade do
            #    bloco. Mesma profundidade para as tres colunas de
            #    armazenagem - quem as separa e o servo, no passo 3.
            motor_A.run_target(V_CARRINHO, PROFUNDIDADES[indice_profundidade])

            # 2b. SO NO PRIMEIRO BLOCO: a garra ainda esta em cima, entao
            #     desce aqui - e essa descida e a zeragem, a unica ida ao
            #     batente da rodada. Do segundo bloco em diante ela ja
            #     chega embaixo, porque o guardar_bloco anterior a desceu.
            if not garra_zerada:
                g.zerar_garra(tempo_ms=TEMPO_ZERAR_GARRA_MS)
                garra_zerada = True

            # 3. servo na coluna certa, arremessa dali mesmo e desce a
            #    garra de volta
            guardar_bloco(coluna_armazenagem)
            ja_pegos[cor] += 1


# =============================================================================
# 4. TESTES E CALIBRACAO
# =============================================================================
# Mude o numero de TESTE la embaixo e rode este arquivo com F5.
#
#   1 -> passeia pelas 8 colunas do tapete   -> ajusta POSICAO_COLUNA
#   2 -> as 3 profundidades do carrinho      -> ajusta PROFUNDIDADES
#   3 -> pegar + guardar pelos botoes do EV3 -> ajusta ARREMESSO_V/_MS
#   4 -> a retirada completa, com a lista de exemplo do constantes.py
#
# A ORDEM IMPORTA: comece pelo 1 (o robo tem de parar no lugar certo
# antes de tudo), depois 2, depois 3.

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


def _teste_1_colunas():
    """
    Anda ate as 8 colunas verticais do tapete, uma de cada vez, na ordem
    fisica (branco1, branco2, verde1, ... amarelo2). NAO mexe em carrinho
    nem em garra - so anda.

    Reaproveita o proprio ir_ate_coluna, a mesma funcao que a prova usa,
    entao o que este teste mede e exatamente o movimento que vai
    acontecer na hora de verdade, ganho por ganho.

    COMO USAR: robo na largada de sempre - de lado para o tapete e
    encostado na parede.

    COMO APLICAR: o erro em mm se SOMA DIRETO ao numero correspondente em
    cte.POSICAO_COLUNA (positivo se o robo ficou aquem da coluna,
    negativo se passou). Como as posicoes sao ABSOLUTAS a partir da
    parede, corrigir uma nao desloca as outras sete.
    """
    posicao_mm = 0
    for cor in cte.CORES:
        for indice_coluna in (0, 1):
            posicao_mm = ir_ate_coluna(cor, indice_coluna, posicao_mm)
            ev3.speaker.beep()
            print(cor, "- coluna", indice_coluna + 1, "- alvo",
                  cte.POSICAO_COLUNA[cor][indice_coluna], "mm")
            print("  meca e aperte o botao CENTRAL para continuar")
            _esperar_botao((Button.CENTER,))
    print("fim - as 8 colunas foram visitadas")


def _teste_2_profundidades():
    """
    As tres profundidades do carrinho, uma de cada vez, com o robo
    parado. Meca com regua onde o carrinho parou em cada uma.

    COMO LER:
      as tres erradas para o mesmo lado -> so a PRIMEIRA esta errada:
          corrija PROFUNDIDADES[0] e some a mesma diferenca nas outras
          duas (o passo entre elas continua valendo);
      a primeira certa e a terceira errada -> o PASSO esta errado:
          os blocos sao igualmente espacados, entao 1->2 e 2->3 tem de
          ser a mesma diferenca;
      o motor fica zumbindo parado na do fundo -> o alvo passou do fim do
          curso mecanico: diminua PROFUNDIDADES[2].
    """
    zerar_carrinho()
    for indice, alvo in enumerate(PROFUNDIDADES):
        motor_A.run_target(V_CARRINHO, alvo)
        print("profundidade", indice, "- alvo", alvo,
              "graus -> parou em", motor_A.angle())
        print("  meca e aperte o botao CENTRAL")
        _esperar_botao((Button.CENTER,))
    motor_A.run_target(V_CARRINHO, 0)


def _teste_3_arremesso(indice_profundidade=2):
    """
    Calibracao INTERATIVA do arremesso e do servo, pelos botoes do EV3. O
    robo nao anda: fica parado e voce dispara o ciclo de pegar + guardar
    quantas vezes quiser, escolhendo no botao a coluna de destino, e
    vendo onde o bloco cai antes de mexer nos numeros.

    O QUE SE AJUSTA AQUI. O arremesso e UM SO para as tres colunas
    (ARREMESSO_V / ARREMESSO_MS), porque quem escolhe a coluna e o servo.
    Se o bloco cai perto ou longe demais DAS TRES, e o arremesso; se ele
    viaja certo mas entra na coluna errada, e o angulo do servo - e esse
    se ajusta no arduino_servos.ino, nao aqui.

    BOTOES:

        DOWN   -> guarda na coluna 1
        CENTER -> guarda na coluna 2
        UP     -> guarda na coluna 3
        LEFT   -> zera a garra de novo (re-conferir a descida ao batente)
        RIGHT  -> sai
        VOLTAR -> para o programa (funciona a qualquer momento)

    COMO USAR: robo parado, um bloco ao alcance da garra na profundidade
    escolhida. Escolha a coluna no botao, veja onde caiu, corrija o
    numero e repita. Entre um arremesso e outro o carrinho fica onde esta
    (estendido), igual a prova - so reponha o bloco.

    `indice_profundidade` : 0 perto, 1 meio, 2 fundo. CONFIRA NAS TRES -
    o mesmo par de arremesso tem de servir as tres, porque o bloco e
    lancado de onde o carrinho parou. Comece pelo fundo, a estendida mais
    longa.
    """
    print("=== arremesso - profundidade", indice_profundidade, "===")
    print("DOWN=col1  CENTER=col2  UP=col3  LEFT=re-zerar  RIGHT=sair")

    # A ACELERACAO do motor_D e o que decide se o tempo do arremesso da
    # para a garra chegar na velocidade pedida: o minimo e
    # 2 x velocidade / aceleracao.
    aceleracao = g.MOTOR_GARRA.control.limits()[1]
    print("  arremesso:", ARREMESSO_V, "graus/s por", ARREMESSO_MS,
          "ms   (minimo", 2000 * ARREMESSO_V // aceleracao, "ms )")

    zerar_carrinho()
    motor_A.run_target(V_CARRINHO, PROFUNDIDADES[indice_profundidade])
    g.zerar_garra(tempo_ms=TEMPO_ZERAR_GARRA_MS)

    while True:
        botao = _esperar_botao()

        if botao == Button.RIGHT:
            print("saindo")
            sv.repouso()
            return

        if botao == Button.LEFT:
            g.zerar_garra(tempo_ms=TEMPO_ZERAR_GARRA_MS)
            print("garra zerada, em", g.angulo_garra(), "graus")
            continue

        coluna = {Button.DOWN: 1, Button.CENTER: 2, Button.UP: 3}[botao]
        print("--- coluna", coluna, "---")
        topo = guardar_bloco(coluna)
        print("  subiu ate", topo, "graus")
        print("  e voltou a", g.angulo_garra(), "graus")
        print("  reponha o bloco e escolha a proxima coluna")


def _teste_4_rodada():
    """
    Retirada completa com a lista de exemplo do constantes.py, para
    conferir a logica de ordem sem depender de uma leitura real.

    Largada da prova: robo encostado na parede, carrinho recolhido, garra
    EM CIMA. O pegar_blocos zera o carrinho, sai andando para a primeira
    coluna e zera a garra la.
    """
    pegar_blocos(cte.LEITURAS_TESTE)


if __name__ == "__main__":

    TESTE = 4

    # So usado no TESTE 3: 0 perto, 1 meio, 2 fundo.
    PROFUNDIDADE = 2

    if TESTE == 1:
        _teste_1_colunas()
    elif TESTE == 2:
        _teste_2_profundidades()
    elif TESTE == 3:
        _teste_3_arremesso(PROFUNDIDADE)
    else:
        _teste_4_rodada()

    ev3.speaker.beep()
