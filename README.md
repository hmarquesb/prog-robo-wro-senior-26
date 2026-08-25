# Robô WRO — EV3 + Pybricks

Código de competição da equipe para a World Robot Olympiad.
Plataforma: **Pybricks MicroPython v2.0 no LEGO EV3**.

> Este README serve tanto para novos integrantes quanto para agentes de IA
> trabalhando no repositório. A seção **Regras do projeto** existe para evitar
> que decisões já testadas sejam desfeitas sem querer.

---

## Onde mexer

**O número que você quer ajustar mora no arquivo que o usa.** Distância de um
trecho, graus de um movimento, velocidade de uma rotina, tempo de uma espera —
tudo escrito ao lado da chamada, para o efeito estar a uma linha de distância.

O [`constantes.py`](constantes.py) guarda **só o que vários arquivos precisam
enxergar igual**: geometria do chassi, limites dos motores, ganhos padrão do PD,
calibração dos sensores, protocolo do servo e o mapa tapete/mosaico.

```
constantes.py    só o COMPARTILHADO entre arquivos
     ↓
setup.py         hardware (Motor, ColorSensor, I2CDevice) — só portas
     ↓
movimento.py     andar, girar_eixo, girar_arco, girar_pivo      ┐ funções
linha.py         seguir_linha, alinhar, procurar_linha          │ de
garra.py         garra do motor_D                               │ controle
servos.py        servo seletor das 3 colunas (via Arduino)      ┘
     ↓
parte1.py        largada → posição de leitura                   ┐
leitura_blocos.py  varre o mosaico → lista de 12 cores          │ rotinas
parte2.py        mosaico → tapete de blocos                     │ da missão
pegar_blocos.py  retira os blocos e guarda nas 3 colunas        │
entregar_blocos.py devolve os blocos ao mosaico, de costas      ┘
     ↓
prog1.py         a prova: emenda as partes na ordem
```

**Não há módulo para o motor A.** Ele é comandado direto, na linha da rotina que
precisa dele — ver *Regras do projeto*, regra 11.

Fora do caminho da prova:

```
diagnostico.py              descobre em que import um programa quebra
teste_arduino.py            a conversa EV3 ↔ Arduino e o servo, na bancada
diagnostico_i2c.py          relatório completo da conversa I2C, para copiar e mandar
teste_escrita_i2c.py        que forma de leitura/escrita o driver do EV3 aceita
arduino_servos/             o sketch do Arduino Nano (não vai para o EV3)
aulapybricks.py             8 lições de Pybricks, material de estudo
adaptador_horn_lego.scad    peça 3D: horn do servo MG90S → eixo LEGO
suporte_mg90s.scad          peça 3D: suporte do servo
```

---

## Hardware

| Porta | Dispositivo | Papel |
|---|---|---|
| A | Motor | Carrinho da correia GT2 **ou** quadrilátero traseiro (embreagem) |
| B | Motor | Roda **esquerda** (`Direction.COUNTERCLOCKWISE`) |
| C | Motor | Roda **direita** (`Direction.CLOCKWISE`) |
| D | Motor | Garra — **anda em cima do carrinho** |
| S1 | Arduino Nano (I2C) | Servo seletor das 3 colunas |
| S3 | Sensor de cor | `sensor_esq` — anda em cima do carrinho |
| S4 | Sensor de cor | `sensor_dir` — anda em cima do carrinho |

### O que se move e o que não se move

O carrinho carrega **só o motor_D e os dois sensores de cor**. As **3
colunas de armazenagem são fixas no topo do robô** — elas não andam com o
carrinho, e quem escolhe em qual delas o bloco cai é o **servo** montado
nelas.

Isso decide quem alinha o quê:

| Etapa | Quem alinha |
|---|---|
| Varredura do mosaico | o **carrinho** (os sensores andam com ele) |
| Escolha da coluna de armazenagem | o **servo** |
| Entrega no mosaico | o **robô** (as colunas são fixas) |

Medidas do chassi (em `constantes.py`, seção 1):

```python
DIAMETRO_RODA = 62.4   # mm
ENTRE_EIXOS   = 184.5  # mm
```

**Sem giroscópio.** É uma decisão deliberada — ver *Regras do projeto*.

---

## Uso rápido

