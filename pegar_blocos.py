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

    1. anda ate a coluna         (ir_ate_posicao)
    2. estende o carrinho ate a profundidade do bloco
       (motor_A.run_target, escrito no proprio laco)
    3. levanta um pouco a garra, PRENDENDO o bloco
       (g.mover_garra_ate_angulo ate cte.ANGULO_PEGAR)
    4. volta o carrinho para cte.POSICAO_ARREMESSO, com o bloco preso
       (motor_A.run_target, tambem no laco)
    5. guarda                    (guardar_bloco: servo -> a garra TERMINA
                                  o movimento, arremessando -> volta)

O MOVIMENTO DA GARRA E PARTIDO EM DOIS, e essa e a ideia da etapa. La
fora, em cima do bloco, ela levanta so ate ANGULO_PEGAR e para - prende,
mas nao joga. O carrinho volta com o bloco preso. So entao ela termina o
movimento, e e o terminar que arremessa.

A POSICAO DE ARREMESSO E ABSOLUTA e igual para os 12 blocos: todos sao
arremessados do MESMO ponto, venham do fundo, do meio ou da frente. E
isso que permite um unico par ARREMESSO_V / ARREMESSO_MS - a distancia
ate a boca das colunas para de mudar com a profundidade. Os dois numeros
moram no constantes.py para poder serem editados sem abrir este arquivo.

AS 3 COLUNAS DO ROBO SAO FILAS. O primeiro bloco que entra e o primeiro
que sai. Como a entrega percorre o mosaico da FILEIRA 4 para a 1, a ordem
de enchimento e a MESMA da ordem de entrega - 4, 3, 2, 1 - e nao o
inverso dela. E isso que cte.COLUNAS_MOSAICO guarda.

O ROBO PRECISA IR E VOLTAR NO TAPETE por causa disso: qual coluna do robo
recebe um bloco depende da CELULA que ele vai preencher, nao de onde ele
foi pego. Com tres filas exigindo ordens diferentes, e as cores
espalhadas pelo tapete, nao existe uma varredura so que atenda as tres.

O QUE DA PARA ESCOLHER e o INTERCALAMENTO das tres filas - e o
planejar() escolhe o de menor percurso, por programacao dinamica, antes
de o robo sair do lugar. O laco so executa o plano.

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

A DESCIDA DA GARRA ACONTECE NA ABERTURA DESTA ETAPA, antes do primeiro
bloco: o carrinho zera, abre ate o fundo e SO ENTAO a garra desce e zera.
Um movimento de cada vez. Assim o laco nao tem caso especial nenhum - os
12 blocos sao iguais.

    (Antes a descida ficava DENTRO do laco, com um "se for o primeiro
    bloco": a garra chegava levantada da etapa anterior e so descia la
    na primeira coluna. Era um caso especial que valia para 1 dos 12.)

PARA CONFERIR NO ROBO: com a garra embaixo desde o inicio, os dois blocos
da frente de uma coluna passam por BAIXO dela toda vez que o carrinho
estende ate o fundo de uma coluna nova - agora nas 8, e nao em 7. Dentro
de uma mesma coluna nao ha risco: ali o carrinho so RECOLHE, por cima de
posicoes ja esvaziadas.

LARGADA (o que a parte3 tem de entregar):

    robo     : de lado para o tapete e ENCOSTADO NA PAREDE. E a posicao 0
               de onde todo o POSICAO_COLUNA foi medido.
    carrinho : RECOLHIDO, encostado no batente de casa.
    garra    : EM CIMA. Quem a desce e a abertura desta etapa.

O CARRINHO SO SE MEXE COM O ROBO PARADO (README, regra 8). O robo PODE
andar com o carrinho estendido - desde que ele virou peca impressa em 3D
ficou leve o bastante -, o proibido e move-lo DURANTE a andada. Por isso
nao ha recolhimento entre um bloco e outro nem para trocar de coluna, e
por isso o robo sai para a primeira coluna ja com o carrinho no fundo.

O MOSAICO PEDE, O ROBO PEGA. Nao ha substituicao de cor: o carrinho
alcanca as 8 colunas do tapete, entao os 6 blocos de cada cor estao todos
disponiveis, e 12 pedidos nunca esgotam 24 alcancaveis.

