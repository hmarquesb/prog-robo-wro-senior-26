#!/usr/bin/env pybricks-micropython
"""
constantes.py - So o que e COMPARTILHADO entre arquivos
=======================================================

Este arquivo NAO e mais o deposito de todos os numeros do projeto. Ele
guarda so o que varios arquivos precisam enxergar igual:

    geometria do chassi     porque movimento.py e linha.py fazem a mesma
                            conta e um erro so nos dois seria pior
    limites dos motores     aplicados no setup.py, valem para o robo todo
    ganhos padrao do PD     valores default das funcoes de movimento e de
                            linha - o ponto de partida de qualquer trecho
    protocolo do servo      tem de bater byte a byte com o Arduino
    mapa do tapete/mosaico  pegar_blocos e entregar_blocos precisam ler a
                            MESMA tabela, senao os blocos saem trocados

O QUE **NAO** MORA MAIS AQUI, e de proposito:

    velocidade de um trecho especifico    -> no arquivo do trecho
    graus de um movimento especifico      -> na linha que faz o movimento
    distancia usada uma vez so            -> onde ela e usada
    tempo de uma rotina                   -> na rotina
    numero que voces mexem testando       -> onde da para ver o efeito

A regra pratica: se o numero so faz sentido dentro de UM arquivo, ele
mora naquele arquivo, ao lado da chamada que o usa. Trazer para ca custa
uma ida e volta entre dois arquivos toda vez que voces querem ajustar um
valor no robo.

Este arquivo nao importa setup.py e NAO CRIA HARDWARE NENHUM - so
numeros. Por isso qualquer modulo pode importa-lo sem risco de import
circular, e rodar F5 nele nao mexe no robo.

INDICE

     1. CHASSI    geometria das rodas
     2. MOTORES   limites, teto de velocidade, ciclo de controle
     3. MOVIMENTO velocidade, aceleracao e PD padrao do andar/girar
     4. LINHA     seguidor, alinhamento e calibracao dos sensores
     5. SERVO     protocolo I2C do seletor de coluna (via Arduino)
     6. TAPETE    as 8 colunas de blocos e a ordem de retirada
     7. MOSAICO   quais celulas vao em qual coluna de armazenagem
     8. TESTE     lista de cores de exemplo e a flag de pular a leitura

UNIDADES (valem no projeto inteiro)

    velocidade de motor .... graus/segundo   (~200 lento, ~500 medio, ~800 rapido)
    tempo .................. milissegundos
    distancia .............. milimetros
    angulo ................. graus
    leitura de sensor ...... 0 a 100
"""

import math
from pybricks.parameters import Color


# =============================================================================
# 1. CHASSI  (medir com regua no robo - ver "Calibracao" no README)
# =============================================================================

DIAMETRO_RODA = 62.4      # mm
ENTRE_EIXOS   = 185     # mm - distancia entre o centro das duas rodas

# mm que o robo anda para cada 1 grau de rotacao da roda. Sai das duas
# medidas acima; nao e um valor para ajustar na mao.
MM_POR_GRAU = math.pi * DIAMETRO_RODA / 360.0


# =============================================================================
# 2. MOTORES
# =============================================================================

# (velocidade, aceleracao, atuacao) passados para control.limits() no
# setup.py. OBRIGATORIO para as rodas: o run() do Pybricks tem um PID
# proprio com limite interno de aceleracao e, sem afrouxa-lo, mexer em
# ACEL/DESACEL nao teria efeito nenhum (ver README, regra 5).
LIMITES_RODA = (1000, 10000, 100)

# O motor_A precisa de aceleracao MUITO mais baixa que as rodas. Sem isso
# ele passa do alvo e fica corrigindo (avanca, volta um pouco, avanca de
# novo). Se ainda oscilar, abaixe o 2o valor.
LIMITES_MOTOR_A = (1000, 3000, 100)

V_LIMITE = 1000   # teto absoluto de velocidade enviada aos motores
DT       = 5       # ms por ciclo dos loops de controle


# =============================================================================
# 3. MOVIMENTO  (valores PADRAO de andar, girar_eixo, girar_arco, girar_pivo)
# =============================================================================
# Sao os defaults das funcoes do movimento.py - o ponto de partida de um
# trecho novo. Cada chamada pode passar os seus proprios valores, e as
# rotinas da prova fazem exatamente isso: o numero que interessa a UM
# trecho fica escrito naquele trecho.

