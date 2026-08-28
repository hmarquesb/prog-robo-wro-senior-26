#!/usr/bin/env pybricks-micropython
"""
diagnostico.py - Descobre EM QUE PONTO o programa quebra
=========================================================

ARQUIVO DE APOIO, NAO E PARTE DA PROVA. Rode com F5 quando um programa
"nao roda" / termina com "error code 1" sem dizer por que. Pode apagar
depois.

Ele importa os modulos do projeto UM DE CADA VEZ, na ordem das camadas
(constantes -> setup -> controle -> missao) e avisa o resultado de cada
etapa NA TELA E POR APITO - ou seja, funciona mesmo sem enxergar o Debug
Console, que e justamente o problema quando so aparece "error code 1".

COMO LER OS APITOS

    apitos curtos, agudos  -> etapa passou (1 apito = etapa 1, e assim
                              por diante: da para contar de longe)
    UM apito longo e grave -> foi ALI que quebrou. O nome da etapa e a
                              mensagem do erro ficam na tela do EV3 por
                              30 segundos.

A ETAPA QUE FALHAR E A RESPOSTA:

    1 (python)      nem apitou -> o arquivo nem chegou a rodar no brick:
                    problema de conexao/download, nao de codigo Python
    2 (constantes)  o constantes.py nao subiu para o EV3, ou tem erro de
                    sintaxe
    3 (setup)       HARDWARE: motor, sensor ou o Arduino do servo
                    desconectado / na porta errada. E a falha mais comum,
                    e derruba TODO programa do projeto, porque todos
                    importam o setup.py
    4 (controle)    erro em movimento / linha / garra / servos
    5 (missao)      erro em parte1 / leitura_blocos_parte2 / parte3 /
                    pegar_blocos / entregar_blocos

Passando as 5, o problema nao esta nos imports: esta no que o programa
FAZ depois - e ai o traceback no Debug Console e que diz onde.
"""

from pybricks.hubs import EV3Brick
from pybricks.tools import wait


# EV3Brick proprio, e nao o do setup.py, de proposito: o setup.py e um
# dos suspeitos, entao este arquivo nao pode depender dele para
# conseguir apitar. Criar dois EV3Brick e inofensivo (ao contrario de
# dois Motor na mesma porta, que ai sim da erro).
brick = EV3Brick()

ETAPA = 0


def _passou(nome):
    """Apita uma vez por etapa cumprida: da para contar de longe."""
    global ETAPA
    ETAPA += 1
    brick.screen.print(str(ETAPA) + " " + nome + " OK")
    print("etapa", ETAPA, nome, "OK")
    for _ in range(ETAPA):
        brick.speaker.beep(1000, 90)
        wait(110)


def _falhou(nome, erro):
    """Apito longo e grave, e o erro fica na tela para ser lido."""
    brick.screen.print("FALHOU: " + nome)
    brick.screen.print(str(erro))
    print("FALHOU em", nome, ":", erro)
    brick.speaker.beep(200, 1500)
    wait(30000)          # tempo de ler a tela antes do programa sair


# --- 1. o brick esta rodando este arquivo? ------------------------------
_passou("python")

# --- 2. numeros (nao toca em hardware) ----------------------------------
try:
    import constantes as cte
    _passou("constantes")
except Exception as e:
    _falhou("constantes", e)
    raise SystemExit

# --- 3. HARDWARE - o suspeito numero 1 ----------------------------------
# Motor/sensor desconectado ou em porta errada quebra aqui, e como todo
# arquivo do projeto importa o setup.py, quebra em todos.
try:
    from setup import ev3, motor_A, motor_B, motor_C, motor_D
    from setup import sensor_esq, sensor_dir, arduino
    _passou("setup")
except Exception as e:
    _falhou("setup (hardware)", e)
    raise SystemExit

# --- 4. camada de controle ----------------------------------------------
try:
    import movimento as m
    import linha as lin
    import garra as g
    import servos_selecionar as sv
    import servos_segurar as sg
    _passou("controle")
except Exception as e:
    _falhou("controle", e)
    raise SystemExit

# --- 5. rotinas da missao -----------------------------------------------
try:
    import parte1
    import leitura_blocos_parte2
    import parte3
    import pegar_blocos
    import entregar_blocos
    _passou("missao")
except Exception as e:
    _falhou("missao", e)
    raise SystemExit

brick.screen.print("tudo importou")
print("os 5 imports passaram - o erro esta no que o programa FAZ,")
print("nao nos imports. Veja o traceback no Debug Console.")
brick.speaker.beep(1500, 600)
wait(5000)
