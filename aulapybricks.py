#!/usr/bin/env pybricks-micropython
"""
aprender_pybricks.py - Como escrever programas em Pybricks EV3
==============================================================

Arquivo INDEPENDENTE. Nao importa movimento.py nem linha.py - e um
laboratorio limpo pra experimentar sem quebrar o codigo da competicao.

COMO USAR
---------
Mude o numero da variavel LICAO la embaixo (secao 9) e rode o arquivo.
Cada licao e uma funcao separada, comentada linha a linha.


=============================================================================
ESTRUTURA DE UM PROGRAMA
=============================================================================

Todo programa Pybricks tem a mesma forma:

    1. A primeira linha do arquivo, sempre:   #!/usr/bin/env pybricks-micropython
    2. Os imports do que voces vao usar
    3. A criacao dos objetos (brick, motores, sensores) - UMA VEZ SO, no topo
    4. O programa em si

Os objetos NUNCA sao criados dentro de funcao. Criar dois objetos Motor na
mesma porta da erro.


=============================================================================
AS UNIDADES  (decore isso, e a fonte de 90% dos erros)
=============================================================================

    Velocidade de motor .... GRAUS POR SEGUNDO
                             ~200 devagar, ~500 media, ~800 rapido
                             o limite fisico do motor Large e ~1000

    Tempo .................. MILISSEGUNDOS
                             wait(1000) espera 1 segundo

    Angulo ................. GRAUS
                             360 = uma volta do eixo do motor

    Distancia .............. MILIMETROS
                             straight(300) anda 30 cm

    Leitura de sensor ...... 0 a 100
                             reflection() e ambient() usam essa escala


=============================================================================
DE ONDE VEM CADA COISA  (o que importar)
=============================================================================

    pybricks.hubs ........... EV3Brick
    pybricks.ev3devices ..... Motor, ColorSensor, TouchSensor,
                              UltrasonicSensor, GyroSensor, InfraredSensor
    pybricks.parameters ..... Port, Direction, Color, Stop, Button
    pybricks.robotics ....... DriveBase
    pybricks.tools .......... wait, StopWatch, DataLog
"""

from pybricks.hubs import EV3Brick
from pybricks.ev3devices import Motor, ColorSensor, TouchSensor
from pybricks.parameters import Port, Direction, Color, Stop, Button
from pybricks.robotics import DriveBase
from pybricks.tools import wait, StopWatch


# =============================================================================
# 0. SETUP
# =============================================================================
# Motor(porta, direcao_positiva)
#
# A direcao define o que conta como "positivo" naquele motor. Como as rodas
# de um robo sao montadas espelhadas, uma delas precisa ser COUNTERCLOCKWISE
# para que, nas duas, velocidade positiva signifique "para frente".
#
# Se voces mandarem os dois pra frente e o robo girar no lugar, e aqui que
# se corrige: troque CLOCKWISE por COUNTERCLOCKWISE em um deles.

ev3 = EV3Brick()

motor_A = Motor(Port.A, Direction.CLOCKWISE)
motor_D = Motor(Port.D, Direction.CLOCKWISE)
motor_B = Motor(Port.B, Direction.COUNTERCLOCKWISE)   # roda esquerda
motor_C = Motor(Port.C, Direction.CLOCKWISE)          # roda direita

sensor1 = ColorSensor(Port.S1)
sensor2 = ColorSensor(Port.S2)
sensor3 = ColorSensor(Port.S3)
sensor4 = ColorSensor(Port.S4)


# =============================================================================
# LICAO 1 - O BRICK: tela, luz e som
# =============================================================================

def licao_1():
    """
    A tela e o melhor amigo de voces na hora de calibrar: da pra imprimir
    valor de sensor e ler direto no robo, sem cabo e sem computador.
    """
    # --- Tela ---
    ev3.screen.clear()               # limpa antes de escrever
    ev3.screen.print("Ola, WRO!")    # cada print vai numa linha nova
    ev3.screen.print("Linha 2")

    # print() aceita varios valores, como o print normal do Python
    ev3.screen.print("Sensor:", sensor1.reflection())

    # --- Luz de status ---
    ev3.light.on(Color.RED)
    wait(500)
    ev3.light.on(Color.GREEN)
    wait(500)
    ev3.light.off()

    # --- Som ---
    ev3.speaker.beep()                              # bip padrao
    ev3.speaker.beep(frequency=1000, duration=200)  # agudo e curto
    ev3.speaker.beep(frequency=200, duration=500)   # grave e longo

    # Notas musicais: nome da nota + oitava + / + duracao
    ev3.speaker.play_notes(['C4/4', 'E4/4', 'G4/4', 'C5/2'])

    # O EV3 fala (so em ingles)
    ev3.speaker.say("Robot ready")

    wait(2000)