V_MAX = 700.0     # velocidade de cruzeiro
V_MIN = 60.0      # velocidade minima. Zero faz o robo "morrer" antes de
                  # chegar; alta demais faz derrapar ao parar.

ACEL    = 900.0
DESACEL = 1200.0  # costuma ser MAIOR que ACEL: freia mais rapido do que
                  # arranca, porque o ponto de parada importa mais

# Ganhos do PD que sincroniza as DUAS RODAS entre si (nao e o da linha).
KP = 2.8   # corrige o erro atual. Robo sai torto -> aumente.
KD = 8.0   # amortece. Robo oscila / treme -> aumente.

# Teto da correcao do PD, como fracao da velocidade do perfil naquele
# instante. Sem ele a correcao pode ficar MAIOR que a propria velocidade
# e zerar a roda atrasada - o robo gira em vez de andar reto (README,
# regra 6). Abaixe para 0.3 se ainda arrancar torto.
CORRECAO_MAX_FRAC = 0.4

TIMEOUT_MOVER_MS = 15000   # trava de seguranca padrao do _mover


# =============================================================================
# 4. LINHA
# =============================================================================

# --- Calibracao dos sensores, como (preto, branco) ---
# Cada sensor le valores diferentes no mesmo preto e no mesmo branco. Sem
# normalizar, o PD da linha nasce com erro constante e o robo anda torto.
# Estes pares saem do lin.calibrar_varrendo() - refaca a varredura quando
# a luz do ginasio mudar. O linha.py ja carrega os dois no import; nao ha
# nada para chamar no comeco do programa.
CAL_SENSOR_ESQ = (4, 49)
CAL_SENSOR_DIR = (3, 43)

LIMIAR_PRETO = 25   # leitura normalizada abaixo disso = preto

# --- Seguidor de linha (defaults do seguir_linha) ---
V_LINHA       = 400.0   # cruzeiro. Comece BAIXO (250) e suba conforme o
                        # PD ficar estavel.
V_MIN_LINHA   = 60.0
ACEL_LINHA    = 900.0
DESACEL_LINHA = 1200.0

# Ganhos do PD da LINHA (posicao em relacao a fita), diferentes do KP/KD
# de movimentacao (sincronismo entre rodas) - ver README, regra 6.
KP_LINHA = 3.0    # robo sai da linha na curva -> aumente
KD_LINHA = 12.0   # robo serpenteia / oscila   -> aumente

TIMEOUT_LINHA_MS = 20000   # trava de seguranca: nada roda para sempre

# --- Alinhamento (alinhar): PD por roda, sobre a LEITURA do sensor ---
KP_ALINHA = 6.0    # robo para longe da linha / muito lento -> aumente
KD_ALINHA = 15.0   # robo ainda passa da linha              -> aumente

V_ALINHA          = 250
V_MIN_ALINHA      = 40
TIMEOUT_ALINHA_MS = 4000

# --- Procura de linha (procurar_linha) ---
V_PROCURA          = 250
V_MIN_PROCURA      = 60
ACEL_PROCURA       = 900.0
KP_PROCURA         = 2.5
KD_PROCURA         = 8.0
TIMEOUT_PROCURA_MS = 5000

# --- Calibracao automatica (calibrar_varrendo) ---
VARREDURA_ANGULO     = 60
VARREDURA_VELOCIDADE = 120


# =============================================================================
# 5. SERVO SELETOR DAS COLUNAS  (Arduino Nano na porta S1, via I2C)
# =============================================================================
# As 3 colunas de armazenagem sao FIXAS no topo do robo. Quem decide em
# qual delas o bloco arremessado cai e um SERVO montado nelas - nao a
# forca do arremesso, que e a mesma para os 12 blocos.
#
# O servo nao e ligado no EV3: quem o comanda e um Arduino Nano
# (arduino_servos.ino), e o EV3 conversa com ele por I2C:
#
#     ESCRITA : 1 byte de comando (os SERVO_CMD_* abaixo)
#     LEITURA : 1 byte de status - 1 = ainda movendo, 0 = terminou
#
# QUEM PEDIR 2 BYTES recebe [status, SERVO_ASSINATURA]. O segundo byte
# nao faz parte da prova: serve para os arquivos de diagnostico provarem
# que quem respondeu foi o Arduino, e nao uma linha presa em zero (que
# devolve 0 para tudo, inclusive para enderecos onde nao ha ninguem).
# Ler 1 byte continua devolvendo so o status, entao o servos.py nao muda.
#
# ATENCAO: leitura de 2 bytes SO funciona na forma read(reg=X, length=2).
# Com reg=None o driver do EV3 nao sabe ler mais de um byte e levanta
# ValueError - que e diferente de OSError: ValueError quer dizer "essa
# operacao nem existe", nao "a conversa falhou".
#
# MORA AQUI, e nao no servos.py, porque estes numeros tem de bater byte a
# byte com o sketch do Arduino - sao um contrato entre dois programas, e
# o teste_arduino.py os repete de proposito para rodar na bancada sem o
# resto do projeto.

