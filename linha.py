#!/usr/bin/env pybricks-micropython
"""
linha.py - Seguidor de linha com dois sensores
==============================================

Hardware vem do setup.py, numeros vem do constantes.py.

COMO USAR
---------
    seguir_linha(tempo_ms=6000)                     # segue por 6 segundos
    seguir_linha(distancia_mm=500)                  # segue 50 cm
    seguir_linha(tempo_ms=8000, parar_se=[cruzamento()])
    seguir_linha(parar_se=[cruzamento()], kp=1.5, kd=12, v_max=600,
                 tempo_ms=5000, ignorar_mm=170)

Os dois sensores ficam UM DE CADA LADO da linha preta (a linha passa entre
eles). Se o robo corrigir para o lado errado, use inverter=True.

Criterios de parada disponiveis:
    distancia  - andou X milimetros
    tempo      - passou X milissegundos  (USE SEMPRE, como rede de seguranca)
    cruzamento - os DOIS sensores no preto ao mesmo tempo
    viu_escuro / viu_claro / viu_cor  - um sensor especifico

CALIBRACAO DOS SENSORES: ja vem carregada do constantes.py
(CAL_SENSOR_ESQ / CAL_SENSOR_DIR) no momento do import. Nao ha nada para
chamar no comeco do programa. Para medir os valores de novo, rode este
arquivo com F5 no TESTE 1 (calibrar_varrendo) e copie o resultado para o
constantes.py.
"""

import math
from pybricks.tools import wait, StopWatch

import constantes as cte
from setup import ev3, motor_B, motor_C, sensor_esq, sensor_dir
from movimento import _perfil_velocidade, _limitar, parar


# =============================================================================
# 1. CALIBRACAO
# =============================================================================
# Cada sensor le valores diferentes no mesmo preto e no mesmo branco. Sem
# normalizar, o PD nasce com erro constante e o robo anda torto - e voces
# tentariam corrigir isso mexendo em KP, que e o caminho errado.
#
# ATENCAO: no MicroPython do EV3 os objetos ColorSensor NAO sao hashable,
# ou seja, nao podem ser chave de dicionario. Por isso a calibracao fica
# em duas variaveis simples em vez de um dict {sensor: valores}, e a
# comparacao e feita com 'is' (mesma identidade de objeto).

_cal_esq = cte.CAL_SENSOR_ESQ
_cal_dir = cte.CAL_SENSOR_DIR


def calibrar(sensor, preto, branco):
    """
    Troca em tempo de execucao o preto e o branco de um sensor.

    Os valores da prova ficam no constantes.py e ja estao valendo desde o
    import - esta funcao serve para o calibrar_varrendo aplicar o que
    acabou de medir.
    """
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


def calibrar_varrendo(angulo=cte.VARREDURA_ANGULO,
                      velocidade=cte.VARREDURA_VELOCIDADE):
    """
    Calibracao automatica dos dois sensores.

    COMO USAR: posicione o robo com os sensores EM CIMA da linha preta e
    rode o TESTE 1 deste arquivo. O robo varre para os dois lados e
    registra o menor e o maior valor de cada sensor.

    Devolve ((preto_esq, branco_esq), (preto_dir, branco_dir)). COPIE OS
    QUATRO NUMEROS para CAL_SENSOR_ESQ / CAL_SENSOR_DIR no constantes.py -
    o que esta funcao aplica vale so ate o programa acabar.

    Se preto e branco sairem muito proximos, o sensor esta mal montado:
    alto demais, baixo demais ou torto.
    """
    min_esq = 100
    max_esq = 0
    min_dir = 100
    max_dir = 0

    graus = ((cte.ENTRE_EIXOS / 2.0) * math.radians(angulo)) / cte.MM_POR_GRAU

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

    parar()

    calibrar(sensor_esq, min_esq, max_esq)
    calibrar(sensor_dir, min_dir, max_dir)

    ev3.speaker.beep()
    return ((min_esq, max_esq), (min_dir, max_dir))


# =============================================================================
# 2. CRITERIOS DE PARADA
# =============================================================================
# Cada criterio e uma tupla (nome, funcao). Use na lista 'parar_se'.

def viu_escuro(sensor, limiar=cte.LIMIAR_PRETO, nome="escuro"):
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


def cruzamento(limiar=cte.LIMIAR_PRETO, nome="cruzamento"):
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
# 3. SEGUIDOR DE LINHA
# =============================================================================

