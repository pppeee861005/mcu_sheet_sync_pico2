# Repository Guidelines

## Project Structure & Module Organization

This repository is a standalone MicroPython Dino Game for ESP32-compatible boards. The project root contains:

- `main.py`: game loop, input handling, physics, scoring, rendering, and difficulty logic.
- `ssd1306.py`: SSD1306 OLED driver.
- `開發進度追蹤表.md`: milestones, hardware configuration, and validation status.
- `.gitignore`: excludes Python cache files such as `__pycache__/` and `*.pyc`.

There is no separate test or asset directory. Hardware behavior is validated on the connected development board.

## Build, Test, and Development Commands

MicroPython files are uploaded directly to the board. From this directory:

```powershell
mpremote connect list
mpremote connect COM3 fs cp ssd1306.py :ssd1306.py
mpremote connect COM3 fs cp main.py :main.py
mpremote connect COM3 reset
mpremote connect COM3 repl
```

Replace `COM3` with the detected serial port. Run a host-side syntax check before uploading:

```powershell
python -m py_compile main.py
```

## Coding Style & Naming Conventions

Use 4-space indentation and clear `snake_case` names. Keep hardware pins and gameplay constants near the top of `main.py`. Use small functions for drawing, physics, input, scoring, and collision logic. Preserve the existing Traditional Chinese documentation and comments where practical. Do not commit generated cache files or credentials.

## Testing Guidelines

No automated test framework is configured. Every gameplay change should pass `py_compile`, then be tested on hardware for OLED output, button input, jumping, collision, scoring, Game Over, restart behavior, and stability over an extended play session. Record meaningful results in `開發進度追蹤表.md`.

## Commit & Pull Request Guidelines

Use short, descriptive Chinese commit subjects, for example:

```text
完成 Pico 小恐龍 v0.4 UI 與平衡調整
```

Keep commits focused. Pull requests should describe the affected gameplay or wiring, list validation steps, note board and pin assumptions, and include screenshots or photos when display or hardware behavior changes.

## Security & Configuration Tips

Review SDA, SCL, and button pin assignments before flashing. Never commit API keys, device tokens, or private deployment settings.
