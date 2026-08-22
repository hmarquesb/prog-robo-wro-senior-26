#!/usr/bin/env pybricks-micropython
"""
entregar_blocos.py - Entrega dos blocos no mosaico
==================================================

Ultima etapa: esvazia as 3 colunas de armazenagem do robo - que o
pegar_blocos.py encheu - de volta no mosaico, um bloco em cada celula.

QUEM ALINHA AQUI E O ROBO, NAO O CARRINHO. As 3 colunas de armazenagem
sao FIXAS no topo do robo: mover o carrinho nao as desloca nem um
milimetro em relacao ao mosaico. Entao, para deixar uma coluna em cima da
celula certa, quem anda e o CHASSI. Este arquivo nunca mexe no motor_A.

    varredura (parte 2)         : quem atravessa o mosaico e o CARRINHO,
                                  porque os sensores andam nele
    entrega   (este arquivo)    : quem atravessa e o ROBO, porque as
                                  colunas nao andam

O ROBO ENTREGA DE COSTAS, da fileira 4 para a 1, andando de RE entre uma
fileira e outra.

A VARREDURA LE POR COLUNA e a ENTREGA ANDA POR FILEIRA. Sao eixos
diferentes, entao a lista de leituras nao e percorrida em ordem: cada
fileira da entrega junta um indice de cada coluna lida.

    leitura :  0  1  2  3 |  4  5  6  7 |  8  9 10 11
    coluna  :  1  1  1  1 |  2  2  2  2 |  3  3  3  3
    fileira :  1  2  3  4 |  4  3  2  1 |  1  2  3  4

    entrega, fileira 4 :  3 (c1)   4 (c2)  11 (c3)
             fileira 3 : 10 (c3)   5 (c2)   2 (c1)
             fileira 2 :  1 (c1)   6 (c2)   9 (c3)
             fileira 1 :  8 (c3)   7 (c2)   0 (c1)

Dentro da fileira a ordem alterna, para o robo terminar uma fileira ja em
cima da coluna onde a proxima comeca - sem atravessar o mosaico a toa.

O INVARIANTE QUE FAZ ISSO FUNCIONAR: nessa ordem, cada coluna de
armazenagem e esvaziada na ordem EXATAMENTE INVERSA a que o pegar_blocos
a encheu:

    coluna 1 : carregada [0, 1, 2, 3]  ->  entregue 3, 2, 1, 0
    coluna 2 : carregada [7, 6, 5, 4]  ->  entregue 4, 5, 6, 7
    coluna 3 : carregada [8, 9, 10, 11] -> entregue 11, 10, 9, 8

Ou seja: as colunas do robo se comportam como PILHA - o ultimo bloco que
entrou e o primeiro que sai. Isso cai pronto da ordem das fileiras; mas
se um dia alguem mexer em FILEIRAS, em cte.COLUNAS_MOSAICO ou na ordem da
varredura, e ISSO que tem de continuar valendo, senao os blocos saem
trocados de celula. O TESTE 1 confere esse invariante sem o robo se
mexer - RODE-O depois de qualquer mudanca nos tres.

FALTA O MECANISMO: soltar_bloco() e um PLACEHOLDER. O robo ainda nao tem
como liberar um bloco da coluna de armazenagem - quando tiver, e so essa
funcao que muda. Todo o resto (ordem, percurso, posicoes) ja esta aqui.
"""

from pybricks.tools import wait

import constantes as cte
import movimento as m
from setup import ev3


# =============================================================================
# OS NUMEROS DESTA ETAPA  (medir com regua / calibrar no robo)
# =============================================================================

# --- Ordem de entrega: as 4 fileiras do mosaico, da fileira 4 para a 1,
# e dentro de cada uma os indices na ordem em que o robo passa por elas.
#
# Os numeros sao indices da lista `leituras`. A varredura le uma COLUNA
# de cada vez, entao cada fileira aqui junta um indice de cada coluna:
#
#     fileira 4 :  3 (c1)   4 (c2)  11 (c3)
#     fileira 3 :  2 (c1)   5 (c2)  10 (c3)
#     fileira 2 :  1 (c1)   6 (c2)   9 (c3)
#     fileira 1 :  0 (c1)   7 (c2)   8 (c3)
#
# DENTRO DA FILEIRA a ordem alterna (c1->c2->c3, depois c3->c2->c1, e
# assim por diante): o robo termina uma fileira ja em cima da coluna onde
# a proxima comeca, e nao atravessa o mosaico a toa. Isso NAO afeta o
# invariante da pilha - so a distancia percorrida.
#
# Mexer aqui muda a ordem da entrega inteira - e obriga a reconferir o
# invariante da pilha (TESTE 1). ---
FILEIRAS = (
    (3,  4, 11),   # fileira 4 - a primeira entregue.  c1 -> c2 -> c3
    (10, 5,  2),   # fileira 3                         c3 -> c2 -> c1
    (1,  6,  9),   # fileira 2                         c1 -> c2 -> c3
    (8,  7,  0),   # fileira 1 - a ultima entregue.    c3 -> c2 -> c1
)