```python
from setup import motor_A, motor_B, motor_C
import movimento as m
import linha as lin
import garra as g
import servos as sv

m.andar(300)
m.andar(300, v_max=800, kp=2.5)          # ajuste só desta chamada
m.andar_por_tempo(1100, 120)             # sem alvo de distância, sem PD
m.girar_eixo(90)
m.girar_arco(200, 45)
m.girar_pivo(motor_C, 90)   # a roda DIREITA gira; o pivô é a esquerda

lin.seguir_linha(tempo_ms=6000, parar_se=[lin.cruzamento()], ignorar_mm=40)
lin.alinhar()

motor_A.run_angle(1000, 320)             # carrinho: relativo
motor_A.run_target(1000, 420)            # carrinho: absoluto (precisa de zero)
motor_A.run_angle(500, -260)             # o outro lado da embreagem

g.zerar_garra()             # UMA VEZ, e SÓ com o carrinho fora do batente
g.descer_garra()
sv.selecionar_coluna(2)     # próximo arremesso cai na coluna 2
```

Os dois mecanismos do motor A **nunca se movem ao mesmo tempo** — é um motor
só. Ver *Regras do projeto*, regra 11.

Os sensores **não precisam ser calibrados no início do programa**: o `linha.py`
carrega `CAL_SENSOR_ESQ` / `CAL_SENSOR_DIR` do `constantes.py` no momento do
import.

### Unidades

| Grandeza | Unidade |
|---|---|
| Velocidade de motor | graus/segundo (~200 lento, ~500 médio, ~800 rápido) |
| Tempo | milissegundos |
| Distância | milímetros |
| Ângulo | graus |
| Leitura de sensor | 0 a 100 |

### Convenção de sinal

**Ângulo positivo = direita**, nas quatro funções de movimento, independente
de qual roda gira no `girar_pivo`.

O argumento do `girar_pivo` é a roda que **se mexe** — a outra é que fica
travada servindo de eixo. O sentido em que ela gira sai do ângulo, não da
escolha: para virar à direita, a roda esquerda vai para a frente e a direita
vai para trás. Escolher a roda só decide **sobre qual quina** o robô pivota.

---

## Regras do projeto

Decisões já testadas. Não desfazer sem motivo forte.

### 1. O número mora onde é usado; `constantes.py` só o que é compartilhado

O critério é **quantos arquivos precisam enxergar aquele valor igual**:

| Vai para `constantes.py` | Fica no arquivo que usa |
|---|---|
| geometria do chassi | distância de um trecho |
| limites dos motores | graus de um movimento |
| ganhos padrão do PD | velocidade de uma rotina |
| calibração dos sensores | tempo de uma espera |
| protocolo do servo (bate com o Arduino) | valor que vocês mexem testando |
| mapa tapete/mosaico (2 programas leem) | perfil usado por um arquivo só |

O motivo é prático: ajustar no robô é um ciclo de *mudar número → rodar → olhar*.
Se o número está em outro arquivo, cada volta desse ciclo custa uma ida e volta
entre dois arquivos — e, pior, some o contexto de qual movimento ele afeta.

Quando um trecho precisa de seis parâmetros de movimento, monte um `dict` **no
próprio arquivo** e passe com `**`:

```python
# em parte2.py
ANDAR_RAPIDO = dict(v_max=700, v_min=200, acel=1100, desacel=1800,
                    kp=2.5, kd=3.5)
...
m.andar(RECUO_PAREDE_MM, timeout=TIMEOUT_PAREDE_MS, **ANDAR_RAPIDO)
```

O que **continua proibido** é o mesmo valor escrito em dois arquivos: um dia
vocês calibram um e rodam o outro. Se dois arquivos precisam do mesmo número,
ele sobe para o `constantes.py`.

### 2. `setup.py` é a única fonte de hardware

Criar dois objetos `Motor` na mesma porta levanta erro em tempo de execução.
Todos os módulos importam de `setup.py`; nenhum instancia hardware.

### 3. Sem `DriveBase` no código de competição

Enquanto um `DriveBase` está ativo, `motor_B` e `motor_C` não podem ser
comandados individualmente — e ele continua ativo depois do `straight()`,
porque segue segurando as rodas. Só `stop()` libera.

O núcleo `_mover()` comanda cada roda separadamente, então os dois não
convivem.

### 4. Sem giroscópio

