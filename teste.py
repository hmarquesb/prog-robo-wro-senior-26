#!/usr/bin/env pybricks-micropython
"""
teste.py - Rascunho: escreva aqui o que quiser testar agora
===========================================================

ARQUIVO DE BANCADA, NAO ENTRA NA PROVA. Nenhum outro arquivo importa este
- da para escrever qualquer coisa aqui sem risco de quebrar a rodada.

COMO USAR: mude o TESTE la embaixo e rode com F5.

    TESTE = 0   RASCUNHO - a area vazia. E aqui que voce escreve.
    TESTE = 1   motor_A pelos botoes: da graus e mostra onde parou
    TESTE = 2   leitura ao vivo dos dois sensores de cor
    TESTE = 3   garra pelos botoes: sobe, desce, zera
    TESTE = 4   servo: passeia pelas 3 colunas

O TESTE 0 nasce vazio DE PROPOSITO. Escreva la, rode, apague, escreva
outra coisa. Nao precisa preservar nada - os testes 1 a 4 continuam
guardados abaixo dele.

TUDO JA ESTA IMPORTADO (ver o bloco de imports): os quatro motores, os
dois sensores, movimento, linha, garra e servos. Nao precisa mexer nos
imports para testar nada.

    Varios desses imports estao sem uso AGORA, e isso e proposital: e o
    que faz o rascunho ficar pronto para receber qualquer coisa sem uma
    ida ao topo do arquivo. Nao "limpe" esta lista.

    m.andar(200)                    m.girar_eixo(90)
    m.andar(200, v_max=300)         m.girar_pivo(motor_C, 90)
    m.andar_por_tempo(1000, 300)    m.girar_arco(200, 45)

    lin.seguir_linha(tempo_ms=3000, parar_se=[lin.cruzamento()])
    lin.alinhar()                   lin.ler(sensor_esq)

    motor_A.run_angle(1000, 320)    motor_A.run_target(1000, 420)
    motor_A.run_angle(1000, -320)   motor_A.angle()
    motor_A.reset_angle(0)

    O SINAL DO MOVIMENTO VAI NO ANGULO, com a velocidade positiva.
    run_angle(-1000, 320) tambem anda, mas misturar as duas formas no
    mesmo programa faz voce perder a conta de para que lado o mecanismo
    foi. Escolha uma - aqui e sempre o sinal no angulo.

    g.zerar_garra()                 g.descer_garra()
    g.mover_garra(600, 720)         g.angulo_garra()

    sv.selecionar_coluna(2)         sv.repouso()

ATALHOS DESTE ARQUIVO (definidos logo abaixo):

    esperar_botao()     espera um aperto e devolve qual foi
    esperar_centro()    espera o CENTER - para pausar entre dois passos
    pausa("texto")      imprime, apita e espera o CENTER

O botao VOLTAR do brick para o programa a qualquer momento.
"""

from pybricks.parameters import Button, Stop, Color
from pybricks.tools import wait, StopWatch

import constantes as cte
import movimento as m
import linha as lin
import garra as g
import servos as sv
from setup import ev3, motor_A, motor_B, motor_C, motor_D
from setup import sensor_esq, sensor_dir


# =============================================================================
# ATALHOS
# =============================================================================

def esperar_botao(botoes=(Button.LEFT, Button.CENTER, Button.RIGHT,
                          Button.UP, Button.DOWN)):
    """
    Espera um aperto NOVO de um dos `botoes` e devolve qual foi.

    Espera soltar o que ja estivesse pressionado, espera o aperto e
    espera soltar de novo - assim um dedo segurando o botao nao dispara
    varios ciclos seguidos.
    """
    while ev3.buttons.pressed():
        wait(10)
    while True:
        pressionados = ev3.buttons.pressed()
        for b in botoes:
            if b in pressionados:
                while ev3.buttons.pressed():
                    wait(10)
                return b
        wait(10)


def esperar_centro():
    """Espera o botao CENTER. Para pausar entre um passo e outro."""
    esperar_botao((Button.CENTER,))


def pausa(texto="aperte CENTER"):
    """Imprime, apita e espera o CENTER - o pare-e-meca de sempre."""
    print(texto)
    ev3.speaker.beep()
    esperar_centro()


# =============================================================================
# TESTE 0 - RASCUNHO
# =============================================================================

