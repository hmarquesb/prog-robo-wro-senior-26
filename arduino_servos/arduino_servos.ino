// ============================================================================
// arduino_servos.ino
//
// Arduino Nano como ESCRAVO I2C do EV3, controlando o SERVO SELETOR DAS
// COLUNAS de armazenagem (mais um servo auxiliar).
// (funciona identico no Uno: mesmos pinos A4/A5 para I2C)
//
// O EV3 manda 1 byte de comando. O Arduino executa e, se perguntado,
// responde se ainda esta movendo.
//
// CONTRATO COM O EV3 - os bytes abaixo tem de bater com a secao 5 do
// constantes.py. Se mudar um lado, mude o outro.
//
// Ligacoes bateria - marrom no vermelho do ev3 (GND)
// Vermelho da bateria é energia e vai no vermelho do servo
// Marrom do servo e GND e tambem vai no vermelho do ev3
// O vermelho do servo vai no vermelho da bateria
// O amarelo do servo vai no arduino. um vai no D9 e o outro servo vai no D10
//
// LIGACOES (ver arduino_ligacoes.html)
//   EV3 pino 3 (vermelho) -> GND
//   EV3 pino 4 (verde)    -> 5V        + pull-up de 82k para SDA e SCL
//   EV3 pino 5 (amarelo)  -> A5 (SCL)
//   EV3 pino 6 (azul)     -> A4 (SDA)
//   Servo 1 sinal (laranja) -> D9      <- o seletor de coluna
//   Servo 2 sinal (laranja) -> D10     <- auxiliar
//   Servos VCC/GND -> bateria 4x AA (6V), com GND unido ao do Arduino
//
// OS 82k SAO O VALOR DA DOCUMENTACAO OFICIAL DO EV3 para os pinos 5 e 6
// (o NXT usava o mesmo). Sao pull-ups fracos: 5V/82k = 60 uA, o que so
// limita velocidade e comprimento de cabo. NAO tem relacao com
// aquecimento - um resistor desses dissipa 0,0003 W.
//
// ---------------------------------------------------------------------------
// ATENCAO - ALIMENTACAO DOS SERVOS (ja fritou um Nano aqui)
//
// O VCC dos servos vai na BATERIA de 4x AA. NUNCA no pino 5V do Nano:
// aquele pino e a SAIDA do regulador de bordo, que aguenta ~150 mA, e um
// MG90S travado puxa 700 mA - 1 A. O regulador esquenta, cheira a
// queimado e morre. Do trio EV3 / Arduino / bateria, o unico fio que se
// une e o GND. A bateria, se for alimentar o Nano, entra no VIN - nunca
// no 5V.
//
// E SERVO FORCANDO BATENTE E STALL CONTINUO. Antes de energizar, gire o
// horn COM A MAO por todo o curso que os ANG_COLUNA_* abaixo pedem. Se
// travar antes, corrija o angulo primeiro - senao o servo passa o teste
// inteiro puxando corrente de rotor travado. Os valores que estao la sao
// PROVISORIOS e nunca foram medidos neste mecanismo.
//
// FUNCIONA IGUAL COM SG90 E MG90S.
//
// ---------------------------------------------------------------------------
// COMO VER O QUE ESTA ACONTECENDO
//
// NAO DEIXE O USB E O CABO DO EV3 LIGADOS AO MESMO TEMPO. Foi isso que
// esquentou o Nano aqui: sem o USB ele fica frio, com os dois juntos
// esquenta. A explicacao que casa com o sintoma e que o pino 4 do EV3
// (~4,3V) esta ligado ao pino 5V do Nano, que ja e alimentado pelos 5V
// do USB - duas fontes amarradas uma na outra, e a diferenca vira
// corrente e calor no regulador. CONFIRMAR ISSO MEDINDO antes de tratar
// como certo; o que ja e certo e o sintoma: os dois juntos esquentam.
//
// PARA USAR OS DOIS AO MESMO TEMPO, o caminho e nao amarrar as fontes:
// o pino 4 do EV3 alimenta SO os pull-ups de 82k, e nao entra no 5V do
// Nano. GND, SDA e SCL continuam ligados normalmente. Testar amanha.
//
// Enquanto isso: para ler a serial, USB sozinho, sem o cabo do EV3.
// Para rodar os diagnosticos, cabo do EV3 sozinho, sem USB - a saida
// deles vai para o Debug Console do VS Code, que nao depende da serial.
//
// Abra o Serial Monitor a 9600. Ele imprime:
//
//   no boot          "arduino_servos v2 pronto"  -> a versao que rodou
//   a cada recepcao  "rx N bytes=B byte=0xNN"    -> o EV3 escreveu
//   a cada comando   "Executou 0xNN"             -> o switch tratou
//
// Se o EV3 escreve e NAO aparece linha "rx", a escrita nao chega ao
// Arduino. Se aparece "rx" com bytes=0, chega o endereco mas nenhum dado
// - e ai o problema e a FORMA da escrita do lado do EV3, nao a fiacao.
// ============================================================================

