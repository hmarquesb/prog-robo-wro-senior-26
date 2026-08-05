#!/usr/bin/env pybricks-micropython
"""
movimento.py - Movimentacao do robo
===================================

Hardware vem do setup.py. Aqui ficam so os movimentos.

Quatro funcoes, todas com aceleracao/desaceleracao suave e PD:

    andar(distancia_mm)                  -> anda reto (positivo = frente)
    girar_eixo(angulo_graus)             -> gira no proprio eixo
    girar_arco(raio_mm, angulo_graus)    -> gira em arco
    girar_pivo(motor_parado, angulo)     -> gira travando uma das rodas

Convencao de sinal, igual nas quatro: ANGULO POSITIVO = DIREITA.

Todas usam o mesmo nucleo interno (_mover), que:
  1. Calcula quantos graus cada roda precisa girar.
  2. Gera um perfil de velocidade trapezoidal (acelera - cruzeiro - desacelera).
  3. Roda um PD que corrige o SINCRONISMO entre as duas rodas em tempo real.

O PD aqui nao segue linha: ele garante que as duas rodas cumpram a proporcao
correta de movimento. E isso que faz o robo andar reto de verdade e parar no
angulo certo, em vez de sair torto por causa de atrito ou nivel de bateria.
"""

import math
from pybricks.tools import wait, StopWatch

from setup import ev3, motor_A, motor_B, motor_C, motor_D


# =============================================================================
# 1. PARAMETROS FISICOS  (medidos no robo)
# =============================================================================

DIAMETRO_RODA = 62.4      # mm
ENTRE_EIXOS   = 185.0     # mm - distancia entre o centro das duas rodas

# mm que o robo anda para cada 1 grau de rotacao da roda
MM_POR_GRAU = math.pi * DIAMETRO_RODA / 360.0


# =============================================================================
# 2. PARAMETROS DE CONTROLE
# =============================================================================

# --- Velocidades, em graus/segundo da roda ---
V_MAX = 700.0     # velocidade de cruzeiro
V_MIN = 60.0      # velocidade minima. Se for 0, o robo "morre" antes de
                  # chegar. Se for alta demais, ele derrapa ao parar.

# --- Aceleracao, em graus/s^2 ---
# ALTO  = arranque/parada brusca (rapido, mas derrapa e perde precisao)
# BAIXO = suave (preciso, mas gasta mais tempo)
ACEL    = 900.0
DESACEL = 1200.0  # costuma ser MAIOR que ACEL: freia mais rapido do que
                  # arranca, porque a precisao do ponto de parada importa mais

# --- Ganhos do PD de sincronismo entre as rodas ---
KP = 2.5   # corrige o erro atual. Aumente se o robo sai torto.
KD = 8.0   # amortece. Aumente se o robo fica oscilando / tremendo.

V_LIMITE = 900.0   # teto absoluto de velocidade enviada aos motores
DT = 5             # ms por ciclo do loop de controle
TIMEOUT = 15000    # ms - trava de seguranca padrao


# =============================================================================
# 3. NUCLEO DE CONTROLE
# =============================================================================

def _sinal(x):
    if x > 0:
        return 1.0
    if x < 0:
        return -1.0
    return 0.0


def _limitar(valor, minimo, maximo):
    return max(minimo, min(maximo, valor))


def _perfil_velocidade(percorrido, total, v_max, v_min, acel, desacel):
    """
    Perfil trapezoidal de velocidade, pela formula  v = sqrt(2 * a * s).

    - No inicio, 'v_sobe' e pequena  -> limita a velocidade (acelerando)
    - No meio,   ambas sao grandes   -> vale v_max (cruzeiro)
    - No fim,    'v_desce' e pequena -> limita a velocidade (freando)
    """
    restante = max(total - percorrido, 0.0)
    v_sobe  = math.sqrt(2.0 * acel * max(percorrido, 0.0)) + v_min
    v_desce = math.sqrt(2.0 * desacel * restante) + v_min
    return max(v_min, min(v_max, v_sobe, v_desce))