def _teste_0_rascunho():
    """
    ESCREVA AQUI. Apague o exemplo e ponha o que quiser testar.

    Nada aqui e sagrado - este e o unico lugar do projeto onde codigo
    descartavel e o esperado.
    """
    print("=== rascunho ===")

    # ---- exemplo, apague ----------------------------------------------
    motor_A.run_angle(1000, 360)
    
    lin.seguir_linha(parar_se=[lin.cruzamento()], kp=1, kd=12, v_max=900,
                     desacel=3000, tempo_ms=5000, ignorar_mm=180)

    m.andar(180, v_max=700, v_min=200, acel=600, desacel=1800,
                    kp=2.5, kd=3.5)

    motor_A.run_angle(-1000, 360)
    

    # -------------------------------------------------------------------


# =============================================================================
# TESTE 1 - motor_A pelos botoes
# =============================================================================

# Tamanhos de passo, do mais fino ao mais grosso. LISTA FIXA, e nao
# multiplicar/dividir por 10: com divisao inteira o passo caia para 5, e
# dai para 1, e o carrinho parava de andar visivelmente sem que desse
# para voltar ao valor de antes.
PASSOS_A = (5, 10, 25, 50, 100, 250, 500)
PASSO_INICIAL = 3     # indice em PASSOS_A - comeca em 50 graus

V_A = 800             # graus/s. SEMPRE POSITIVO - ver a nota do sentido.

# Zeragem contra o batente (CENTER). Mesmos numeros do pegar_blocos.py.
V_ZERAR_A     = -400
FORCA_ZERAR_A = 60


def _teste_1_motor_a():
    """
    Move o motor_A em passos e imprime o angulo depois de cada um. E o
    jeito rapido de descobrir quantos graus vale um movimento antes de
    escrever o numero numa rotina.

        UP     -> anda +passo   (angulo POSITIVO)
        DOWN   -> anda -passo   (angulo NEGATIVO)
        LEFT   -> passo menor   (anda menos por aperto)
        RIGHT  -> passo maior
        CENTER -> zera contra o batente e marca angulo 0
        VOLTAR -> sai

    QUEM INVERTE O SENTIDO E O UP/DOWN, nao o LEFT/RIGHT. O LEFT/RIGHT so
    escolhe o TAMANHO do passo, e sempre um valor positivo - ele nunca
    faz o carrinho ir para o outro lado.

    O SINAL VAI NO ANGULO, E A VELOCIDADE FICA POSITIVA:

        motor_A.run_angle(800, -50)     # assim
        motor_A.run_angle(-800, 50)     # nao assim

    As duas formas existem no Pybricks, mas misturar as duas no mesmo
    programa e o jeito mais rapido de perder a conta de para que lado o
    mecanismo foi. Este teste usa so a primeira.

    O angulo impresso e ABSOLUTO, contado do ultimo CENTER. Anote o valor
    quando o mecanismo estiver onde voce quer - e esse numero que vai
    para o run_target da rotina.

    CUIDADO AO CRUZAR O ZERO: no negativo a embreagem engata o OUTRO
    mecanismo. Se um passo mexer no que voce nao esperava, olhe o angulo
    impresso - provavelmente ele acabou de trocar de sinal.
    """
    indice = PASSO_INICIAL
    print("=== motor_A ===")
    print("UP/DOWN move  LEFT/RIGHT muda o tamanho do passo  CENTER zera")
    print("passo:", PASSOS_A[indice], "graus   angulo:", motor_A.angle())

    while True:
        botao = esperar_botao()

        if botao == Button.CENTER:
            motor_A.run_until_stalled(V_ZERAR_A, then=Stop.HOLD,
                                      duty_limit=FORCA_ZERAR_A)
            motor_A.reset_angle(0)
            print("zerado no batente - angulo 0")
            continue

        if botao == Button.LEFT:
            indice = max(0, indice - 1)
            print("passo:", PASSOS_A[indice], "graus")
            continue

        if botao == Button.RIGHT:
            indice = min(len(PASSOS_A) - 1, indice + 1)
            print("passo:", PASSOS_A[indice], "graus")
            continue

        delta = PASSOS_A[indice] if botao == Button.UP else -PASSOS_A[indice]
        motor_A.run_angle(V_A, delta)
        print(delta, "graus  ->  agora em", motor_A.angle())