#include <Wire.h>
#include <Servo.h>

// Endereco de 7 bits. O Pybricks usa o MESMO numero, sem deslocar.
#define ENDERECO   0x04

#define PINO_SERVO1  9
#define PINO_SERVO2 10

// Segundo byte de toda resposta. Quem ler 2 bytes recebe
// [status, ASSINATURA] e sabe que falou com ESTE sketch; um barramento
// em curto com o GND devolveria [0, 0], e um sem escravo, [0xFF, 0xFF].
// Leitura de 1 byte continua recebendo so o status, como sempre.
#define ASSINATURA 0x5A

// ---- Relato pela serial ----
// Ponha 0 antes da prova. Serial.print a 9600 BLOQUEIA enquanto esvazia
// o buffer - cada linha custa uns 20 ms, e ela sai no loop, bem no
// instante em que o EV3 acabou de mandar um comando e esta esperando.
// Nao quebra nada (o pendente segura o status em ocupado), mas atrasa.
// Com 1, o Serial Monitor a 9600 mostra boot, recepcoes e comandos.
#define DEBUG 1

#if DEBUG
  #define LOG(x)        Serial.print(x)
  #define LOGLN(x)      Serial.println(x)
  #define LOGHEXLN(x)   Serial.println(x, HEX)
#else
  #define LOG(x)
  #define LOGLN(x)
  #define LOGHEXLN(x)
#endif

// ---- Angulos do SELETOR (servo 1) ----
// UM ANGULO POR COLUNA DE ARMAZENAGEM. Ajustar depois de montar: o "90"
// mecanico raramente e o 90 do servo. Um bloco caindo na coluna errada se
// conserta AQUI, nao no Python (regra 11 do README).
// VALORES PROVISORIOS ate medir no robo.
#define ANG_REPOUSO    0
#define ANG_COLUNA_1  45
#define ANG_COLUNA_2  90
#define ANG_COLUNA_3 135

// ---- Angulos do servo auxiliar ----
// SERVO2, nao "S2": aqui o 2 e o numero do servo. A porta do EV3 e a
// S1 - confundir as duas ja custou uma tarde de diagnostico.
#define ANG_SERVO2_REPOUSO   0
#define ANG_SERVO2_ACIONADO 90

// Velocidade do servo, para o EV3 saber quando pode seguir. Um SG90 sem
// carga faz ~60 graus em 120 ms (~2 ms/grau); com carga e mais lento.
// Meca com cronometro no curso mais longo e ajuste.
// O tempo e proporcional ao curso: ir da coluna 1 a 3 demora mais que da
// 1 a 2, e um tempo fixo ou desperdicaria prova ou arremessaria antes de
// o seletor chegar.
#define TEMPO_POR_GRAU   3    // ms por grau percorrido
#define TEMPO_MINIMO    80    // ms - folga para o servo arrancar

// ---- Comandos vindos do EV3 (constantes.py secao 5) ----
#define CMD_COLUNA_1 0x10
#define CMD_REPOUSO  0x11
#define CMD_COLUNA_2 0x12
#define CMD_COLUNA_3 0x13

// Servo auxiliar - nenhum modulo do EV3 usa hoje.
#define CMD_SERVO2_ACIONA  0x20
#define CMD_SERVO2_REPOUSO 0x21

Servo servo1, servo2;

// 'volatile' porque estas variaveis sao escritas dentro de uma interrupcao
// (o recebimento I2C) e lidas no loop principal. Sem isso o compilador pode
// otimizar a leitura e o loop nunca ver a mudanca.
volatile uint8_t comando_novo = 0;
volatile bool tem_comando = false;

// Marcado JA NA INTERRUPCAO, antes de o loop executar o comando. Sem isso
// existe uma janela em que o EV3 ja escreveu, o loop ainda nao rodou, e a
// pergunta de status responde "terminou" - o EV3 arremessaria antes de o
// seletor sair do lugar.
volatile bool pendente = false;

// Contadores de diagnostico. Contam RECEPCOES, nao comandos: uma recepcao
// com zero bytes (so o endereco) tambem conta, e e justamente ela que
// distingue "a escrita nao chega" de "chega vazia".
volatile uint16_t rx_total = 0;
volatile uint8_t rx_bytes = 0;
uint16_t rx_impresso = 0;

unsigned long fim_movimento = 0;
int angulo_atual = ANG_REPOUSO;   // para calcular o curso do proximo salto


