#!/usr/bin/env pybricks-micropython
"""
parte2.py - Do mosaico ate o tapete de blocos
=============================================

O trecho que liga a LEITURA do mosaico a RETIRADA dos blocos.

    parte1.executar()             largada -> posicao de leitura
    leitura_blocos.ler_mosaico()  varre o mosaico -> 12 cores
    parte2.executar()             <-- ESTE ARQUIVO
    pegar_blocos(leituras)        retira os 12 blocos

Roda de dois jeitos, igual as outras partes:

    F5 neste arquivo  -> executa so este trecho (posicione o robo na mao
                         onde a leitura termina)
    prog1.py          -> chamado na sequencia da prova

DE ONDE O ROBO VEM (fim do ler_mosaico):

    posicao : onde o avanco final da varredura o deixou, em cima do mosaico
    garra   : EM CIMA - a parte1 a levantou e o ler_mosaico nao a baixou
    carrinho: na posicao da coluna 1 da varredura, fora do batente

PARA ONDE ELE TEM DE IR (largada do pegar_blocos):

    posicao : DE LADO para o tapete de blocos e ENCOSTADO NA PAREDE. E a
              posicao 0 de onde todo o POSICAO_COLUNA foi medido - se o
              robo parar 1 cm adiantado, as 8 colunas erram 1 cm.
    carrinho: RECOLHIDO. O pegar_blocos zera contra o batente antes do
              primeiro bloco, entao o que importa e que ele esteja perto
              de casa e nao atrapalhe a andada.
    garra   : EM CIMA. O pegar_blocos sai andando direto para a primeira
              coluna e so zera a garra la, ja parado - entao ela tem de
              chegar la levantada, senao raspa no tapete no caminho.

Nao mexa na garra aqui: ela ja chega em cima e e assim que tem de ficar.

Os numeros deste trecho ficam logo abaixo, neste arquivo.
"""

import movimento as m
import linha as lin
from setup import ev3, motor_A, motor_C


# =============================================================================
# OS NUMEROS DESTE TRECHO
# =============================================================================

CARRINHO_V  = 1000
CARRINHO_MM = 200     # graus do motor_A: tira o carrinho do batente para
                      # atravessar. Movimento RELATIVO - aqui nao ha zero.
CARRINHO_RECOLHER = -200   # e devolve, antes de encostar na parede

AVANCO_MM    = 50
PIVO_1_GRAUS = -90

# Encostar na parede: em vez de medir a distancia exata, o robo anda de re
# COM FOLGA e deixa a parede parar o robo. O timeout e o que tira ele de
# la quando as rodas ja estao patinando - sem ele o _mover ficaria
# empurrando ate o TIMEOUT_MOVER_MS (15 s).
#
# So vale se a parede aguentar o encosto. Se o robo ricochetear ou subir
# nela, troque por uma distancia medida com regua.
RECUO_PAREDE_MM   = -600
TIMEOUT_PAREDE_MS = 2500   # primeiro encosto, vindo de longe
TIMEOUT_PAREDE_2_MS = 600  # reencosto, ja perto

LINHA_ATE_TAPETE = dict(kp=1.5, kd=12, v_max=600, desacel=3000,
                        tempo_ms=5000, ignorar_mm=170)

ANDAR_AJUSTE = dict(v_max=300, v_min=200, acel=500, desacel=1800,
                    kp=2.5, kd=3.5)
ANDAR_RAPIDO = dict(v_max=700, v_min=200, acel=1100, desacel=1800,
                    kp=2.5, kd=3.5)
GIRAR_PIVO = dict(v_max=800, acel=800, desacel=1600, kp=3.1, kd=7.33)


def executar():
    """
    Leva o robo do mosaico ate a largada da retirada dos blocos.

    O robo termina ENCOSTANDO NA PAREDE de re, duas vezes: em vez de
    medir a distancia exata, ele anda com folga e deixa a parede parar o
    robo. Quem tira ele de la e o timeout, quando as rodas ja estao
    patinando - sem ele o _mover ficaria empurrando por 15 s.

    O carrinho sai do batente para atravessar e volta antes do encosto na
    parede - os dois movimentos sao RELATIVOS, porque quem estabelece o
    zero e o pegar_blocos, ja na primeira coluna.
    """
    motor_A.run_angle(CARRINHO_V, CARRINHO_MM)

    lin.seguir_linha(parar_se=[lin.cruzamento()], **LINHA_ATE_TAPETE)
    m.andar(AVANCO_MM, **ANDAR_AJUSTE)

    m.girar_pivo(motor_C, PIVO_1_GRAUS, **GIRAR_PIVO)

    motor_A.run_angle(CARRINHO_V, CARRINHO_RECOLHER)

    m.andar(RECUO_PAREDE_MM, timeout=TIMEOUT_PAREDE_MS, **ANDAR_RAPIDO)

    # Esquadrejar contra a parede com dois pivos opostos, um em cada
    # quina. Desligado no ultimo teste - religue se o robo chegar torto.
    # m.girar_pivo(motor_B, 30, **GIRAR_PIVO)
    # m.girar_pivo(motor_C, -30, **GIRAR_PIVO)

    m.andar(RECUO_PAREDE_MM, timeout=TIMEOUT_PAREDE_2_MS, **ANDAR_RAPIDO)


if __name__ == "__main__":
    executar()
    ev3.speaker.beep()