Encoder + reancoragem física em linhas pretas (`alinhar()`). Em vez de tentar
não acumular erro, o erro é **zerado** contra uma referência física do tapete.
A equipe já teve problemas de drift com o giro EV3.

### 5. `control.limits()` no `setup.py` é obrigatório

```python
motor_B.control.limits(*cte.LIMITES_RODA)
motor_C.control.limits(*cte.LIMITES_RODA)
motor_A.control.limits(*cte.LIMITES_MOTOR_A)
```

O `run()` do Pybricks tem um controlador PID próprio com limite interno de
aceleração. Sem afrouxá-lo, existem **dois limitadores em série** e o interno
é quem manda — mexer em `ACEL`/`DESACEL` não teria efeito nenhum.

Tem que ser no `setup.py` porque a documentação exige motor parado. Os
**valores** ficam no `constantes.py`; só a chamada mora aqui.

O motor A leva limites bem mais baixos que as rodas: sem isso ele passa do
alvo do `run_target` e fica corrigindo (estende, recolhe um pouco, estende de
novo). O limite é do motor, então vale para os dois mecanismos que ele aciona.

### 6. Três PDs independentes

| Onde | O PD controla | Ganhos |
|---|---|---|
| `_mover` | diferença de encoder entre as rodas | `KP` / `KD` |
| `seguir_linha` | diferença entre os dois sensores | `KP_LINHA` / `KD_LINHA` |
| `alinhar` | leitura de cada sensor, roda por roda | `KP_ALINHA` / `KD_ALINHA` |

Grandezas diferentes. Usar o mesmo valor nos três deixa um mole e outro
oscilando.

O `alinhar()` é o único que **não** sincroniza as rodas, e isso é proposital:
o objetivo é desacoplar as duas para que cada uma ache a linha sozinha.

**Duas travas no PD do `_mover()` — não remover.** Sem elas o próprio PD faz
o robô girar uma roda só em vez de andar reto:

| Trava | O que impede |
|---|---|
| `CORRECAO_MAX_FRAC` | a correção passar da velocidade do perfil e **zerar** a roda atrasada |
| parada pelo `min` das duas rodas | o loop terminar com uma roda devendo |

O caso ruim é a **largada**: ali o perfil ainda está em `v_min`, o valor mais
baixo do trajeto, e é justo o instante em que as duas rodas vencem o atrito
estático em momentos diferentes. O erro pula alguns graus de uma vez, o termo
D multiplica esse pulo por `KD` e a correção passa de `v_min` fácil. Sem teto,
`v_esq = v - correcao` vira zero ou negativo. E, com uma roda parada, a
**média** de progresso só chega em 1.0 quando a outra anda o **dobro** do
alvo — o robô fica girando esse tempo todo.

O `TESTE 0` do `movimento.py` mede as duas coisas: imprime quantos graus cada
roda andou num `andar(500)`. Iguais ao alvo → o PD está bem e robô torto é
problema mecânico. Uma perto de zero → a correção está zerando aquela roda.

O termo D é normalizado para um ciclo de `DT` ms. Sem isso o `KD` efetivo
varia com o tempo que o ciclo levou (leitura de encoder e escrita de motor
passam pelo sistema de arquivos), e o mesmo número vale coisas diferentes em
momentos diferentes do programa. A escala do `KD` não mudou — todos os valores
já calibrados continuam valendo.

### 7. Sempre usar `tempo_ms` como rede de segurança

Mesmo quando já existe outro critério. Sem ele, um sensor que nunca vê preto
faz o robô andar até o fim da rodada. Todo `dict` de seguidor de linha do
projeto (`LINHA_ATE_MOSAICO`, `LINHA_ATE_TAPETE`…) já traz `tempo_ms`; as
chamadas soltas da `parte1` também.

### 8. Não mover o carrinho enquanto o robô anda

O deslocamento de massa muda a dinâmica no meio do percurso e o PD sai de
sintonia. Já foi testado e não funcionou.

Mover o carrinho junto com **outro mecanismo**, robô parado, é tranquilo —
use `esperar=False` nos dois e espere depois.

A proibição é **mover durante a andada**, não andar com ele para fora. Desde
que o carrinho virou peça impressa em 3D (era LEGO), ele ficou leve o
bastante para o robô andar com ele **parado onde estiver, inclusive todo
estendido** — é o que o `pegar_blocos.py` faz entre uma coluna e outra, em vez
de recolher e estender de novo a cada bloco.

