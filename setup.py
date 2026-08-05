#!/usr/bin/env pybricks-micropython
"""
setup.py - Hardware do robo
===========================

Unico lugar onde os objetos de hardware sao criados. Todos os outros
arquivos importam daqui.

Isso nao e so organizacao: criar DOIS objetos Motor na mesma porta da erro
em tempo de execucao. Centralizando aqui, isso nao acontece.

Se voces trocarem uma porta, mudam so neste arquivo.
"""

import math
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor, ColorSensor
from pybricks.parameters import Port, Direction, Stop
from pybricks.tools import wait, StopWatch


ev3 = EV3Brick()

motor_A = Motor(Port.A, Direction.CLOCKWISE)
motor_D = Motor(Port.D, Direction.CLOCKWISE)

motor_B = Motor(Port.B, Direction.COUNTERCLOCKWISE)   # roda ESQUERDA
motor_C = Motor(Port.C, Direction.CLOCKWISE)          # roda DIREITA

# --- Sensores de cor ---
# Nomeados pela funcao. Se o robo corrigir para o lado errado no seguidor
# de linha, TROQUE AS DUAS LINHAS ABAIXO (ou use inverter=True).
sensor_esq = ColorSensor(Port.S3)
sensor_dir = ColorSensor(Port.S4)
motor_B.control.limits(1000, 10000, 100)
motor_C.control.limits(1000, 10000, 100)

# motor_A (carrinho) sem limits configurado ficava oscilando (estende,
# recolhe um pouco, estende de novo) ao tentar chegar num alvo com
# run_target - aceleracao padrao do Pybricks e agressiva demais para o
# carrinho e ele passa do ponto e corrige repetidas vezes. Acel bem mais
# baixa que a das rodas (motor_B/C) para chegar suave e direto.
# AJUSTE no robo real: se ainda oscilar, abaixe ainda mais a aceleracao
# (2o valor) ou reduza a velocidade usada nas chamadas de mover_carrinho.
motor_A.control.limits(1000, 2000, 100)