# A PORTA (S1) nao mora aqui: porta e hardware, e hardware e setup.py.
SERVO_ENDERECO = 0x04     # 7 bits dos dois lados, sem deslocar

# Comando por COLUNA DE ARMAZENAGEM (1, 2 ou 3): poe o seletor na boca da
# coluna pedida. Tem de bater com o switch do arduino_servos.ino.
#
# O sketch trata os quatro, um angulo para cada. Um byte que nao exista
# la cai no default, e o sketch segura o status em "ocupado" de proposito
# para o EV3 apitar o timeout em vez de achar que deu certo.
SERVO_CMD_COLUNA_1 = 0x10
SERVO_CMD_COLUNA_2 = 0x12
SERVO_CMD_COLUNA_3 = 0x13
SERVO_CMD_REPOUSO  = 0x11

# Segundo byte da resposta (ver acima). So os diagnosticos usam.
SERVO_ASSINATURA = 0x5A

SERVO_CMD = {
    1: SERVO_CMD_COLUNA_1,
    2: SERVO_CMD_COLUNA_2,
    3: SERVO_CMD_COLUNA_3,
}

# SEGUNDO SERVO (D10 no Arduino), o que SEGURA e LIBERA os blocos. Mesmo
# barramento, mesmo byte de status - so muda o comando. O sketch ja trata
# os dois (CMD_SERVO2_ACIONA / CMD_SERVO2_REPOUSO).
#
# QUAL DOS DOIS ANGULOS SEGURA e questao de montagem, nao de programa: se
# o teste mostrar invertido, troque ANG_SERVO2_ACIONADO e
# ANG_SERVO2_REPOUSO no arduino_servos.ino, nao estes bytes.
SERVO_CMD_SEGURAR = 0x20
SERVO_CMD_LIBERAR = 0x21

# Rede de seguranca da espera: se em SERVO_TIMEOUT_MS o Arduino nao disser
# que terminou, o programa desiste, apita e SEGUE. Tem de caber o curso
# inteiro do servo com folga (o sketch calcula o tempo pelo curso, a
# TEMPO_POR_GRAU ms por grau).
#
# O SERVO DOS BLOCOS ANDA EM RAMPA, de SERVO2_PASSO_GRAUS em
# SERVO2_PASSO_GRAUS - hoje ~112 ms para o curso dele, sobra de resto. Se
# um dia ele for muito desacelerado no sketch, refaca a conta
# (curso x PASSO_MS / PASSO_GRAUS) e suba este numero junto.
SERVO_TIMEOUT_MS = 2000

# Quantas vezes tentar de novo quando o barramento nao responde. A
# primeira leitura depois de ligar as vezes sai vazia.
SERVO_TENTATIVAS = 3


# =============================================================================
# 6. TAPETE DE BLOCOS
# =============================================================================

# --- ATE ONDE a garra levanta para PRENDER o bloco, sem arremessa-lo ---
# O movimento da garra e PARTIDO EM DOIS. Com o carrinho estendido em
# cima do bloco, ela levanta SO ATE AQUI e para - o bastante para prender,
# nao para jogar. O carrinho volta com o bloco preso, e so entao ela
# termina o movimento, que e o que arremessa.
#
# E um ANGULO ABSOLUTO, em graus do motor_D contados do batente que o
# zerar_garra marcou - a mesma referencia do g.ANGULO_ABAIXADA, de onde
# ela sai. Tem de ser MAIOR que ele.
#
#   o bloco escapa quando o carrinho volta  -> AUMENTE
#   a garra ja joga o bloco aqui            -> diminua
#
# COMO MEDIR, em vez de adivinhar: o teste_pegar_fileiras.py imprime o
# angulo em que a garra parou depois de fechar em cima do bloco. E esse
# numero, ou um pouco menos.
#
# VALOR PROVISORIO - nunca foi medido neste mecanismo.
ANGULO_PEGAR = 450

