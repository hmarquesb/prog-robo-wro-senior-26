#!/usr/bin/env pybricks-micropython
"""
leitura_blocos.py - Leitura do mosaico
======================================

Varre o mosaico em zigue-zague e devolve as 12 cores pedidas, na ordem
de varredura. E essa lista que o pegar_blocos.py consome (ver
COLUNAS_MOSAICO no constantes.py, que traduz a ordem de varredura para
"as 4 cores da coluna 1", etc.).

Roda de dois jeitos:

    F5 neste arquivo  -> executa so a leitura e imprime a lista
    prog1.py          -> chama ler_mosaico() depois da parte1 e passa a
                         lista adiante, na sequencia da prova

Por isso a varredura esta dentro de ler_mosaico(), e nao solta no
arquivo: solta, ela rodaria no momento do `import`.

QUEM VARRE O MOSAICO E O CARRINHO, e continua sendo: os dois sensores de
cor andam em cima dele (sao eles e o motor_D a parte movel). O que ficou
fixo no topo do robo foram as COLUNAS DE ARMAZENAGEM, e elas nao
participam da leitura - so da entrega, e la quem se move e o robo.

As cores saem do sensor.color() cru, e nao do lin.ler() - aqui interessa
QUAL cor e, nao quanto reflete, entao a calibracao do seguidor de linha
nao entra nessa conta. Ela ainda importa para o seguir_linha do comeco.

Os numeros deste trecho ficam logo abaixo, neste arquivo.
"""

from pybricks.parameters import Stop

import movimento as m
import linha as lin
from setup import ev3, motor_A, sensor_esq, sensor_dir


# =============================================================================
# OS NUMEROS DESTE TRECHO
# =============================================================================

# --- Posicoes do carrinho, em GRAUS do motor_A, em que cada coluna do
# mosaico fica debaixo do SENSOR DE COR ---
# Contadas do zero que a zeragem em cima do mosaico marca no batente de
# casa. Continuam sendo posicoes DO CARRINHO: os dois sensores andam com
# ele.
#
# PLACEHOLDER - MEDIR NO ROBO. O carrinho passou a ser comandado em graus
# do motor, e nao mais em mm de correia, entao os valores antigos em
# milimetro nao servem de referencia.
COLUNA_1 = 120
COLUNA_2 = 220
COLUNA_3 = 420

V_CARRINHO = 1000     # graus/s do motor_A na varredura

# Carrinho na ida ate o mosaico, antes da varredura comecar. E um
# movimento RELATIVO: nao ha zero ainda, ele so tira o carrinho do
# batente para o robo atravessar com ele fora.
CARRINHO_NA_IDA = 300

# --- Zeragem do carrinho contra o batente de casa, ja em cima do
# mosaico. E daqui que as COLUNA_* passam a valer.
#
#   trava antes de chegar no batente -> aumente a FORCA
#   estala / range ao bater          -> diminua a VELOCIDADE
V_ZERAR     = -400    # graus/s, negativo = recolhe
FORCA_ZERAR = 60      # duty_limit em %

# --- Percurso ---
ENTRE_FILEIRAS_MM = 50    # avanco de uma fileira do mosaico para a proxima
AVANCO_INICIAL_MM = 180   # entra em cima da primeira fileira
AVANCO_FINAL_MM   = 225   # sai de cima do mosaico

# Em cima do mosaico: devagar e freando forte, porque cada celula e
# pequena e o erro de uma fileira se soma na proxima.
ANDAR_MOSAICO = dict(v_max=300, v_min=200, acel=300, desacel=3000,
                     kp=1.9, kd=3.5)

LINHA_ATE_MOSAICO = dict(kp=1, kd=12, v_max=600, desacel=3000,
                         tempo_ms=5000, ignorar_mm=180)


# Cada passo da varredura: (tipo de movimento, valor, sensor a ler
# depois, rotulo). "carrinho" leva o motor_A a uma das 3 posicoes acima;
# "andar" avanca o robo uma fileira. O zigue-zague sai daqui: colunas
# 1-2-3 na primeira fileira, 3-2-1 na segunda, e assim por diante.
PASSOS = [
    ("carrinho", COLUNA_1, sensor_esq, "posicao 1"),
    ("carrinho", COLUNA_2, sensor_dir, "posicao 2"),
    ("carrinho", COLUNA_3, sensor_dir, "posicao 3"),
    ("andar", ENTRE_FILEIRAS_MM, sensor_dir, "avanco 1"),
    ("carrinho", COLUNA_2, sensor_dir, "posicao 2"),
    ("carrinho", COLUNA_1, sensor_esq, "posicao 1"),
    ("andar", ENTRE_FILEIRAS_MM, sensor_esq, "avanco 2"),
    ("carrinho", COLUNA_2, sensor_dir, "posicao 2"),
    ("carrinho", COLUNA_3, sensor_dir, "posicao 3"),
    ("andar", ENTRE_FILEIRAS_MM, sensor_dir, "avanco 3"),
    ("carrinho", COLUNA_2, sensor_dir, "posicao 2"),
    ("carrinho", COLUNA_1, sensor_esq, "posicao 1"),
]


def ler_mosaico(passos=PASSOS):
    """
    Varre o mosaico e devolve a lista das 12 cores, na ordem da varredura.

    Pressupoe o robo onde a parte1 o deixou, e a garra fora do caminho.

    A ZERAGEM ACONTECE JA EM CIMA DO MOSAICO, e nao antes de sair: e a
    varredura que precisa da posicao exata, e zerar aqui apaga qualquer
    folga acumulada no caminho. Antes disso o carrinho so e tirado do
    batente por um movimento relativo (CARRINHO_NA_IDA).

    ATENCAO: a zeragem gira o motor_A contra o batente com o robo parado
    em cima do mosaico. Confira no robo se nada da traseira encosta no
    tapete durante esse movimento.

    E a lista devolvida que o pegar_blocos.pegar_blocos() recebe.
    """
    motor_A.run_angle(V_CARRINHO, CARRINHO_NA_IDA)

    lin.seguir_linha(parar_se=[lin.cruzamento()], **LINHA_ATE_MOSAICO)

    m.andar(AVANCO_INICIAL_MM, **ANDAR_MOSAICO)

    # Daqui em diante as COLUNA_* sao absolutas, contadas deste zero.
    motor_A.run_until_stalled(V_ZERAR, then=Stop.HOLD, duty_limit=FORCA_ZERAR)
    motor_A.reset_angle(0)

    leituras = []
    for tipo, valor, sensor, nome in passos:
        if tipo == "carrinho":
            motor_A.run_target(V_CARRINHO, valor)
        else:
            m.andar(valor, **ANDAR_MOSAICO)
        cor = sensor.color()
        print(nome, ":", cor)
        leituras.append(cor)

    m.andar(AVANCO_FINAL_MM, **ANDAR_MOSAICO)

    return leituras


if __name__ == "__main__":
    leituras = ler_mosaico()
    print(leituras)
    ev3.speaker.beep()
