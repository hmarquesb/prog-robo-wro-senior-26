#!/usr/bin/env pybricks-micropython
"""
movimento.py - Movimentacao do robo
===================================

Hardware vem do setup.py. Aqui ficam so os movimentos.

Quatro funcoes, todas com aceleracao/desaceleracao suave e PD:

    andar(distancia_mm)                  -> anda reto (positivo = frente)
    girar_eixo(angulo_graus)             -> gira no proprio eixo
    girar_arco(raio_mm, angulo_graus)    -> gira em arco
    girar_pivo(motor_girando, angulo)    -> gira travando a OUTRA roda

Convencao de sinal, igual nas quatro: ANGULO POSITIVO = DIREITA.

Todas usam o mesmo nucleo interno (_mover), que:
  1. Calcula quantos graus cada roda precisa girar.
  2. Gera um perfil de velocidade trapezoidal (acelera - cruzeiro - desacelera).
  3. Roda um PD que corrige o SINCRONISMO entre as duas rodas em tempo real.

O PD aqui nao segue linha: ele garante que as duas rodas cumpram a proporcao
correta de movimento. E isso que faz o robo andar reto de verdade e parar no
angulo certo, em vez de sair torto por causa de atrito ou nivel de bateria.

Duas travas existem para o PD nao virar o problema em vez da solucao, e nao
devem ser removidas (TESTE 0 no fim do arquivo mede as duas):

  TETO DA CORRECAO (CORRECAO_MAX_FRAC) - a correcao nunca pode passar de uma
  fracao da velocidade que o perfil pediu. Sem isso ela zera a roda atrasada
  e o robo GIRA em vez de andar reto.

  PARADA PELAS DUAS RODAS - o loop so termina quando a roda que esta ATRAS
  chega, nao quando a media chega. Pela media, uma roda parada faz a outra
  andar o dobro do alvo antes de o movimento "acabar".
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

# Teto da correcao do PD, como FRACAO da velocidade que o perfil pediu
# para a roda naquele instante.
#
# Sem esse teto o PD tem autoridade total sobre a velocidade: a correcao
# entra como  v_esq = v - correcao , e nada impede que `correcao` fique
# MAIOR que `v`. Quando isso acontece a roda atrasada e mandada para zero
# (ou para tras) e so a outra anda - o robo GIRA em vez de andar reto.
#
# E facil de acontecer no COMECO de qualquer movimento: ali o perfil ainda
# esta em v_min, o valor mais baixo do trajeto inteiro, e e exatamente o
# instante em que as duas rodas vencem o atrito estatico em momentos
# diferentes. O erro pula alguns graus de uma vez, o termo D multiplica
# esse pulo por KD e a correcao passa de v_min sem esforco.
#
# Com o teto, a roda mais lenta nunca cai abaixo de (1 - fracao) da
# velocidade dela e nenhuma das duas troca de sentido: o PD continua
# corrigindo, mas por diferenca de velocidade, nao parando roda.
#
# 0.5 = a diferenca entre as rodas nunca passa de metade da velocidade.
# Sobra autoridade de giro de sobra. Abaixe para 0.3 se ainda arrancar
# torto; suba com cuidado - perto de 1.0 o teto deixa de proteger.
CORRECAO_MAX_FRAC = 0.5

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
           kp=KP, kd=KD, correcao_max_frac=CORRECAO_MAX_FRAC,
           parar_no_fim=True, segurar=False, timeout=TIMEOUT):
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

    # Menor das duas fracoes: e a roda mais LENTA que define quanto de
    # correcao cabe sem inverter ninguem. Num arco fechado a roda de dentro
    # anda a 0.3 da velocidade da de fora, entao um teto calculado so em
    # cima de `v` ainda a mandaria para tras.
    # No pivo uma das fracoes e 0 (roda travada, que nem recebe comando):
    # ali quem manda e a fracao da roda que sobrou.
    frac_min = min(abs(frac_esq), abs(frac_dir))
    if frac_min == 0.0:
        frac_min = max(abs(frac_esq), abs(frac_dir))

    # Roda com alvo ZERO (pivo): trava com hold() para servir de eixo.
    # Sem isso o atrito da outra roda empurra ela e o pivo escorrega.
    if alvo_esq == 0:
        motor_B.hold()
    if alvo_dir == 0:
        motor_C.hold()

    erro_ant = 0.0
    relogio = StopWatch()
    relogio_ciclo = StopWatch()

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

        # Duas medidas de progresso, com papeis diferentes:
        #
        #   MEDIA  -> alimenta o perfil de velocidade. E onde o ROBO esta,
        #             entao e por ela que ele acelera e freia.
        #   MINIMO -> criterio de parada. O movimento so acabou quando as
        #             DUAS rodas chegaram.
        #
        # Sair pela media deixava a roda atrasada devendo: com uma em 1.03
        # e a outra em 0.97 a media da 1.0, o loop terminava e o PD - o
        # unico que podia acertar aquilo - desligava junto. Pior: com uma
        # roda PARADA a media so chega em 1.0 quando a outra anda o DOBRO
        # do alvo, entao o robo passava todo esse tempo girando em vez de
        # desistir. Pelo minimo o loop continua enquanto faltar roda, o
        # perfil ja esta em v_min (a media passou de 1.0, `restante` zerou)
        # e o timeout continua sendo a saida de emergencia.
        progresso = (p_esq + p_dir) / 2.0
        completo = min(p_esq, p_dir)

        if completo >= 1.0:
            break
        if relogio.time() > timeout:
            break                      # trava de seguranca: robo empacou

        v = _perfil_velocidade(progresso * ref, ref, v_max, v_min, acel, desacel)

        # --- PD de sincronismo ---
        # erro > 0  =>  roda esquerda ADIANTADA em relacao a direita
        erro = ref * (p_esq - p_dir)

        # A derivada e NORMALIZADA para um ciclo de DT ms. `erro - erro_ant`
        # sozinho nao e uma derivada: ele cresce junto com o tempo que o
        # ciclo levou, e o ciclo real no EV3 nao e DT - e DT mais o custo de
        # ler os dois encoders e escrever nos dois motores, tudo pelo
        # sistema de arquivos do Linux, que varia conforme o que mais
        # estiver rodando (o motor_A segurando o carrinho, por exemplo).
        # Sem dividir, o mesmo KD vale coisas diferentes em momentos
        # diferentes do programa e nao ha como calibra-lo.
        #
        # Dividir por dt_ms e multiplicar por DT mantem o KD na MESMA
        # escala de antes - num ciclo que realmente leve DT ms o valor nao
        # muda -, entao todos os kd ja calibrados (parte1, parte2,
        # leitura_blocos, pegar_blocos) continuam valendo.
        dt_ms = relogio_ciclo.time()
        relogio_ciclo.reset()
        if dt_ms < 1:
            dt_ms = DT
        derivada = (erro - erro_ant) * DT / dt_ms
        erro_ant = erro

        correcao = kp * erro + kd * derivada

        # TETO DA CORRECAO (ver CORRECAO_MAX_FRAC): sem ele a correcao pode
        # ficar maior que a propria velocidade do perfil e ZERAR a roda
        # atrasada - o robo gira em vez de andar. Acontecia na largada, com
        # o perfil ainda em v_min e o termo D reagindo ao atrito estatico
        # das duas rodas cedendo em instantes diferentes.
        limite_correcao = correcao_max_frac * v * frac_min
        correcao = _limitar(correcao, -limite_correcao, limite_correcao)

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
          kp=KP, kd=KD, correcao_max_frac=CORRECAO_MAX_FRAC,
          parar_no_fim=True, segurar=False, timeout=TIMEOUT):
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
           kp=kp, kd=kd, correcao_max_frac=correcao_max_frac,
           parar_no_fim=parar_no_fim, segurar=segurar,
           timeout=timeout)


def girar_eixo(angulo_graus,
               v_max=V_MAX, v_min=V_MIN, acel=ACEL, desacel=DESACEL,
               kp=KP, kd=KD, correcao_max_frac=CORRECAO_MAX_FRAC,
               parar_no_fim=True, segurar=False, timeout=TIMEOUT):
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
           kp=kp, kd=kd, correcao_max_frac=correcao_max_frac,
           parar_no_fim=parar_no_fim, segurar=segurar,
           timeout=timeout)


def girar_arco(raio_mm, angulo_graus, re=False,
               v_max=V_MAX, v_min=V_MIN, acel=ACEL, desacel=DESACEL,
               kp=KP, kd=KD, correcao_max_frac=CORRECAO_MAX_FRAC,
               parar_no_fim=True, segurar=False, timeout=TIMEOUT):
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
           kp=kp, kd=kd, correcao_max_frac=correcao_max_frac,
           parar_no_fim=parar_no_fim, segurar=segurar,
           timeout=timeout)


def girar_pivo(motor_girando, angulo_graus,
               *, v_max=V_MAX, v_min=V_MIN, acel=ACEL, desacel=DESACEL,
               kp=KP, kd=KD, correcao_max_frac=CORRECAO_MAX_FRAC,
               parar_no_fim=True, segurar=False, timeout=TIMEOUT):
    """
    Gira pivotando sobre UMA das rodas: a roda escolhida descreve todo o
    arco e a OUTRA fica travada, servindo de eixo.

    motor_girando : a roda que SE MEXE - motor_B (esquerda) ou motor_C
                    (direita). Quem fica parada e a outra.
    angulo_graus  : > 0 gira o robo para a DIREITA (mesma convencao das
                    outras funcoes, independente de qual roda se mexe)

    O sentido em que a roda gira sai do angulo, nao de quem voce escolheu:
    para virar a DIREITA, a roda ESQUERDA vai para a frente e a DIREITA vai
    para tras. Escolher a roda so decide sobre qual quina o robo pivota.

    O raio de giro e o ENTRE_EIXOS inteiro (nao a metade), entao a roda que
    se move percorre o DOBRO da distancia de um girar_eixo do mesmo angulo.
    Mais lento, mas prende uma quina do robo no lugar.

    Quando usar em vez de girar_eixo:
      - manter um mecanismo parado em cima de um objeto enquanto o robo gira
      - virar encostado numa parede sem raspar
      - sair de um canto sem perder a referencia daquele lado

        girar_pivo(motor_C, 90)    # gira a roda direita (para tras),
                                   # pivotando na esquerda: 90 a direita
        girar_pivo(motor_B, 90)    # gira a roda esquerda (para a frente),
                                   # pivotando na direita: 90 a direita
    """
    arco_mm = ENTRE_EIXOS * math.radians(angulo_graus)

    if motor_girando is motor_C:
        # So a roda DIREITA se mexe; pivo na esquerda. Para virar a DIREITA
        # ela precisa andar para TRAS.
        alvo_esq, alvo_dir = 0, _mm_para_graus(-arco_mm)

    elif motor_girando is motor_B:
        # So a roda ESQUERDA se mexe; pivo na direita. Para virar a DIREITA
        # ela anda para a FRENTE.
        alvo_esq, alvo_dir = _mm_para_graus(arco_mm), 0

    else:
        raise ValueError(
            "motor_girando deve ser motor_B (esquerda) ou motor_C (direita)")

    _mover(alvo_esq, alvo_dir,
           v_max=v_max, v_min=v_min, acel=acel, desacel=desacel,
           kp=kp, kd=kd, correcao_max_frac=correcao_max_frac,
           parar_no_fim=parar_no_fim, segurar=segurar,
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
#   TESTE 0 -> diagnostico do PD      (as duas rodas andaram o mesmo?)
#   TESTE 1 -> ajusta DIAMETRO_RODA   (distancia percorrida)
#   TESTE 2 -> ajusta ENTRE_EIXOS     (angulo do giro)
#   TESTE 3 -> ajusta KP e KD         (robo sair reto e estavel)
#   TESTE 4 -> ajusta ACEL/DESACEL    (velocidade sem derrapar)

if __name__ == "__main__":

    #ev3.speaker.beep()
    #wait(500)

    # ---- TESTE 0: o PD esta sincronizando as rodas? ------------------------
    # Rode ANTES de qualquer outro teste, e sempre que o robo sair torto ou
    # girar uma roda so. Nao precisa de regua: o _mover zera os dois
    # encoders na largada e nunca mais mexe neles, entao o angulo lido aqui
    # e exatamente o que cada roda andou naquele movimento.
    #
    # COMO LER:
    #   esq == dir == alvo  -> o PD esta fazendo o trabalho dele. Se mesmo
    #                          assim o robo sai torto, o problema e MECANICO
    #                          (roda bamba, pneu de diametro diferente,
    #                          derrapagem) - nao adianta mexer em KP/KD.
    #   esq != dir          -> sobrou erro de sincronismo. A diferenca em
    #                          graus vira erro de direcao:
    #                          angulo = diferenca * MM_POR_GRAU / ENTRE_EIXOS
    #   uma delas perto de 0 -> a correcao esta zerando aquela roda. Abaixe
    #                          CORRECAO_MAX_FRAC (0.5 -> 0.3) e/ou KD.
    #
    # O ciclo real tambem sai impresso. Ele NAO e DT: e DT mais o custo de
    # ler os encoders e escrever nos motores. So esta aqui para conferir que
    # nao explodiu (uns 3x DT ja e muito) - o KD nao depende mais dele.
    alvo_graus = _mm_para_graus(500)
    andar(500)
    print("TESTE 0 - andar(500)")
    print("  alvo :", alvo_graus, "graus por roda")
    print("  esq  :", motor_B.angle())
    print("  dir  :", motor_C.angle())
    print("  dif  :", motor_B.angle() - motor_C.angle(), "graus")
    wait(1000)

    relogio_teste = StopWatch()
    for _ in range(100):
        motor_B.angle()
        motor_C.angle()
        motor_B.run(0)
        motor_C.run(0)
        wait(DT)
    print("  ciclo real:", relogio_teste.time() / 100.0, "ms   (DT =", DT, ")")
    parar()
    wait(1000)
    andar(-500)
    wait(1000)

    # ---- TESTE 1: distancia -------------------------------------------------
    # Marque o chao, rode, meca com regua.
    #   Andou MENOS que 500 mm -> DIMINUA  DIAMETRO_RODA
    #   Andou MAIS  que 500 mm -> AUMENTE  DIAMETRO_RODA
    #andar(500)
    #wait(1000)
    #andar(-500)
    #wait(1000)

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
    # O argumento e a roda que SE MEXE, entao nas duas linhas abaixo quem
    # gira e a direita e o pivo e a ESQUERDA. Marque no chao onde esta a
    # roda parada: ela nao pode sair do lugar. Se escorregar, o problema e
    # mecanico (peso mal distribuido, pouca aderencia), nao de codigo.
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