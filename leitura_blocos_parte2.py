#!/usr/bin/env pybricks-micropython
"""
leitura_blocos_parte2.py - Leitura do mosaico
=============================================

Varre o mosaico e devolve as 12 cores, na ordem de varredura. E essa
lista que o pegar_blocos.py consome (ver COLUNAS_MOSAICO no
constantes.py, que traduz a ordem de varredura para "as 4 cores da
coluna 1", etc.).

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

A VARREDURA E POR COLUNA, e nao por fileira, e comeca pela DIREITA:

    coluna 3 (direita)  : o robo AVANCA lendo as 4 fileiras
    coluna 2 (meio)     : o robo VOLTA lendo as 4, de tras para a frente
    coluna 1 (esquerda) : o robo AVANCA de novo lendo as 4

O carrinho so muda de coluna DUAS VEZES na rodada inteira (uma por
troca), em vez de tres vezes por fileira. Quem faz o vaivem e o robo.

    indice :  0  1  2  3 |  4  5  6  7 |  8  9 10 11
    coluna :  3  3  3  3 |  2  2  2  2 |  1  1  1  1
    fileira:  1  2  3  4 |  4  3  2  1 |  1  2  3  4

ESSA TABELA E O CONTRATO com o resto do programa. Mexer na ordem dos
PASSOS obriga a mexer junto em COLUNAS_MOSAICO (constantes.py) e em
FILEIRAS (entregar_blocos.py) - senao os blocos saem em celulas
trocadas. O TESTE 1 do entregar_blocos.py confere se os tres continuam
combinando, sem o robo se mexer.

O ZERO DO CARRINHO E O FIM DO CURSO, e nao o batente de casa. Antes de
entrar no mosaico o carrinho ABRE TUDO contra o batente e aquele ponto
vira o 0. As tres colunas sao alvos NEGATIVOS a partir dali - elas dizem
quanto o carrinho recolhe:

    0      todo aberto
    -250   coluna 3 (direita)
    -400   coluna 2 (meio)
    -550   coluna 1 (esquerda)

Zerar na abertura, e nao em casa, poe a referencia do lado ONDE A
VARREDURA ACONTECE: a folga da correia fica toda para o lado de casa, que
a leitura nao usa. UM ALVO POSITIVO aqui nao recolhe nada - manda abrir
alem do batente, e o motor fica empurrando o fim do curso parado.

DA PARA PULAR A LEITURA INTEIRA: com cte.PULAR_LEITURA = True o robo
ATRAVESSA o mosaico numa andada so - sem parar em fileira nenhuma, sem
mexer no carrinho e sem ler sensor - e o ler_mosaico() devolve as 12
cores escritas na mao em cte.LEITURAS_MANUAIS. O robo para no MESMO ponto
de sempre, entao o parte3 e tudo o que vem depois nao mudam nada. Serve
para testar a retirada e a entrega sem depender do sensor de cor, e para
rodar com o mosaico digitado a mao se a leitura estiver falhando.

As cores saem do sensor.color() cru, e nao do lin.ler() - aqui interessa
QUAL cor e, nao quanto reflete, entao a calibracao do seguidor de linha
nao entra nessa conta. Ela ainda importa para o seguir_linha do comeco.

Os numeros deste trecho ficam logo abaixo, neste arquivo.
"""

from pybricks.parameters import Stop
from pybricks.tools import wait
import constantes as cte
import movimento as m
import linha as lin
from setup import ev3, motor_A, sensor_esq, sensor_dir


# =============================================================================
# OS NUMEROS DESTE TRECHO
# =============================================================================

# --- Posicoes do carrinho, em GRAUS do motor_A, em que cada coluna do
# mosaico fica debaixo do SENSOR DE COR ---
#
# O ZERO E O CARRINHO TODO ABERTO, e nao o batente de casa: a varredura
# abre tudo contra o fim do curso e chama aquele ponto de 0. Por isso as
# tres sao NEGATIVAS - elas dizem quanto o carrinho RECOLHE a partir do
# fim do curso.
#
#     0      carrinho todo aberto (o batente)
#    -250    coluna 3, a direita  - a mais perto do fim do curso
#    -400    coluna 2, o meio
#    -550    coluna 1, a esquerda - a que mais recolhe
#
# UM VALOR POSITIVO AQUI NAO RECOLHE NADA: manda o carrinho abrir alem do
# batente, e o motor fica empurrando o fim do curso sem sair do lugar.
#
# Sao posicoes DO CARRINHO: os dois sensores andam com ele.
#
# PLACEHOLDER - MEDIR NO ROBO. O espacamento de 150 saiu dos valores
# antigos (que eram contados da casa); confira se as tres celulas ficam
# igualmente espacadas.
COLUNA_3 = -270
COLUNA_2 = -1050
COLUNA_1 = -1400

V_CARRINHO = 1000     # graus/s do motor_A na varredura

# --- Abertura ate o fim do curso: e ela que define o ZERO ---
# Roda uma vez, antes da varredura. Abrir contra o batente e mais
# confiavel que confiar num alvo em graus: a referencia vira mecanica e
# nao acumula a folga da correia.
V_ABRIR     = 1000     # graus/s contra o batente do fim do curso
FORCA_ABRIR = 80      # duty_limit em %

# --- Percurso ---
# Quanto o robo anda de uma fileira do mosaico para a proxima. O SINAL
# entra na tabela de PASSOS, nao aqui: na coluna 2 ele e negativo, porque
# a leitura volta.
ENTRE_FILEIRAS_MM = 40

ENTRADA_MOSAICO_MM = 155   # entra em cima da primeira fileira