# --- ONDE o carrinho para para a garra jogar o bloco na coluna ---
# Depois de alcancar o bloco, o carrinho volta PARA ESTA POSICAO e so
# entao a garra arremessa. Vale para os 12 blocos.
#
# E uma POSICAO ABSOLUTA, em graus do motor_A contados do batente de casa
# - a mesma referencia das PROFUNDIDADES do pegar_blocos.py. Nao e "volte
# tanto": e "va para o grau tal".
#
# CONSEQUENCIA, e e o motivo de ser absoluta: os 12 blocos sao
# arremessados EXATAMENTE DO MESMO LUGAR, venham eles do fundo, do meio ou
# da frente. A distancia ate a boca das colunas para de mudar com a
# profundidade, e por isso um unico par de arremesso (ARREMESSO_V /
# ARREMESSO_MS, no pegar_blocos.py) serve para todos.
#
#   o bloco nao chega na boca da coluna    -> AUMENTE (arremessa de mais
#                                             longe do robo)
#   o bloco passa da coluna                -> diminua
#
# OS DOIS LIMITES DESTE NUMERO:
#
#   nao pode ser ~0 - com o carrinho no batente de casa a garra bate na
#   estrutura do robo antes do fim do curso (ver garra.py), e logo depois
#   do arremesso vem uma descida da garra;
#
#   nao pode cair em cima de um bloco que ainda esta la - a retirada vai
#   do fundo para a frente, entao as posicoes da FRENTE seguem ocupadas.
#   Ficar mais para dentro que PROFUNDIDADES[0] resolve.
#
# None desliga: o robo arremessa de onde pegou, sem mover o carrinho.
POSICAO_ARREMESSO = 510

# --- Distancia (mm) que o robo anda, A PARTIR DA PAREDE, ate ficar
# alinhado de lado com cada uma das 8 colunas verticais do tapete:
# [coluna mais proxima do inicio, coluna irma] de cada cor.
#
# Sao posicoes ABSOLUTAS, nao "ande mais tanto": errar uma nao desloca as
# outras sete, e o erro em mm se soma direto ao numero correspondente
# (positivo se o robo ficou aquem da coluna, negativo se passou).
#
# E O PRIMEIRO DA FILA DE CALIBRACAO, antes de profundidade e de
# arremesso - tudo o mais depende de o robo parar no lugar certo. Rode
# pegar_blocos.py no TESTE 1. ---
POSICAO_COLUNA = {
    Color.WHITE:  [80, 160],
    Color.GREEN:  [245, 305],
    Color.BLUE:   [415, 480],
    Color.YELLOW: [565, 645],
}

# Mesma ordem fisica do tapete. Existe como tupla (e nao so como as
# chaves de POSICAO_COLUNA) porque a ordem de iteracao de um dict no
# MicroPython e arbitraria, e o passeio pelas 8 colunas (TESTE 1 do
# pegar_blocos.py) precisa de uma ordem estavel.
CORES = (Color.WHITE, Color.GREEN, Color.BLUE, Color.YELLOW)

# --- Ordem em que os 6 blocos de UMA cor saem, como
# (indice_coluna, indice_profundidade):
#
#     indice_coluna       : 0 = coluna mais proxima do inicio, 1 = irma
#     indice_profundidade : 0 perto, 1 meio, 2 fundo
#       (as tres profundidades ficam no pegar_blocos.py)
#
# Duas decisoes estao escritas aqui, e o resto do programa so le a tabela:
#
# 1. DO FUNDO PARA A FRENTE dentro de cada coluna. E o que garante que
#    nunca haja um bloco ATRAS do que esta sendo arremessado. De quebra,
#    as tres profundidades saem em ordem DECRESCENTE: o carrinho estende
#    uma vez ate o fim e depois so RECOLHE, dois passos curtos. Estender
#    e o movimento caro; recolher e barato.
#
# 2. UMA COLUNA DE CADA VEZ, esvaziando a primeira antes de ir para a
#    irma. Assim e uma andada so por cor, e ela termina na coluna irma,
#    mais adiante no tapete, ja perto da cor seguinte.
ORDEM_NA_COR = (
    (0, 2),   # coluna de perto, bloco do FUNDO - onde o robo ja chegou
    (0, 1),   # coluna de perto, bloco do meio  - so recolhe o carrinho
    (0, 0),   # coluna de perto, bloco de perto - idem
    (1, 2),   # coluna irma,     bloco do FUNDO - ANDA ate a coluna irma
    (1, 1),   # coluna irma,     bloco do meio  - nao anda mais
    (1, 0),   # coluna irma,     bloco de perto - termina aqui, adiantado
)
BLOCOS_POR_COR = len(ORDEM_NA_COR)

