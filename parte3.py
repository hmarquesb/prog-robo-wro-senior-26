#!/usr/bin/env pybricks-micropython
"""
parte3.py - Do mosaico ate o tapete de blocos
=============================================

O trecho que liga a LEITURA do mosaico a RETIRADA dos blocos.

    parte1.executar()          largada -> posicao de leitura
    ler_mosaico()              varre o mosaico -> 12 cores  (parte 2)
    parte3.executar()          <-- ESTE ARQUIVO
    pegar_blocos(leituras)     retira os 12 blocos

Roda de dois jeitos, igual as outras partes:

    F5 neste arquivo  -> executa so este trecho (posicione o robo na mao
                         onde a leitura termina)
    prog1.py          -> chamado na sequencia da prova

DE ONDE O ROBO VEM (fim do ler_mosaico):

    posicao : onde o avanco final da varredura o deixou, em cima do mosaico
    garra   : EM CIMA - a parte1 a levantou e a leitura nao a baixou
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

from pybricks.tools import wait

import movimento as m
import linha as lin
from setup import ev3, motor_A, motor_C,motor_B


# =============================================================================
# OS NUMEROS DESTE TRECHO
# =============================================================================



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
    motor_A.run_angle(1000, 510)

    lin.seguir_linha(parar_se=[lin.cruzamento()], kp=2.2, kd=11, v_max=800, desacel=500,
                         tempo_ms=1500, ignorar_mm=250)
    m.andar(165, v_max=500, v_min=100, acel=600, desacel=900, kp=2.5, kd=3.5)
    
    
    motor_A.run_angle(-1000, 650, wait=False)
    m.girar_pivo(motor_B, -145,  v_max=1000, acel=800, desacel=1400, kp=2.2, kd=7.33)
    while not motor_A.control.done():
        wait(10)
    m.girar_pivo(motor_C, 55, v_max=1000, acel=800, desacel=1400, kp=2.2, kd=7.33)

    m.andar(-100, v_max=800, v_min=100, acel=600, desacel=900, kp=2.5, kd=3.5)
    m.andar_por_tempo(500, -200)


if __name__ == "__main__":
    executar()
    ev3.speaker.beep()
