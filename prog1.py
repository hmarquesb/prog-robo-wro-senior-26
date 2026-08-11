#!/usr/bin/env pybricks-micropython
"""
prog1.py - Programa da prova
============================

Emenda as partes do percurso na ordem em que elas acontecem na rodada:

    parte1.executar()             largada -> posicao de leitura
    leitura_blocos.ler_mosaico()  varre o mosaico -> 12 cores
    parte2.executar()             mosaico -> tapete de blocos
    pegar_blocos(leituras)        retira os 12 blocos
    (percurso que falta)          tapete de blocos -> volta ao mosaico
    entregar_blocos(leituras)     devolve os 12 blocos no mosaico

E SO ISSO QUE ESTE ARQUIVO FAZ. Nenhum numero de percurso mora aqui: os
tempos, distancias e ganhos continuam cada um no seu arquivo, calibrados
onde voces ja mexem neles. Copiar as sequencias para ca criaria uma
segunda copia dos mesmos numeros, e um dia voces calibrariam uma e
rodariam a outra.

Cada parte continua rodando sozinha com F5 no arquivo dela - util para
testar uma so sem repetir a rodada inteira. O que muda aqui e a emenda:
a calibracao dos sensores acontece UMA VEZ, no comeco, e nao a cada
parte.

ANTES DE RODAR A RODADA INTEIRA, QUATRO COISAS FALTAM (as etapas que
dependem delas ficam comentadas ate ficarem prontas):

    1. o PERCURSO do parte2.py, que esta vazio esperando os movimentos
    2. a CALIBRACAO do pegar_blocos.py - POSICAO_COLUNA (as 8 distancias
       a partir da parede), PROFUNDIDADES_CARRINHO (perto/meio, em mm - o
       bloco do fundo nao usa mm, o carrinho estende ate o fim do curso
       dele), o CURSO_MM do carrinho.py (se ele estiver maior que o curso
       real, o carrinho trava ao estender) e os arremessos V_GARRA_SUBIR /
       TEMPO_GARRA_SUBIR_MS - estes ultimos NAS TRES PROFUNDIDADES, ja que
       o bloco e lancado de onde o carrinho parou. Da para calibrar tudo
       isso SEM o parte2: ponha o robo na mao na largada e rode o
       pegar_blocos.py com F5.
    3. o MECANISMO DE SOLTAR o bloco (soltar_bloco no entregar_blocos.py),
       que ainda nao existe no robo. Sem ele o entregar_blocos faz o
       caminho e apita em cada celula, mas nao entrega nada.
    4. o PERCURSO DE VOLTA do tapete de blocos ate o mosaico, que ninguem
       escreveu ainda - o equivalente do parte2, na outra direcao. E o que
       poe o robo em cima da FILEIRA 4, que e de onde o entregar_blocos
       comeca (ele entrega de costas, da fileira 4 para a 1).

PARA ACRESCENTAR UMA PARTE NOVA: escreva o arquivo dela com a sequencia
dentro de uma funcao (como parte1.executar), importe aqui e chame na
posicao certa. Nao cole a sequencia aqui dentro.
"""
from setup import ev3
import parte1
import leitura_blocos
import parte2
from pegar_blocos import pegar_blocos
from entregar_blocos import entregar_blocos


# --- 1. Sensores -------------------------------------------------------
# Uma vez para a rodada inteira. A parte1 tambem chamaria isso se rodasse
# sozinha (no __main__ dela), mas aqui quem manda e este arquivo.
parte1.calibrar_sensores()

# --- 2. Percurso ate o mosaico ----------------------------------------
parte1.executar()

# --- 3. Leitura do mosaico --------------------------------------------
# Devolve as 12 cores na ordem da varredura - a mesma ordem que o
# pegar_blocos.py espera receber.
leituras = leitura_blocos.ler_mosaico()
print("mosaico lido:", leituras)

# --- 4. Percurso ate o tapete de blocos --------------------------------
# DESCOMENTE quando o percurso do parte2.py estiver escrito. Vazio, ele
# so zera o carrinho e o robo continuaria em cima do mosaico - e o
# pegar_blocos contaria as 8 colunas a partir do lugar errado.
# Termina com o robo encostado na parede e o carrin3,,ho zerado, que e
# exatamente a largada da etapa 5.
parte2.executar()

# --- 5. Retirada dos blocos --------------------------------------------
# DESCOMENTE junto com a etapa 4 (e depois de calibrar o pegar_blocos).
# Nao precisa de zerar_carrinho aqui: quem faz isso e a ultima linha do
# parte2.executar(), e entre uma coisa e outra nao pode haver andada.
pegar_blocos(leituras)

# --- 6. Volta ao mosaico ------------------------------------------------
# NAO EXISTE AINDA. Falta o percurso que leva o robo do tapete de blocos
# de volta para cima da FILEIRA 4 do mosaico - o parte2 ao contrario.
# Escreva num arquivo proprio (parte3.py) e chame aqui, como as outras
# partes; nao cole a sequencia dentro deste arquivo.

# --- 7. Entrega dos blocos ----------------------------------------------
# DESCOMENTE quando a etapa 6 existir E o soltar_bloco do
# entregar_blocos.py estiver escrito. Sem a etapa 6 o robo esta no tapete
# de blocos, e o entregar_blocos comecaria a soltar bloco no lugar errado.
# entregar_blocos(leituras)

ev3.speaker.beep()
