#!/usr/bin/env pybricks-micropython
"""
parte1.py - Primeira parte do percurso
======================================

Do inicio ate o robo ficar posicionado para a leitura do mosaico.

Roda de dois jeitos:

    F5 neste arquivo  -> executa so esta parte
    prog1.py          -> chama executar() na sequencia da prova,
                         emendando com o resto

Por isso o percurso esta dentro de executar(), e nao solto no arquivo:
solto, ele rodaria no momento do `import` la no prog1.py - antes da hora
e sem ninguem ter pedido.

OS NUMEROS FICAM NAS PROPRIAS CHAMADAS, de proposito: este e o trecho
que mais se ajusta no robo, e ler o efeito de um numero exige ve-lo na
linha que o usa. So o que e do robo inteiro (geometria, ganhos padrao,
calibracao dos sensores) vem do constantes.py.

O MOTOR A E COMANDADO DIRETO: motor_A.run_angle(velocidade, graus), com
os graus daquele passo escritos na linha. Movimentos RELATIVOS - quem
estabelece um zero e a etapa que precisa de posicao absoluta
(leitura_blocos e pegar_blocos), cada uma na sua hora.

A calibracao dos sensores nao precisa de chamada nenhuma: o linha.py
carrega CAL_SENSOR_ESQ / CAL_SENSOR_DIR do constantes.py no import.
"""

import movimento as m
import linha as lin
from setup import ev3, motor_A, motor_B, motor_C


def executar():
    """
    Faz a primeira parte do percurso, do inicio ate a posicao de leitura.

    Pressupoe o robo na largada.

    A ordem do comeco importa: o carrinho sai do batente ANTES de
    qualquer descida de garra, senao ela bate na estrutura do robo antes
    do fim do curso (ver garra.py).

    Todos os motor_A.run_angle daqui sao RELATIVOS: este trecho nao
    estabelece zero nenhum, so tira e devolve o carrinho conforme o
    percurso precisa. Quem zera e a etapa seguinte.

    Ao terminar, o robo esta parado onde o ler_mosaico() do
    leitura_blocos.py comeca, com a garra em cima.
    """
   
    motor_A.run_angle(1000,320)
    m.girar_pivo(motor_C, -45,  v_max=900, acel=800, desacel=1600, kp=2.4, kd=7.6)
    m.girar_pivo(motor_B, 45, v_max=900, acel=800, desacel=1600, kp=2.4, kd=7.6)

    lin.seguir_linha(parar_se=[lin.cruzamento()], kp=1, kd=13, v_max=1000, desacel=4000,
                         tempo_ms=5000, ignorar_mm=520)
    m.andar(90, v_max=800, v_min=200, acel=1100, desacel=1800,
                    kp=2.5, kd=3.5)
    m.girar_eixo(-90,v_max=800, desacel=1200, kp=2.5, kd=7)
    motor_A.run_angle(-750,450,wait=False)
    m.andar_por_tempo(1100,-120,frente=True)
    m.andar(110, v_max=800, v_min=200, acel=1100, desacel=1800,
                    kp=2.5, kd=3.5)
    m.girar_pivo(motor_C, 90,  v_max=900, acel=800, desacel=1600, kp=2.4, kd=7.33)
    m.andar(-290, v_max=700, v_min=200, acel=1100, desacel=1800,
                    kp=2.5, kd=3.5)
    m.girar_pivo(motor_C, -30,  v_max=900, acel=800, desacel=1600, kp=2.4, kd=7.33)
    #m.andar(80, v_max=500, v_min=200, acel=1100, desacel=1800,
     #               kp=2.5, kd=3.5)
    m.girar_pivo(motor_B, 30,  v_max=900, acel=800, desacel=1600, kp=2.4, kd=7.33) 
    lin.seguir_linha(parar_se=[lin.cruzamento()], kp=1, kd=13, v_max=1000, desacel=4000,
                         tempo_ms=5000, ignorar_mm=600)
    m.girar_pivo(motor_C, 90,  v_max=900, acel=800, desacel=1600, kp=2.4, kd=7.33)
    motor_A.run_angle(700,450)           
    m.girar_pivo(motor_C, -180,  v_max=900, acel=800, desacel=1600, kp=3, kd=8.7) 
    motor_A.run_angle(-700,400)#volta pro batente 
    lin.seguir_linha(parar_se=[lin.cruzamento()], kp=1, kd=13, v_max=900, desacel=4000,
                         tempo_ms=5000, ignorar_mm=200)

    # Se um dia entrar uma descida de garra aqui, faca-a BLOQUEANTE (com
    # o robo parado): descer com esperar=False ENQUANTO o robo andava
    # entortava o robo no teste real.


if __name__ == "__main__":
    executar()
    ev3.speaker.beep()