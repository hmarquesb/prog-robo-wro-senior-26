#!/usr/bin/env pybricks-micropython
from setup import sensor_esq, sensor_dir, motor_A, motor_B, motor_C, motor_D, ev3, wait
import setup as s
import movimento as m
import linha as lin
import carrinho as c

entre_movimentos = 40
primeira_posicao = 28
segunda_posicao = 45
terceira_posicao = 95

V_ANDAR = dict(v_max=300, v_min=200, acel=3000, desacel=3000, kp=1.5, kd=3.5)

def ler_bloco(sensor, nome):
    cor = sensor.color()
    print(nome, ":", cor)
    return cor

# cada passo: (tipo de movimento, valor, sensor a ler depois, rotulo)
passos = [
    ("carrinho", primeira_posicao, sensor_esq, "posicao 1"),
    ("carrinho", segunda_posicao, sensor_dir, "posicao 2"),
    ("carrinho", terceira_posicao, sensor_dir, "posicao 3"),
    ("andar", entre_movimentos, sensor_dir, "avanco 1"),
    ("carrinho", segunda_posicao, sensor_dir, "posicao 2"),
    ("carrinho", primeira_posicao, sensor_esq, "posicao 1"),
    ("andar", entre_movimentos, sensor_esq, "avanco 2"),
    ("carrinho", segunda_posicao, sensor_dir, "posicao 2"),
    ("carrinho", terceira_posicao, sensor_dir, "posicao 3"),
    ("andar", entre_movimentos, sensor_dir, "avanco 3"),
    ("carrinho", segunda_posicao, sensor_dir, "posicao 2"),
    ("carrinho", primeira_posicao, sensor_esq, "posicao 1"),
]

c.zerar_carrinho(velocidade=800, forca=90)
c.mover_carrinho(65, velocidade=500)
lin.seguir_linha(kp=1.2, kd=12, v_max=750, desacel=3000, tempo_ms=5000,
                parar_se=[lin.cruzamento()], ignorar_mm=200)

m.andar(190, **V_ANDAR)
c.zerar_carrinho(velocidade=800, forca=90)

leituras = []
for tipo, valor, sensor, nome in passos:
    if tipo == "carrinho":
        c.mover_carrinho(valor, velocidade=500)
    else:
        m.andar(valor, **V_ANDAR)
    leituras.append(ler_bloco(sensor, nome))

m.andar(200, **V_ANDAR)

print(leituras)
