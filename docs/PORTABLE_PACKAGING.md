# Portable icon and path design for v0.5.2

The **RyuSCOPE dragon-crosshair emblem** is included at `assets/ryuscope-emblem.png` for the desktop entry and optional binary build. Its PNG pixels are the artwork from the established project emblem, resized for app icons. No new logo was generated.

## Key requirements

- **Do not publish the developer's Steam library paths, login username, mounted volumes, Proton prefixes, saves or credentials.** The repository contains no user-specific Steam paths.
- **Users select their own Steam libraries and games.** The helper `src_support/steam_paths.py` discovers standard Steam installations and allows manual additional library selection via the GUI. It stores added paths in the user's XDG configuration directory, not in the Git repository.
- Steam games remain in the user's own Steam library. RyuSCOPE must not copy, modify or automatically generate Proton prefixes.
- Preserve the existing `main.py` and integration modules from the **actual working** v0.5.2 build. This kit adds packaging assets and an optional path helper; it does not rewrite the running game launcher.

## Qt app icon (in the actual source)

The `.desktop` launcher and PyInstaller bundle use the provided emblem. To also show it as the *Qt window/taskbar icon* in the source, locate your existing `QApplication` setup and use:

```python
from pathlib import Path
import sys
from PySide6.QtGui import QIcon

root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
icon = root / "assets" / "ryuscope-emblem.png"
if icon.is_file():
    app.setWindowIcon(QIcon(str(icon)))
```

Only apply this snippet after inspecting the real v0.5.2 source, checking its Qt binding, and replacing `app` with the actual QApplication instance. Keep any existing icon behavior if it already works.

## GUI folder picker

For PySide6, a safe manual picker can look like:

```python
from PySide6.QtWidgets import QFileDialog
from src_support.steam_paths import save_library
folder = QFileDialog.getExistingDirectory(window, 'Choose your Steam library folder')
if folder:
    save_library(folder)
```

Integrate the helper into the existing UI after reviewing its source. Do not claim auto-discovery is functioning in v0.5.2 simply because this module is present.

## Installation and packaging

- Source-based install: run `bash scripts/setup-python.sh`, then `bash scripts/run-local.sh`.
- Optional per-user menu shortcut: `bash scripts/install-desktop.sh` (no sudo).
- Optional onedir Linux binary: install PyInstaller inside the app `.venv`, then `bash scripts/build-linux.sh`.
- **System requirements still include Gamescope and compatible Steam/Proton/Game runtimes**. PyInstaller does not bundle these.
- No Windows `.exe` is produced because RyuSCOPE is a Linux desktop application.
- Test every binary on a fresh user environment and SteamOS Desktop Mode before announcing it as a ready-made release.

**Release gate:** the real working v0.5.2 source files are not included in this *portable merge kit*. A downloadable runnable binary cannot be produced from documentation and artwork alone.