A garra é mais leve, mas não é de graça: descer a garra com `esperar=False`
**enquanto o robô andava** entortou o robô no teste real da `parte1`, e
voltou a ser feito com o robô parado.

### 9. Parâmetros explícitos, sem `**kwargs` na definição

As funções listam todos os parâmetros. Mais verboso, mas o editor autocompleta
e erro de digitação aparece na hora certa.

Isso vale para a **definição**. Na **chamada**, passar um `dict` do próprio
arquivo com `**` é o jeito recomendado (regra 1).

### 10. A garra tem um zero, e ele é marcado uma vez só

O curso da garra termina num batente mecânico. Descer sempre "por tempo"
parece funcionar, mas a sobra de cada descida se **acumula**. Com o zero
marcado uma vez (`zerar_garra`), toda descida vira "vá para
`ANGULO_ABAIXADA`" e para sempre na mesma altura.

**A garra só desce o curso inteiro com o carrinho fora do batente.** Recolhido,
ele faz a garra bater na estrutura do robô antes do fim do curso, e o zero sai
alto — junto com todas as descidas do programa. Carrinho primeiro, sempre.

### 11. O motor A é comandado direto, sem módulo no meio

Não existe `carrinho.py`, e não deve voltar a existir. Cada rotina chama o
motor na linha onde ele é usado, com os graus daquele passo escritos ali:

```python
motor_A.run_angle(1000, 320)     # relativo: gira 320° a partir de onde está
motor_A.run_target(1000, 420)    # absoluto: precisa de um zero antes
```

**Por quê:** funções como `estender_carrinho()` ou `descer_quadrilatero()`
escondiam justamente o número que a equipe mais ajusta. Para mudar quanto o
carrinho sai num trecho era preciso abrir outro arquivo, achar a constante,
descobrir se ela era usada em mais algum lugar, e só então mudar. Agora o
número está na linha que produz o movimento.

O `motor_A` aciona uma **embreagem**: o **sentido** de giro decide qual
mecanismo recebe o movimento — positivo estende o carrinho, negativo desce o
quadrilátero traseiro. O mecanismo **desengatado** fica onde estava, sem motor
segurando. Isso é mecânica, e o programa não modela: ele só manda graus.

Três consequências que **não dá para contornar no programa**:

1. **Os dois nunca se movem ao mesmo tempo.** É um motor só. Pedir um
   enquanto o outro anda cancela o movimento anterior no meio.
2. **Descer o quadrilátero exige o carrinho recolhido**, senão o trilho
   recolhe inteiro no caminho — com a garra e os sensores em cima dele.
3. **Zerar contra o batente mexe na traseira.** A busca gira no negativo, então
   *desce* o quadrilátero no caminho. No começo do programa é inofensivo; o
   `ler_mosaico` zera parado em cima do mosaico — confira se a traseira não
   encosta em nada ali.

**Quem precisa de posição absoluta zera por conta própria**, com duas linhas
visíveis, em vez de chamar uma função:

```python
motor_A.run_until_stalled(V_ZERAR, then=Stop.HOLD, duty_limit=FORCA_ZERAR)
motor_A.reset_angle(0)
```

São duas etapas que fazem isso — `leitura_blocos` (as 3 posições da varredura)
e `pegar_blocos` (as 3 profundidades). A `parte1` e a `parte2` não zeram: lá
tudo é `run_angle` relativo.

**Se a sua embreagem for ao contrário**, inverta o `Direction` do `motor_A` no
`setup.py` — não espalhe sinais negativos pelas rotinas.

### 12. A coluna de armazenagem é escolhida pelo servo, não pela força

As 3 colunas são **fixas no topo do robô**. O servo põe a boca da coluna certa
debaixo da garra, e há **um par de arremesso** (`ARREMESSO_V` / `_MS`, em
`pegar_blocos.py`) para os 12 blocos — a mesma força e a mesma profundidade de
carrinho para todos.

**Não reintroduza força por coluna nem profundidade por coluna.** Já foi assim,
com seis números que interagiam entre si, e cada um mudava o efeito do outro. Se
o bloco entra na coluna errada, o ajuste é o **ângulo do servo**, no
`arduino_servos.ino` — não é uma mudança de Python.