def _mover(alvo_esq, alvo_dir,
           v_max=V_MAX, v_min=V_MIN, acel=ACEL, desacel=DESACEL,
           kp=KP, kd=KD, parar_no_fim=True, segurar=False, timeout=TIMEOUT):
    """
    Nucleo generico. Recebe quantos GRAUS cada roda deve girar e executa
    com perfil de velocidade + PD de sincronismo.

    alvo_esq / alvo_dir : graus de rotacao de cada roda (com sinal)
        iguais e positivos  -> anda reto pra frente
        opostos             -> gira no proprio eixo
        proporcionais       -> arco
        um deles zero       -> pivo
    """
    if alvo_esq == 0 and alvo_dir == 0:
        return

    motor_B.reset_angle(0)
    motor_C.reset_angle(0)

    # 'ref' = a roda que percorre MAIS. O perfil e calculado em cima dela;
    # a outra acompanha proporcionalmente.
    ref = max(abs(alvo_esq), abs(alvo_dir))

    frac_esq = alvo_esq / ref     # fracao de velocidade de cada roda
    frac_dir = alvo_dir / ref

    s_esq = _sinal(alvo_esq)
    s_dir = _sinal(alvo_dir)

    # Roda com alvo ZERO (pivo): trava com hold() para servir de eixo.
    # Sem isso o atrito da outra roda empurra ela e o pivo escorrega.
    if alvo_esq == 0:
        motor_B.hold()
    if alvo_dir == 0:
        motor_C.hold()

    erro_ant = 0.0
    relogio = StopWatch()

    while True:
        ang_esq = motor_B.angle()
        ang_dir = motor_C.angle()

        # --- Progresso: fracao do movimento ja cumprida (0.0 a 1.0) ---
        p_esq = ang_esq / alvo_esq if alvo_esq != 0 else 0.0
        p_dir = ang_dir / alvo_dir if alvo_dir != 0 else 0.0

        # A roda de alvo zero nao entra no erro de sincronismo
        if alvo_esq == 0:
            p_esq = p_dir
        if alvo_dir == 0:
            p_dir = p_esq

        progresso = (p_esq + p_dir) / 2.0

        if progresso >= 1.0:
            break
        if relogio.time() > timeout:
            break                      # trava de seguranca: robo empacou

        v = _perfil_velocidade(progresso * ref, ref, v_max, v_min, acel, desacel)

        # --- PD de sincronismo ---
        # erro > 0  =>  roda esquerda ADIANTADA em relacao a direita
        erro = ref * (p_esq - p_dir)
        correcao = kp * erro + kd * (erro - erro_ant)
        erro_ant = erro

        # A correcao entra no SENTIDO DE MARCHA de cada roda (por isso o
        # sinal do alvo). E isso que faz a mesma formula servir para reto,
        # giro no eixo, arco e pivo.
        v_esq = v * frac_esq - correcao * s_esq
        v_dir = v * frac_dir + correcao * s_dir

        # A roda travada nao recebe comando: fica em hold() o tempo todo
        if alvo_esq != 0:
            motor_B.run(_limitar(v_esq, -V_LIMITE, V_LIMITE))
        if alvo_dir != 0:
            motor_C.run(_limitar(v_dir, -V_LIMITE, V_LIMITE))

        wait(DT)

    if parar_no_fim:
        if segurar:
            motor_B.hold()
            motor_C.hold()
        else:
            motor_B.brake()
            motor_C.brake()


# =============================================================================
# 4. FUNCOES DE MOVIMENTO
# =============================================================================

def _mm_para_graus(mm):
    return mm / MM_POR_GRAU


