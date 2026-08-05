#!/usr/bin/env pybricks-micropython
"""
linha.py - Seguidor de linha com dois sensores
==============================================

Hardware vem do setup.py. Constantes fisicas vem do movimento.py.

COMO USAR
---------
    seguir_linha(tempo_ms=6000)                     # segue por 6 segundos
    seguir_linha(distancia_mm=500)                  # segue 50 cm
    seguir_linha(tempo_ms=8000, parar_se=[cruzamento()])

Os dois sensores ficam UM DE CADA LADO da linha preta (a linha passa entre
eles). Se o robo corrigir para o lado errado, use inverter=True.

Criterios de parada disponiveis:
    distancia  - andou X milimetros
    tempo      - passou X milissegundos  (USE SEMPRE, como rede de seguranca)
    cruzamento - os DOIS sensores no preto ao mesmo tempo
    viu_escuro / viu_claro / viu_cor  - um sensor especifico
"""

import math
from pybricks.parameters import Color
from pybricks.tools import wait, StopWatch

from setup import ev3, motor_B, motor_C, sensor_esq, sensor_dir
from movimento import (
    MM_POR_GRAU, ENTRE_EIXOS, V_LIMITE, DT,
    _perfil_velocidade, _limitar,
)


# =============================================================================
# 1. PARAMETROS DE CONTROLE
# =============================================================================

# --- Velocidade do seguidor, em graus/s da roda ---
V_LINHA = 400.0    # cruzeiro. Comece BAIXO (250) e va subindo conforme o PD
                   # ficar estavel. Nao adianta velocidade alta com o robo
                   # serpenteando.
V_MIN_LINHA = 60.0

ACEL_LINHA    = 900.0
DESACEL_LINHA = 1200.0

# --- Ganhos do PD da linha ---
# Diferentes dos KP/KD de movimento.py: la e sincronismo entre rodas,
# aqui e posicao em relacao a linha.
KP_LINHA = 3.0   # forca da correcao. Robo sai da linha nas curvas -> aumente.
KD_LINHA = 12.0  # amortecimento. Robo serpenteia / oscila -> aumente.

# --- Ganhos do PD de alinhamento ---
# Atua sobre a LEITURA do sensor: quanto mais escuro ele ja esta lendo,
# mais devagar a roda anda. Assim ela chega na linha rastejando.
KP_ALINHA = 6.0    # robo para longe da linha / muito lento -> aumente
KD_ALINHA = 15.0   # robo ainda passa da linha -> aumente

LIMIAR_PRETO = 25   # abaixo disso, considera preto

TIMEOUT_PADRAO = 20000   # ms. Trava de seguranca: nada roda pra sempre.


# =============================================================================
# 2. CALIBRACAO
# =============================================================================
# Cada sensor le valores diferentes no mesmo preto e no mesmo branco. Sem
# normalizar, o PD nasce com erro constante e o robo anda torto - e voces
# tentariam corrigir isso mexendo em KP, que e o caminho errado.

PRETO_PADRAO  = 6
BRANCO_PADRAO = 75

# ATENCAO: no MicroPython do EV3 os objetos ColorSensor NAO sao hashable,
# ou seja, nao podem ser chave de dicionario. Por isso a calibracao fica em
# duas variaveis simples em vez de um dict {sensor: valores}.
# A comparacao e feita com 'is' (mesma identidade de objeto).
_cal_esq = (PRETO_PADRAO, BRANCO_PADRAO)
_cal_dir = (PRETO_PADRAO, BRANCO_PADRAO)


def calibrar(sensor, preto, branco):
    """Define manualmente os valores de preto e branco de um sensor."""
    global _cal_esq, _cal_dir
    if sensor is sensor_esq:
        _cal_esq = (preto, branco)
    else:
        _cal_dir = (preto, branco)


