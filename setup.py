#!/usr/bin/env pybricks-micropython
"""
setup.py - Hardware do robo
===========================

Unico lugar onde os objetos de hardware sao criados. Todos os outros
arquivos importam daqui.

Isso nao e so organizacao: criar DOIS objetos Motor na mesma porta da
erro em tempo de execucao. Centralizando aqui, isso nao acontece.

Se voces trocarem uma porta, mudam so neste arquivo.

    Porta A   carrinho da correia GT2 + quadrilatero traseiro
    Porta B   roda ESQUERDA   (COUNTERCLOCKWISE)
    Porta C   roda DIREITA    (CLOCKWISE)
    Porta D   garra (anda em cima do carrinho)
    Porta S1  Arduino Nano (I2C) - servo seletor das colunas
    Porta S3  sensor de cor esquerdo  (anda em cima do carrinho)
    Porta S4  sensor de cor direito   (anda em cima do carrinho)

O MOTOR A E COMANDADO DIRETO, sem modulo no meio: cada rotina chama
motor_A.run_angle(velocidade, graus) com os graus daquele passo, escritos
na propria linha. Uma embreagem decide qual mecanismo recebe o movimento
conforme o SENTIDO de giro, mas isso e mecanica - o programa so manda
graus.

    motor_A.run_angle(1000, 320)    # positivo
    motor_A.run_angle(500, -260)    # negativo

Se o sentido sair trocado, inverta o Direction do motor_A aqui embaixo em
vez de espalhar sinais negativos pelas rotinas.
"""

from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor, ColorSensor
from pybricks.iodevices import I2CDevice
from pybricks.parameters import Port, Direction

import constantes as cte


ev3 = EV3Brick()

motor_A = Motor(Port.A, Direction.CLOCKWISE)          # carrinho / traseira
motor_D = Motor(Port.D, Direction.CLOCKWISE)          # garra

motor_B = Motor(Port.B, Direction.COUNTERCLOCKWISE)   # roda ESQUERDA
motor_C = Motor(Port.C, Direction.CLOCKWISE)          # roda DIREITA

# Nomeados pela funcao. Se o robo corrigir para o lado errado no seguidor
# de linha, TROQUE AS DUAS LINHAS ABAIXO (ou use inverter=True).
sensor_esq = ColorSensor(Port.S3)
sensor_dir = ColorSensor(Port.S4)

# O servo das colunas nao e ligado no EV3: quem o comanda e um Arduino
# Nano, e o EV3 conversa com ele por I2C. Mora aqui pelo mesmo motivo dos
# motores - dois I2CDevice na mesma porta seriam dois donos do mesmo
# barramento. Quem fala o protocolo e o servos_selecionar.py; o
# servos_segurar.py (o outro servo, no D10 do Arduino) importa dele.
#
# O teste de bancada (teste_arduino.py) cria o proprio I2CDevice DE
# PROPOSITO: ele roda com so o cabo do Arduino plugado, e importar este
# arquivo la exigiria os 4 motores conectados.
arduino = I2CDevice(Port.S1, cte.SERVO_ENDERECO)

# Os limites tem de ser aplicados AQUI, e nao no movimento.py: o Pybricks
# exige o motor parado quando control.limits() e chamado, e isto roda
# antes de qualquer codigo de movimento (ver README, regra 5).
motor_B.control.limits(*cte.LIMITES_RODA)
motor_C.control.limits(*cte.LIMITES_RODA)
motor_A.control.limits(*cte.LIMITES_MOTOR_A)