# =============================================================================
# TESTE 2 - sensores de cor ao vivo
# =============================================================================

def _teste_2_sensores(vezes=200):
    """
    Imprime as duas leituras a cada 200 ms, cruas e normalizadas, mais a
    cor que cada sensor reconhece.

        reflexao : 0 a 100 como o sensor devolve, sem calibracao
        lin.ler  : 0 a 100 ja normalizado pelo CAL_SENSOR_* do
                   constantes.py - e ISTO que o seguidor de linha usa
        cor      : o sensor.color(), que e o que a varredura do mosaico le

    O QUE CONFERIR: passe os sensores por preto e por branco. Se o valor
    normalizado nao chegar perto de 0 no preto e de 100 no branco, a
    calibracao esta velha - rode linha.py no TESTE 1 e copie os quatro
    numeros para o constantes.py.
    """
    print("=== sensores ===  esq(bruto,norm,cor) | dir(bruto,norm,cor)")
    for _ in range(vezes):
        print(sensor_esq.reflection(), int(lin.ler(sensor_esq)),
              sensor_esq.color(), " | ",
              sensor_dir.reflection(), int(lin.ler(sensor_dir)),
              sensor_dir.color())
        wait(200)


# =============================================================================
# TESTE 3 - garra pelos botoes
# =============================================================================

SUBIR_V  = 600
SUBIR_MS = 720


def _teste_3_garra():
    """
    Sobe, desce e zera a garra pelos botoes, imprimindo o angulo.

        UP     -> sobe por tempo (SUBIR_V x SUBIR_MS) - o mesmo tipo de
                  movimento do arremesso
        DOWN   -> desce ate g.ANGULO_ABAIXADA (angulo absoluto)
        CENTER -> zera: desce ao batente e chama aquele ponto de zero
        VOLTAR -> sai

    ZERE ANTES DE MAIS NADA (CENTER): sem isso o angulo impresso nao tem
    referencia nenhuma.

    E ZERE COM O CARRINHO FORA DO BATENTE - com ele recolhido a garra
    bate na estrutura do robo antes do fim do curso e o zero sai alto.
    Use o TESTE 1 para tirar o carrinho primeiro, ou descomente a linha
    do motor_A aqui embaixo.
    """
    print("=== garra ===")
    print("UP sobe  DOWN desce  CENTER zera")

    # Descomente para tirar o carrinho do batente antes de zerar:
    # motor_A.run_angle(1000, 120)

    while True:
        botao = esperar_botao()

        if botao == Button.CENTER:
            g.zerar_garra()
            print("zerada - agora em", g.angulo_garra(), "graus")
        elif botao == Button.UP:
            g.mover_garra(SUBIR_V, SUBIR_MS)
            print("subiu ate", g.angulo_garra(), "graus")
        elif botao == Button.DOWN:
            g.descer_garra()
            print("desceu ate", g.angulo_garra(), "graus")


# =============================================================================
# TESTE 4 - servo seletor
# =============================================================================

def _teste_4_servo():
    """
    Passeia pelas 3 colunas e volta ao repouso, parando em cada uma.

    O QUE CONFERIR:
      1. as tres paradas caem na BOCA de cada coluna. Se o servo parar
         entre duas, o angulo se ajusta no arduino_servos.ino, nao aqui;
      2. nenhum "servo nao terminou" (apito longo). Se aparecer, ou o
         servo esta forcando um batente, ou o comando daquela coluna
         ainda nao existe no sketch (hoje so 0x10 e 0x11 existem la);
      3. o servo nao fica zumbindo parado - zumbido e servo empurrando o
         fim do curso.

    Se NADA responder, o problema e a conversa e nao o servo: rode o
    teste_arduino.py, que testa so o barramento.
    """
    print("=== servo ===")
    sv.repouso()
    wait(500)

    for coluna in (1, 2, 3):
        ok = sv.selecionar_coluna(coluna)
        print("coluna", coluna, "->", "OK" if ok else "FALHOU")
        wait(1000)

    sv.repouso()


# =============================================================================
# ESCOLHA
# =============================================================================

if __name__ == "__main__":

    TESTE = 0

    testes = (_teste_0_rascunho, _teste_1_motor_a, _teste_2_sensores,
              _teste_3_garra, _teste_4_servo)
    testes[TESTE]()

    ev3.speaker.beep()