Falha de I2C **não para a prova**: `servos.py` transforma `OSError` em apito e
`False`. Um bloco na coluna errada custa pontos; um programa morto custa a
rodada.

### 13. Na entrega, quem alinha é o chassi

As colunas são fixas no robô, então mover o carrinho **não as desloca** em
relação ao mosaico. Para pôr uma coluna em cima da célula certa, quem anda é o
robô inteiro:

| Etapa | Quem atravessa o mosaico |
|---|---|
| Varredura (`leitura_blocos`) | o **carrinho** — os sensores andam nele |
| Entrega (`entregar_blocos`) | o **robô** — as colunas não andam |

`entregar_blocos.py` **nunca toca no `motor_A`**. Se um dia aparecer um
`motor_A.run_*` lá dentro, é bug.

Se as 3 colunas do robô já estiverem espaçadas como as 3 do mosaico, ponha os
três `POSICAO_ROBO_COLUNA` em `0`: o robô para uma vez por fileira e solta os
três blocos sem andar entre eles.

---

## Calibração

**A ordem importa.** Calibrar ganhos antes da geometria faz vocês compensarem
erro de medida com ganho — e aí tudo desregula quando a bateria muda.

A coluna "Onde" diz o arquivo em que o valor mora **e** onde rodar o teste —
são o mesmo arquivo, de propósito (regra 1).

| # | O que ajustar | Onde |
|---|---|---|
| 1 | `DIAMETRO_RODA` | `constantes.py` → `movimento.py`, `TESTE = 1` |
| 2 | `ENTRE_EIXOS` | `constantes.py` → `movimento.py`, `TESTE = 2` |
| 3 | `CAL_SENSOR_ESQ` / `CAL_SENSOR_DIR` | `constantes.py` → `linha.py`, `TESTE = 1` |
| 4 | `KP_LINHA` / `KD_LINHA` | `constantes.py` → `linha.py`, `TESTE = 2` |
| 5 | `V_LINHA` | `constantes.py`, só depois que o PD estiver estável |
| 6 | ângulos do servo (no `arduino_servos.ino`) | `servos.py`, F5 |
| 7 | `POSICAO_COLUNA` (as 8 colunas) | `constantes.py` → `pegar_blocos.py`, `TESTE = 1` |
| 8 | `PROFUNDIDADES` (as 3 do carrinho) | `pegar_blocos.py`, `TESTE = 2` |
| 9 | `ANGULO_ABAIXADA`, `TEMPO_ZERAR_MS` | `garra.py`, F5 |
| 10 | `ARREMESSO_V` / `_MS` | `pegar_blocos.py`, `TESTE = 3` (a rodada inteira) |
| 11 | `COLUNA_1/2/3` (varredura do mosaico) | `leitura_blocos_parte2.py`, F5 |
| 12 | `POSICAO_ROBO_COLUNA` (posições do **robô**) | `entregar_blocos.py`, `TESTE = 2` |

Detalhes:

1. **`DIAMETRO_RODA`** — `andar(500)`, medir com régua.
   Andou menos → diminua. Andou mais → aumente.

2. **`ENTRE_EIXOS`** — quatro `girar_eixo(90)` têm que fechar uma volta exata.
   Girou de menos → aumente. Girou de mais → diminua.

3. **Sensores** — posicione os sensores em cima da linha preta, rode
   `calibrar_varrendo()` e **copie os quatro números para o `constantes.py`**.
   O que a função aplica vale só até o programa acabar.

4. **`KP_LINHA` / `KD_LINHA`** — em velocidade baixa (`v_max=250`).
   Serpenteia → aumente `KD`. Sai na curva → aumente `KP`.

6. **Servo** — `servos.py` passeia pelas 3 colunas e volta ao repouso. As três
   paradas têm que cair na **boca** de cada coluna. Se o servo parar entre
   duas, o ângulo se ajusta no `arduino_servos.ino`, não no Python. Se nada
   responder, o problema é a conversa e não o servo: rode `teste_arduino.py`.

7. **`POSICAO_COLUNA`** — o robô anda até as 8 colunas do tapete, parando em
   cada uma para vocês medirem. O erro em mm se **soma direto** ao número
   correspondente; como são posições absolutas a partir da parede, corrigir
   uma não desloca as outras sete. **É o primeiro da fila do tapete** — tudo o
   mais depende de o robô parar no lugar certo.