void setup() {
  servo1.attach(PINO_SERVO1);
  servo2.attach(PINO_SERVO2);
  servo1.write(ANG_REPOUSO);
  servo2.write(ANG_SERVO2_REPOUSO);

  Wire.begin(ENDERECO);
  Wire.onReceive(aoReceber);
  Wire.onRequest(aoPerguntar);

#if DEBUG
  Serial.begin(9600);
#endif
  LOGLN("arduino_servos v2 pronto");
}


void loop() {
  // O comando e EXECUTADO AQUI, nao dentro da interrupcao.
  //
  // Isso e importante: aoReceber() roda como interrupcao, e mexer em servo
  // de dentro de uma interrupcao pode travar o Arduino, porque a biblioteca
  // Servo tambem usa interrupcao de temporizador. Aqui a interrupcao so
  // anota o comando e sai; quem age e o loop.
  //
  // Serial.print tambem NAO pode ir para dentro da interrupcao - ele
  // depende de interrupcoes para esvaziar o buffer. Por isso o relato de
  // recepcao sai daqui, comparando o contador com o que ja foi impresso.
  noInterrupts();
  uint16_t total = rx_total;
  uint8_t bytes = rx_bytes;
  uint8_t ultimo = comando_novo;
  interrupts();

  if (total != rx_impresso) {
    rx_impresso = total;
    LOG("rx ");
    LOG(total);
    LOG(" bytes=");
    LOG(bytes);
    LOG(" byte=0x");
    LOGHEXLN(ultimo);
  }

  if (tem_comando) {
    noInterrupts();
    uint8_t cmd = comando_novo;
    tem_comando = false;
    interrupts();

    executar(cmd);
    pendente = false;   // so agora fim_movimento vale; a espera do EV3 passa
                        // a olhar o relogio em vez do "acabei de receber"
  }
}


// Move o seletor e calcula quanto tempo esse curso leva.
void mover_seletor(int angulo) {
  int curso = angulo - angulo_atual;
  if (curso < 0) curso = -curso;

  servo1.write(angulo);
  angulo_atual = angulo;

  unsigned long duracao = (unsigned long)curso * TEMPO_POR_GRAU;
  if (duracao < TEMPO_MINIMO) duracao = TEMPO_MINIMO;
  fim_movimento = millis() + duracao;
}


void executar(uint8_t cmd) {
  switch (cmd) {
    case CMD_COLUNA_1: mover_seletor(ANG_COLUNA_1); break;
    case CMD_COLUNA_2: mover_seletor(ANG_COLUNA_2); break;
    case CMD_COLUNA_3: mover_seletor(ANG_COLUNA_3); break;
    case CMD_REPOUSO:  mover_seletor(ANG_REPOUSO);  break;

    case CMD_SERVO2_ACIONA:
      servo2.write(ANG_SERVO2_ACIONADO);
      fim_movimento = millis() + (unsigned long)TEMPO_POR_GRAU * 90;
      break;
    case CMD_SERVO2_REPOUSO:
      servo2.write(ANG_SERVO2_REPOUSO);
      fim_movimento = millis() + (unsigned long)TEMPO_POR_GRAU * 90;
      break;

    default:
      // NAO da para responder "deu erro" - o protocolo so tem 1 byte de
      // status. Entao seguramos o status em "ocupado" ate o EV3 desistir:
      // o servos.py apita e imprime o timeout, que e o sinal de que um
      // comando chegou aqui sem tratamento. Melhor que o silencio de
      // fingir que terminou.
      fim_movimento = millis() + 5000;
      LOG("Comando desconhecido: 0x");
      LOGHEXLN(cmd);
      return;
  }

  LOG("Executou 0x");
  LOGHEXLN(cmd);
}


// Chamado por interrupcao quando o EV3 escreve. So anota e sai.
//
// Fica com o PRIMEIRO byte, nao com o ultimo: se o mestre mandar a
// escrita no formato "registrador + dado" (que e como o driver do EV3
// conversa com sensor I2C), o comando e o primeiro byte e o resto e
// enchimento.
void aoReceber(int quantos) {
  if (Wire.available()) {
    comando_novo = Wire.read();
    tem_comando = true;
    pendente = true;
  }

  while (Wire.available()) {   // descarta o que vier depois
    Wire.read();
  }

  rx_bytes = (uint8_t)quantos;
  rx_total++;                  // conta ate a recepcao VAZIA, de proposito
}


// Chamado por interrupcao quando o EV3 le.
//
// Byte 1: 1 = ainda movendo, 0 = pronto.
// Byte 2: ASSINATURA - so chega a quem pede 2 bytes, e serve para provar
//         que a resposta veio deste sketch e nao de uma linha em curto.
void aoPerguntar() {
  bool ocupado = pendente || (millis() < fim_movimento);
  Wire.write(ocupado ? 1 : 0);
  Wire.write(ASSINATURA);
}