UMA CELULA E PULADA (apito + print, rodada segue) em dois casos: quando a
leitura dela nao deu cor de tapete - PRETO, None, vermelho, marrom - e
quando o mosaico pediu aquela cor mais de 6 vezes. Sem essas duas
guardas seriam KeyError e IndexError, e uma celula ruim custaria os
outros onze blocos. As duas acontecem no planejar(), antes de o robo sair
do lugar.

pegar_blocos() DEVOLVE A ORDEM DE ENCHIMENTO das 3 colunas do robo. Em
rodada limpa ela e igual a cte.COLUNAS_MOSAICO; o que ela acrescenta e o
registro do que FALTOU, quando alguma celula foi pulada. O
entregar_blocos esvazia cada coluna na ordem INVERSA a essa.
"""

from pybricks.parameters import Button, Stop
from pybricks.tools import wait, StopWatch

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
# espacados no tapete. Se o perto estiver certo e o fundo errado, o passo
# esta errado - nao mexa so no fundo.
#
# PLACEHOLDER - MEDIR NO ROBO (TESTE 2 no fim deste arquivo). O fundo
# saiu do passo dos outros dois (900 - 100 = 800), nao de uma medida
# propria: confira os tres com regua.
PROFUNDIDADES = (110, 900, 1700)

V_CARRINHO = 1000    # graus/s do motor_A ao trocar de profundidade

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
V_ZERAR     = -800    # graus/s, negativo = recolhe
FORCA_ZERAR = 70      # duty_limit em %

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
# TEM DE SERVIR AS TRES PROFUNDIDADES: o bloco e lancado de onde o
# carrinho parou, e a distancia ate a boca das colunas muda com ela.
# Ajuste os dois numeros e rode o TESTE 3 (a retirada inteira) - se o
# bloco cai perto ou longe demais nos 12, e este par; se ele viaja certo
# mas entra na coluna errada, e o angulo do servo, no arduino_servos.ino.
ARREMESSO_V  = 900
ARREMESSO_MS = 500

# Tempo da zeragem da garra AQUI, com o carrinho todo estendido em cima
# da coluna: o curso livre e mais longo que o do garra.py, entao o tempo
# e outro.
TEMPO_ZERAR_GARRA_MS = 800

# Troca de coluna no tapete: o robo anda de lado para os blocos, muitas
# vezes com o carrinho estendido.
ANDAR_BLOCOS = dict(v_max=450, v_min=100, acel=200, desacel=1000,
                    kp=6, kd=3)

# --- Timeout do carrinho ao trocar de profundidade/arremesso ---
# MESMA IDEIA do timeout da garra (ver TIMEOUT_MS no garra.py):
# run_target com wait=True nao tem rede de seguranca nenhuma - se o
# carrinho travar no meio do curso (bloco emperrado, fio preso, mecanica
# forcando) ele fica empurrando ali PARA SEMPRE, e o programa nunca sai
# daquela linha. Foi o que comecou a acontecer de vez em quando na
# extensao.
#
# Maior que o TIMEOUT_MS da garra porque o curso do carrinho e mais
# longo (fundo a fundo, ida e volta) e mais lento (V_CARRINHO << as
# velocidades da garra).
TIMEOUT_CARRINHO_MS = 2000


def _run_target_com_timeout(velocidade, alvo, timeout=TIMEOUT_CARRINHO_MS):
    """
    motor_A.run_target(velocidade, alvo) com timeout - o mesmo padrao de
    garra.mover_garra_ate_angulo/esperar_garra. NAO E UM WRAPPER QUE
    ESCONDE NUMERO NENHUM (ver decisao 9 do README/CLAUDE.md, que rejeita
    por nome um wrapper "estender_carrinho()" por esse motivo): velocidade
    e alvo continuam explicitos na propria linha de quem chama, igual
    seriam num run_target() direto. O que esta funcao acrescenta e so o
    polling com relogio - a mecanica de "nao empurrar para sempre".

    Sem isto, run_target(wait=True) nao tem rede de seguranca: se o
    carrinho travar no meio do curso (bloco emperrado, mecanica forcando)
    ele fica empurrando ali PARA SEMPRE e o programa nunca sai daquela
    linha. Foi o que comecou a acontecer de vez em quando na extensao.

    Dispara SEM esperar (wait=False) e faz o proprio polling: se o motor
    nao chegar em `timeout`, para de empurrar (hold - segura a posicao
    onde travou, nao solta o carrinho no meio do tapete), apita, imprime
    onde parou e devolve False. O robo CONTINUA a rodada - travar ali de
    vez teria custado os outros onze blocos.

    Devolve True se chegou no alvo, False se estourou o timeout.

    ESTOURAR AQUI NAO E CALIBRACAO DE NUMERO: PROFUNDIDADES e
    POSICAO_ARREMESSO ja sao medidos no robo. Um estouro aqui e um
    travamento MECANICO daquela vez - bloco emperrado, fio preso -, nao
    um alvo errado. Se estourar toda hora no mesmo indice de
    profundidade, ai sim o alvo esta alto demais.
    """
    motor_A.run_target(velocidade, alvo, then=Stop.HOLD, wait=False)
    relogio = StopWatch()
    while not motor_A.control.done():
        if relogio.time() > timeout:
            motor_A.hold()
            ev3.speaker.beep(200, 300)
            print("carrinho nao chegou em", alvo,
                  "- travou em", motor_A.angle(), "graus")
            return False
        wait(10)
    return True


# =============================================================================
# 1. ESCOLHA DO BLOCO
# =============================================================================

def coluna_de_armazenagem(indice_celula):
    """
    Em qual das 3 colunas do robo (1, 2 ou 3) o bloco daquela celula do
    mosaico tem de ser guardado.

    Le do cte.COLUNAS_MOSAICO, que e a mesma tabela que o
    entregar_blocos.py consulta para saber de onde tirar cada bloco.

    Devolve None para indice fora de 0..11.
    """
    for coluna in (1, 2, 3):
        if indice_celula in cte.COLUNAS_MOSAICO[coluna]:
            return coluna
    return None


def filas_de_enchimento(leituras):
    """
    Devolve as 3 filas de enchimento - uma por coluna do robo -, cada uma
    com os indices de celula NA ORDEM OBRIGATORIA em que aquela coluna
    tem de ser carregada.

    ESSA ORDEM NAO E ESCOLHA NOSSA. As colunas sao FILAS: o primeiro
    bloco que entra e o primeiro que sai. A entrega percorre o mosaico da
    fileira 4 para a 1, entao a ordem de SAIDA de cada coluna esta dada -
    e numa fila a de ENTRADA e IGUAL a ela, nao o inverso. E isso que
    cte.COLUNAS_MOSAICO ja guarda.

    Duas coisas tiram uma celula da fila, com apito e print, e a rodada
    segue sem ela:

      - a leitura nao deu cor de tapete (PRETO, None, vermelho, marrom);
      - o mosaico pediu aquela cor mais de BLOCOS_POR_COR vezes.

    Tirar uma celula NAO quebra a fila: as que sobram continuam na mesma
    ordem relativa. A coluna so termina com menos blocos do que o previsto.
    """
    ja_pedidos = {}
    for cor in cte.CORES:
        ja_pedidos[cor] = 0

    filas = []
    for coluna in (1, 2, 3):
        fila = []
        for indice_celula in cte.COLUNAS_MOSAICO[coluna]:
            cor = leituras[indice_celula]

            if cor not in cte.CORES:
                ev3.speaker.beep(200, 300)
                print("celula", indice_celula, "leu", cor,
                      "- nao e cor do tapete, pulando")
                continue

            if ja_pedidos[cor] >= cte.BLOCOS_POR_COR:
                ev3.speaker.beep(200, 300)
                print("acabaram os blocos", cor, "- celula", indice_celula,
                      "vai ficar vazia")
                continue

            ja_pedidos[cor] += 1
            fila.append(indice_celula)
        filas.append(fila)

    return filas


def planejar(leituras):
    """
    Monta a ORDEM DE RETIRADA dos blocos e devolve uma lista de passos:

        (posicao_mm, indice_profundidade, indice_celula, cor)

    O QUE E FIXO E O QUE E LIVRE:

      FIXO   a ordem DENTRO de cada coluna do robo (filas_de_enchimento):
             as colunas sao filas, entao elas tem de ser enchidas na
             MESMA ordem em que vao ser entregues (fileira 4 -> 1).
      FIXO   a ordem DENTRO de uma cor (cte.ORDEM_NA_COR): esvazia a
             coluna de perto - fundo, meio, perto - e so entao a irma.
             E o que garante que nunca haja bloco ATRAS do que esta sendo
             arremessado, e que o carrinho so RECOLHA dentro de uma coluna.
      LIVRE  o INTERCALAMENTO das 3 filas entre si. E so aqui que da para
             otimizar - e e o que esta funcao faz.

    POR QUE O ROBO PRECISA IR E VOLTAR NO TAPETE: a coluna do robo que
    recebe um bloco e ditada pela CELULA do mosaico que ele vai preencher,
    nao por onde ele foi pego. Como cada coluna tem de ser enchida numa
    ordem especifica, e as cores dessas celulas estao espalhadas pelo
    tapete, nao existe ordem que atenda as tres filas numa varredura so.

    COMO ESCOLHE: programacao dinamica sobre o estado

        (quanto ja saiu de cada fila, posicao do robo)

    Sao 5x5x5 combinacoes de indice, cada uma com no maximo 3 posicoes
    possiveis - umas centenas de estados. Roda uma vez, antes de o robo
    sair do lugar, e da o intercalamento de MENOR PERCURSO, nao um
    palpite. Um guloso "pega sempre a fila mais perto" fica ~20% pior.

    A CONTAGEM POR COR NAO PRECISA ENTRAR NA CHAVE: quantos blocos de
    cada cor ja sairam e consequencia de quanto saiu de cada fila, entao
    dois caminhos ate o mesmo estado tem sempre a mesma contagem.
    """
    filas = filas_de_enchimento(leituras)
    total = len(filas[0]) + len(filas[1]) + len(filas[2])

    # Chave: (i0, i1, i2, posicao_mm).  Valor: (custo_mm, ordem_das_celulas)
    estados = {(0, 0, 0, 0): (0, ())}

    for _ in range(total):
        proximos = {}

        for chave in estados:
            custo, ordem = estados[chave]
            posicao = chave[3]

            # Quantos de cada cor ja foram pegos ate aqui - e isso que
            # diz de qual das duas colunas do tapete sai o proximo.
            contagens = {}
            for cor in cte.CORES:
                contagens[cor] = 0
            for celula in ordem:
                contagens[leituras[celula]] += 1

            for fila in range(3):
                if chave[fila] >= len(filas[fila]):
                    continue      # esta fila ja acabou

                indice_celula = filas[fila][chave[fila]]
                cor = leituras[indice_celula]
                indice_coluna, _ = cte.ORDEM_NA_COR[contagens[cor]]
                destino = cte.POSICAO_COLUNA[cor][indice_coluna]

                novo_custo = custo + abs(destino - posicao)
                avancos = [chave[0], chave[1], chave[2]]
                avancos[fila] += 1
                nova_chave = (avancos[0], avancos[1], avancos[2], destino)

                anterior = proximos.get(nova_chave)
                if anterior is None or novo_custo < anterior[0]:
                    proximos[nova_chave] = (novo_custo,
                                            ordem + (indice_celula,))

        estados = proximos

    # O melhor entre os estados finais.
    melhor = None
    for chave in estados:
        if melhor is None or estados[chave][0] < melhor[0]:
            melhor = estados[chave]

    if melhor is None:
        return []

    print("percurso planejado:", melhor[0], "mm")

    # Traduz a ordem escolhida em passos executaveis.
    passos = []
    contagens = {}
    for cor in cte.CORES:
        contagens[cor] = 0

    for indice_celula in melhor[1]:
        cor = leituras[indice_celula]
        indice_coluna, indice_profundidade = cte.ORDEM_NA_COR[contagens[cor]]
        passos.append((cte.POSICAO_COLUNA[cor][indice_coluna],
                       indice_profundidade, indice_celula, cor))
        contagens[cor] += 1

    return passos


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


def ir_ate_posicao(destino_mm, posicao_atual_mm):
    """
    Anda reto da posicao atual ate `destino_mm` (mm contados da parede).
    Devolve a nova posicao.

    Nao faz NADA se ja estiver la (delta 0) - o caso do 2o e do 3o bloco
    de uma mesma coluna do tapete, que saem so recolhendo o carrinho.

    NAO MEXE NO CARRINHO NEM NA GARRA, DE PROPOSITO. O robo anda com o
    carrinho onde o bloco anterior o deixou, inclusive todo estendido;
    recolher so para andar seriam 12 idas e voltas de graca. A garra
    chega aqui EMBAIXO, porque o guardar_bloco anterior ja a desceu.
    """
    delta_mm = destino_mm - posicao_atual_mm
    if delta_mm != 0:
        m.andar(delta_mm, **ANDAR_BLOCOS)
    return destino_mm


def guardar_bloco(coluna_armazenagem):
    """
    Poe o SERVO na coluna de armazenagem pedida, TERMINA o movimento da
    garra - e o terminar que arremessa o bloco para dentro do robo - e JA
    DESCE A GARRA DE VOLTA. Esta funcao nao mexe no motor_A.

    ESPERA O BLOCO JA PRESO (cte.ANGULO_PEGAR) e o CARRINHO JA NA POSICAO
    DE ARREMESSO (cte.POSICAO_ARREMESSO). Quem faz as duas coisas e o
    laco, nos passos 3 e 4.

    O ARREMESSO E POR TEMPO e comeca de ANGULO_PEGAR, nao de baixo - o
    arco que sobra e menor que o do curso inteiro. Mexeu no ANGULO_PEGAR,
    o par ARREMESSO_V / ARREMESSO_MS muda junto.

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
    """
    sv.selecionar_coluna(coluna_armazenagem)
    g.mover_garra(ARREMESSO_V, ARREMESSO_MS)
    g.descer_garra()


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

    A ABERTURA E A MESMA PARA OS 12 BLOCOS: zera o carrinho, estende ate
    o fundo, zera a garra. So entao o laco comeca. O laco em si nao tem
    caso especial nenhum - todo bloco e andar, estender, guardar.

    A GARRA E ZERADA UMA VEZ SO, aqui no comeco. E a unica vez em que ela
    encosta no batente; dali em diante toda descida (dentro do
    guardar_bloco) e uma volta ao mesmo angulo absoluto, um pouco antes
    dele. Por isso a altura de pegar nao muda do primeiro para o decimo
    segundo bloco e o motor nunca fica empurrando o fim do curso.

    UM MOVIMENTO DE CADA VEZ: o carrinho abre ate o fundo, espera, e SO
    ENTAO a garra zera. Ja foi sobreposto com wait=False e um atraso, e
    foi desfeito depois de testar no robo.

    A ORDEM E O QUE IMPORTA, nao o tempo economizado: com o carrinho
    recolhido a garra bate na estrutura do robo antes do fim do curso, e
    o zero sairia alto - junto com todas as descidas da rodada (ver
    garra.py).

    O carrinho vai ate o FUNDO porque e o curso livre mais longo, que e
    para o que o TEMPO_ZERAR_GARRA_MS foi calibrado.

    O ROBO ANDA COM O CARRINHO ESTENDIDO ate a primeira coluna, e isso
    esta certo: o proibido e move-lo DURANTE a andada, nao andar com ele
    para fora (README, regra 8).

    A ORDEM DE RETIRADA vem do planejar(): as 3 filas tem ordem fixa, e
    ele escolhe o intercalamento de menor percurso entre elas. O robo vai
    e volta pelo tapete - e o preco de as colunas terem ordem obrigatoria.

    DEVOLVE (carregadas, posicao_mm):

        carregadas : a ORDEM DE ENCHIMENTO das 3 colunas do robo, como
                     {coluna: [indices de celula, na ordem em que
                     entraram]}. Como as colunas sao FILAS, essa e tambem
                     a ordem em que os blocos vao sair. Em rodada limpa e
                     igual a cte.COLUNAS_MOSAICO; o que muda e quando uma
                     celula foi pulada.
        posicao_mm : onde o robo PAROU, em mm da parede - a mesma
                     referencia de POSICAO_COLUNA. Depende da leitura do
                     mosaico daquela rodada (a ultima coluna visitada nao
                     e sempre a mesma), entao quem for voltar para a
                     parede depois (parte4.py) precisa saber daqui quanto
                     falta andar, em vez de supor a pior distancia.

    O MOSAICO PEDE, O ROBO PEGA. Nao ha substituicao de cor: as 8 colunas
    do tapete estao ao alcance, entao os 6 blocos de cada cor estao todos
    disponiveis, e 12 pedidos nunca esgotam 24 alcancaveis. Celulas com
    leitura ruim ou com cor pedida demais ficam de fora ja no planejar().
    """
    zerar_carrinho()

    # UM MOVIMENTO DE CADA VEZ. O carrinho vai ate o fundo e SO ENTAO a
    # garra zera - nada de wait=False aqui.
    #
    # Ja foi sobreposto (carrinho com wait=False e a zeragem da garra por
    # cima), e foi desfeito depois de testar no robo: a ordem e o que
    # importa, nao o tempo economizado. A garra so tem curso livre com o
    # carrinho fora do batente; partindo juntos ela bate na estrutura e o
    # zero sai alto, o que desloca TODAS as alturas da rodada.
    _run_target_com_timeout(V_CARRINHO, PROFUNDIDADES[2])
    g.zerar_garra(tempo_ms=TEMPO_ZERAR_GARRA_MS)

    posicao_mm = 0          # encostado na parede: o zero de POSICAO_COLUNA
    carregadas = {1: [], 2: [], 3: []}

    for destino_mm, indice_profundidade, indice_celula, cor in planejar(leituras):
        coluna_armazenagem = coluna_de_armazenagem(indice_celula)

        print(destino_mm, "mm -", cor, "-> coluna", coluna_armazenagem)

        # 1. anda ate a coluna do tapete, com o carrinho onde estiver.
        #    O delta pode ser NEGATIVO: o robo vai e volta pelo tapete,
        #    porque as tres filas tem de ser enchidas em ordens que nao
        #    cabem numa varredura so (ver planejar).
        posicao_mm = ir_ate_posicao(destino_mm, posicao_mm)

        # 2. ja parado na coluna: o carrinho vai ate a profundidade do
        #    bloco. Mesma profundidade para as tres colunas de
        #    armazenagem - quem as separa e o servo, no passo 4.
        _run_target_com_timeout(V_CARRINHO, PROFUNDIDADES[indice_profundidade])

        # 3. LEVANTA UM POUCO a garra, prendendo o bloco. Ela para em
        #    cte.ANGULO_PEGAR: e o bastante para segurar, e nao o
        #    bastante para arremessar - isso fica para o passo 5.
        g.mover_garra_ate_angulo(cte.ANGULO_PEGAR)

        # 4. COM O BLOCO PRESO, volta o carrinho para a posicao de
        #    arremesso - a MESMA para os 12 blocos, venham do fundo, do
        #    meio ou da frente. E isso que permite um unico par de
        #    arremesso: a distancia ate a boca das colunas para de mudar
        #    com a profundidade.
        #    None desliga e o robo arremessa de onde pegou.
        if cte.POSICAO_ARREMESSO is not None:
            _run_target_com_timeout(V_CARRINHO, cte.POSICAO_ARREMESSO)

        # 5. servo na coluna certa, a garra TERMINA o movimento (e o que
        #    arremessa) e volta para baixo
        guardar_bloco(coluna_armazenagem)
        carregadas[coluna_armazenagem].append(indice_celula)

    return carregadas, posicao_mm