def seguir_linha(distancia_mm=None, tempo_ms=None, parar_se=None,
                 v_max=cte.V_LINHA, v_min=cte.V_MIN_LINHA,
                 acel=cte.ACEL_LINHA, desacel=cte.DESACEL_LINHA,
                 kp=cte.KP_LINHA, kd=cte.KD_LINHA,
                 inverter=False, parar_no_fim=True, segurar=False,
                 timeout=cte.TIMEOUT_LINHA_MS, ignorar_mm=0):
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
    ignorar_mm   : ignora os criterios de parar_se nos primeiros N mm.

                   Serve para quando o robo COMECA em cima de uma marca
                   preta e pararia sem sair do lugar. E em MILIMETROS, e
                   nao em tempo, porque tempo depende da velocidade - que
                   muda com o nivel da bateria e com a rampa de
                   aceleracao. A distancia e direta: "so comece a olhar
                   depois de andar 40 mm".

    ---- Exemplos ----
        seguir_linha(tempo_ms=6000)
        seguir_linha(distancia_mm=500)

        # so procura a faixa preta depois de sair de cima da atual
        seguir_linha(tempo_ms=8000, parar_se=[cruzamento()], ignorar_mm=40)

        # com os ganhos daquele trecho, escritos na propria chamada
        seguir_linha(parar_se=[cruzamento()], kp=1, kd=13, v_max=1000,
                     desacel=4000, tempo_ms=5000, ignorar_mm=520)
    """
    motor_B.reset_angle(0)
    motor_C.reset_angle(0)

    total = distancia_mm / cte.MM_POR_GRAU if distancia_mm is not None else None
    ignorar_graus = ignorar_mm / cte.MM_POR_GRAU

    erro_ant = 0.0
    relogio = StopWatch()
    motivo = "timeout"

    while True:
        t = relogio.time()

        # Distancia percorrida, em graus de roda. Calculada ANTES dos
        # criterios porque o ignorar_mm depende dela.
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

        # Os criterios de parar_se so passam a valer depois da carencia
        # de distancia. Com o padrao 0, valem desde o primeiro ciclo.
        if percorrido >= ignorar_graus:
            disparou = _checar(parar_se)
            if disparou is not None:
                motivo = disparou
                break

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

        motor_B.run(_limitar(v + correcao, -cte.V_LIMITE, cte.V_LIMITE))
        motor_C.run(_limitar(v - correcao, -cte.V_LIMITE, cte.V_LIMITE))

        wait(cte.DT)

    if parar_no_fim:
        parar(segurar)

    return motivo


# =============================================================================
# 4. ALINHAMENTO (reancoragem)
# =============================================================================

def alinhar(velocidade=cte.V_ALINHA, v_min=cte.V_MIN_ALINHA,
            limiar=cte.LIMIAR_PRETO,
            kp=cte.KP_ALINHA, kd=cte.KD_ALINHA,
            timeout=cte.TIMEOUT_ALINHA_MS, re=False, segurar=True):
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

        wait(cte.DT)

    parar(segurar)

    return parou_esq and parou_dir


def procurar_linha(velocidade=cte.V_PROCURA, v_min=cte.V_MIN_PROCURA,
                   acel=cte.ACEL_PROCURA, limiar=cte.LIMIAR_PRETO,
                   kp=cte.KP_PROCURA, kd=cte.KD_PROCURA,
                   timeout=cte.TIMEOUT_PROCURA_MS, re=False,
                   parar_no_fim=True, ignorar_mm=0):
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

    ignorar_graus = ignorar_mm / cte.MM_POR_GRAU
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

        motor_B.run(_limitar((v - correcao) * sentido, -cte.V_LIMITE, cte.V_LIMITE))
        motor_C.run(_limitar((v + correcao) * sentido, -cte.V_LIMITE, cte.V_LIMITE))

        wait(cte.DT)

    if parar_no_fim:
        parar()

    return achou


# =============================================================================
# 5. TESTE / CALIBRACAO
# =============================================================================
# Mude o numero de TESTE la embaixo e rode este arquivo com F5.
#
#   0 -> leitura crua dos dois sensores (anote preto e branco)
#   1 -> calibracao automatica: copie os 4 numeros para o constantes.py
#   2 -> PD em velocidade baixa: ajuste KP_LINHA e KD_LINHA
#   3 -> parada por cruzamento
#   4 -> reancoragem (seguir ate o cruzamento e esquadrejar)
#
# So depois que o PD estiver estavel e que faz sentido subir V_LINHA.

def _teste_0_leitura():
    """Passe o robo sobre preto e branco e anote os valores."""
    for _ in range(50):
        print(sensor_esq.reflection(), sensor_dir.reflection())
        wait(200)


def _teste_1_calibrar():
    """Sensores EM CIMA da linha preta. Copie o resultado ao constantes.py."""
    print(calibrar_varrendo())


def _teste_2_pd():
    """
    Robo serpenteia   -> aumente KD_LINHA
    Robo sai na curva -> aumente KP_LINHA
    """
    print("parou por:", seguir_linha(tempo_ms=8000, v_max=250))


def _teste_3_cruzamento():
    print("parou por:", seguir_linha(tempo_ms=8000,
                                     parar_se=[cruzamento()],
                                     ignorar_mm=40))


def _teste_4_reancoragem():
    seguir_linha(tempo_ms=6000, parar_se=[cruzamento()], ignorar_mm=40)
    alinhar()


if __name__ == "__main__":

    TESTE = 1

    testes = (_teste_0_leitura, _teste_1_calibrar, _teste_2_pd,
              _teste_3_cruzamento, _teste_4_reancoragem)
    testes[TESTE]()

    ev3.speaker.beep()
