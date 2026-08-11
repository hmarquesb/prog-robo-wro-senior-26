#!/usr/bin/env pybricks-micropython
"""
leitura_blocos.py - Leitura do mosaico
======================================

Varre o mosaico em zigue-zague e devolve as 12 cores pedidas, na ordem
de varredura. E essa lista que o pegar_blocos.py consome (ver
COLUNAS_MOSAICO la, que traduz a ordem de varredura para "as 4 cores da
coluna 1", etc.).

Roda de dois jeitos:

    F5 neste arquivo  -> executa so a leitura e imprime a lista
    prog1.py          -> chama ler_mosaico() depois da parte1 e passa a
                         lista adiante, na sequencia da prova

Por isso a varredura esta dentro de ler_mosaico(), e nao solta no
arquivo: solta, ela rodaria no momento do `import`.

As cores saem do sensor.color() cru, e nao do lin.ler() - aqui interessa
QUAL cor e, nao quanto reflete, entao a calibracao do seguidor de linha
nao entra nessa conta. Ela ainda importa para o seguir_linha do comeco.
"""
from setup import sensor_esq, sensor_dir, motor_A, motor_B, motor_C, motor_D, ev3, wait
import setup as s
import movimento as m
import linha as lin
import carrinho as c
import garra as g


# Posicoes do carrinho (mm) em que cada coluna do mosaico fica debaixo do
# sensor, e quanto o robo avanca de uma fileira para a proxima.
entre_movimentos = 45
primeira_posicao = 25
segunda_posicao = 45
terceira_posicao = 95

V_ANDAR = dict(v_max=300, v_min=200, acel=300, desacel=3000, kp=1.9, kd=3.5)


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


def ler_mosaico(passos=passos):
    """
    Varre o mosaico e devolve a lista das 12 cores, na ordem da varredura.

    Pressupoe o robo onde a parte1 o deixou e os sensores ja calibrados
    (o seguir_linha do comeco depende disso; a leitura das cores, nao).

    Zera o carrinho duas vezes de proposito: uma no comeco, para a ida ate
    o mosaico, e outra ja em cima dele, imediatamente antes da varredura -
    e a varredura que precisa da posicao exata, e essa segunda zeragem
    apaga qualquer folga acumulada no caminho.

    E a lista devolvida que o pegar_blocos.pegar_blocos() recebe.
    """
    g.mover_garra(600, 1500, s.Stop.HOLD,esperar=False)
    c.zerar_carrinho(velocidade=800, forca=90)
    c.mover_carrinho(55, velocidade=500)
    lin.seguir_linha(kp=1.5, kd=12, v_max=600, desacel=3000, tempo_ms=5000,
                     parar_se=[lin.cruzamento()], ignorar_mm=180)

    m.andar(180, **V_ANDAR)
    c.zerar_carrinho(velocidade=800, forca=90)

    leituras = []
    for tipo, valor, sensor, nome in passos:
        if tipo == "carrinho":
            c.mover_carrinho(valor, velocidade=500)
        else:
            m.andar(valor, **V_ANDAR)
        leituras.append(ler_bloco(sensor, nome))

    m.andar(225, **V_ANDAR)

    return leituras


if __name__ == "__main__":
    # Sozinho, este arquivo nao calibra os sensores - o seguir_linha do
    # comeco roda com o que estiver valendo. Rodando dentro do prog1.py,
    # quem calibrou foi a parte1.
    leituras = ler_mosaico()
    print(leituras)
    ev3.speaker.beep()