def ler(sensor):
    """Leitura normalizada 0-100 (0 = preto, 100 = branco)."""
    preto, branco = _cal_esq if sensor is sensor_esq else _cal_dir
    bruto = sensor.reflection()
    if branco <= preto:
        return bruto
    return _limitar((bruto - preto) * 100.0 / (branco - preto), 0.0, 100.0)


def calibrar_varrendo(angulo=60, velocidade=120):
    """
    Calibracao automatica dos dois sensores.

    COMO USAR: posicione o robo com os sensores EM CIMA da linha preta e
    chame no inicio do programa. O robo varre para os dois lados e registra
    o menor e o maior valor de cada sensor.

    Devolve ((preto_esq, branco_esq), (preto_dir, branco_dir)). Se preto e
    branco sairem muito proximos, o sensor esta mal montado: alto demais,
    baixo demais ou torto.
    """
    min_esq = 100
    max_esq = 0
    min_dir = 100
    max_dir = 0

    graus = ((ENTRE_EIXOS / 2.0) * math.radians(angulo)) / MM_POR_GRAU

    # Tres varreduras RELATIVAS: centro -> um lado -> outro lado -> centro
    for delta in (graus, -2.0 * graus, graus):
        motor_B.reset_angle(0)
        motor_C.reset_angle(0)
        sentido = 1 if delta > 0 else -1
        motor_B.run(velocidade * sentido)
        motor_C.run(-velocidade * sentido)
        while abs(motor_B.angle()) < abs(delta):
            ve = sensor_esq.reflection()
            vd = sensor_dir.reflection()
            if ve < min_esq:
                min_esq = ve
            if ve > max_esq:
                max_esq = ve
            if vd < min_dir:
                min_dir = vd
            if vd > max_dir:
                max_dir = vd
            wait(5)

    motor_B.brake()
    motor_C.brake()

    calibrar(sensor_esq, min_esq, max_esq)
    calibrar(sensor_dir, min_dir, max_dir)

    ev3.speaker.beep()
    return ((min_esq, max_esq), (min_dir, max_dir))


# =============================================================================
# 3. CRITERIOS DE PARADA
# =============================================================================
# Cada criterio e uma tupla (nome, funcao). Use na lista 'parar_se'.

def viu_escuro(sensor, limiar=LIMIAR_PRETO, nome="escuro"):
    """Dispara quando o sensor entra no preto."""
    def cond():
        return ler(sensor) < limiar
    return (nome, cond)


def viu_claro(sensor, limiar=75, nome="claro"):
    """Dispara quando o sensor entra no branco."""
    def cond():
        return ler(sensor) > limiar
    return (nome, cond)


def viu_cor(sensor, cor, nome=None):
    """
    Dispara quando o sensor reconhece uma cor.
    Cores: Color.BLACK, BLUE, GREEN, YELLOW, RED, WHITE, BROWN.

        viu_cor(sensor_dir, Color.GREEN)
    """
    def cond():
        return sensor.color() == cor
    return (nome or "cor", cond)


def cruzamento(limiar=LIMIAR_PRETO, nome="cruzamento"):
    """
    Dispara quando os DOIS sensores estao no preto ao mesmo tempo.
    E o jeito de detectar uma faixa transversal tendo so dois sensores.
    """
    def cond():
        return ler(sensor_esq) < limiar and ler(sensor_dir) < limiar
    return (nome, cond)


def _checar(criterios):
    """Devolve o nome do primeiro criterio disparado, ou None."""
    if not criterios:
        return None
    for nome, funcao in criterios:
        if funcao():
            return nome
    return None


# =============================================================================
# 4. SEGUIDOR DE LINHA
# =============================================================================