# =============================================================================
# 4. TESTES E CALIBRACAO
# =============================================================================
# Mude o numero de TESTE la embaixo e rode este arquivo com F5.
#
#   1 -> passeia pelas 8 colunas do tapete -> ajusta POSICAO_COLUNA
#   2 -> as 3 profundidades do carrinho    -> ajusta PROFUNDIDADES
#   3 -> a retirada completa, com a lista de exemplo do constantes.py
#
# A ORDEM IMPORTA: comece pelo 1 (o robo tem de parar no lugar certo
# antes de tudo), depois 2, e so entao rode a retirada inteira.
#
# O ARREMESSO NAO TEM TESTE PROPRIO: e um par so (ARREMESSO_V/_MS) para
# os 12 blocos, entao nao ha nada para comparar entre um bloco e outro -
# ajuste os dois numeros e rode o TESTE 3. Se o bloco viaja certo mas cai
# na coluna errada, o problema e o angulo do servo, no
# arduino_servos.ino: rode o servos.py para conferir isso separado.

def _esperar_centro():
    """
    Espera um aperto NOVO do botao CENTRAL do EV3.

    Primeiro espera SOLTAR o que ja estivesse pressionado na entrada,
    depois espera o aperto e espera ele soltar antes de devolver - assim
    um dedo segurando o botao nao dispara varias paradas seguidas.

    O botao fisico VOLTAR nao entra aqui: ele para o programa inteiro, e
    e o jeito de sair da calibracao a qualquer momento.
    """
    while ev3.buttons.pressed():          # solta o que estava preso
        wait(10)
    while Button.CENTER not in ev3.buttons.pressed():
        wait(10)
    while ev3.buttons.pressed():
        wait(10)


