#!/usr/bin/env pybricks-micropython
"""
parte1.py - Primeira parte do percurso
======================================

Do inicio ate o robo ficar posicionado para a leitura do mosaico.

Roda de dois jeitos:

    F5 neste arquivo  -> calibra os sensores e executa so esta parte
    prog1.py          -> chama calibrar_sensores() e executar() na
                         sequencia da prova, emendando com o resto

Por isso o percurso esta dentro de executar(), e nao solto no arquivo:
solto, ele rodaria no momento do `import` la no prog1.py - antes da hora
e sem ninguem ter pedido.

Os numeros aqui estao calibrados no robo, e este e o UNICO lugar onde
eles existem: o prog1.py chama esta funcao em vez de repetir a sequencia.
Calibrou aqui, valeu para a prova inteira.
"""
from setup import sensor_esq, sensor_dir, motor_A, motor_B, motor_C, motor_D, ev3, wait
import setup as s
import movimento as m
import linha as lin
import carrinho as c
import garra as g


def calibrar_sensores():
    """
    Ensina aos dois sensores o preto e o branco DESTE tapete.

    Separada de executar() porque vale para o programa inteiro, e nao so
    para esta parte: quem emenda varias partes (prog1.py) calibra UMA VEZ
    no comeco, em vez de repetir a cada uma.

    Os pares (escuro, claro) saem do lin.calibrar_varrendo - repita a
    varredura quando a luz do ginasio mudar.
    """
    lin.calibrar(sensor_esq, 4, 49)
    lin.calibrar(sensor_dir, 3, 43)


def executar():
    """
    Faz a primeira parte do percurso, do inicio ate a posicao de leitura.

    Pressupoe os sensores JA CALIBRADOS (calibrar_sensores) e o robo na
    largada.

    A ordem do comeco importa: o carrinho sai do batente ANTES do
    zerar_garra, senao a garra bate na estrutura do robo antes do fim do
    curso e o zero dela - a referencia de todas as descidas do programa -
    sairia alto (ver garra.py).

    Ao terminar, o robo esta parado onde o ler_mosaico() do
    leitura_blocos.py comeca.
    """
    c.zerar_carrinho(velocidade=800, forca=90)
    c.mover_carrinho(30, velocidade=1000,esperar=True)

    m.girar_pivo(motor_C, -45, v_max=800, acel=800, desacel=1600, kp=3.1, kd=7.33)
    m.girar_pivo(motor_B, 45, v_max=800, acel=800, desacel=1600, kp=3.1, kd=7.33)

    g.zerar_garra()

    lin.seguir_linha(kp=1.2, kd=13, v_max=1000, desacel=4000, tempo_ms=5000,
                     parar_se=[lin.cruzamento()], ignorar_mm=390)
    m.andar(110, v_max=300, v_min=100, acel=800, desacel=1500, kp=2.5, kd=3.5)
    
    g.mover_garra(500, 720, s.Stop.HOLD)     # sobe
    
    lin.seguir_linha(kp=1.2, kd=12, v_max=850, desacel=2000, tempo_ms=5000,
                     parar_se=[lin.cruzamento()], ignorar_mm=290)
    m.andar(100, v_max=700, v_min=200, acel=1100, desacel=1800, kp=2.5, kd=3.5)
    m.girar_eixo(90, v_max=550, desacel=1200, kp=3, kd=7)
    # BLOQUEANTE de proposito: descer a garra ENQUANTO o robo anda
    # (esperar=False) entortava o robo no teste real - o mesmo risco que
    # o cabecalho do garra.py ja avisava. Desce primeiro, parado, so
    # depois anda.
    m.andar(-100, v_max=700, v_min=200, acel=1100, desacel=1800, kp=2.5, kd=3.5)
    g.descer_garra()
    #m.andar(-100, v_max=700, v_min=200, acel=1100, desacel=1800, kp=2.5, kd=3.5)

    m.andar(-340, v_max=700, v_min=200, acel=1100, desacel=1800, kp=2.5, kd=3.5)
    m.girar_eixo(90, v_max=550, desacel=1200, kp=3, kd=7)


if __name__ == "__main__":
    calibrar_sensores()
    executar()
    ev3.speaker.beep()
