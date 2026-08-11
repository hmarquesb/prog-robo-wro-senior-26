#!/usr/bin/env pybricks-micropython
"""
parte2.py - Do mosaico ate o tapete de blocos
=============================================

O trecho que liga a LEITURA do mosaico a RETIRADA dos blocos.

    parte1.executar()             largada -> posicao de leitura
    leitura_blocos.ler_mosaico()  varre o mosaico -> 12 cores
    parte2.executar()             <-- ESTE ARQUIVO
    pegar_blocos(leituras)        retira os 12 blocos

O PERCURSO AINDA NAO ESTA ESCRITO. O arquivo existe pronto para receber
os movimentos: a funcao, o que ela pode usar, o estado em que o robo
chega, o estado em que ele tem de sair e a zeragem do carrinho no fim ja
estao no lugar. Falta so preencher a secao marcada dentro de executar().

Roda de dois jeitos, igual as outras partes:

    F5 neste arquivo  -> calibra os sensores e executa so este trecho
                         (posicione o robo na mao onde a leitura termina)
    prog1.py          -> chamado na sequencia da prova

DE ONDE O ROBO VEM (fim do ler_mosaico):

    posicao : onde o m.andar(225) do fim da varredura o deixou, em cima
              do mosaico
    garra   : EM CIMA - o ler_mosaico a levantou logo no comeco e nao a
              baixou mais
    carrinho: na primeira_posicao da varredura (uns 25 mm), fora do
              batente

PARA ONDE ELE TEM DE IR (largada do pegar_blocos):

    posicao : DE LADO para o tapete de blocos e ENCOSTADO NA PAREDE. E
              a posicao 0 de onde todo o POSICAO_COLUNA foi medido - se
              o robo parar 1 cm adiantado, as 8 colunas erram 1 cm.
    carrinho: ZERADO e FECHADO (no batente), e essa e a ultima linha
              desta funcao (ver la).
    garra   : EM CIMA. O pegar_blocos sai andando direto para a primeira
              coluna e so zera a garra la, ja parado - entao ela tem de
              chegar aqui levantada, senao raspa no tapete no caminho.

Como o robo fica de lado para os blocos, ele chega ali de RE ou girando
no fim - quem resolve isso e o percurso escrito aqui.
"""
from setup import sensor_esq, sensor_dir, motor_A, motor_B, motor_C, motor_D, ev3, wait
import setup as s
import movimento as m
import linha as lin
import carrinho as c
import garra as g


# Parametros do andar/girar deste trecho. Existem aqui, com nome, para
# nao repetir os mesmos numeros em cada chamada la embaixo - mesmo
# esquema do V_ANDAR do leitura_blocos.py. Ajuste conforme for testando.
V_ANDAR = dict(v_max=700, v_min=200, acel=1100, desacel=1800, kp=2.5, kd=3.5)
V_GIRAR = dict(v_max=550, desacel=1200, kp=3, kd=7)

# Encostar na parede: em vez de medir a distancia exata, o robo anda de re
# COM FOLGA contra a parede e deixa ela parar o robo. `timeout` e o que
# tira ele de la quando as rodas ja estao patinando - sem isso o _mover
# ficaria empurrando ate o timeout padrao (15 s).
#
# So vale se a parede aguentar o encosto. Se o robo ricochetear ou subir
# nela, troque por uma distancia medida com regua.
RECUO_NA_PAREDE_MM = -600
TIMEOUT_PAREDE_MS  = 2500


def executar():
    """
    Leva o robo do mosaico ate a largada da retirada dos blocos.

    Entrada : robo onde o ler_mosaico() parou, garra em cima, carrinho
              fora do batente (ver o cabecalho do arquivo).
    Saida   : robo de lado para o tapete de blocos, encostado na parede,
              carrinho ZERADO e FECHADO, garra EM CIMA - exatamente o que
              o pegar_blocos espera.

    Nao mexa na garra aqui: ela ja chega em cima e e assim que tem de
    ficar. O pegar_blocos zera a garra sozinho, na primeira coluna.
    """

    # =========================================================
    # ESCREVA O PERCURSO AQUI
    # =========================================================

    c.zerar_carrinho(velocidade=800, forca=90)
    c.mover_carrinho(60, velocidade=500)
    lin.seguir_linha(kp=1.5, kd=12, v_max=600, desacel=3000, tempo_ms=5000,
                     parar_se=[lin.cruzamento()], ignorar_mm=170)
    m.andar(48, v_max=300, v_min=200, acel=500, desacel=1800, kp=2.5, kd=3.5)
    m.girar_pivo(motor_C, -90, v_max=800, acel=800, desacel=1600, kp=3.1, kd=7.33)
    m.andar(-600, timeout=2500, **V_ANDAR)
    m.girar_pivo(motor_B, 30, v_max=800, acel=800, desacel=1600, kp=3.1, kd=7.33)
    m.girar_pivo(motor_C, -30, v_max=800, acel=800, desacel=1600, kp=3.1, kd=7.33)
    m.andar(-600, timeout=600, **V_ANDAR)


if __name__ == "__main__":
    # Testar so este trecho: ponha o robo na mao onde a leitura termina e
    # rode. A calibracao vem do parte1 para nao existirem duas copias dos
    # mesmos numeros de sensor.
    import parte1

    parte1.calibrar_sensores()
    executar()
    ev3.speaker.beep()