# =============================================================================
# LICAO 2 - MOTOR: os cinco comandos de movimento
# =============================================================================

def licao_2():
    """
    Todos os comandos de motor comecam pela VELOCIDADE, em graus por segundo.
    """
    # --- 1. run_angle(velocidade, angulo) ---
    # Gira o angulo pedido e para. E o comando mais usado.
    motor_A.run_angle(300, 360)      # uma volta a 300 deg/s
    wait(500)
    motor_A.run_angle(300, -360)     # angulo negativo = sentido contrario
    wait(500)

    # --- 2. run_time(velocidade, tempo_ms) ---
    # Gira por um tempo determinado.
    motor_A.run_time(300, 1000)      # 300 deg/s durante 1 segundo
    wait(500)

    # --- 3. run_target(velocidade, angulo_alvo) ---
    # Vai ate uma posicao ABSOLUTA. A direcao e escolhida sozinha:
    # ele acha o caminho ate o alvo, nao importa onde esteja agora.
    motor_A.reset_angle(0)           # define a posicao atual como zero
    motor_A.run_target(300, 90)      # vai pro angulo 90
    motor_A.run_target(300, 0)       # volta pro zero
    wait(500)

    # --- 4. run(velocidade) ---
    # Comeca a girar e NAO espera. O programa continua na linha seguinte.
    # Use quando voces mesmos vao decidir quando parar.
    motor_A.run(200)
    wait(1500)                       # o motor gira durante esta espera
    motor_A.stop()

    # --- 5. run_until_stalled(velocidade, then, duty_limit) ---
    # Gira ate TRAVAR contra alguma coisa. Perfeito pra encontrar um
    # batente mecanico e zerar a posicao a partir dele.
    # duty_limit limita a forca (em %), pra nao arrebentar o mecanismo.
    motor_A.run_until_stalled(200, then=Stop.HOLD, duty_limit=30)
    motor_A.reset_angle(0)           # o batente agora e o zero
    ev3.speaker.beep()

    # --- Ler a posicao ---
    # angle() ACUMULA: tres voltas seguidas devolvem 1080, nao 0.
    ev3.screen.print("angulo:", motor_A.angle())
    ev3.screen.print("veloc:", motor_A.speed())

    # --- Os tres jeitos de parar ---
    motor_A.stop()    # solta: o motor gira livre e para por atrito
    motor_A.brake()   # freia: resiste, mas cede se voce empurrar
    motor_A.hold()    # trava: segura a posicao ativamente, com forca


# =============================================================================
# LICAO 3 - ESPERAR OU NAO ESPERAR
# =============================================================================

def licao_3():
    """
    Por padrao, run_angle() PARA o programa e so devolve o controle quando
    o motor termina. Com wait=False ele dispara o comando e segue na hora.

    E assim que se faz duas coisas ao mesmo tempo no Pybricks.
    """
    # --- Padrao: um depois do outro ---
    ev3.screen.clear()
    ev3.screen.print("Um de cada vez")
    motor_A.run_angle(300, 360)      # espera terminar...
    motor_D.run_angle(300, 360)      # ...e so entao comeca este

    wait(1000)

    # --- wait=False: os dois juntos ---
    ev3.screen.print("Os dois juntos")
    motor_A.run_angle(300, 360, wait=False)
    motor_D.run_angle(300, 360, wait=False)

    # control.done() diz se o comando daquele motor ja acabou.
    # Use quando precisar sincronizar de novo:
    while not motor_A.control.done() or not motor_D.control.done():
        wait(10)

    ev3.speaker.beep()

    # --- O uso real disso ---
    # Levantar a garra ENQUANTO o robo anda, em vez de um depois do outro:
    #
    #     motor_A.run_angle(500, 180, wait=False)   # garra comeca a subir
    #     robo.straight(400)                        # robo anda ao mesmo tempo
    #     while not motor_A.control.done():         # so entao espera a garra
    #         wait(10)


