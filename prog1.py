#!/usr/bin/env pybricks-micropython
"""
prog1.py - Programa da prova
============================

Emenda as partes do percurso na ordem em que elas acontecem na rodada:

    parte1.executar()          largada -> posicao de leitura
    ler_mosaico()              varre o mosaico -> 12 cores  (parte 2)
    parte3.executar()          mosaico -> tapete de blocos
    pegar_blocos(leituras)     retira os 12 blocos
    (percurso que falta)       tapete de blocos -> volta ao mosaico
    entregar_blocos(leituras)  devolve os 12 blocos no mosaico

E SO ISSO QUE ESTE ARQUIVO FAZ. Nenhum numero e nenhum movimento moram
aqui - cada parte traz os seus. Cada parte continua rodando sozinha com
F5 no arquivo dela, util para testar uma so sem repetir a rodada inteira.

A calibracao dos sensores tambem nao precisa de chamada: o linha.py
carrega CAL_SENSOR_ESQ / CAL_SENSOR_DIR do constantes.py no import.

AINDA FALTAM TRES COISAS PARA A RODADA INTEIRA (as etapas que dependem
delas estao comentadas ate ficarem prontas):

    1. o MECANISMO DE SOLTAR o bloco (soltar_bloco no entregar_blocos.py),
       que ainda nao existe no robo. Sem ele o entregar_blocos faz o
       caminho e apita em cada celula, mas nao entrega nada.
    2. o PERCURSO DE VOLTA do tapete de blocos ate o mosaico - o
       equivalente do parte3, na outra direcao. E o que poe o robo em
       cima da FILEIRA 4, que e de onde o entregar_blocos comeca (ele
       entrega de costas, da fileira 4 para a 1).
    3. a MISSAO DO QUADRILATERO TRASEIRO. Falta decidir ONDE na rodada
       ele desce. Ele e acionado pelo mesmo motor_A do carrinho, entao
       so pode se mexer com o robo parado e com o carrinho recolhido -
       e um motor_A.run_angle() escrito na parte que precisar dele.

PARA ACRESCENTAR UMA PARTE NOVA: escreva o arquivo dela com a sequencia
dentro de uma funcao (como parte1.executar), os numeros dela no proprio
arquivo, importe aqui e chame na posicao certa. Nao cole a sequencia aqui
dentro.
"""

from setup import ev3
import parte1
import leitura_blocos_parte2
import parte3
from pegar_blocos import pegar_blocos
from entregar_blocos import entregar_blocos


# --- 1. Percurso ate o mosaico -----------------------------------------
parte1.executar()

# --- 2. Leitura do mosaico ---------------------------------------------
# Devolve as 12 cores na ordem da varredura - a mesma ordem que o
# pegar_blocos.py espera receber.
leituras = leitura_blocos_parte2.ler_mosaico()
print("mosaico lido:", leituras)

# --- 3. Percurso ate o tapete de blocos --------------------------------
# Termina com o robo encostado na parede e o carrinho recolhido, que e
# exatamente a largada da etapa 4.
parte3.executar()

# --- 4. Retirada dos blocos --------------------------------------------
# O proprio pegar_blocos zera o carrinho contra o batente antes do
# primeiro bloco - e dali que saem as tres profundidades.
#
# Devolve a ORDEM EM QUE AS 3 COLUNAS DO ROBO FORAM ENCHIDAS. A entrega
# precisa disso: cada coluna e uma pilha, e tem de ser esvaziada na ordem
# inversa a que foi enchida.
carregadas = pegar_blocos(leituras)
print("colunas carregadas:", carregadas)

# --- 5. Volta ao mosaico -----------------------------------------------
# NAO EXISTE AINDA. Falta o percurso que leva o robo do tapete de blocos
# de volta para cima da FILEIRA 4 do mosaico - o parte3 ao contrario.
# Escreva num arquivo proprio (parte4.py) e chame aqui, como as outras
# partes; nao cole a sequencia dentro deste arquivo.

# --- 6. Entrega dos blocos ---------------------------------------------
# DESCOMENTE quando a etapa 5 existir E o soltar_bloco do
# entregar_blocos.py estiver escrito. Sem a etapa 5 o robo esta no tapete
# de blocos, e o entregar_blocos comecaria a soltar bloco no lugar errado.
# entregar_blocos(leituras)

ev3.speaker.beep()
