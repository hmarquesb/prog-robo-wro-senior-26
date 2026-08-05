#!/usr/bin/env pybricks-micropython
"""
carrinho.py - Carrinho da correia GT2
=====================================

Hardware vem do setup.py.

Controle do carrinho que desliza na correia, com posicao em MILIMETROS
em vez de graus de motor.

Os movimentos podem ser BLOQUEANTES (padrao) ou NAO BLOQUEANTES
(esperar=False), para acionar o carrinho junto com outro mecanismo.

NAO mova o carrinho enquanto o robo anda ou segue linha: o deslocamento
de massa muda a dinamica no meio do percurso e o PD sai de sintonia.
Mover junto com OUTRO MECANISMO, com o robo parado, e tranquilo.
"""

from pybricks.parameters import Stop
from pybricks.tools import wait, StopWatch

from setup import ev3, motor_A, motor_D


# =============================================================================
# 1. CONFIGURACAO
# =============================================================================

MOTOR_CARRINHO = motor_A

# --- Geometria da correia ---
# Uma volta da polia puxa a correia por:  numero_de_dentes x passo
# A GT2 tem passo de 2 mm. A polia mais comum do kit tem 20 dentes:
#     20 x 2 = 40 mm por volta
# CONFIRA A SUA POLIA contando os dentes. Se este numero estiver errado,
# TODAS as distancias em mm ficam erradas.
DENTES_POLIA  = 20
PASSO_CORREIA = 2.0
MM_POR_GRAU   = (DENTES_POLIA * PASSO_CORREIA) / 360.0

# Curso util, do batente recolhido ate o limite. MEDIR COM REGUA.
CURSO_MM = 150.0

V_CARRINHO = 400.0     # graus/s do motor


# =============================================================================
# 2. FUNCOES
# =============================================================================

def zerar_carrinho(velocidade=200, forca=30):
    """
    Encontra o batente mecanico e define aquele ponto como zero.

    Roda o motor contra o batente com forca limitada ate travar, e entao
    zera o encoder. CHAME NO INICIO DE TODO PROGRAMA: sem isso, a posicao
    em mm nao tem referencia nenhuma.

    forca : duty_limit em %. Baixo o bastante pra nao arrebentar a correia
            nem forcar o mecanismo. Comece em 30.
    """
    MOTOR_CARRINHO.run_until_stalled(-velocidade, then=Stop.HOLD,
                                     duty_limit=forca)
    MOTOR_CARRINHO.reset_angle(0)
    ev3.speaker.beep()


def posicao_carrinho():
    """Quanto o carrinho andou desde o zero, em MILIMETROS."""
    return MOTOR_CARRINHO.angle() * MM_POR_GRAU


def mover_carrinho(destino_mm, velocidade=V_CARRINHO, esperar=True):
    """
    Leva o carrinho ate uma posicao ABSOLUTA, medida do batente+.

        0        = recolhido
        CURSO_MM = totalmente estendido

    esperar=True  -> so devolve o controle quando o carrinho chegar
    esperar=False -> dispara o comando e volta na hora, deixando o carrinho
                     se mover enquanto o programa segue

    O esperar=False serve para acionar o carrinho JUNTO com outro mecanismo
    (a garra, por exemplo), em vez de um depois do outro:

        mover_carrinho(120, esperar=False)     # carrinho comeca a sair
        motor_D.run_angle(500, 180, wait=False)  # garra comeca a abrir
        esperar_carrinho()                     # agora espera os dois
        while not motor_D.control.done():
            wait(10)

    ATENCAO: nao use esperar=False para mover o carrinho ENQUANTO o robo
    anda ou segue linha. O deslocamento de massa muda a dinamica do robo
    no meio do percurso e o PD sai de sintonia.
    """
    destino_mm = max(0.0, min(CURSO_MM, destino_mm))
    MOTOR_CARRINHO.run_target(velocidade, destino_mm / MM_POR_GRAU,
                              then=Stop.HOLD, wait=esperar)


def carrinho_chegou():
    """True quando o carrinho terminou o ultimo movimento."""
    return MOTOR_CARRINHO.control.done()


def esperar_carrinho(timeout=5000):
    """
    Bloqueia ate o carrinho chegar. Devolve False se estourar o timeout
    (carrinho travado ou fora do curso).
    """
    relogio = StopWatch()
    while not carrinho_chegou():
        if relogio.time() > timeout:
            return False
        wait(10)
    return True


def recolher(velocidade=V_CARRINHO, esperar=True):
    """Volta o carrinho para a posicao zero."""
    mover_carrinho(0, velocidade=velocidade, esperar=esperar)


def estender(esperar=True):
    """Leva o carrinho ate o fim do curso."""
    mover_carrinho(CURSO_MM, esperar=esperar)


# =============================================================================
# 3. TESTE
# =============================================================================

if __name__ == "__main__":

    # ---- Conferir a geometria da correia ----
    # Zera, manda ir a 100 mm, e voces MEDEM COM REGUA.
    #   Andou menos que 100 -> a polia tem MENOS dentes do que voces acharam
    #   Andou mais  que 100 -> tem MAIS dentes
    zerar_carrinho()
    wait(500)
    mover_carrinho(100)
    ev3.screen.print("Meca com regua!")
    wait(5000)
    recolher()

    # ---- Carrinho e garra ao mesmo tempo ----
    # Os dois disparam sem esperar, e so depois o programa espera os dois.
    # Fica bem mais rapido que fazer um de cada vez.
    #
    # estender(esperar=False)                    # carrinho comeca a sair
    # motor_D.run_angle(500, 180, wait=False)    # garra comeca a abrir
    #
    # esperar_carrinho()                         # agora espera os dois
    # while not motor_D.control.done():
    #     wait(10)
    #
    # ev3.speaker.beep()

    ev3.speaker.beep()