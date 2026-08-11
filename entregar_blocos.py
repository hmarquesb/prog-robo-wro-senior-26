#!/usr/bin/env pybricks-micropython
"""
entregar_blocos.py - Entrega dos blocos no mosaico
==================================================

Ultima etapa: esvazia as 3 colunas de armazenagem do robo - que o
pegar_blocos.py encheu - de volta no mosaico, um bloco em cada celula.

O ROBO ENTREGA DE COSTAS. A leitura (leitura_blocos.py) varre o mosaico
avancando da fileira 1 para a 4; a entrega volta por cima, da fileira 4
para a 1, andando de RE entre uma fileira e outra. Por isso as 3 ULTIMAS
cores lidas sao as 3 PRIMEIRAS entregues.

Dentro de cada fileira a ordem e a MESMA em que foi lida - so a ordem das
FILEIRAS inverte:

    leitura :  0  1  2 | 3  4  5 | 6  7  8 |  9 10 11
    entrega :  9 10 11 | 6  7  8 | 3  4  5 |  0  1  2

Isso preserva o zigue-zague de graca. A varredura terminou a fileira 4 na
coluna 1, e a entrega comeca a fileira 3 na coluna 1 - o carrinho nunca
atravessa o mosaico a toa:

    fileira 4 (indices  9, 10, 11) : coluna 3 -> 2 -> 1
    fileira 3 (indices  6,  7,  8) : coluna 1 -> 2 -> 3
    fileira 2 (indices  3,  4,  5) : coluna 3 -> 2 -> 1
    fileira 1 (indices  0,  1,  2) : coluna 1 -> 2 -> 3

O INVARIANTE QUE FAZ ISSO FUNCIONAR: nessa ordem, cada coluna de
armazenagem e esvaziada na ordem EXATAMENTE INVERSA a que o pegar_blocos
a encheu. A coluna 1 foi carregada na ordem [0, 5, 6, 11] e e entregue em
11, 6, 5, 0; a coluna 2 foi [1, 4, 7, 10] e sai 10, 7, 4, 1; a coluna 3
foi [2, 3, 8, 9] e sai 9, 8, 3, 2.

Ou seja: as colunas do robo se comportam como PILHA - o ultimo bloco que
entrou e o primeiro que sai. Nao ha nada a fazer para conseguir isso, ele
cai pronto da ordem das fileiras; mas se um dia alguem mexer em
FILEIRAS_ENTREGA ou em COLUNAS_MOSAICO, e ISSO que tem de continuar
valendo, senao os blocos saem trocados de celula. O teste no fim do
arquivo confere esse invariante sem o robo se mexer.

FALTA O MECANISMO: soltar_bloco() e um PLACEHOLDER. O robo ainda nao tem
como liberar um bloco da coluna de armazenagem - quando tiver, e so essa
funcao que muda. Todo o resto (ordem, percurso, posicoes) ja esta aqui.

As distancias/posicoes abaixo sao PLACEHOLDERS - MEDIR COM REGUA /
ajustar no robo real.
"""
from setup import ev3, wait
import movimento as m
import carrinho as c
from pegar_blocos import COLUNAS_MOSAICO


# =============================================================================
# 1. CONFIGURACAO (medir com regua / calibrar no robo)
# =============================================================================

# --- Ordem de entrega: as 4 fileiras do mosaico, da ULTIMA lida para a
# primeira, e dentro de cada uma os indices na ordem em que foram lidos.
#
# Os numeros sao indices da lista `leituras` que o leitura_blocos.py
# devolve. Mexer aqui muda a ordem da entrega inteira - e obriga a
# reconferir o invariante da pilha (ver o teste no fim do arquivo). ---
FILEIRAS_ENTREGA = (
    (9, 10, 11),   # fileira 4 - a ultima lida, a primeira entregue
    (6,  7,  8),   # fileira 3
    (3,  4,  5),   # fileira 2
    (0,  1,  2),   # fileira 1 - a primeira lida, a ultima entregue
)

# --- Posicao do carrinho (mm) em que cada coluna do mosaico fica debaixo
# do ponto de SOLTAR o bloco.
#
# Comecam iguais as posicoes de LEITURA do leitura_blocos.py
# (primeira_posicao / segunda_posicao / terceira_posicao), mas nao ha
# motivo para continuarem iguais: la o alvo era o sensor de cor, aqui e
# por onde o bloco cai. Se o mecanismo de soltar nao estiver no mesmo
# lugar do sensor, os tres valores mudam junto, pelo mesmo offset.
# PLACEHOLDER - MEDIR NO ROBO. ---
POSICAO_CARRINHO_COLUNA = {
    1: 25,
    2: 45,
    3: 95,
}

# Quanto o robo anda de RE de uma fileira para a anterior. Mesmo passo do
# `entre_movimentos` da leitura, so que negativo - a entrega desfaz o
# caminho da varredura. Se a leitura andou 45 mm por fileira, aqui e 45
# (o sinal entra na chamada, nao no valor). PLACEHOLDER.
ENTRE_FILEIRAS_MM = 45

V_ANDAR = dict(v_max=300, v_min=200, acel=300, desacel=3000, kp=1.9, kd=3.5)

V_CARRINHO_ENTREGA = 500


# =============================================================================
# 2. FUNCOES
# =============================================================================

