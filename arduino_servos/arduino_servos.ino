// ============================================================================
// arduino_servos.ino
//
// Arduino Nano como ESCRAVO I2C do EV3, controlando dois servos.
// (funciona identico no Uno: mesmos pinos A4/A5 para I2C)
//
// O EV3 manda 1 byte de comando. O Arduino executa e, se perguntado,
// responde se ainda esta movendo.
//
// LIGACOES (ver arduino_ligacoes.html)
//   EV3 pino 3 (vermelho) -> GND
//   EV3 pino 4 (verde)    -> 5V        + pull-up de 4,7k para SDA e SCL
//   EV3 pino 5 (amarelo)  -> A5 (SCL)
//   EV3 pino 6 (azul)     -> A4 (SDA)
//   Servo 1 sinal (laranja) -> D9
//   Servo 2 sinal (laranja) -> D10
//   Servos VCC/GND -> bateria 4x AA (6V), com GND unido ao do Arduino
//
// FUNCIONA IGUAL COM SG90 E MG90S.
// ============================================================================

#include <Wire.h>
#include <Servo.h>

// Endereco de 7 bits. O Pybricks usa o MESMO numero, sem deslocar.
#define ENDERECO   0x04

#define PINO_SERVO1  9
#define PINO_SERVO2 10

// Angulos. Ajustar depois de montar no mecanismo: o "90" mecanico raramente
// e exatamente o 90 do servo.
#define ANG_REPOUSO  0
#define ANG_ACIONADO 90

// Quanto tempo o servo leva para percorrer o curso. Serve para o EV3 saber
// quando pode seguir. Meca com cronometro e ajuste.
#define TEMPO_CURSO 400   // ms

// ---- Comandos vindos do EV3 ----
#define CMD_S1_ACIONA 0x10
#define CMD_S1_REPOUSO 0x11
#define CMD_S2_ACIONA 0x20
#define CMD_S2_REPOUSO 0x21
#define CMD_AMBOS_ACIONA  0x30
#define CMD_AMBOS_REPOUSO 0x31

Servo servo1, servo2;

// 'volatile' porque estas variaveis sao escritas dentro de uma interrupcao
// (o recebimento I2C) e lidas no loop principal. Sem isso o compilador pode
// otimizar a leitura e o loop nunca ver a mudanca.
volatile uint8_t comando_novo = 0;
volatile bool tem_comando = false;

unsigned long fim_movimento = 0;


void setup() {
  servo1.attach(PINO_SERVO1);
  servo2.attach(PINO_SERVO2);
  servo1.write(ANG_REPOUSO);
  servo2.write(ANG_REPOUSO);

  Wire.begin(ENDERECO);
  Wire.onReceive(aoReceber);
  Wire.onRequest(aoPerguntar);

  Serial.begin(9600);
  Serial.println("Pronto");
}


void loop() {
  // O comando e EXECUTADO AQUI, nao dentro da interrupcao.
  //
  // Isso e importante: aoReceber() roda como interrupcao, e mexer em servo
  // de dentro de uma interrupcao pode travar o Arduino, porque a biblioteca
  // Servo tambem usa interrupcao de temporizador. Aqui a interrupcao so
  // anota o comando e sai; quem age e o loop.
  if (tem_comando) {
    noInterrupts();
    uint8_t cmd = comando_novo;
    tem_comando = false;
    interrupts();

    executar(cmd);
  }
}


void executar(uint8_t cmd) {
  switch (cmd) {
    case CMD_S1_ACIONA:   servo1.write(ANG_ACIONADO); break;
    case CMD_S1_REPOUSO:  servo1.write(ANG_REPOUSO);  break;
    case CMD_S2_ACIONA:   servo2.write(ANG_ACIONADO); break;
    case CMD_S2_REPOUSO:  servo2.write(ANG_REPOUSO);  break;
    case CMD_AMBOS_ACIONA:
      servo1.write(ANG_ACIONADO);
      servo2.write(ANG_ACIONADO);
      break;
    case CMD_AMBOS_REPOUSO:
      servo1.write(ANG_REPOUSO);
      servo2.write(ANG_REPOUSO);
      break;
    default:
      Serial.print("Comando desconhecido: 0x");
      Serial.println(cmd, HEX);
      return;
  }

  fim_movimento = millis() + TEMPO_CURSO;

  Serial.print("Executou 0x");
  Serial.println(cmd, HEX);
}


// Chamado por interrupcao quando o EV3 escreve. So anota e sai.
void aoReceber(int quantos) {
  while (Wire.available()) {
    comando_novo = Wire.read();
    tem_comando = true;
  }
}


// Chamado por interrupcao quando o EV3 le.
// Devolve 1 = ainda movendo, 0 = pronto.
void aoPerguntar() {
  Wire.write(millis() < fim_movimento ? 1 : 0);
}