# --- Quanto o ROBO anda para deixar cada coluna de armazenagem em cima
# da celula certa, em mm, relativo ao inicio da fileira.
#
# SAO POSICOES DO ROBO, e nao do carrinho: as colunas sao fixas no topo,
# entao quem se desloca de uma celula a outra e o chassi inteiro.
#
# SE AS 3 COLUNAS DO ROBO JA ESTIVEREM ESPACADAS COMO AS 3 DO MOSAICO,
# ponha os tres em 0: o robo para uma vez por fileira e solta os tres
# blocos sem andar entre eles. Foi para deixar essa escolha aberta que os
# valores sao tres numeros, e nao um passo unico.
#
# PLACEHOLDERS - MEDIR NO ROBO (TESTE 2). ---
POSICAO_ROBO_COLUNA = {
    1: 0,
    2: 45,
    3: 90,
}

# Quanto o robo anda de RE de uma fileira para a anterior. E o mesmo passo
# que a leitura andou para a frente - a entrega desfaz o caminho da
# varredura. O sinal entra na conta, nao no valor.
ENTRE_FILEIRAS_MM = 50

# Passos curtos em cima do mosaico, freando forte: cada celula e pequena
# e o erro de uma fileira se soma na proxima.
ANDAR_ENTREGA = dict(v_max=300, v_min=200, acel=300, desacel=3000,
                     kp=1.9, kd=3.5)


# =============================================================================
# 1. FUNCOES
# =============================================================================

def coluna_do_indice(indice):
    """
    Diz em qual coluna do mosaico (1, 2 ou 3) mora um indice da lista
    `leituras` - que e a mesma coluna de armazenagem do robo em que o
    pegar_blocos guardou aquele bloco.

    Le do cte.COLUNAS_MOSAICO de proposito, em vez de ter uma tabela
    propria: a traducao indice -> coluna e a mesma que o pegar_blocos.py
    usa, e duas copias um dia divergem.

    Devolve None se o indice nao estiver em coluna nenhuma (so acontece
    com indice fora de 0..11).
    """
    for coluna in (1, 2, 3):
        if indice in cte.COLUNAS_MOSAICO[coluna]:
            return coluna
    return None


def soltar_bloco(coluna_armazenagem):
    """
    PLACEHOLDER - O MECANISMO AINDA NAO EXISTE.

    Tem de liberar UM bloco da coluna de armazenagem `coluna_armazenagem`
    (1, 2 ou 3) para o mosaico, e voltar deixando a coluna pronta para
    soltar o proximo.

    Quando for escrita, ela e o UNICO ponto deste arquivo que muda - a
    ordem, o percurso e as posicoes ja estao prontos em volta dela.

    O que ela pode contar quando e chamada:
      - o robo esta PARADO com aquela coluna em cima da celula certa;
      - o bloco que tem de sair e o que entrou POR ULTIMO naquela coluna
        (as colunas esvaziam como pilha - ver o cabecalho do arquivo).

    O que ela nao pode fazer:
      - mover o robo (quem anda e o entregar_blocos);
      - mexer no motor_A. O carrinho nao participa da entrega, e move-lo
        nao desloca as colunas - elas sao fixas.

    Por enquanto so avisa e segue, para dar para testar o PERCURSO e a
    ORDEM sem o mecanismo: o robo faz o caminho inteiro, para em cada
    celula e apita, e nenhum bloco cai.
    """
    print("  [soltar_bloco] coluna", coluna_armazenagem, "- NAO IMPLEMENTADO")
    ev3.speaker.beep(400, 80)
    wait(300)