def seguir_linha(distancia_mm=None, tempo_ms=None, parar_se=None,
                 v_max=V_LINHA, v_min=V_MIN_LINHA,
                 acel=ACEL_LINHA, desacel=DESACEL_LINHA,
                 kp=KP_LINHA, kd=KD_LINHA,
                 inverter=False, parar_no_fim=True, segurar=False,
                 timeout=TIMEOUT_PADRAO, ignorar_ms=0, ignorar_mm=0,
                 motor_extra=None, velocidade_extra=0, tempo_extra_ms=0,
                 acionar_extra_mm=None):
    """
    Segue a linha ate algum criterio de parada disparar.
    Devolve o NOME do criterio que parou o robo.

    ---- Criterios (pode combinar quantos quiser) ----
    distancia_mm : para depois de andar essa distancia
    tempo_ms     : para depois desse tempo. SEMPRE use, como rede de seguranca
    parar_se     : lista de criterios, ex: [cruzamento()]

    Retorna "distancia", "tempo", "timeout" ou o nome do criterio.

    ---- Ajustes ----
    inverter     : True se o robo corrigir para o lado errado
    parar_no_fim : False emenda com o proximo movimento sem frear
    ignorar_ms   : ignora os criterios de parar_se nos primeiros N ms.
    ignorar_mm   : ignora os criterios de parar_se nos primeiros N mm.

                   Servem para o mesmo problema: o robo COMECA em cima de
                   uma marca preta e pararia sem sair do lugar. A versao em
                   MILIMETROS e mais confiavel, porque tempo depende da
                   velocidade - que muda com o nivel da bateria e com a
                   rampa de aceleracao. Ja a distancia e direta: "so comece
                   a olhar depois de andar 40 mm".

                   Se os dois forem usados, o criterio so passa a valer
                   quando as DUAS condicoes forem cumpridas.

    ---- Motor extra (ex: girar motor_D sem parar de seguir linha) ----
    motor_extra      : motor a acionar durante o seguimento (ex: motor_D).
                        Disparado com wait=False, entao NAO bloqueia o PD
                        da linha - o motor gira sozinho por conta propria
                        enquanto o loop de seguir_linha continua rodando.
    velocidade_extra : graus/s passados para motor_extra.run_time(...)
    tempo_extra_ms   : duracao em ms passada para motor_extra.run_time(...)
    acionar_extra_mm : distancia percorrida (mm, media das duas rodas) em
                        que motor_extra dispara. Preferir mm a ms pelo
                        mesmo motivo do ignorar_mm: tempo depende da
                        velocidade, que muda com a bateria e a rampa de
                        aceleracao - distancia e direta.
                        Se o seguidor parar mais cedo (por parar_se, por
                        exemplo) antes de chegar nessa distancia, o motor
                        extra dispara mesmo assim ao final, como rede de
                        seguranca - assim ele nunca deixa de girar.

    ---- Exemplos ----
        seguir_linha(tempo_ms=6000)
        seguir_linha(distancia_mm=500)

        # so procura a faixa preta depois de sair de cima da atual
        seguir_linha(tempo_ms=8000, parar_se=[cruzamento()], ignorar_mm=40)

        seguir_linha(tempo_ms=8000, v_max=250,
                     parar_se=[viu_cor(sensor_dir, Color.GREEN)])

        # gira motor_D depois de andar 400 mm seguindo a linha
        seguir_linha(tempo_ms=5000, motor_extra=motor_D,
                     velocidade_extra=400, tempo_extra_ms=1200,
                     acionar_extra_mm=400)
    """
    motor_B.reset_angle(0)
    motor_C.reset_angle(0)

    total = distancia_mm / MM_POR_GRAU if distancia_mm is not None else None
    ignorar_graus = ignorar_mm / MM_POR_GRAU
    acionar_extra_graus = (
        acionar_extra_mm / MM_POR_GRAU if acionar_extra_mm is not None else None
    )

    erro_ant = 0.0
    relogio = StopWatch()
    motivo = "timeout"
    extra_disparado = motor_extra is None

    while True:
        t = relogio.time()

        # Distancia percorrida, em graus de roda. Calculada ANTES dos
        # criterios porque o ignorar_mm e o acionar_extra_mm dependem dela.
        percorrido = (abs(motor_B.angle()) + abs(motor_C.angle())) / 2.0

        # ---- Criterios de parada ----
        if tempo_ms is not None and t >= tempo_ms:
            motivo = "tempo"
            break
        if t >= timeout:
            motivo = "timeout"
            break
        if total is not None and percorrido >= total:
            motivo = "distancia"
            break

        # Os criterios de parar_se so passam a valer depois das duas
        # carencias (tempo E distancia). Com os padroes 0, valem desde o
        # primeiro ciclo.
        if t >= ignorar_ms and percorrido >= ignorar_graus:
            disparou = _checar(parar_se)
            if disparou is not None:
                motivo = disparou
                break

        # ---- Motor extra (nao bloqueia, so dispara e segue o loop) ----
        if not extra_disparado and percorrido >= acionar_extra_graus:
            motor_extra.run_time(velocidade_extra, tempo_extra_ms, wait=False)
            extra_disparado = True

        # ---- Perfil de velocidade ----
        if total is not None:
            # distancia conhecida: acelera no inicio, desacelera no fim
            v = _perfil_velocidade(percorrido, total, v_max, v_min, acel, desacel)
        else:
            # distancia desconhecida: so acelera e mantem cruzeiro
            v = min(v_max, math.sqrt(2.0 * acel * percorrido) + v_min)

        # ---- PD da linha ----
        # erro > 0  =>  sensor esquerdo mais CLARO que o direito
        #           =>  a linha esta mais para a direita
        #           =>  o robo derivou para a esquerda, precisa virar a direita
        erro = ler(sensor_esq) - ler(sensor_dir)
        if inverter:
            erro = -erro

        correcao = kp * erro + kd * (erro - erro_ant)
        erro_ant = erro

        motor_B.run(_limitar(v + correcao, -V_LIMITE, V_LIMITE))
        motor_C.run(_limitar(v - correcao, -V_LIMITE, V_LIMITE))

        wait(DT)

    if parar_no_fim:
        if segurar:
            motor_B.hold()
            motor_C.hold()
        else:
            motor_B.brake()
            motor_C.brake()

    # Rede de seguranca: se o seguidor parou antes de acionar_extra_ms
    # (por causa de parar_se, por exemplo), dispara o motor extra aqui
    # mesmo assim, para ele nunca deixar de girar.
    if not extra_disparado:
        motor_extra.run_time(velocidade_extra, tempo_extra_ms, wait=False)

    return motivo