# =============================================================================
# LICAO 4 - SENSOR DE COR: as quatro leituras
# =============================================================================

def licao_4():
    """
    O sensor de cor tem quatro modos. Escolher o certo muda completamente
    o desempenho do robo.
    """
    ev3.screen.clear()
    relogio = StopWatch()

    while relogio.time() < 15000:      # roda por 15 segundos
        ev3.screen.clear()

        # --- 1. reflection() -> 0 a 100 ---
        # Acende luz vermelha e mede quanto voltou.
        # E ESTE que se usa pra seguir linha: e rapido e devolve um numero
        # continuo, que da pra jogar direto num PD.
        ev3.screen.print("refl:", sensor1.reflection())

        # --- 2. color() -> Color.ALGUMACOISA, ou None ---
        # Tenta adivinhar a cor. Devolve um objeto Color:
        #   Color.BLACK, BLUE, GREEN, YELLOW, RED, WHITE, BROWN
        # Devolve None quando nao reconhece nada.
        cor = sensor1.color()
        ev3.screen.print("cor:", cor)

        # Comparacao:
        if cor == Color.GREEN:
            ev3.light.on(Color.GREEN)
        elif cor == Color.RED:
            ev3.light.on(Color.RED)
        else:
            ev3.light.off()

        # --- 3. rgb() -> tres valores de 0 a 100 ---
        # Mede vermelho, verde e azul separadamente. Da mais informacao que
        # color(), e voces mesmos definem o criterio. Util quando color()
        # confunde duas cores parecidas do tapete.
        r, g, b = sensor1.rgb()
        ev3.screen.print("rgb:", int(r), int(g), int(b))

        # --- 4. ambient() -> 0 a 100 ---
        # Luz do ambiente, sem acender o LED. Quase nao serve em competicao,
        # porque a iluminacao do salao muda o tempo todo.

        wait(300)


# =============================================================================
# LICAO 5 - DRIVEBASE: comandar as duas rodas juntas
# =============================================================================

def licao_5():
    """
    DriveBase junta os dois motores de tracao num objeto so, que aceita
    comandos em milimetros e graus do ROBO (nao do motor).

    AVISO IMPORTANTE - e por isso que o movimento.py nao usa DriveBase:
    enquanto o DriveBase estiver ATIVO, voces NAO podem comandar motor_B e
    motor_C individualmente. E ele continua ativo DEPOIS de terminar um
    straight(), porque segue segurando as rodas no lugar.
    So o robo.stop() libera os motores de novo.
    """
    # DriveBase(motor_esquerdo, motor_direito, diametro_roda, entre_eixos)
    # As duas medidas em milimetros.
    robo = DriveBase(motor_B, motor_C, wheel_diameter=62.4, axle_track=185)

    # settings(veloc_reta, acel_reta, veloc_giro, acel_giro)
    # reta em mm/s e mm/s^2; giro em graus/s e graus/s^2
    robo.settings(300, 500, 150, 300)

    robo.straight(300)        # 300 mm pra frente
    wait(500)
    robo.straight(-300)       # 300 mm de re
    wait(500)

    robo.turn(90)             # 90 graus no proprio eixo, sentido horario
    wait(500)
    robo.turn(-90)            # anti-horario

    # drive(velocidade_reta, taxa_de_giro) -> movimento continuo, nao para
    robo.drive(200, 30)       # 200 mm/s andando e girando 30 graus/s = curva
    wait(2000)

    # Medidas acumuladas desde o inicio
    ev3.screen.print("dist:", robo.distance())
    ev3.screen.print("ang:", robo.angle())

    # Obrigatorio pra liberar motor_B e motor_C
    robo.stop()


# =============================================================================
# LICAO 6 - LOOPS: esperar uma condicao
# =============================================================================