def entregar_blocos(leituras):
    """
    Devolve os 12 blocos ao mosaico, DE COSTAS: fileira 4, 3, 2, 1.

    `leituras` : a mesma lista de 12 cores que a leitura (parte 2)
                 devolveu e o pegar_blocos.py consumiu. Aqui ela so serve
                 para IMPRIMIR o que deveria estar caindo em cada celula -
                 quem decide de qual coluna o bloco sai e a posicao dele
                 na lista, nao a cor. Passe a lista mesmo assim: e ela que
                 permite conferir a entrega olhando o terminal.

    PRESSUPOE:
      - o robo parado em cima da FILEIRA 4 do mosaico (a ultima lida),
        alinhado como estava na varredura, so que de costas para o
        caminho da entrega;
      - as 3 colunas de armazenagem cheias, na ordem que o pegar_blocos
        as encheu;
      - a garra fora do caminho (ela nao participa da entrega).

    Chegar nessa posicao NAO e trabalho deste arquivo - e do percurso que
    liga o tapete de blocos de volta ao mosaico, do mesmo jeito que o
    parte3.py liga o mosaico ao tapete.

    COMO O ROBO SE MOVE. Ele guarda UMA posicao absoluta ao longo do eixo
    da entrega, e cada celula e um alvo nesse eixo:

        alvo = base da fileira + POSICAO_ROBO_COLUNA[coluna]

    A base da fileira anda ENTRE_FILEIRAS_MM de RE a cada troca de
    fileira. Como as duas coisas entram no mesmo alvo, ha UM andar por
    celula - a troca de fileira e a de coluna acontecem no mesmo
    movimento, sem um desfazer o outro.

    O MOTOR_A NAO E TOCADO EM LUGAR NENHUM desta funcao. O carrinho pode
    estar onde o percurso de volta o deixou; ele nao muda nada aqui.
    """
    posicao_mm = 0        # onde o robo esta no eixo da entrega
    base_fileira = 0      # onde comeca a fileira atual

    for numero, fileira in enumerate(FILEIRAS):
        if numero > 0:
            # de costas para a fileira anterior. O sinal esta aqui, e nao
            # em ENTRE_FILEIRAS_MM, para o valor continuar sendo uma
            # distancia comparavel com a da leitura.
            base_fileira -= ENTRE_FILEIRAS_MM

        for indice in fileira:
            coluna = coluna_do_indice(indice)
            alvo_mm = base_fileira + POSICAO_ROBO_COLUNA[coluna]

            print("fileira", len(FILEIRAS) - numero,
                  "- celula", indice, "- coluna", coluna,
                  "- deveria cair", leituras[indice])

            if alvo_mm != posicao_mm:
                m.andar(alvo_mm - posicao_mm, **ANDAR_ENTREGA)
                posicao_mm = alvo_mm

            soltar_bloco(coluna)


# =============================================================================
# 2. TESTES
# =============================================================================
# Mude o numero de TESTE la embaixo e rode este arquivo com F5.
#
#   1 -> o invariante da pilha, sem o robo se mexer
#   2 -> o percurso e a ordem, sem soltar nada

def _teste_1_invariante():
    """
    Cada coluna TEM de ser entregue na ordem inversa a que foi carregada,
    senao os blocos saem em celulas trocadas. Rode isto sempre que mexer
    em FILEIRAS ou em cte.COLUNAS_MOSAICO.

    Nao mexe no robo: e so conta.
    """
    print("invariante da pilha (carregada x entregue):")
    tudo_ok = True
    for coluna in (1, 2, 3):
        carregada = list(cte.COLUNAS_MOSAICO[coluna])
        entregue = []
        for fileira in FILEIRAS:
            for indice in fileira:
                if coluna_do_indice(indice) == coluna:
                    entregue.append(indice)
        esperado = carregada[::-1]
        ok = entregue == esperado
        tudo_ok = tudo_ok and ok
        print("  coluna", coluna, ":", carregada, "->", entregue,
              "OK" if ok else "ERRADO, esperado " + str(esperado))
    if not tudo_ok:
        ev3.speaker.beep(200, 500)
    print("invariante:", "OK" if tudo_ok else "QUEBRADO")
    wait(2000)


def _teste_2_percurso():
    """
    Ponha o robo NA MAO em cima da fileira 4 do mosaico, na mesma posicao
    em que a varredura o deixou. Ele vai fazer o caminho inteiro, parar
    em cada uma das 12 celulas e apitar - o soltar_bloco ainda nao solta
    nada.

    Confira duas coisas, com o mosaico do lado:
      1. as paradas caem MESMO em cima das celulas. Erradas em bloco,
         todas para o mesmo lado -> POSICAO_ROBO_COLUNA (os tres juntos).
         Erradas so em uma coluna -> so aquele valor;
      2. a fileira anda o passo certo. Se ele for acumulando erro de
         fileira em fileira, e o ENTRE_FILEIRAS_MM.
    """
    entregar_blocos(cte.LEITURAS_TESTE)


if __name__ == "__main__":

    TESTE = 1

    if TESTE == 1:
        _teste_1_invariante()
    else:
        _teste_2_percurso()

    ev3.speaker.beep()