def andar(distancia_mm,
          v_max=V_MAX, v_min=V_MIN, acel=ACEL, desacel=DESACEL,
          kp=KP, kd=KD, parar_no_fim=True, segurar=False, timeout=TIMEOUT):
    """
    Anda em linha reta. Positivo = frente, negativo = re.

        andar(500)                     # meio metro pra frente
        andar(-200)                    # 20 cm de re
        andar(300, v_max=300)          # devagar, pra manobra fina
        andar(400, parar_no_fim=False) # emenda com o proximo movimento
    """
    graus = _mm_para_graus(distancia_mm)
    _mover(graus, graus,
           v_max=v_max, v_min=v_min, acel=acel, desacel=desacel,
           kp=kp, kd=kd, parar_no_fim=parar_no_fim, segurar=segurar,
           timeout=timeout)


def girar_eixo(angulo_graus,
               v_max=V_MAX, v_min=V_MIN, acel=ACEL, desacel=DESACEL,
               kp=KP, kd=KD, parar_no_fim=True, segurar=False, timeout=TIMEOUT):
    """
    Gira no proprio eixo: as rodas giram em sentidos opostos e o centro
    do robo fica parado.

        girar_eixo(90)     # quarto de volta pra direita
        girar_eixo(-180)   # meia volta pra esquerda
    """
    # Cada roda percorre o arco de um circulo de raio = metade do entre-eixos
    arco_mm = (ENTRE_EIXOS / 2.0) * math.radians(angulo_graus)
    graus = _mm_para_graus(arco_mm)
    _mover(graus, -graus,
           v_max=v_max, v_min=v_min, acel=acel, desacel=desacel,
           kp=kp, kd=kd, parar_no_fim=parar_no_fim, segurar=segurar,
           timeout=timeout)


def girar_arco(raio_mm, angulo_graus, re=False,
               v_max=V_MAX, v_min=V_MIN, acel=ACEL, desacel=DESACEL,
               kp=KP, kd=KD, parar_no_fim=True, segurar=False, timeout=TIMEOUT):
    """
    Gira descrevendo um arco. O raio e medido do centro do circulo ate o
    CENTRO DO ROBO (o meio do eixo das rodas).

    raio_mm      : sempre positivo
    angulo_graus : > 0 curva para a DIREITA, < 0 para a ESQUERDA
    re           : True faz o mesmo arco andando de re

        girar_arco(0, 90)      == girar_eixo(90)
        girar_arco(92.5, 90)   -> pivo sobre a roda direita (ENTRE_EIXOS/2)
        girar_arco(300, 90)    -> curva ampla e suave
        girar_arco(50, 90)     -> curva fechada; a roda interna anda PARA TRAS
                                  (o codigo lida com isso sozinho)
    """
    sentido = 1.0 if angulo_graus >= 0 else -1.0
    ang_rad = math.radians(abs(angulo_graus))

    arco_externo = (raio_mm + ENTRE_EIXOS / 2.0) * ang_rad
    arco_interno = (raio_mm - ENTRE_EIXOS / 2.0) * ang_rad

    if sentido > 0:      # direita: roda esquerda e a externa
        mm_esq, mm_dir = arco_externo, arco_interno
    else:                # esquerda: roda direita e a externa
        mm_esq, mm_dir = arco_interno, arco_externo

    if re:
        mm_esq, mm_dir = -mm_esq, -mm_dir

    _mover(_mm_para_graus(mm_esq), _mm_para_graus(mm_dir),
           v_max=v_max, v_min=v_min, acel=acel, desacel=desacel,
           kp=kp, kd=kd, parar_no_fim=parar_no_fim, segurar=segurar,
           timeout=timeout)