def licao_6():
    """
    Padrao classico: liga os motores, espera uma condicao acontecer, para.
    E o esqueleto de quase tudo que um robo de competicao faz.
    """
    # --- Andar ate ver preto ---
    motor_B.run(300)
    motor_C.run(300)

    while sensor1.reflection() > 20:     # enquanto estiver CLARO, continua
        wait(10)                         # o wait e obrigatorio: sem ele o
                                         # loop trava o processador

    motor_B.brake()
    motor_C.brake()
    ev3.speaker.beep()

    wait(1000)

    # --- O mesmo, com trava de tempo ---
    # SEMPRE facam isso na competicao. Sem o relogio, se o sensor nunca ver
    # preto, o robo anda pra sempre e voces perdem a rodada.
    relogio = StopWatch()
    motor_B.run(-300)
    motor_C.run(-300)

    while sensor1.reflection() > 20:
        if relogio.time() > 3000:        # rede de seguranca: 3 segundos
            ev3.screen.print("Desisti!")
            break                        # sai do loop
        wait(10)

    motor_B.brake()
    motor_C.brake()


# =============================================================================
# LICAO 7 - BOTOES E CRONOMETRO
# =============================================================================

def licao_7():
    """
    Os botoes do brick servem pra escolher qual missao rodar sem precisar
    reconectar o computador no meio do treino.
    """
    ev3.screen.clear()
    ev3.screen.print("Aperte um botao")
    ev3.screen.print("BAIXO = sair")

    while True:
        # pressed() devolve uma LISTA com os botoes apertados neste instante.
        # Botoes: Button.LEFT, RIGHT, UP, DOWN, CENTER
        botoes = ev3.buttons.pressed()

        if Button.LEFT in botoes:
            ev3.light.on(Color.GREEN)
            ev3.screen.print("ESQUERDA")
            wait(300)

        elif Button.RIGHT in botoes:
            ev3.light.on(Color.RED)
            ev3.screen.print("DIREITA")
            wait(300)

        elif Button.CENTER in botoes:
            ev3.speaker.beep()
            ev3.screen.print("CENTRO")
            wait(300)

        elif Button.DOWN in botoes:
            break

        wait(50)

    # --- Cronometro ---
    relogio = StopWatch()          # ja comeca a contar
    motor_A.run_angle(500, 720)
    ev3.screen.print("Levou", relogio.time(), "ms")

    relogio.reset()                # zera
    relogio.pause()                # congela
    relogio.resume()               # volta a contar


# =============================================================================
# LICAO 8 - DESAFIO: juntando tudo
# =============================================================================

def licao_8():
    """
    Mini-missao usando os conceitos das licoes anteriores:
      1. Espera apertar CENTRO pra comecar
      2. Anda ate achar a linha preta
      3. Le a cor e reage
      4. Gira e volta

    Depois de rodar, tentem reescrever este programa do zero sem olhar.
    """
    # --- 1. Espera o botao ---
    ev3.screen.clear()
    ev3.screen.print("CENTRO p/ comecar")
    while Button.CENTER not in ev3.buttons.pressed():
        wait(50)
    ev3.speaker.beep()

    # --- 2. Anda ate achar preto, com trava de tempo ---
    relogio = StopWatch()
    motor_B.run(300)
    motor_C.run(300)
    achou = False

    while relogio.time() < 5000:
        if sensor1.reflection() < 20:
            achou = True
            break
        wait(10)

    motor_B.brake()
    motor_C.brake()

    if not achou:
        ev3.speaker.say("I got lost")
        return                      # sai da funcao aqui mesmo

    # --- 3. Le a cor e reage ---
    ev3.speaker.beep()
    cor = sensor1.color()
    ev3.screen.print("Achei:", cor)

    if cor == Color.GREEN:
        motor_A.run_angle(500, 180)                     # abre a garra
    elif cor == Color.RED:
        motor_A.run_angle(500, -180)                    # fecha
    else:
        ev3.speaker.beep(frequency=200, duration=500)   # grave = nao reconheci

    # --- 4. Gira e volta ---
    robo = DriveBase(motor_B, motor_C, wheel_diameter=62.4, axle_track=185)
    robo.turn(180)
    robo.straight(200)
    robo.stop()                     # libera os motores

    ev3.speaker.say("Done")


# =============================================================================
# 9. ESCOLHA A LICAO AQUI
# =============================================================================

LICAO = 1

if __name__ == "__main__":

    licoes = {
        1: licao_1,
        2: licao_2,
        3: licao_3,
        4: licao_4,
        5: licao_5,
        6: licao_6,
        7: licao_7,
        8: licao_8,
    }

    ev3.screen.clear()
    ev3.screen.print("Licao", LICAO)
    wait(1000)

    licoes[LICAO]()

    ev3.speaker.beep()