def coluna_do_indice(indice, colunas=COLUNAS_MOSAICO):
    """
    Diz em qual coluna do mosaico (1, 2 ou 3) mora um indice da lista
    `leituras` - que e a mesma coluna de armazenagem do robo em que o
    pegar_blocos guardou aquele bloco.

    Le do COLUNAS_MOSAICO do pegar_blocos.py de proposito, em vez de ter
    uma tabela propria: a traducao indice -> coluna e a mesma nos dois
    programas, e duas copias um dia divergem.

    Devolve None se o indice nao estiver em coluna nenhuma (so acontece
    com indice fora de 0..11).
    """
    for coluna in (1, 2, 3):
        if indice in colunas[coluna]:
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
      - o robo esta PARADO em cima da fileira certa;
      - o carrinho esta parado em POSICAO_CARRINHO_COLUNA[coluna], ou
        seja, alinhado com a celula certa;
      - o bloco que tem de sair e o que entrou POR ULTIMO naquela coluna
        (as colunas esvaziam como pilha - ver o cabecalho do arquivo).

    O que ela nao pode fazer:
      - mover o robo (quem anda e o entregar_blocos);
      - deixar o carrinho fora da posicao em que o encontrou, senao a
        proxima celula sai deslocada.

    Por enquanto so avisa e segue, para dar para testar o PERCURSO e a
    ORDEM sem o mecanismo: o robo faz o caminho inteiro, para em cada
    celula e apita, e nenhum bloco cai.
    """
    print("  [soltar_bloco] coluna", coluna_armazenagem, "- NAO IMPLEMENTADO")
    ev3.speaker.beep(400, 80)
    wait(300)


def entregar_blocos(leituras,
                     fileiras=FILEIRAS_ENTREGA,
                     posicoes_carrinho=POSICAO_CARRINHO_COLUNA,
                     entre_fileiras_mm=ENTRE_FILEIRAS_MM,
                     velocidade_carrinho=V_CARRINHO_ENTREGA,
                     colunas_mosaico=COLUNAS_MOSAICO):
    """
    Devolve os 12 blocos ao mosaico, DE COSTAS: fileira 4, 3, 2, 1.

    `leituras` : a mesma lista de 12 cores que o leitura_blocos.py
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
    parte2.py liga o mosaico ao tapete.

    Por celula: leva o carrinho ate a coluna e solta. Ao trocar de
    fileira, anda de RE `entre_fileiras_mm`. A primeira fileira nao anda -
    o robo ja esta nela.

    O CARRINHO SO SE MEXE COM O ROBO PARADO, e o robo so anda com o
    carrinho parado. Nunca junte as duas coisas aqui: e a regra do
    carrinho.py, e no meio do mosaico um deslocamento de massa custa a
    celula inteira.
    """
    c.zerar_carrinho(velocidade=800, forca=90)

    for numero, fileira in enumerate(fileiras):
        if numero > 0:
            # de costas para a fileira anterior. O sinal esta aqui, e nao
            # em ENTRE_FILEIRAS_MM, para o valor continuar sendo uma
            # distancia comparavel com a da leitura.
            m.andar(-entre_fileiras_mm, **V_ANDAR)

        for indice in fileira:
            coluna = coluna_do_indice(indice, colunas_mosaico)
            print("fileira", len(fileiras) - numero,
                  "- celula", indice, "- coluna", coluna,
                  "- deveria cair", leituras[indice])
            c.mover_carrinho(posicoes_carrinho[coluna],
                             velocidade=velocidade_carrinho)
            soltar_bloco(coluna)


# =============================================================================
# 3. TESTE
# =============================================================================

if __name__ == "__main__":

    from pybricks.parameters import Color

    # Mesma lista de exemplo do pegar_blocos.py, para dar para acompanhar
    # os dois lado a lado.
    leituras_teste = [
        Color.YELLOW, Color.GREEN, Color.BLUE,
        Color.YELLOW, Color.GREEN, Color.WHITE,
        Color.BLUE, Color.YELLOW, Color.GREEN,
        Color.YELLOW, Color.BLUE, Color.YELLOW,
    ]

    # ---- TESTE 1: o invariante da pilha (sem o robo se mexer) -----------
    # Cada coluna TEM de ser entregue na ordem inversa a que foi
    # carregada, senao os blocos saem em celulas trocadas. Rode isto
    # sempre que mexer em FILEIRAS_ENTREGA ou em COLUNAS_MOSAICO.
    print("invariante da pilha (carregada x entregue):")
    tudo_ok = True
    for coluna_teste in (1, 2, 3):
        carregada = list(COLUNAS_MOSAICO[coluna_teste])
        entregue = []
        for fileira_teste in FILEIRAS_ENTREGA:
            for indice_teste in fileira_teste:
                if coluna_do_indice(indice_teste) == coluna_teste:
                    entregue.append(indice_teste)
        esperado = carregada[::-1]
        ok = entregue == esperado
        tudo_ok = tudo_ok and ok
        print("  coluna", coluna_teste, ":", carregada, "->", entregue,
              "OK" if ok else "ERRADO, esperado " + str(esperado))
    if not tudo_ok:
        ev3.speaker.beep(200, 500)
    print("invariante:", "OK" if tudo_ok else "QUEBRADO")
    wait(2000)

    # ---- TESTE 2: percurso e ordem, sem soltar nada ---------------------
    # Ponha o robo NA MAO em cima da fileira 4 do mosaico, na mesma
    # posicao em que a varredura o deixou. Ele vai fazer o caminho
    # inteiro, parar em cada uma das 12 celulas e apitar - o soltar_bloco
    # ainda nao solta nada.
    #
    # Confira duas coisas, com o mosaico do lado:
    #   1. as paradas caem MESMO em cima das celulas. Erradas em bloco,
    #      todas para o mesmo lado -> POSICAO_CARRINHO_COLUNA (as tres
    #      juntas). Erradas so em uma coluna -> so aquele valor;
    #   2. a fileira anda o passo certo. Se ele for acumulando erro de
    #      fileira em fileira, e o ENTRE_FILEIRAS_MM.
    entregar_blocos(leituras_teste)

    ev3.speaker.beep()
