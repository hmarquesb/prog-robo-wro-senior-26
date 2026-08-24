# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Competition code for a WRO (World Robot Olympiad) team robot. Platform: **Pybricks MicroPython v2.0 on LEGO EV3**, written and edited in VS Code but executed on the EV3 brick itself — not on this machine. There is no build system, package manager, or automated test suite; "testing" means running a file's `if __name__ == "__main__":` block physically on the robot and measuring with a ruler / eyeballing behavior.

There is also **no Python interpreter on this machine** — not even for a syntax check. Verify edits by reading, and by cross-checking names (e.g. grep every `cte.X` against the definitions in `constantes.py`).

`README.md` is written for both humans and AI agents and is the primary source of truth — read it in full before making non-trivial changes. It documents tested decisions (see "Regras do projeto" in the README) that must not be casually reverted.

## Running code

- No terminal build/lint/test commands apply here — this is not a hosted Python project.
- VS Code + the `lego-education.ev3-micropython` extension deploys to the EV3 over USB/network.
- `.vscode/launch.json` → F5 runs whichever `.py` file is currently open in the editor (`${relativeFile}`), so each module's own `if __name__ == "__main__":` block acts as its manual test/calibration routine. Those blocks select a routine with a `TESTE` (or `MODO`) variable — never by commenting/uncommenting code.
- Only `**/*.py` is downloaded to the brick (`ev3devBrowser.download.include` in `.vscode/settings.json`); every module a program imports must exist on the EV3, but non-`.py` files (README, `.scad`) are filtered out automatically.

## Architecture

Three layers, one-directional:

```
constantes.py          ONLY what several files must read identically
   ↓
setup.py               the only place Motor/ColorSensor/I2CDevice/EV3Brick are built
   ↓
movimento.py  ←  linha.py        control functions
garra.py  ,  servos.py
   ↓
parte1.py, leitura_blocos.py, parte2.py,      mission routines
pegar_blocos.py, entregar_blocos.py
   ↓
prog1.py               the competition program: sequences the parts
```

**There is no module for `motor_A`.** Mission routines call it directly —
`motor_A.run_angle(speed, degrees)` / `run_target(...)` — with the degrees for
that step written on the line itself. See decision 9.

**Mechanism map** (this is what most of the design decisions follow from):

| Thing | Moves with | Notes |
|---|---|---|
| Garra (`motor_D`) | the sled | rides on the carrinho |
| Both colour sensors | the sled | so the mosaic sweep is still a sled move |
| 3 storage columns | **nothing** — fixed on top of the robot | so delivery alignment is a *chassis* move |
| Which column receives a block | the servo (I2C → Arduino, port S1) | not throw force |
| Sled / rear quadrilateral | `motor_A`, two outputs of a clutch | sign of the command picks which one engages |

