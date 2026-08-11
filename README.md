# Robô WRO — EV3 + Pybricks

Código de competição da equipe para a World Robot Olympiad.
Plataforma: **Pybricks MicroPython v2.0 no LEGO EV3**.

> Este README serve tanto para novos integrantes quanto para agentes de IA
> trabalhando no repositório. A seção **Regras do projeto** existe para evitar
> que decisões já testadas sejam desfeitas sem querer.

---

## Hardware

| Porta | Dispositivo | Papel |
|---|---|---|
| A | Motor | Carrinho da correia GT2 |
| B | Motor | Roda **esquerda** (`Direction.COUNTERCLOCKWISE`) |
| C | Motor | Roda **direita** (`Direction.CLOCKWISE`) |
| D | Motor | Mecanismo (garra) |
| S3 | Sensor de cor | `sensor_esq` |
| S4 | Sensor de cor | `sensor_dir` |

Medidas do chassi (em `movimento.py`):

```python
DIAMETRO_RODA = 62.4   # mm
ENTRE_EIXOS   = 185.0  # mm
```

**Sem giroscópio.** É uma decisão deliberada — ver *Regras do projeto*.

---

## Arquivos

```
setup.py       Hardware. Único lugar onde Motor() e ColorSensor() são criados.
movimento.py   andar, girar_eixo, girar_arco, girar_pivo
linha.py       seguir_linha, alinhar, procurar_linha, calibração
carrinho.py    carrinho da correia GT2
garra.py       garra do motor_D (zerar, descer, arremessar)

leitura_blocos.py   varre o mosaico → lista de 12 cores
pegar_blocos.py     retira os blocos do tapete e guarda nas 3 colunas
entregar_blocos.py  devolve os blocos ao mosaico, de costas (fileira 4 → 1)
parte1.py           largada → posição de leitura
parte2.py           mosaico → tapete de blocos
prog1.py            programa da missão (o que roda de fato)

aprender_pybricks.py        8 lições de Pybricks, material de estudo
adaptador_horn_lego.scad    peça 3D: horn do servo MG90S → eixo LEGO
suporte_mg90s.scad          peça 3D: suporte do servo
```

Dependências:

```
setup.py  ←  movimento.py  ←  linha.py
   ↑                            
   └────  carrinho.py
```

---

## Uso rápido

```python
from setup import sensor_esq, sensor_dir, motor_B, motor_C, motor_D, ev3
import movimento as m
import linha as lin
import carrinho as c

# Calibração fixa (valores medidos uma vez com lin.calibrar_varrendo())
lin.calibrar(sensor_esq, 6, 75)
lin.calibrar(sensor_dir, 6, 75)

c.zerar_carrinho(forca=40)

m.andar(300)
m.girar_eixo(90)
m.girar_arco(200, 45)
m.girar_pivo(motor_C, 90)   # a roda DIREITA gira; o pivô é a esquerda

lin.seguir_linha(tempo_ms=6000, parar_se=[lin.cruzamento()], ignorar_mm=40)
lin.alinhar()
```

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

### 1. `setup.py` é a única fonte de hardware

Criar dois objetos `Motor` na mesma porta levanta erro em tempo de execução.
Todos os módulos importam de `setup.py`; nenhum instancia hardware.

### 2. Sem `DriveBase` no código de competição

Enquanto um `DriveBase` está ativo, `motor_B` e `motor_C` não podem ser
comandados individualmente — e ele continua ativo depois do `straight()`,
porque segue segurando as rodas. Só `stop()` libera.

O núcleo `_mover()` comanda cada roda separadamente, então os dois não
convivem.

### 3. Sem giroscópio

Encoder + reancoragem física em linhas pretas (`alinhar()`). Em vez de tentar
não acumular erro, o erro é **zerado** contra uma referência física do tapete.
A equipe já teve problemas de drift com o giro EV3.

### 4. `control.limits()` no `setup.py` é obrigatório

```python
motor_B.control.limits(1000, 10000, 100)
motor_C.control.limits(1000, 10000, 100)
```

O `run()` do Pybricks tem um controlador PID próprio com limite interno de
aceleração. Sem afrouxá-lo, existem **dois limitadores em série** e o interno
é quem manda — mexer em `ACEL`/`DESACEL` não teria efeito nenhum.

Tem que ser no `setup.py` porque a documentação exige motor parado.

### 5. Três PDs independentes

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

### 6. Sempre usar `tempo_ms` como rede de segurança

Mesmo quando já existe outro critério. Sem ele, um sensor que nunca vê preto
faz o robô andar até o fim da rodada.

### 7. Não mover o carrinho enquanto o robô anda

O deslocamento de massa muda a dinâmica no meio do percurso e o PD sai de
sintonia. Já foi testado e não funcionou.

Mover o carrinho junto com **outro mecanismo**, robô parado, é tranquilo —
use `esperar=False` nos dois e espere depois.

A proibição é **mover durante a andada**, não andar com ele para fora. Desde
que o carrinho virou peça impressa em 3D (era LEGO), ele ficou leve o
bastante para o robô andar com ele **parado onde estiver, inclusive todo
estendido** — é o que o `pegar_blocos.py` faz entre uma coluna e outra, em vez
de recolher e estender de novo a cada bloco.

### 8. Parâmetros explícitos, sem `**kwargs`

As funções listam todos os parâmetros. Mais verboso, mas o editor autocompleta
e erro de digitação aparece na hora certa.

---

## Calibração

**A ordem importa.** Calibrar ganhos antes da geometria faz vocês compensarem
erro de medida com ganho — e aí tudo desregula quando a bateria muda.

1. **`DIAMETRO_RODA`** — `movimento.py`, teste 1.
   `andar(500)`, medir com régua.
   Andou menos → diminua. Andou mais → aumente.

2. **`ENTRE_EIXOS`** — `movimento.py`, teste 2.
   Quatro `girar_eixo(90)` têm que fechar uma volta exata.
   Girou de menos → aumente. Girou de mais → diminua.

3. **Sensores** — `linha.py`, `calibrar_varrendo()`.
   Rodar uma vez, anotar os quatro números, fixar com `lin.calibrar()` no
   programa da missão. Sem normalizar, o PD nasce com erro constante.

4. **`KP_LINHA` / `KD_LINHA`** — em velocidade baixa (`v_max=250`).
   Serpenteia → aumente `KD`. Sai na curva → aumente `KP`.

5. **`V_LINHA`** — só depois que o PD estiver estável.

6. **`DENTES_POLIA`** — `carrinho.py`. `mover_carrinho(100)`, medir com régua.

---

## Armadilhas do MicroPython no EV3

Coisas que funcionam no Python do computador e quebram no robô.

- **`ColorSensor` não é hashable.** Não pode ser chave de dicionário. Já
  causou `TypeError: unsupported type for __hash__`. Use comparação com `is`.
- **Sem f-strings.** `f"valor: {x}"` não compila. Use `print("valor:", x)`.
- **`run_until_stalled` não funciona em motor MÉDIO**, só em motor grande.
  Em motor médio levanta *"operation is not valid in the current state"*.
  A versão `zerar_carrinho(esperar=False)` usa `dc()` e funciona nos dois.
- **`control.limits()` com torque baixo pode levantar EPERM** mesmo com o
  motor parado. Por isso o zeramento não-bloqueante usa `dc()` em vez de
  limitar torque.
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