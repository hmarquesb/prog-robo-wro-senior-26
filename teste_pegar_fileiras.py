#!/usr/bin/env pybricks-micropython
"""
teste_pegar_fileiras.py - Abrir o carrinho e pegar UM bloco
============================================================

ARQUIVO DE APOIO, NAO E PARTE DA PROVA. So o comeco do ciclo, isolado: o
carrinho abre ate o bloco e a garra fecha em cima dele. Nada de servo,
nada de arremesso, nada de laco - se este pedaco nao funciona, o resto
nao tem o que provar.

UM MOVIMENTO DE CADA VEZ. Nenhum wait=False, nenhum control.done(): cada
linha so comeca quando a anterior terminou. Assim da para olhar o robo e
saber exatamente em que linha ele esta.

SEM AS FUNCOES DO PROJETO E SEM CONSTANTES. Nada de garra.py ou
pegar_blocos.py, e nenhum nome em MAIUSCULA guardando numero: cada valor
esta escrito na linha em que ele age.

ESTES NUMEROS SAO COPIAS dos do pegar_blocos.py e do garra.py, e nao
andam juntos com eles. Quando um valor estiver bom, leve-o para o arquivo
da prova na mao.

COMO A GARRA FUNCIONA AQUI, que e o que os sinais dizem:

    NEGATIVO  fecha  - e fechando que ela prende o bloco
    POSITIVO  abre
    zero      o batente, marcado uma vez na abertura

A ORDEM NAO E GOSTO: o carrinho SEMPRE antes da garra. Ela so tem curso
livre com ele fora do batente de casa; fechando com o carrinho recolhido
ela bate na estrutura do robo antes do fim do curso, e o zero sai alto -
o que desloca todas as alturas depois.

O ROBO NAO ANDA. Ponha-o na mao em frente a uma coluna do tapete, com o
bloco do FUNDO no lugar. So o carrinho (motor A) e a garra (motor D) -
nem servo, nem sensores, nem rodas.

O QUE CONFERIR
--------------
  1. o carrinho recolhe ate travar e SO ENTAO abre. Indo para o lado
     errado, troque o sinal do -800 da zeragem.
  2. a garra FECHA na zeragem, ate encostar no batente. Se ela abrir em
     vez de fechar, o Direction do motor D esta invertido - PARE, porque
     o zero sai no fim errado do curso e tudo depois sai torto junto.
  3. ela ENCOSTA mesmo no batente. Parando antes, aumente os 700 ms.
  4. a garra abre o bastante para o bloco caber embaixo dela. Se nao
     couber, aumente os 500.
  5. o carrinho para com a garra em cima do bloco do fundo. Antes ou
     depois, e o 1800.
  6. a garra fecha e PRENDE o bloco. Nao prendendo, aumente os 1100 ms
     do fechamento; rangendo no fim do curso, diminua.

O angulo impresso no fim diz onde a garra parou ao fechar. E o numero que
interessa levar para o pegar_blocos.py depois.
"""

from pybricks.ev3devices import Motor
from pybricks.hubs import EV3Brick
from pybricks.parameters import Direction, Port, Stop
from pybricks.tools import wait


ev3 = EV3Brick()

# As direcoes tem de ser as MESMAS do setup.py, senao os graus escritos
# aqui embaixo significam outra coisa.
motor_A = Motor(Port.A, Direction.CLOCKWISE)      # carrinho da correia
motor_D = Motor(Port.D, Direction.CLOCKWISE)      # garra


if __name__ == "__main__":

    ev3.screen.clear()
    print("=== abrir o carrinho e pegar o bloco ===")

    # ---- 1. zera o carrinho -------------------------------------------
    # Recolhe ate travar no batente de casa e chama aquele ponto de zero.
    # O 1800 do passo 2 conta dali.
    #   -800  velocidade, negativa = recolhe
    #     70  duty_limit em %: trava antes do batente -> aumente
    motor_A.run_until_stalled(-800, then=Stop.HOLD, duty_limit=70)
    motor_A.reset_angle(0)
    print("1. carrinho zerado")

    # ---- 2. abre o carrinho -------------------------------------------
    # Ate a profundidade do bloco do FUNDO. Espera terminar antes de
    # qualquer movimento da garra.
    motor_A.run_target(1000, 1600)
    print("2. carrinho aberto em", motor_A.angle(), "graus")
    wait(1000)

    # ---- 3. zera a garra ----------------------------------------------
    # FECHA por tempo ate o batente e chama aquele ponto de zero. Por
    # tempo, e nao por angulo, porque um alvo em cima do batente nunca
    # "chega" e o programa esperaria para sempre.
    #   -800  velocidade, negativa = fecha
    #    700  ms empurrando. CURTO DEMAIS marca o zero no meio do
    #         caminho, e ai o 500 do passo 4 conta de um lugar que nao e
    #         o batente.
    motor_D.run_time(-800, 700, then=Stop.HOLD)
    motor_D.reset_angle(0)
    print("3. garra zerada no batente")

    # ---- 4. abre a garra ----------------------------------------------
    # 500 graus a partir do batente: a altura de espera, com o bloco
    # cabendo embaixo dela.
    #   nao abre o bastante para o bloco entrar -> AUMENTE
    

    # ---- 5. pega o bloco ----------------------------------------------
    # Fecha em cima do bloco. E o movimento que prende - e, no ciclo
    # inteiro, o mesmo que taca.
    #   nao prende o bloco     -> AUMENTE os 1100
    #   range no fim do curso  -> diminua
    motor_D.run_time(800, 1600, then=Stop.HOLD)
    print("5. garra fechou em", motor_D.angle(), "graus")

    ev3.screen.print("fechou em")
    ev3.screen.print(motor_D.angle())
    ev3.speaker.beep()