def _teste_1_colunas():
    """
    Anda ate as 8 colunas verticais do tapete, uma de cada vez, na ordem
    fisica (branco1, branco2, verde1, ... amarelo2). NAO mexe em carrinho
    nem em garra - so anda.

    Reaproveita o proprio ir_ate_posicao, a mesma funcao que a prova usa,
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
            alvo_mm = cte.POSICAO_COLUNA[cor][indice_coluna]
            posicao_mm = ir_ate_posicao(alvo_mm, posicao_mm)
            ev3.speaker.beep()
            print(cor, "- coluna", indice_coluna + 1, "- alvo", alvo_mm, "mm")
            print("  meca e aperte o botao CENTRAL para continuar")
            _esperar_centro()
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
          os blocos sao igualmente espacados, entao perto->meio e
          meio->fundo tem de ser a mesma diferenca;
      o motor fica zumbindo parado na do fundo -> o alvo passou do fim do
          curso mecanico: diminua PROFUNDIDADES[2].
    """
    zerar_carrinho()
    for indice, alvo in enumerate(PROFUNDIDADES):
        _run_target_com_timeout(V_CARRINHO, alvo)
        print("profundidade", indice, "- alvo", alvo,
              "graus -> parou em", motor_A.angle())
        print("  meca e aperte o botao CENTRAL")
        _esperar_centro()

    _run_target_com_timeout(V_CARRINHO, 0)