# --- EXCECOES: cores que comecam pela coluna IRMA, e nao pela de perto ---
#
# Mesma tabela de cima, so que com as duas metades trocadas: esvazia a
# coluna 1 (a irma, mais adiante no tapete) inteira - fundo, meio, perto -
# e SO ENTAO volta para a coluna 0. Dentro de cada coluna a ordem nao
# muda: do FUNDO PARA A FRENTE continua valendo, e e o que garante que
# nunca haja bloco atras do que esta sendo arremessado.
#
# O BRANCO ESTA AQUI POR MOTIVO FISICO: a primeira coluna branca e a mais
# perto da largada, e pega-la antes da irma nao funciona no mecanismo.
# Nao e otimizacao de percurso - o planejar() ja cuida disso sozinho -,
# entao nao "conserte" mexendo aqui: se uma cor volta para o padrao, tire
# a linha dela do dict.
ORDEM_NA_COR_IRMA_PRIMEIRO = (
    (1, 2),   # coluna irma,     bloco do FUNDO
    (1, 1),   # coluna irma,     bloco do meio  - so recolhe o carrinho
    (1, 0),   # coluna irma,     bloco de perto - idem
    (0, 2),   # coluna de perto, bloco do FUNDO - ANDA de volta
    (0, 1),   # coluna de perto, bloco do meio
    (0, 0),   # coluna de perto, bloco de perto
)

# Cor -> ordem propria. Quem NAO esta aqui usa o ORDEM_NA_COR de cima.
ORDEM_POR_COR = {
    Color.WHITE: ORDEM_NA_COR_IRMA_PRIMEIRO,
}


def ordem_da_cor(cor):
    """
    A ordem dos 6 blocos daquela cor: a excecao dela, se tiver uma, senao
    o ORDEM_NA_COR padrao.

    Existe como funcao (a unica deste arquivo) porque o planejar() le
    esta tabela em dois lugares - ao medir o percurso e ao traduzir a
    ordem escolhida em passos -, e os dois tem de ver a MESMA ordem. Se
    um deles usasse o padrao e o outro a excecao, o robo andaria um
    percurso e executaria outro.
    """
    return ORDEM_POR_COR.get(cor, ORDEM_NA_COR)

# A ORDEM ENTRE AS COLUNAS DO ROBO NAO MORA MAIS AQUI. Existia um
# ORDEM_RETIRADA = (1, 3, 2), que mandava encher uma coluna de cada vez.
# As colunas continuam sendo filas, e a ordem DENTRO de cada uma
# continua fixa (e o COLUNAS_MOSAICO abaixo) - o que ficou livre foi o
# INTERCALAMENTO entre elas, e quem escolhe o de menor percurso e o
# pegar_blocos.planejar().


# =============================================================================
# 7. MOSAICO
# =============================================================================

# Indices de `leituras` (a lista de 12 cores da varredura) agrupados por
# coluna do mosaico, NA ORDEM EM QUE A COLUNA DO ROBO TEM DE SER ENCHIDA:
# fileira 4 primeiro, fileira 1 por ultimo.
#
# POR QUE DA FILEIRA 4 PARA A 1 - as duas coisas que mandam:
#
#   1. as colunas do robo sao FILA, nao pilha: o primeiro bloco que entra
#      e o primeiro que sai;
#   2. a entrega percorre o mosaico da FILEIRA 4 para a 1.
#
#   Numa fila a ordem de entrada E a ordem de saida. Logo a ordem de
#   enchimento tem de ser exatamente a ordem de entrega: 4, 3, 2, 1.
#
# Os indices saem da ordem da varredura (leitura_blocos_parte2.py), que
# le uma COLUNA de cada vez, comecando pela DIREITA:
#
#     indice :  0  1  2  3 |  4  5  6  7 |  8  9 10 11
#     coluna :  3  3  3  3 |  2  2  2  2 |  1  1  1  1
#     fileira:  1  2  3  4 |  4  3  2  1 |  1  2  3  4
#
# Cruzando as duas tabelas, a fileira 4 de cada coluna e o indice 11 (col
# 1), 4 (col 2) e 3 (col 3) - e sao esses que aparecem primeiro abaixo. A
# coluna 2 e a unica que sai em ordem crescente, porque foi lida de volta.
#
# MORA AQUI PORQUE SAO DOIS PROGRAMAS: diz ao pegar_blocos em que coluna
# do robo guardar cada bloco, e ao entregar_blocos de qual coluna tira-lo.
# Duas copias um dia divergem, e ai os blocos saem em celulas trocadas.
#
# MEXEU AQUI, mexeu na varredura ou na ordem da entrega? As tres tem de
# andar juntas.
COLUNAS_MOSAICO = {
    1: [11, 10, 9, 8],   # fileiras 4, 3, 2, 1
    2: [4, 5, 6, 7],     # fileiras 4, 3, 2, 1  (lida de volta)
    3: [3, 2, 1, 0],     # fileiras 4, 3, 2, 1
}


