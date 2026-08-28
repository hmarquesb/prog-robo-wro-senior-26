#!/usr/bin/env pybricks-micropython
from pybricks.parameters import Stop
from pybricks.tools import wait

import constantes as cte
import movimento as m
import linha as lin
from setup import ev3, motor_A, motor_B, motor_C, sensor_esq


def executar():
    m.andar(-560, v_max=1000, v_min=200, acel=1100, desacel=1100,
            kp=2.5, kd=3.5)
    
    motor_A.run_angle(1000, 895)
    
    m.girar_eixo(-10,v_max=800, desacel=1200, kp=2.5, kd=7)
    m.girar_eixo(10,v_max=800, desacel=1200, kp=2.5, kd=7) 
    
    m.andar_por_tempo(1000,-250)
    
    lin.seguir_linha(parar_se=[lin.cruzamento()], kp=2, kd=6.5, v_max=800,
                    desacel=700, tempo_ms=5000, ignorar_mm=100)
    m.girar_eixo(180,v_max=1000, desacel=1200, kp=2.1, kd=7)
    m.andar(-365, v_max=1000, v_min=300, acel=1100, desacel=1800,
            kp=2.5, kd=3.5)
    
    motor_A.run_angle(1000, -150)
    
    
    
    
    
    lin.seguir_linha(parar_se=[lin.cruzamento()], kp=2, kd=6.5, v_max=700,
                    acel=1000, desacel=700, tempo_ms=5000, ignorar_mm=100)
    m.girar_pivo(motor_C, -90, v_max=1000, acel=800, desacel=1400, kp=2.8, kd=6.8)
    m.andar(250, v_max=1000, v_min=200, acel=1100, desacel=1100,
            kp=2.5, kd=3.5)
    m.andar_por_tempo(300,500)
    
    m.andar(-75, v_max=700, v_min=200, acel=1100, desacel=1800,
            kp=2.5, kd=3.5)
    m.girar_eixo(-90,v_max=900, desacel=900, kp=3.3, kd=7)
    
    
    m.andar(-165, v_max=300, v_min=100, acel=1000, desacel=1000,
            kp=2.5, kd=3.5)
    motor_A.run_angle(1000, 150)
    
    m.girar_eixo(-10,v_max=800, desacel=1200, kp=2.5, kd=7)
    m.girar_eixo(10,v_max=800, desacel=1200, kp=2.5, kd=7) 
    
    m.andar_por_tempo(1000,-250)
    
    m.andar(215, v_max=1000, v_min=200, acel=1500, desacel=1000,
            kp=2.5, kd=3.5)
    m.girar_pivo(motor_C, -90,  v_max=1000, acel=1500, desacel=1500, kp=2.5, kd=7)
    lin.seguir_linha(parar_se=[lin.viu_escuro(sensor_esq)], kp=2.7, kd=6.5, v_max=800,
                    acel=1000, desacel=1100, ignorar_mm=500)
    
    
    m.andar(135, v_max=300, v_min=200, acel=1500, desacel=1000,
            kp=2.5, kd=3.5)
    m.andar_por_tempo(700,350)

    m.andar(-60, v_max=300, v_min=100, acel=1500, desacel=1000,
            kp=2.5, kd=3.5)
    m.girar_eixo(90, v_max=1000, desacel=1200, kp=2.6, kd=7)
    
    m.andar(350, v_max=1000, v_min=200, acel=1000, desacel=1000,
            kp=2.5, kd=3.5)
    m.girar_pivo(motor_B, 40, v_max=1000, acel=1000, desacel=1000, kp=2.7, kd=7.33)
    m.andar(130, v_max=1000, v_min=200, acel=1000, desacel=1000,
            kp=2.5, kd=3.5)
    m.girar_pivo(motor_C, -40, v_max=1000, acel=1000, desacel=1000, kp=2.7, kd=7.33)
    m.andar(170, v_max=1000, v_min=200, acel=1000, desacel=1000,
            kp=2.5, kd=3.5)
    
    
    m.andar(-100, v_max=1000, v_min=200, acel=1500, desacel=1000,
            kp=2.5, kd=3.5)
    
    m.girar_eixo(-94,v_max=1000, desacel=1200, kp=2.1, kd=7)
    m.andar(-135, v_max=1000, v_min=200, acel=1500, desacel=1000,
            kp=2.5, kd=3.5)
    
   
    motor_A.run_angle(-1000, 400)
   
   
   
   
    m.andar(215, v_max=1000, v_min=200, acel=1500, desacel=1000,
            kp=2.5, kd=3.5)
    m.andar_por_tempo(700,350)

    m.andar(-85, v_max=300, v_min=100, acel=1500, desacel=1000,
            kp=2.5, kd=3.5)

    m.girar_eixo(95, v_max=1000, desacel=1200, kp=2.5, kd=7)
    m.andar(780, v_max=1000, v_min=200, acel=1500, desacel=1500,
            kp=2.5, kd=3.5)

    
if __name__ == "__main__":
    executar()
    ev3.speaker.beep()