def _teste_3_rodada():
    """
    Retirada completa com a lista de exemplo do constantes.py, para
    conferir a logica de ordem sem depender de uma leitura real.

    Largada da prova: robo encostado na parede, carrinho recolhido, garra
    EM CIMA. O pegar_blocos zera o carrinho, abre ate o fundo, zera a
    garra, e so entao sai andando para a primeira coluna.

    Imprime o PLANO antes de sair do lugar - da para conferir a ordem no
    terminal, com o robo parado, antes de deixar ele executar. As posicoes
    NAO saem em ordem crescente, e nem podem: cada coluna do robo e uma
    fila com ordem de enchimento fixa, entao o robo vai e volta. O que o
    planejar() minimiza e a soma dessas idas e vindas.
    """
    print("plano da retirada (posicao mm, profundidade, celula, cor):")
    for destino_mm, profundidade, celula, cor in planejar(cte.LEITURAS_TESTE):
        print("  ", destino_mm, "mm  prof", profundidade,
              " celula", celula, " ", cor,
              " -> coluna", coluna_de_armazenagem(celula))

    carregadas, posicao_final_mm = pegar_blocos(cte.LEITURAS_TESTE)
    print("parou em", posicao_final_mm, "mm da parede")

    # CONFERE AS FILAS: cada coluna tem de ter sido enchida exatamente na
    # ordem de cte.COLUNAS_MOSAICO (menos as celulas que foram puladas).
    # Como as colunas sao FILA, essa e tambem a ordem em que os blocos vao
    # sair - se isto quebrar, a entrega sai com os blocos em celulas
    # trocadas.
    print("filas (ordem de enchimento x ordem exigida):")
    for coluna in (1, 2, 3):
        exigida = []
        for celula in cte.COLUNAS_MOSAICO[coluna]:
            if celula in carregadas[coluna]:
                exigida.append(celula)
        ok = carregadas[coluna] == exigida
        print("  coluna", coluna, ":", carregadas[coluna],
              "OK" if ok else ("QUEBRADO, esperado " + str(exigida)))
        if not ok:
            ev3.speaker.beep(200, 500)


if __name__ == "__main__":

    TESTE = 3

    if TESTE == 1:
        _teste_1_colunas()
    elif TESTE == 2:
        _teste_2_profundidades()
    else:
        _teste_3_rodada()

    ev3.speaker.beep()
