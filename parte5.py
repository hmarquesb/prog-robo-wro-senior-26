#!/usr/bin/env pybricks-micropython
from pybricks.parameters import Stop
from pybricks.tools import wait

import constantes as cte
import movimento as m
import linha as lin
from setup import ev3, motor_A, motor_B, motor_C, sensor_esq


def executar():
    m.girar_eixo(180,v_max=800, desacel=1200, kp=2.5, kd=7)
    
    motor_A.run_angle(1000, 900)
    lin.seguir_linha(parar_se=[lin.cruzamento()], kp=1.7, kd=6.5, v_max=1000,
                     desacel=1000, tempo_ms=5000, ignorar_mm=140)
    wait(100)
    m.girar_eixo(-55, v_max=800, desacel=1200, kp=2.5, kd=7)

    motor_A.run_angle(-1000, 300, wait=False)
    m.andar(325, v_max=700, v_min=200, acel=1100, desacel=1800,
            kp=2.5, kd=3.5)
    
    m.girar_eixo(-125,v_max=800, desacel=1200, kp=2.5, kd=7)  
    
    motor_A.run_angle(500, 350, wait=False)
    m.andar_por_tempo(1500,-400,frente=True)
    
    lin.seguir_linha(parar_se=[lin.viu_escuro(sensor_esq)], kp=1.7, kd=6.5,
                     v_max=1000, desacel=1000, tempo_ms=5000, ignorar_mm=100)
    m.girar_pivo(motor_C, -90,  v_max=900, acel=800, desacel=1600, kp=2.4, kd=7.6)

if __name__ == "__main__":
    executar()
    ev3.speaker.beep()