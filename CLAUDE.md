# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Competition code for a WRO (World Robot Olympiad) team robot. Platform: **Pybricks MicroPython v2.0 on LEGO EV3**, written and edited in VS Code but executed on the EV3 brick itself — not on this machine. There is no build system, package manager, or automated test suite; "testing" means running a file's `if __name__ == "__main__":` block physically on the robot and measuring with a ruler / eyeballing behavior.

`README.md` is written for both humans and AI agents and is the primary source of truth — read it in full before making non-trivial changes. It documents tested decisions (see "Regras do projeto" in the README) that must not be casually reverted.

## Running code

- No terminal build/lint/test commands apply here — this is not a hosted Python project.
- VS Code + the `lego-education.ev3-micropython` extension deploys to the EV3 over USB/network.
- `.vscode/launch.json` → F5 runs whichever `.py` file is currently open in the editor (`${relativeFile}`), so each module's own `if __name__ == "__main__":` block acts as its manual test/calibration routine.
- Only `**/*.py` is downloaded to the brick (`ev3devBrowser.download.include` in `.vscode/settings.json`); every module a program imports must exist on the EV3, but non-`.py` files (README, `.scad`) are filtered out automatically.

## Architecture

Import graph (one-directional):

```
setup.py  ←  movimento.py  ←  linha.py
   ↑
   └────  carrinho.py
```

- **`setup.py`** — the *only* place hardware objects (`Motor`, `ColorSensor`, `EV3Brick`) are constructed. Creating two `Motor` objects on the same port raises a runtime error, so every other module imports motors/sensors from here rather than instantiating anything itself. If a port changes, it changes only in this file. It also sets `motor_B.control.limits()` / `motor_C.control.limits()` — required here (not in `movimento.py`) because Pybricks demands the motor be stationary when called, and it must run before any movement code executes.
- **`movimento.py`** — chassis locomotion (`andar`, `girar_eixo`, `girar_arco`, `girar_pivo`). All four are thin wrappers around one internal core, `_mover(alvo_esq, alvo_dir, ...)`, which takes per-wheel target degrees, runs a trapezoidal speed profile (`_perfil_velocidade`), and layers a PD loop on top that corrects *synchronization* between the two wheels (not line position). Sign convention across all four: **positive angle = turn right**.
- **`linha.py`** — dual-sensor line following (`seguir_linha`, `alinhar`, `procurar_linha`) plus sensor calibration (`calibrar`, `calibrar_varrendo`) and a small library of stop conditions (`viu_escuro`, `viu_claro`, `viu_cor`, `cruzamento`) built as `(nome, func)` tuples passed via `parar_se=[...]`. Imports shared constants/helpers from `movimento.py` (`MM_POR_GRAU`, `ENTRE_EIXOS`, `_perfil_velocidade`, `_limitar`) rather than duplicating them.
- **`carrinho.py`** — GT2 belt-driven sled on `motor_A`, positioned in millimeters instead of motor degrees (`zerar_carrinho`, `mover_carrinho`, `recolher`, `estender`, `esperar_carrinho`).
- **`prog1.py`** — the actual mission program that runs at competition; composes the above modules with tuned parameters.
- **`aulapybricks.py`** — standalone teaching file (lessons 1–8, selected via the `LICAO` variable). Deliberately does not import `movimento.py`/`linha.py`; don't treat it as part of the competition code path.

### Load-bearing design decisions (don't undo without strong reason — details/rationale in README "Regras do projeto")

1. No `DriveBase` in competition code — it holds `motor_B`/`motor_C` exclusively while active (even after `straight()` finishes), which conflicts with `_mover()` commanding each wheel individually.
2. No gyroscope — deliberate, due to past EV3 gyro drift issues. Heading error is corrected by re-anchoring against black tape lines (`linha.alinhar()`) instead of trying to avoid accumulating error.
3. Three separate PD loops with independent gains — wheel-sync PD in `_mover` (`KP`/`KD`), line-following PD in `seguir_linha` (`KP_LINHA`/`KD_LINHA`), and per-wheel alignment PD in `alinhar` (`KP_ALINHA`/`KD_ALINHA`). They act on different quantities; sharing gains detunes at least one of them. `alinhar()` intentionally does *not* synchronize the two wheels — each hunts for the line independently.
4. Never move the belt carrinho while the robot is driving/line-following — the mass shift detunes the drive PD mid-run (already tried, didn't work). Moving it alongside a *different* stationary mechanism (e.g. the claw) using `esperar=False` on both is fine.
5. Functions list every parameter explicitly, no `**kwargs` — trades verbosity for autocomplete and immediate typo errors.
6. `seguir_linha`/movement calls should always pass `tempo_ms`/`timeout` as a safety net even when another stop criterion is set, since a sensor that never triggers would otherwise run indefinitely.

### Units (consistent across the whole codebase)

| Quantity | Unit |
|---|---|
| Motor speed | degrees/second (~200 slow, ~500 medium, ~800 fast) |
| Time | milliseconds |
| Distance | millimeters |
| Angle | degrees |
| Sensor reading | 0–100 (normalized via `linha.ler()`, not raw `reflection()`) |

### Calibration order matters

Physical geometry before PD gains before speed — calibrating gains first makes you compensate measurement error with gain, which then breaks when battery level changes. Order: `DIAMETRO_RODA` → `ENTRE_EIXOS` → sensor calibration (`calibrar_varrendo`) → `KP_LINHA`/`KD_LINHA` (at low speed) → `V_LINHA` → `DENTES_POLIA` (carrinho). Full step-by-step procedure is in the README "Calibração" section.

## MicroPython-on-EV3 gotchas

Things that work in desktop Python but break on the robot (see README "Armadilhas" for the full list):

- `ColorSensor` is not hashable — can't be a dict key; compare sensor identity with `is`.
- No f-strings — use `print("valor:", x)`.
- `run_until_stalled` only works on large motors, not medium motors.
- Sensor reads are the most expensive operation in a control loop (go through the Linux filesystem) — never read the same sensor twice per cycle.
- No hardware floating point (`sqrt`, division are emulated) and no `async`/`multitask` — concurrency is done via `wait=False` + polling `control.done()`.
