# Repository Guidelines

## Project Structure & Module Organization

This repository is a collection of independent maker projects rather than one monolithic application. Each top-level directory is a project or learning track, such as `餐券遊戲機`, `倒車雷達`, `Mcu課程`, and `智慧音箱`. Hardware prototypes generally keep their MicroPython entry point in `main.py`, with local drivers such as `ssd1306.py` beside it. Design notes, purchase lists, and development plans are stored as Markdown in the relevant project directory. `智慧音箱` also contains a Vercel Python API under `api/` and application modules under `src/`.

## Build, Test, and Development Commands

There is no repository-wide build system. For MicroPython projects, prefer using the official `mpremote` tool to upload files, monitor REPL, and reset boards:

```powershell
# Upload script to MCU root and reset board
python -m mpremote connect <COM_PORT> cp <file> :<file> + reset

# Interactive REPL session
python -m mpremote connect <COM_PORT> repl
```

For the `智慧音箱` service, install dependencies from its requirements file and run the framework's local server as appropriate for the current entry point:

```powershell
python -m pip install -r 智慧音箱/requirements.txt
python -m pip install -r 智慧音箱/src/requirements.txt
```

Deployments are configured by `智慧音箱/vercel.json`; validate locally before deploying to Vercel.

## Communication & Language

- Always communicate with the user in Traditional Chinese (繁體中文).
- Preserve existing Traditional Chinese documentation, code comments, and naming conventions.

## MicroPython & Cloud Conventions

- **Wi-Fi Multi-SSID Prioritization**: When configuring fallback Wi-Fi networks in MCU code, list the highest-priority network first (e.g. mobile hotspot first, home Wi-Fi as backup).
- **Cloud Sync Architecture**: Communication with Google Apps Script (GAS) or web hooks operates over short-lived HTTPS REST API requests (request-response pattern), not persistent raw TCP/WebSocket connections.

## Coding Style & Naming Conventions

Use 4-space indentation for Python, clear `snake_case` names, and small functions focused on one hardware or service responsibility. Preserve the existing project language and naming where practical, including Chinese directory and Markdown names. Keep board pin assignments and hardware constants near the top of the relevant module. Avoid committing generated files such as `__pycache__/`.

## Testing Guidelines

No test framework or coverage threshold is currently configured. For hardware code, perform a board-level smoke test covering startup, sensor input, display/output, and safe failure behavior. For `智慧音箱`, add focused unit tests when changing service logic and manually exercise the API endpoint before deployment.

## Commit & Pull Request Guidelines

Existing history uses short, descriptive Chinese commit subjects (for example, `建立貓咪餐券 v1.0 小遊戲`). Follow the same style: describe the project and outcome, and keep each commit focused. Pull requests should explain the affected project, list hardware or configuration changes, include validation steps, and attach photos or screenshots when behavior or wiring changes.

## Security & Configuration Tips

Never commit API keys, credentials, device tokens, or private deployment settings. Use environment variables for service secrets and document required variable names without their values. Review pin mappings and power assumptions before flashing code to physical hardware.
