#!/usr/bin/env pybricks-micropython
"""
entregar_blocos_parte4.py - Do tapete de blocos de volta ao mosaico (INICIO)
=============================================================================

O trecho que comeca o "percurso que falta" citado no prog1.py: tapete de
blocos -> mosaico, para a entrega poder comecar.

    pegar_blocos(leituras)              retira os 12 blocos    (ja existe)
    entregar_blocos_parte4.executar(posicao_mm)  <-- ESTE ARQUIVO (so o
                                        realinhamento, ver "O QUE FALTA")
    (entrega em si)                     devolve os 12 blocos no mosaico
                                        - EM REESCRITA, ver "O QUE FALTA"

Roda de dois jeitos, igual as outras partes:

    F5 neste arquivo  -> executa so este trecho, com POSICAO_TESTE la
                         embaixo no lugar do valor que o pegar_blocos
                         devolveria
    prog1.py          -> chamado na sequencia da prova, com a posicao de
                         verdade que pegar_blocos() devolveu

DE ONDE O ROBO VEM (fim do pegar_blocos):

    posicao  : em cima de QUALQUER UMA das 8 colunas do tapete - o
               pegar_blocos anda e volta pelo tapete, entao a ultima
               coluna visitada depende da leitura do mosaico daquela
               rodada, nao e sempre a mesma. E POR ISSO que executar()
               recebe `posicao_mm`: sem ela, so restaria supor a pior
               distancia possivel e andar o mesmo tempo sempre, mesmo
               quando o robo parou logo na primeira coluna.
    carrinho : em cte.POSICAO_ARREMESSO (fixo, o pegar_blocos termina todo
               bloco ali) - NAO precisa recolher antes de andar: o robo ja
               anda com ele estendido desde a parte3 (virou peca impressa
               em 3D leve o bastante - README, regra 8).
    garra    : embaixo (guardar_bloco desce ela depois de cada arremesso)

DUAS ETAPAS, E CADA UMA RESOLVE UMA COISA DIFERENTE:

    1. `m.andar(-distancia, ...)` - PD de sincronismo, RAPIDO E PRECISO,
       usando a posicao que o pegar_blocos ja sabe. Cobre quase toda a
       volta sem gastar tempo de mais nem menos, mas SO ATE UMA MARGEM
       antes da parede - nunca a distancia inteira.
    2. `m.andar_por_tempo(...)` - cego, por TEMPO, so nessa margem que
       sobrou. E ESTA ETAPA QUE REALINHA DE VERDADE: e o CONTATO FISICO
       com a parede que zera o erro de odometria acumulado pelo
       pegar_blocos (README, regra 3 - sem gyro, a correcao vem de
       reencostar em algo fisico, nao de confiar no calculo).

POR QUE NAO FAZER TUDO NA ETAPA 1: se `posicao_mm` ja carrega erro
acumulado (e ele carrega - e o motivo de existir o realinhamento), um
andar() que tentasse fechar a distancia INTEIRA por calculo chegaria
exatamente nesse erro, sem corrigir nada. A margem que sobra para a etapa
2 e o que da ao robo alguma coisa de verdade para encostar.

POR QUE NAO FAZER TUDO NA ETAPA 2 (como a primeira versao deste arquivo
fazia): empurrar cego a distancia INTEIRA (ate 630 mm, hoje) por tempo
gasta mais bateria/tempo de prova que precisa, e passa mais tempo com as
rodas derrapando contra a parede no fim. Usar `posicao_mm` encurta isso
para so a margem.

O QUE FALTA (ver prog1.py, item 2 da lista "ainda faltam"): isto so
resolve o REALINHAMENTO contra a parede. Ainda falta:

    1. o percurso que leva o robo dali ate ficar em cima da FILEIRA 4 do
       mosaico;
    2. a entrega em si (a antiga entregar_blocos.py foi removida de
       proposito para ser reescrita do zero).

A antiga entregar_blocos.py media alinhamento pelo ROBO (colunas fixas no
topo, quem anda e o chassi) e as 3 colunas de armazenagem como FILA - se
a reescrita mudar essa decisao, atualize tambem a docstring do
pegar_blocos.py, que depende da mesma ordem.
"""

import movimento as m
from setup import ev3


# =============================================================================
# OS NUMEROS DESTE TRECHO
# =============================================================================

# --- Etapa 1: volta precisa, calculada a partir de posicao_mm ---
# So estes ganhos mudam a velocidade/suavidade dessa etapa - a DISTANCIA
# nao e um numero fixo daqui, e sim `posicao_mm - MARGEM_ENCOSTO_MM`,
# calculada dentro de executar().
ANDAR_VOLTA = dict(v_max=800, v_min=150, acel=900, desacel=1200,
                   kp=2.5, kd=3.5)

# Quanto FICA FALTANDO de proposito depois da etapa 1, para a etapa 2
# encostar de verdade. PLACEHOLDER - CALIBRAR NO ROBO.
#
#   etapa 1 already empurra a parede (sobra pouco tempo de deslizar
#   na etapa 2, ou nenhum)          -> AUMENTE a margem
#   etapa 2 demora muito girando as rodas no ar antes de tocar
#                                    -> diminua a margem
MARGEM_ENCOSTO_MM = 80

# --- Etapa 2: encosto cego, so na margem que sobrou ---
# PLACEHOLDER - CALIBRAR NO ROBO. O tempo tem de dar conta da MARGEM
# acima MAIS a folga do erro de odometria que a etapa 1 ainda carrega,
# mais um pouco de folga para a parede realmente parar o robo antes do
# tempo acabar.
V_ENCOSTAR        = -300    # graus/s do motor_B/motor_C, negativo = re
TEMPO_ENCOSTAR_MS = 1500

# Posicao usada quando este arquivo roda sozinho com F5 (sem pegar_blocos
# antes para fornecer a de verdade). Troque para testar outras distancias.
POSICAO_TESTE = 400


def executar(posicao_mm):
    """
    Reencosta o robo na parede do tapete de blocos, de re, para zerar o
    erro de odometria acumulado pelo pegar_blocos.

    `posicao_mm` : onde o pegar_blocos deixou o robo, em mm da parede - o
                   segundo valor que pegar_blocos() devolve. E o que
                   permite andar so o necessario em vez de supor sempre a
                   pior distancia (ver docstring do modulo).

    NAO MEXE NO CARRINHO NEM NA GARRA: os dois ja chegam prontos para
    andar (ver docstring do modulo).
    """
    # 1. volta precisa, ate uma MARGEM antes da parede - nunca a
    #    distancia inteira (ver "POR QUE NAO FAZER TUDO NA ETAPA 1").
    distancia_precisa = posicao_mm - MARGEM_ENCOSTO_MM
    if distancia_precisa > 0:
        m.andar(-distancia_precisa, **ANDAR_VOLTA)

    # 2. so a margem, as cegas por tempo - e o CONTATO FISICO desta etapa
    #    que realinha de verdade, nao o calculo da etapa 1.
    m.andar_por_tempo(TEMPO_ENCOSTAR_MS, V_ENCOSTAR)
    


if __name__ == "__main__":
    executar(POSICAO_TESTE)
    ev3.speaker.beep()
