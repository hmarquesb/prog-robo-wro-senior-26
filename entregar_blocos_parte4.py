#!/usr/bin/env pybricks-micropython
"""
entregar_blocos_parte4.py - Do tapete de blocos de volta ao mosaico (INICIO)
=============================================================================

O trecho que comeca o "percurso que falta" citado no prog1.py: tapete de
blocos -> mosaico, para a entrega poder comecar.

    pegar_blocos(leituras)              retira os 12 blocos E VOLTA PARA A
                                        PAREDE                 (ja existe)
    entregar_blocos_parte4.executar()   <-- ESTE ARQUIVO
    (entrega em si)                     devolve os 12 blocos no mosaico
                                        - EM REESCRITA, ver "O QUE FALTA"

Roda de dois jeitos, igual as outras partes:

    F5 neste arquivo  -> executa so este trecho, com o robo posto a mao na
                         largada descrita abaixo
    prog1.py          -> chamado na sequencia da prova

DE ONDE O ROBO VEM (fim do pegar_blocos):

    posicao  : ENCOSTADO NA PAREDE do tapete de blocos, o mesmo ponto de
               largada da etapa anterior. O realinhamento morava AQUI e
               foi para o fim do pegar_blocos: e ele que sabe em que
               coluna parou, entao e ele que consegue voltar andando so o
               que falta, em vez de supor a pior distancia. Por isso
               executar() nao recebe mais `posicao_mm` - o ponto de
               partida e sempre o mesmo.
    carrinho : na PROFUNDIDADE do ultimo bloco pego - o pegar_blocos volta
               para la depois de cada arremesso, para tirar a garra de
               baixo das colunas antes de descer. Qual das tres depende da
               rodada, e por isso a primeira coisa daqui e RECOLHER ele
               contra o batente: o percurso abaixo tem curva e seguidor de
               linha, e com o carrinho para fora ele bate.
    garra    : embaixo (o pegar_blocos desce ela no fim do ciclo de cada
               bloco, ja fora da posicao de arremesso)

O QUE FALTA (ver prog1.py, item 2 da lista "ainda faltam"): a entrega em
si - a antiga entregar_blocos.py foi removida de proposito para ser
reescrita do zero.

A antiga entregar_blocos.py media alinhamento pelo ROBO (colunas fixas no
topo, quem anda e o chassi) e as 3 colunas de armazenagem como FILA - se
a reescrita mudar essa decisao, atualize tambem a docstring do
pegar_blocos.py, que depende da mesma ordem.
"""

from pybricks.parameters import Stop
from pybricks.tools import wait

import movimento as m
import linha as lin
import servos_segurar as sg
from setup import ev3, motor_A, motor_C


# =============================================================================
# OS NUMEROS DESTE TRECHO
# =============================================================================

# --- Recolhimento do carrinho, contra o batente de casa ---
# O robo chega aqui com o carrinho na profundidade do ultimo bloco pego, e
# o percurso abaixo passa por curvas e por seguidor de linha - com o
# carrinho para fora ele bate e desequilibra. Gira ate travar e SEGURA.
#
# NAO E UMA ZERAGEM: nao ha reset_angle aqui, porque nada neste arquivo
# conta graus a partir do batente. Quem zera e o pegar_blocos, na abertura
# dele, e e por isso que os numeros nao sao compartilhados com os de la.
#
#   trava antes de chegar no batente  -> aumente a FORCA
#   estala / range ao bater           -> diminua a VELOCIDADE
V_RECOLHER     = -350   # graus/s, negativo = recolhe
FORCA_RECOLHER = 50     # duty_limit em %

# --- O recuo que acontece ENTRE abrir e fechar o servo dos blocos ---
# Devagar de proposito: sao 40 mm, e o robo esta com o bloco ja solto
# atras dele. Acelerar/frear forte aqui arrasta o que acabou de sair.
#
# A DISTANCIA nao mora aqui: ela esta escrita na propria linha do
# m.andar(), la embaixo, junto do movimento que ela descreve.
ANDAR_SOLTAR = dict(v_max=150, v_min=100, acel=500, desacel=500,
                    kp=2.5, kd=3.5)


def executar():
    """
    Leva o robo do tapete de blocos de volta ao mosaico.

    LARGADA: o robo chega ENCOSTADO NA PAREDE do tapete de blocos - quem
    faz a volta e o encosto e o proprio pegar_blocos, no fim dele. Por
    isso esta funcao nao recebe posicao nenhuma: o ponto de partida e
    sempre o mesmo, e ja esta alinhado contra algo fisico.

    A GARRA ja chega embaixo (o pegar_blocos desce ela no fim do ciclo de
    cada bloco). O CARRINHO chega estendido, e a primeira coisa aqui e
    recolher ele.

    TERMINA SOLTANDO QUATRO BLOCOS, um por fileira: recua ate a fileira,
    abre o servo dos blocos, fecha de novo - quatro vezes. Sai da funcao
    com o servo ABERTO, para nao ficar segurando nada depois da entrega.
    """
    # o carrinho volta para casa antes de o robo sair andando em curva
    motor_A.run_until_stalled(V_RECOLHER, then=Stop.HOLD,
                              duty_limit=FORCA_RECOLHER)

    m.girar_pivo(motor_C, -30, v_max=900, acel=800, desacel=1600,
                 kp=2.4, kd=7.33)
    m.andar(370, v_max=1000, v_min=300, acel=1000, desacel=1000,
            kp=2.5, kd=3.5)
    m.girar_eixo(-60, v_max=700, desacel=1200, kp=2.5, kd=7)
    motor_A.run_angle(1000, 1100)
    motor_A.run_angle(-1000, 210)
    lin.seguir_linha(parar_se=[lin.cruzamento()], kp=1.5, kd=13,
                     v_max=900, desacel=1000, tempo_ms=5000, ignorar_mm=200)
    m.andar(60, v_max=800, v_min=100, acel=1000, desacel=1000,
            kp=2.5, kd=3.5)
    m.girar_eixo(-180, v_max=700, desacel=1200, kp=2.5, kd=7)
    m.andar(-270, v_max=800, v_min=100, acel=1000, desacel=1000,
            kp=2.5, kd=3.5)

    # SOLTA OS QUATRO BLOCOS, um por fileira. Cada volta e a mesma coisa:
    # recua ate a fileira, abre o servo (o bloco cai), fecha de novo antes
    # de andar para a proxima.
    #
    # AS PAUSAS NAO SAO ESPERA DE SERVO - disso o servos_segurar.py ja
    # cuida, esperando o Arduino confirmar o fim do movimento. Elas sao o
    # tempo de o BLOCO cair e assentar, que o Arduino nao tem como saber.
    #
    # Os dois comandos sao do SEGUNDO servo do Arduino (servos_segurar.py),
    # nao do seletor de coluna. Se abrir e fechar estiverem trocados, ou se
    # o curso estiver grande demais, os angulos ficam no
    # arduino_servos.ino - nao aqui.
    #
    # O ROBO SO ANDA COM OS DOIS SERVOS PARADOS: os comandos esperam a
    # confirmacao do Arduino antes de devolver o controle, entao a andada
    # da volta seguinte comeca com o servo ja no lugar.
    for _ in range(4):
        m.andar(-51, **ANDAR_SOLTAR)
        wait(200)
        sg.liberar()
        wait(500)
        sg.segurar()
        wait(200)

    m.andar(-150, v_max=1000, v_min=200, acel=1000, desacel=1000,
            kp=2.5, kd=3.5)
    sg.liberar()

if __name__ == "__main__":
    executar()
    ev3.speaker.beep()
