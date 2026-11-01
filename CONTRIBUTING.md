# Contributing and testing

RyuSCOPE GS is still in early development. Please open an issue with reproducible observations instead of asserting broad compatibility.

Include:
- RyuSCOPE version or commit hash
- Distribution and version; Desktop Mode or SteamOS Gaming Mode; Wayland/X11 session
- GPU, Mesa/driver and Vulkan versions, Gamescope and MangoHud versions (where relevant)
- Game engine/API where known (native Vulkan, DXVK, VKD3D-Proton, OpenGL, etc.)
- Steam/Proton version and **whether** the game used an external Steam library; do not post personal full paths
- Input/output resolution, filter, fullscreen/window mode and refresh rate
- Expected versus observed behavior, logs with identifying fields removed

Never attach saves, `steamapps`, `compatdata`, `pfx`, user credentials, Steam authentication or paid game assets. Logs may leak home directories, usernames and Steam IDs. Redact before sharing.

Feature work follows [docs/ROADMAP.md](docs/ROADMAP.md).

For existing results and native Linux/Proton evidence, see [COMPATIBILITY_RESULTS.md](docs/COMPATIBILITY_RESULTS.md). For novice testers use [QUICKSTART.md](docs/QUICKSTART.md).