- **`constantes.py`** — **only values that several files must read identically**: chassis geometry, motor limits, default PD gains for `movimento`/`linha`, sensor calibration, the servo I2C protocol (a contract with the Arduino sketch), and the block-mat/mosaic tables that `pegar_blocos` and `entregar_blocos` both consume. 8 short sections. Imports nothing but `math` and `pybricks.parameters`, so anything can import it without a cycle. **A number used by one file belongs in that file** (decision 1).
- **`setup.py`** — the *only* place hardware objects are constructed. Creating two `Motor` objects on the same port raises a runtime error, so every other module imports motors/sensors from here. It also applies `control.limits()` (values from `constantes.py`) — required here because Pybricks demands the motor be stationary, and it must run before any movement code.
- **`movimento.py`** — chassis locomotion (`andar`, `girar_eixo`, `girar_arco`, `girar_pivo`, `andar_por_tempo`, `parar`). The first four are thin wrappers around one internal core, `_mover(alvo_esq, alvo_dir, ...)`, which takes per-wheel target degrees, runs a trapezoidal speed profile (`_perfil_velocidade`), and layers a PD loop on top that corrects *synchronization* between the two wheels (not line position). Sign convention: **positive angle = turn right**. `andar_por_tempo` is the odd one out — no target, no PD, both wheels at one speed for a fixed time; for pushing against a wall, not for covering a distance.
- **`linha.py`** — dual-sensor line following (`seguir_linha`, `alinhar`, `procurar_linha`) plus sensor calibration (`calibrar`, `calibrar_varrendo`) and a small library of stop conditions (`viu_escuro`, `viu_claro`, `viu_cor`, `cruzamento`) built as `(nome, func)` tuples passed via `parar_se=[...]`. Sensor calibration is applied **at import** from `cte.CAL_SENSOR_ESQ`/`_DIR` — no start-of-program call needed. Borrows `_perfil_velocidade`, `_limitar` and `parar` from `movimento.py` rather than duplicating them.
- **`garra.py`** — `motor_D` claw, which rides on the sled. Two primitives (`mover_garra` by time, `mover_garra_ate_angulo` by absolute angle); `zerar_garra` and `descer_garra` are combinations of them. Its tuning numbers (`ANGULO_ABAIXADA`, `V_DESCER`, `TIMEOUT_MS`, `TEMPO_ZERAR_MS`) live at the top of the file, not in `constantes.py`. The throw pair belongs to `pegar_blocos.py`, which is what throws.
- **`servos.py`** — the column-selector servo, reached over I2C through an Arduino Nano on port S1 (`selecionar_coluna(1|2|3)`, `repouso()`). Writes 1 command byte, polls 1 status byte until the Arduino reports done. `OSError` on the bus becomes a beep and `False`, never a traceback. The Arduino sketch (`arduino_servos.ino`) is **not in this repo** and currently only knows commands `0x10`/`0x11` — the column 2 and 3 commands (`0x12`/`0x13`) still have to be added there.
- **`pegar_blocos.py`** — block retrieval, and also the home of its own calibration: `TESTE 1` walks the 8 mat columns, `TESTE 2` steps the 3 sled depths, `TESTE 3` is the full run. There is no separate calibration file — the interactive routines live next to the numbers and the functions they exercise. The throw pair has no test of its own: it is one pair for all 12 blocks, so there is nothing to compare block-to-block — tune the numbers and run `TESTE 3`. The loop has **no special case for the first block**: the sled zeroes, extends to the deepest depth and the claw zeroes there, before the loop starts. Two guards skip a cell rather than raise (colour not on the mat; colour requested more than 6 times).
- **`entregar_blocos.py`** — delivery. **Never touches `motor_A`**: the storage columns are fixed to the robot, so alignment is a chassis move (decision 11). Tracks one absolute position along the delivery axis; row change and column change fold into a single `m.andar()` per cell.
- **`prog1.py`** — the actual mission program; sequences `parte1` → `leitura_blocos` → `parte2` → `pegar_blocos` (→ missing return route → `entregar_blocos`). Holds no numbers and no movement sequences.
- **`diagnostico.py`** / **`teste_arduino.py`** — support files, not on the mission path. The second is deliberately standalone (no `setup.py`, so it runs on the bench with only the Arduino plugged) and therefore repeats the I2C constants; keep them in sync with `constantes.py` section 5.
- **`aulapybricks.py`** — standalone teaching file (lessons 1–8, selected via the `LICAO` variable). Deliberately does not import the competition modules; don't treat it as part of the competition code path.

### Load-bearing design decisions (don't undo without strong reason — details/rationale in README "Regras do projeto")

