#!/usr/bin/env pybricks-micropython
from setup import sensor_esq, sensor_dir, motor_A, motor_B, motor_C, motor_D, ev3, wait
import setup as s
import movimento as m
import linha as lin
import carrinho as c

lin.calibrar(sensor_esq, 4, 49)
lin.calibrar(sensor_dir, 3, 43)

c.zerar_carrinho(velocidade=800, forca=90)
c.mover_carrinho(33, velocidade=500)
m.girar_pivo(motor_C,-47,v_max=900, acel=800, desacel=1600, kp=3.1, kd=7.33)
m.girar_pivo(motor_B, 47,v_max=900, acel=800, desacel=1600, kp=3.1, kd=7.33)
motor_D.run_time(-500,1200,then=s.Stop.COAST)
lin.seguir_linha(kp=1.2, kd=12, v_max=750, desacel=3000, tempo_ms=5000,
                parar_se=[lin.cruzamento()], ignorar_mm=400)
m.andar(100,v_max=300,v_min=200,acel=1100,desacel=1800,kp=1.5, kd=3.5)
motor_D.run_time(500,1000,then=s.Stop.HOLD)
lin.seguir_linha(kp=1.2, kd=12, v_max=850, desacel=2000, tempo_ms=5000,
                parar_se=[lin.cruzamento()], ignorar_mm=300)
m.girar_eixo(130, v_max=700, desacel=1200, kp=3, kd=7.33)
motor_D.run_time(-500, 1000, then=s.Stop.COAST)