AVANCO_FINAL_MM = 200   # sai de cima do mosaico

# Em cima do mosaico: devagar e freando forte, porque cada celula e
# pequena e o erro de uma fileira se soma na proxima.
ANDAR_MOSAICO = dict(v_max=300, v_min=200, acel=300, desacel=3000,
                     kp=2.0, kd=3.5)


# Cada passo da varredura: (tipo de movimento, valor, sensor a ler
# depois, rotulo).
#
#   "carrinho"  leva o motor_A a uma posicao ABSOLUTA, contada do
#               carrinho todo aberto. Sempre NEGATIVA (recolhe).
#   "andar"     move o ROBO `valor` mm  (negativo = de re)
#
# O rotulo e "c<coluna> f<fileira>", para o print bater com o mosaico que
# voce tem na frente.
PASSOS = [
    # --- COLUNA 3 (direita): a PRIMEIRA lida, e a que menos recolhe ----
    # O carrinho ja esta todo aberto quando o laco comeca, entao este
    # primeiro passo e so o recuo ate a coluna 3.
    ("carrinho", COLUNA_3, sensor_dir, "c3 f1"),
    ("andar",  ENTRE_FILEIRAS_MM, sensor_dir, "c3 f2"),
    ("andar",  ENTRE_FILEIRAS_MM, sensor_dir, "c3 f3"),
    ("andar",  ENTRE_FILEIRAS_MM, sensor_dir, "c3 f4"),

    # --- COLUNA 2 (meio): VOLTA lendo, da fileira 4 para a 1 -----------
    # O carrinho troca de coluna com o robo ja parado na fileira 4.
    ("carrinho", COLUNA_2, sensor_dir, "c2 f4"),
    ("andar", -ENTRE_FILEIRAS_MM, sensor_dir, "c2 f3"),
    ("andar", -ENTRE_FILEIRAS_MM, sensor_dir, "c2 f2"),
    ("andar", -ENTRE_FILEIRAS_MM, sensor_dir, "c2 f1"),

    # --- COLUNA 1 (esquerda): avanca lendo as 4 fileiras ---------------
    ("carrinho", COLUNA_1, sensor_esq, "c1 f1"),
    ("andar",  ENTRE_FILEIRAS_MM, sensor_esq, "c1 f2"),
    ("andar",  ENTRE_FILEIRAS_MM, sensor_esq, "c1 f3"),
    ("andar",  ENTRE_FILEIRAS_MM, sensor_esq, "c1 f4"),
]


def ler_mosaico(passos=PASSOS):
    """
    Varre o mosaico e devolve a lista das 12 cores, na ordem da varredura.

    Pressupoe o robo onde a parte1 o deixou, e a garra fora do caminho.

    O CARRINHO ABRE TUDO E ZERA ALI, logo depois do seguidor de linha e
    antes de entrar no mosaico. Daquele ponto em diante as tres COLUNA_*
    sao alvos absolutos negativos - o carrinho so recolhe durante a
    varredura inteira, nunca abre de novo.

    O robo termina na FILEIRA 4 (a varredura da coluna 1 avanca de novo),
    que e de onde o AVANCO_FINAL_MM o tira.

    E a lista devolvida que o pegar_blocos.pegar_blocos() recebe.

    COM cte.PULAR_LEITURA LIGADO nada disso acontece: o robo ATRAVESSA o
    mosaico numa andada so e devolve as cores escritas na mao em
    cte.LEITURAS_MANUAIS. Ver o bloco logo abaixo.
    """
    # --- ATALHO: passar reto pelo mosaico, sem ler ---------------------
    # Nao zera o carrinho, nao troca de coluna, nao le sensor nenhum: so
    # anda a MESMA distancia total que a varredura andaria, para largar o
    # robo no mesmo ponto de sempre - o parte3 comeca de la.
    #
    # A distancia sai somada dos proprios PASSOS, e nao escrita a mao, para
    # nao ficar para tras quando a tabela mudar. Os passos "carrinho" nao
    # movem o robo e ficam de fora; os da coluna 2 sao negativos e se
    # cancelam com a ida, entao a conta hoje da 155 + 120 - 120 + 120 + 200.
    #
    # Vai numa andada so, e nao em dez: dentro do mosaico nao ha nada para
    # acertar por fileira, e um movimento longo erra menos que dez curtos.
    if cte.PULAR_LEITURA:
        distancia = ENTRADA_MOSAICO_MM + AVANCO_FINAL_MM
        for tipo, valor, sensor, nome in passos:
            if tipo == "andar":
                distancia += valor

        print("PULAR_LEITURA ligado - atravessa", distancia,
              "mm sem ler e usa as cores da mao")
        m.andar(distancia, **ANDAR_MOSAICO)
        return list(cte.LEITURAS_MANUAIS)

    motor_A.run_until_stalled(V_ABRIR, then=Stop.HOLD, duty_limit=FORCA_ABRIR)
    motor_A.reset_angle(0)
    
    m.andar(ENTRADA_MOSAICO_MM, **ANDAR_MOSAICO)  # entra na primeira fileira

    leituras = []
    for tipo, valor, sensor, nome in passos:

        if tipo == "carrinho":
            motor_A.run_target(V_CARRINHO, valor)
        else:
            m.andar(valor, **ANDAR_MOSAICO)
            wait(30)
        cor = sensor.color()
        print(len(leituras), nome, ":", cor)
        leituras.append(cor)

    m.andar(AVANCO_FINAL_MM, **ANDAR_MOSAICO)
    
    return leituras


if __name__ == "__main__":
    leituras = ler_mosaico()
    print(leituras)
    ev3.speaker.beep()