def girar_pivo(motor_parado, angulo_graus,
               *, v_max=V_MAX, v_min=V_MIN, acel=ACEL, desacel=DESACEL,
               kp=KP, kd=KD, parar_no_fim=True, segurar=False, timeout=TIMEOUT):
    """
    Gira pivotando sobre UMA das rodas. A roda escolhida fica travada e
    serve de eixo; a outra descreve todo o arco.

    motor_parado : motor_B (roda esquerda) ou motor_C (roda direita)
    angulo_graus : > 0 gira o robo para a DIREITA (mesma convencao das
                   outras funcoes, independente de qual roda ficou parada)

    O raio de giro e o ENTRE_EIXOS inteiro (nao a metade), entao a roda que
    se move percorre o DOBRO da distancia de um girar_eixo do mesmo angulo.
    Mais lento, mas prende uma quina do robo no lugar.

    Quando usar em vez de girar_eixo:
      - manter um mecanismo parado em cima de um objeto enquanto o robo gira
      - virar encostado numa parede sem raspar
      - sair de um canto sem perder a referencia daquele lado

        girar_pivo(motor_C, 90)    # trava a roda direita, gira 90 a direita
        girar_pivo(motor_B, -90)   # trava a roda esquerda, gira 90 a esquerda
    """
    arco_mm = ENTRE_EIXOS * math.radians(angulo_graus)

    if motor_parado is motor_C:
        # Pivo na roda ESQUERDA: para virar a DIREITA, a roda direita
        # precisa andar para TRAS.
        alvo_esq, alvo_dir = 0, _mm_para_graus(-arco_mm)

    elif motor_parado is motor_B:
        # Pivo na roda DIREITA: para virar a DIREITA, a roda esquerda
        # anda para a FRENTE.
        alvo_esq, alvo_dir = _mm_para_graus(arco_mm), 0

    else:
        raise ValueError(
            "motor_parado deve ser motor_B (esquerda) ou motor_C (direita)")

    _mover(alvo_esq, alvo_dir,
           v_max=v_max, v_min=v_min, acel=acel, desacel=desacel,
           kp=kp, kd=kd, parar_no_fim=parar_no_fim, segurar=segurar,
           timeout=timeout)


def parar(segurar=False):
    """Para os dois motores de tracao imediatamente."""
    if segurar:
        motor_B.hold()
        motor_C.hold()
    else:
        motor_B.brake()
        motor_C.brake()


# =============================================================================
# 5. TESTE / CALIBRACAO
# =============================================================================
# Ordem de calibracao:
#   TESTE 1 -> ajusta DIAMETRO_RODA   (distancia percorrida)
#   TESTE 2 -> ajusta ENTRE_EIXOS     (angulo do giro)
#   TESTE 3 -> ajusta KP e KD         (robo sair reto e estavel)
#   TESTE 4 -> ajusta ACEL/DESACEL    (velocidade sem derrapar)

if __name__ == "__main__":

    ev3.speaker.beep()
    wait(500)

    # ---- TESTE 1: distancia -------------------------------------------------
    # Marque o chao, rode, meca com regua.
    #   Andou MENOS que 500 mm -> DIMINUA  DIAMETRO_RODA
    #   Andou MAIS  que 500 mm -> AUMENTE  DIAMETRO_RODA
    andar(500)
    wait(1000)
    andar(-500)
    wait(1000)

    # ---- TESTE 2: giro no eixo ---------------------------------------------
    # 4 giros de 90 = uma volta completa. O robo tem que voltar apontando
    # exatamente para onde comecou.
    #   Girou de MENOS -> AUMENTE  ENTRE_EIXOS
    #   Girou de MAIS  -> DIMINUA  ENTRE_EIXOS
    # for _ in range(4):
    #     girar_eixo(90)
    #     wait(500)

    # ---- TESTE 3: arco e pivo ----------------------------------------------
    # girar_arco(300, 90)
    # wait(1000)
    # girar_arco(300, -90)
    # wait(1000)
    #
    # Marque no chao onde esta a roda travada: ela nao pode sair do lugar.
    # Se escorregar, o problema e mecanico (peso mal distribuido, pouca
    # aderencia), nao de codigo.
    # girar_pivo(motor_C, 90)
    # wait(1000)
    # girar_pivo(motor_C, -90)

    # ---- TESTE 4: sequencia encadeada --------------------------------------
    # parar_no_fim=False emenda movimentos sem freada entre eles: mais
    # rapido, mas perde um pouco de precisao na transicao.
    # andar(400, parar_no_fim=False)
    # girar_arco(200, 90, parar_no_fim=False)
    # andar(300)

    ev3.speaker.beep()