# =============================================================================
# 5. ALINHAMENTO (reancoragem)
# =============================================================================

def alinhar(velocidade=250, v_min=40, limiar=LIMIAR_PRETO,
            kp=KP_ALINHA, kd=KD_ALINHA, timeout=4000, re=False, segurar=True):
    """
    Esquadreja o robo numa linha preta transversal.

    Cada roda anda de forma INDEPENDENTE ate o seu sensor ver preto. Quem
    chega primeiro para e espera o outro. Resultado: o robo fica
    perpendicular a linha, nao importa com que angulo chegou.

    Aqui NAO ha PD de sincronismo entre as rodas, e isso e proposital: o
    objetivo e desacoplar as duas para que cada uma ache a linha sozinha.
    Sincronizar destruiria o alinhamento.

    Esta e a peca que substitui o giroscopio: em vez de tentar nao acumular
    erro, voces ZERAM o erro contra uma referencia fisica do tapete.
    Use depois de giros ou trechos longos.

    Devolve True se as duas rodas acharam a linha dentro do timeout.
    """
    sentido = -1 if re else 1

    erro_ant_esq = 0.0
    erro_ant_dir = 0.0
    parou_esq = False
    parou_dir = False
    relogio = StopWatch()

    while not (parou_esq and parou_dir):
        if relogio.time() > timeout:
            break

        if not parou_esq:
            erro = ler(sensor_esq) - limiar
            if erro <= 0:
                motor_B.hold() if segurar else motor_B.brake()
                parou_esq = True
            else:
                v = kp * erro + kd * (erro - erro_ant_esq)
                erro_ant_esq = erro
                motor_B.run(_limitar(v, v_min, velocidade) * sentido)

        if not parou_dir:
            erro = ler(sensor_dir) - limiar
            if erro <= 0:
                motor_C.hold() if segurar else motor_C.brake()
                parou_dir = True
            else:
                v = kp * erro + kd * (erro - erro_ant_dir)
                erro_ant_dir = erro
                motor_C.run(_limitar(v, v_min, velocidade) * sentido)

        wait(DT)

    if segurar:
        motor_B.hold()
        motor_C.hold()
    else:
        motor_B.brake()
        motor_C.brake()

    return parou_esq and parou_dir