1. **A number lives in the file that uses it; `constantes.py` holds only what is shared.** The test is how many files must read the value identically — chassis geometry, motor limits, default PD gains, sensor calibration, the servo protocol, and the mat/mosaic tables qualify; a trecho's distance, a routine's speed, one movement's degrees do not. Parameter bundles are `dict`s defined in the file that passes them (`ANDAR_MOSAICO` in `leitura_blocos.py`, `ANDAR_BLOCOS` in `pegar_blocos.py`, `GIRAR_PIVO` in `parte2.py`), spread with `**`. The rationale is the tuning loop: change number → run → look. Anything that puts the number in another file adds a round trip to every iteration. What is still forbidden is the *same* value written in two files — that one goes up to `constantes.py`.
2. No `DriveBase` in competition code — it holds `motor_B`/`motor_C` exclusively while active (even after `straight()` finishes), which conflicts with `_mover()` commanding each wheel individually.
3. No gyroscope — deliberate, due to past EV3 gyro drift issues. Heading error is corrected by re-anchoring against black tape lines (`linha.alinhar()`) instead of trying to avoid accumulating error.
4. Three separate PD loops with independent gains — wheel-sync PD in `_mover` (`KP`/`KD`), line-following PD in `seguir_linha` (`KP_LINHA`/`KD_LINHA`), and per-wheel alignment PD in `alinhar` (`KP_ALINHA`/`KD_ALINHA`). They act on different quantities; sharing gains detunes at least one of them. `alinhar()` intentionally does *not* synchronize the two wheels — each hunts for the line independently.
5. Never move the belt carrinho while the robot is driving/line-following — the mass shift detunes the drive PD mid-run (already tried, didn't work). Driving *with* it extended is fine; moving it *during* the drive is not. Moving it alongside a *different* stationary mechanism using `esperar=False` on both is fine.
6. The garra has one zero, marked once per program by `zerar_garra`, and it requires the carrinho already out of its home stop — otherwise the claw hits the robot's frame before the bottom stop and every descent of the run is off.
7. Functions list every parameter explicitly, no `**kwargs` *in the definition* — trades verbosity for autocomplete and immediate typo errors. `**` at the *call site* is the recommended style (decision 1).
8. `seguir_linha`/movement calls should always pass `tempo_ms`/`timeout` as a safety net even when another stop criterion is set, since a sensor that never triggers would otherwise run indefinitely.
9. **`motor_A` is commanded directly, with no module in between.** There is no `carrinho.py` and it should not come back. Each routine calls `motor_A.run_angle(speed, degrees)` (relative) or `run_target(speed, degrees)` (absolute) on the line where the movement happens, with that step's degrees written there. Wrappers like `estender_carrinho()` hid exactly the number the team tunes most. The clutch means the **sign** picks which mechanism engages — positive extends the sled, negative lowers the rear quadrilateral — but that is mechanics; the program just sends degrees and does not model branches or clamp at zero. Consequences that still can't be worked around: the two never move simultaneously; lowering the quadrilateral needs the sled retracted; and stalling toward negative to find the home stop *dips the rear mechanism*, which matters because `ler_mosaico` zeros while parked on the mosaic. If the clutch is reversed, flip `Direction` for `motor_A` in `setup.py` rather than scattering negative signs.
10. **Absolute sled positions need a zero, and it is written inline, not wrapped.** Two routines need it — `leitura_blocos` (3 sweep positions) and `pegar_blocos` (3 depths). Both do `run_until_stalled(...)` + `reset_angle(0)` as two visible lines. `parte1`/`parte2` establish no zero; everything there is relative `run_angle`.
11. **The storage column is chosen by the servo, not by throw force.** One throw pair (`ARREMESSO_V`/`_MS` in `pegar_blocos.py`) and one nominal depth for all 12 blocks. Don't reintroduce per-column force or per-column depth — a block landing in the wrong column is a servo-angle fix in the Arduino sketch, not a Python change.
12. **Delivery alignment is a chassis move**, because the storage columns are fixed to the robot. `POSICAO_ROBO_COLUNA` are robot positions; `entregar_blocos.py` must never touch `motor_A`. If the robot's 3 fixed columns already match the mosaic's spacing, set all three to `0` and the robot stops once per row.

### Units (consistent across the whole codebase)

| Quantity | Unit |
|---|---|
| Motor speed | degrees/second (~200 slow, ~500 medium, ~800 fast) |
| Time | milliseconds |
| Distance | millimeters |
| Angle | degrees |
| Sensor reading | 0–100 (normalized via `linha.ler()`, not raw `reflection()`) |

### Calibration order matters

Physical geometry before PD gains before speed — calibrating gains first makes you compensate measurement error with gain, which then breaks when battery level changes. Order: `DIAMETRO_RODA` → `ENTRE_EIXOS` → sensor calibration (`calibrar_varrendo`) → `KP_LINHA`/`KD_LINHA` (at low speed) → `V_LINHA` → servo angles → `POSICAO_COLUNA` → `PROFUNDIDADES` → garra → throw pair → mosaic sweep positions → `POSICAO_ROBO_COLUNA`. The full step-by-step, with which file/`TESTE` to run for each, is in the README "Calibração" table — and each value lives in the same file as its test.

**All sled positions are placeholders until measured on the robot.** They are now degrees of `motor_A`, not millimetres of belt: the clutch sits between motor and pulley, so no pre-clutch millimetre figure converts. This affects `PROFUNDIDADES` (`pegar_blocos.py`) and `COLUNA_1/2/3` (`leitura_blocos_parte2.py`).

**The two sled zeros run in opposite directions, and that is deliberate.** `pegar_blocos` zeroes against the *home* stop (`V_ZERAR` negative) and its `PROFUNDIDADES` are positive; `leitura_blocos_parte2` zeroes against the *fully-open* stop (`V_ABRIR` positive) and its `COLUNA_*` are negative. Each file is self-contained and says so at the top — but don't copy a target from one into the other.

## MicroPython-on-EV3 gotchas

Things that work in desktop Python but break on the robot (see README "Armadilhas" for the full list):

- `ColorSensor` is not hashable — can't be a dict key; compare sensor identity with `is`.
- No f-strings — use `print("valor:", x)`.
- `run_until_stalled` only works on large motors, not medium motors — hence the sled zeroing (motor A, large) finds its stop by stalling while `zerar_garra` (motor D, medium) finds it by time.
- Sensor reads are the most expensive operation in a control loop (go through the Linux filesystem) — never read the same sensor twice per cycle.
- No hardware floating point (`sqrt`, division are emulated) and no `async`/`multitask` — concurrency is done via `wait=False` + polling `control.done()`.