# =============================================================================
# 8. DADOS DE TESTE
# =============================================================================

# Lista de exemplo, para testar a logica de ordem sem depender de uma
# leitura real do mosaico (rode leitura_blocos_parte2.py para obter a de
# verdade). Usada pelos testes do pegar_blocos.py e do entregar_blocos.py
# - a mesma nos dois, para dar para acompanhar os dois lado a lado.
#
# Este exemplo tem AMARELO 5 vezes, dentro dos BLOCOS_POR_COR = 6 que o
# tapete tem de cada cor. Para ver o robo PULAR uma celula por falta de
# bloco (o unico caso em que ele nao entrega os 12), ponha uma cor 7
# vezes ou mais.
LEITURAS_TESTE = [
    Color.YELLOW, Color.GREEN, Color.BLUE,
    Color.YELLOW, Color.GREEN, Color.WHITE,
    Color.BLUE, Color.YELLOW, Color.GREEN,
    Color.YELLOW, Color.BLUE, Color.YELLOW,
]


# --- PULAR A LEITURA DO MOSAICO E USAR AS CORES ESCRITAS NA MAO ---
#
# Com PULAR_LEITURA = True o ler_mosaico() NAO le nada: o robo atravessa o
# mosaico numa andada so, sem parar em fileira nenhuma e sem mexer no
# carrinho, e devolve LEITURAS_MANUAIS abaixo. Dali para a frente a rodada
# segue igual - o pegar_blocos recebe essa lista pelo prog1 e nao sabe a
# diferenca.
#
# PARA QUE SERVE: testar o resto da rodada (retirada, arremesso, entrega)
# sem depender do sensor de cor, e rodar a prova com o mosaico digitado na
# mao quando a leitura estiver falhando. Voce olha o mosaico, escreve as
# 12 cores aqui, roda o prog1.
#
# MORA AQUI, e nao no leitura_blocos_parte2.py, porque DOIS arquivos leem
# a mesma coisa: o ler_mosaico decide se varre ou atravessa, e o TESTE 3
# do pegar_blocos.py usa esta lista no lugar da LEITURAS_TESTE quando a
# flag esta ligada.
#
# ATENCAO AO DESLIGAR NA HORA DA PROVA: com True o robo passa reto pelo
# mosaico. Se as cores digitadas nao forem as do mosaico daquela rodada,
# ele entrega os 12 blocos nas celulas erradas sem reclamar de nada.
PULAR_LEITURA = False

# As 12 cores NA ORDEM DA VARREDURA - a mesma da LEITURAS_TESTE e a mesma
# que o COLUNAS_MOSAICO (secao 7) indexa:
#
#     indice :  0  1  2  3 |  4  5  6  7 |  8  9 10 11
#     coluna :  3  3  3  3 |  2  2  2  2 |  1  1  1  1
#     fileira:  1  2  3  4 |  4  3  2  1 |  1  2  3  4
#
# Ou seja: a coluna 3 (a DIREITA) primeiro, de cima para baixo; a coluna 2
# DE VOLTA, da fileira 4 para a 1; a coluna 1 de novo da 1 para a 4. Nao e
# a ordem em que se le o mosaico com o olho - confira contra a tabela.
#
# So Color.WHITE, GREEN, BLUE e YELLOW valem; qualquer outra coisa o
# planejar() pula com apito, igual faria com uma leitura ruim.
LEITURAS_MANUAIS = [
    Color.YELLOW, Color.GREEN, Color.BLUE,
    Color.YELLOW, Color.GREEN, Color.WHITE,
    Color.BLUE, Color.YELLOW, Color.GREEN,
    Color.YELLOW, Color.BLUE, Color.YELLOW,
]