def procurar_linha(velocidade=250, v_min=60, acel=900.0,
                   limiar=LIMIAR_PRETO, kp=2.5, kd=8.0,
                   timeout=5000, re=False, parar_no_fim=True, ignorar_mm=0):
    """
    Anda reto ate QUALQUER um dos dois sensores ver preto, com PD de
    sincronismo entre as rodas.

    Sem esse PD o robo deriva na aproximacao e chega na linha ja torto,
    o que sobrecarrega o alinhar() logo depois.

    ignorar_mm : so comeca a olhar os sensores depois de andar N mm.
                 Use quando o robo parte de cima de uma linha.

    Devolve True se achou a linha dentro do timeout.
    """
    sentido = -1 if re else 1

    motor_B.reset_angle(0)
    motor_C.reset_angle(0)

    ignorar_graus = ignorar_mm / MM_POR_GRAU
    erro_ant = 0.0
    relogio = StopWatch()
    achou = False

    while relogio.time() < timeout:
        percorrido = (abs(motor_B.angle()) + abs(motor_C.angle())) / 2.0

        if percorrido >= ignorar_graus:
            if ler(sensor_esq) < limiar or ler(sensor_dir) < limiar:
                achou = True
                break

        v = min(velocidade, math.sqrt(2.0 * acel * percorrido) + v_min)

        # '* sentido' converte diferenca de encoder em diferenca de PROGRESSO,
        # para funcionar tambem de re.
        erro = (motor_B.angle() - motor_C.angle()) * sentido
        correcao = kp * erro + kd * (erro - erro_ant)
        erro_ant = erro

        motor_B.run(_limitar((v - correcao) * sentido, -V_LIMITE, V_LIMITE))
        motor_C.run(_limitar((v + correcao) * sentido, -V_LIMITE, V_LIMITE))

        wait(DT)

    if parar_no_fim:
        motor_B.brake()
        motor_C.brake()

    return achou


# =============================================================================
# 6. TESTE / CALIBRACAO
# =============================================================================
# Ordem:
#   1. Confira as leituras cruas (TESTE 0)
#   2. Calibre (TESTE 1)
#   3. Ajuste KP_LINHA e KD_LINHA em velocidade BAIXA (TESTE 2)
#   4. So depois suba V_LINHA

if __name__ == "__main__":

    # ---- TESTE 0: leitura crua ---------------------------------------------
    # Passe o robo sobre preto e branco e anote os valores.
    # while True:
    #     print(sensor_esq.reflection(), sensor_dir.reflection())
    #     wait(200)

    # ---- TESTE 1: calibracao -----------------------------------------------
    # Posicione o robo com os sensores em cima da linha preta.
    print(calibrar_varrendo())
    wait(1000)

    # ---- TESTE 2: PD em velocidade baixa -----------------------------------
    #   Robo serpenteia   -> aumente KD_LINHA
    #   Robo sai na curva -> aumente KP_LINHA
    print("parou por:", seguir_linha(tempo_ms=8000, v_max=250))

    # ---- TESTE 3: parada por cruzamento ------------------------------------
    # print("parou por:", seguir_linha(tempo_ms=8000,
    #                                  parar_se=[cruzamento()],
    #                                  ignorar_ms=300))

    # ---- TESTE 4: reancoragem ----------------------------------------------
    # seguir_linha(tempo_ms=6000, parar_se=[cruzamento()], ignorar_ms=300)
    # alinhar()

    ev3.speaker.beep()