8. **`PROFUNDIDADES`** — as três posições do carrinho, em **graus do
   `motor_A`** (não mais em mm de correia). O teste zera contra o batente e
   para nas três, esperando o `CENTER` entre elas.
   As três erradas para o mesmo lado → só a primeira está errada, some a mesma
   diferença nas outras duas. A primeira certa e a terceira errada → o **passo**
   está errado: os blocos são igualmente espaçados, então perto→meio e
   meio→fundo têm de ser a mesma diferença. Motor zumbindo parado na do fundo →
   o alvo passou do fim de curso mecânico.

10. **Arremesso** — **não tem teste próprio**: é um par só para os 12 blocos,
    então não há nada para comparar entre um bloco e outro. Ajuste os dois
    números e rode o `TESTE 3`, a rodada inteira.
    Ele tem de servir às **três profundidades**, porque o bloco é lançado de
    onde o carrinho parou. Bloco perto/longe demais nos 12 → é o arremesso.
    Bloco viajando certo mas entrando na coluna errada → é o servo (item 6),
    ajustado no `arduino_servos.ino`.

12. **`POSICAO_ROBO_COLUNA`** — posições do **robô**, não do carrinho: as
    colunas são fixas, então quem anda de uma célula à outra é o chassi. O
    `TESTE 2` faz o caminho inteiro e apita em cada uma das 12 células sem
    soltar nada.

Todo arquivo que tem mais de um teste usa uma variável `TESTE` no fim — mude o
número e rode com F5, não é preciso comentar e descomentar nada.

---

## Armadilhas do MicroPython no EV3

Coisas que funcionam no Python do computador e quebram no robô.

- **`ColorSensor` não é hashable.** Não pode ser chave de dicionário. Já
  causou `TypeError: unsupported type for __hash__`. Use comparação com `is` —
  é por isso que a calibração dos sensores são duas variáveis e não um dict.
- **Sem f-strings.** `f"valor: {x}"` não compila. Use `print("valor:", x)`.
- **`run_until_stalled` não funciona em motor MÉDIO**, só em motor grande.
  Em motor médio levanta *"operation is not valid in the current state"*.
  Por isso a zeragem do carrinho (motor A, grande) acha o batente por
  travamento, e o `zerar_garra` (motor D, médio) acha **por tempo**.
- **`control.limits()` com torque baixo pode levantar EPERM** mesmo com o
  motor parado.
- **Leitura de sensor é a operação mais cara do loop.** Passa pelo sistema de
  arquivos do Linux. Não leia o mesmo sensor duas vezes no mesmo ciclo.
- **Sem ponto flutuante em hardware.** `sqrt` e divisão são emulados. Rápido o
  bastante para o loop de 5 ms, mas não é de graça.
- **Sem `async`.** Não existe `multitask` nem `run_task` no EV3. Para fazer
  duas coisas ao mesmo tempo, use `wait=False` nos comandos de motor e
  `control.done()` para sincronizar.

---

## Ambiente

VS Code + extensão `lego-education.ev3-micropython`.

`.vscode/settings.json`:

```json
"ev3devBrowser.download.include": "**/*.py",
"python.languageServer": "Pylance"
```

O template da LEGO vem com `"None"` no language server, o que desliga
autocomplete. Para as dicas de parâmetro funcionarem também é preciso
`pip install pybricks-stubs` e instalar as extensões Python e Pylance.

`.vscode/launch.json` usa `${relativeFile}`, então **F5 roda o arquivo aberto**.

Todos os módulos importados precisam estar no EV3 — o filtro de download só
serve para cortar arquivos que não são `.py`.

---

## Peças 3D

Arquivos `.scad` paramétricos, abertos no OpenSCAD (gratuito).
F5 pré-visualiza, F6 renderiza, F7 exporta STL.

Cada arquivo tem uma variável `MODO` no topo com cupons de teste que imprimem
em poucos minutos. **Sempre imprimir o cupom antes da peça inteira** — os
encaixes precisam de duas ou três iterações de tolerância.

Configuração de impressão: 0,15 mm de camada, **5 paredes**, 40% de
preenchimento, sem suportes, com brim, compensação de pé de elefante 0,2 mm.
Paredes importam mais que preenchimento nessas peças.
