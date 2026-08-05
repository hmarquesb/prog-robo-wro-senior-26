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
m.girar_pivo(motor_C,-45,v_max=900, acel=800, desacel=1600, kp=3.1, kd=7.33)
m.girar_pivo(motor_B, 45,v_max=900, acel=800, desacel=1600, kp=3.1, kd=7.33)
lin.seguir_linha(kp=1.6, kd=12, v_max=750, desacel=3000, tempo_ms=5000,
                parar_se=[lin.cruzamento()], ignorar_mm=400)

m.andar(-30,v_max=300,v_min=200,acel=3000,desacel=3000,kp=1.5, kd=3.5, parar_no_fim=True)

m.girar_pivo(motor_C,-30,v_max=900, acel=800, desacel=1600, kp=3.1, kd=7.33)
m.girar_pivo(motor_B, 30,v_max=900, acel=800, desacel=1600, kp=3.1, kd=7.33)

m.andar(20,v_max=300,v_min=200,acel=3000,desacel=3000,kp=1.5, kd=3.5, parar_no_fim=True)
#wait(200)

motor_D.run_time(200,1000,then=s.Stop.COAST)
motor_D.run_time(-500,1000,then=s.Stop.HOLD)

m.girar_pivo(motor_B, 30,v_max=900, acel=800, desacel=1600, kp=3.1, kd=7.33)
m.girar_pivo(motor_C,-30,v_max=900, acel=800, desacel=1600, kp=3.1, kd=7.33)

#c.mover_carrinho(18, velocidade=500, esperar=False)   # recolhe um pouco (33 - 15)
#motor_D.run_time(-200, 700, then=s.Stop.HOLD, wait=False)
#c.esperar_carrinho()
#while not motor_D.control.done():
#    wait(10)

#c.mover_carrinho(33, velocidade=500)                   # abre a mesma quantidade

#lin.seguir_linha(kp=1.6, kd=12, v_max=850, desacel=2000, tempo_ms=5000,
#                parar_se=[lin.cruzamento()], ignorar_mm=300)

#m.girar_eixo(130, v_max=700, desacel=1200, kp=3, kd=7.33, parar_no_fim=True)

#motor_D.run_time(200, 1000, then=s.Stop.HOLD)          # abaixa o grabber (mesmos valores do primeiro giro)





#--------------1---------------------
#s.motor_D.run_until_stalled(400,then=s.Stop.COAST)
#s.motor_D.run_time(-1000,1200,then=s.Stop.COAST)
#s.motor_D.run_time(1000,1200,then=s.Stop.COAST)



#----------------------
#m.girar_pivo(s.motor_C, -30,acel=800, desacel=1600,kp=3.5, kd=7.33, parar_no_fim=False)
#m.girar_pivo(s.motor_B, 30,acel=800, desacel=1600,kp=3.5, kd=7.33, parar_no_fim=False)   
#andar(300,v_max=800,desacel=1800,kp=3, kd=7.33, parar_no_fim=False)
    #girar_eixo(-90,kp=3, kd=7.33, parar_no_fim=True)
    #girar_pivo(motor_B, -90,acel=800, desacel=1600,kp=3.5, kd=7.33, parar_no_fim=True)