# 🐉 RyuSCOPE GS

### Gamescope GUI for Linux gaming | RyujinWARE™

**🎮 NATIVE LINUX + STEAM/PROTON GAME LAUNCH SUPPORT DEMONSTRATED!**

> **v0.5.2 development checkpoint** · **Native Linux AND Steam/Proton launches demonstrated** · Five games tested on the developer's CachyOS / AMD system.

**RyuSCOPE GS** is a graphical launcher for configuring [Gamescope](https://github.com/ValveSoftware/gamescope) launch options for Linux games. The current development build has successfully launched **native Linux games and Windows games through Steam/Proton**. The five-game test record includes legacy, modern, and native titles.

**Important download notice:** This repository documentation package is GitHub-ready, but **does not contain the current runnable v0.5.2 application source**. To publish an installable release, the developer must add the preserved working `v0.5.2` Python application and its dependency manifest to this repository, verify the launch procedure, and then update the install status. **Do not tag documentation-only files as a functional app release.**

## ✅ Tested: native Linux + Proton launch paths

| Game | Launch mode | Gamescope game → output resolution | Test evidence |
|---|---|---|---|
| Fallout: New Vegas | Proton (reported) | Not recorded | Developer reported successful launch |
| STAR WARS: Galactic Racer | Proton 11.0 | 1920×1080 → 2560×1440 (logical) | Gamescope → Steam → Proton → game executable observed |
| Sleeping Dogs: Definitive Edition | Proton 11.0 | 1600×900 → 1920×1080 | Gamescope → Steam → Proton chain observed; gameplay success reported |
| Clair Obscur: Expedition 33 | Proton Experimental | 1920×1080 → 2560×1440 (logical) | Gamescope → Steam → Proton chain observed; gameplay success reported |
| **Half-Life 2** | **Native Linux (no Proton)** | **1280×720 → 1920×1080** | Gamescope → Steam Linux Runtime → `hl2.sh` observed; native launch reported |

All listed sessions used a **requested 180 FPS Gamescope limit (`-r 180`)**. The developer's physical monitor is **1920×1080 at 180 Hz**. A 2560×1440 Gamescope output request on that monitor is a *logical* output configuration, **not** proof of physical 1440p display output. Launches and resolution flags have been validated separately from actual scaling-filter quality. The tests do not prove universal game, driver, or distro compatibility.

**Full evidence and caveats:** [Compatibility results](docs/COMPATIBILITY_RESULTS.md) and [verification guide](docs/VERIFY_GAMESCOPE.md).

## 🧭 Get started

- **For developers/publishers:** [Install & use guide](docs/INSTALL_AND_USE.md), [environment checks](scripts/check-environment.sh), and [GitHub publishing guide](docs/HOW_TO_PUBLISH.md).
- **For first-time testers:** [Jesse's simple step-by-step guide](docs/JESSE_TEST_GUIDE.md) and [test report template](docs/TEST_REPORT.md).
- **For compatibility testing:** [Test plan](docs/TEST_PLAN.md) and [observed results](docs/COMPATIBILITY_RESULTS.md).

See the [publication checklist](docs/PUBLISH_CHECKLIST.md) before tagging a release.

**Before the runnable source is merged:** Run `bash scripts/check-environment.sh` from the repo directory to identify installed tools. `bash scripts/run-local.sh` is a convenience launcher that will **stop with a clear error** if the actual application entry point is absent. No script installs system packages or touches game data.

## ⚙️ Compatibility today

- **Operating system tested:** CachyOS KDE (Arch family) on an AMD Radeon RX 7800 XT. Other distributions, NVIDIA/Intel GPUs, and SteamOS desktops require external tests.
- **Native Linux:** Steam Linux Runtime launch path confirmed with Half-Life 2, **not** through Proton.
- **Proton:** Multiple successful Steam game launches observed with Proton 11.0 and Proton Experimental. RyuSCOPE does **not** bundle Proton or games; Steam manages its own compatibility tools.
- **GPU telemetry:** **AMD GPU monitoring only in v0.5.2. NVIDIA and Intel GPU monitoring are not supported/verified.** This statement concerns monitoring, *not* a blanket restriction on Gamescope launching games on other GPU vendors.
- **Still not verified in v0.5.2:** FSR/NIS filter effectiveness, Gamescope-native `--mangoapp` overlay, Steam Overlay disable functionality, LACT integration, and frame generation.
- **Future target: AMD + NVIDIA + Intel.** RyuSCOPE will aim for cross-vendor game launching, telemetry and backend compatibility, **but NVIDIA/Intel have not been tested yet**. See the [vendor support plan](docs/GPU_VENDOR_SUPPORT_PLAN.md).

## 🗺️ Roadmap

| Version | Goal |
|---|---|
| **v0.5.2** | Preserve the working native-Linux and Proton Gamescope launch checkpoint; invite outside testers after a reproducible installable package is prepared |
| **v0.6** | Finish Gamescope/Steam compatibility, verify upscaling filters, discover Steam libraries and per-game Proton prefixes safely |
| **v0.6.1** | MangoHud through Gamescope `--mangoapp`, clickable HUD customization, optional Steam Overlay disable setting |
| **v0.6.2** | Read-only LACT telemetry integration and RyuSCOPE graphs, with vendor-specific verification |
| **v0.6.3** | Real frame-generation integration and compatibility validation |
| **v1.0** | Stabilization, broader hardware testing, documented public release |

See the [full roadmap](docs/ROADMAP.md).

### 🔬 Related Linux projects and what we can do differently

Our roadmap overlaps with existing Gamescope/overlay tools. Rather than claim invented firsts, we are focusing on easier first-run setup, transparent launch diagnostics, safe per-game Steam workflows and evidence-based cross-vendor support. See the [current comparison of ScopeBuddy, ScopeBuddy GUI, GOverlay, SteamTinkerLaunch and LACT](docs/COMPETITIVE_LANDSCAPE.md).

## 🔒 Safety, privacy, and licensing

Use your **own Steam library**. RyuSCOPE is not distributed with game binaries, Steam account files, game saves, or Proton prefixes. Do not commit real `steamapps/`, `compatdata/`, `pfx/`, local logs, credentials, or personal launch profiles. Planned prefix discovery is read-only; see [Proton-prefix notes](docs/PROTON_PREFIXES.md).

A source license **has not yet been chosen**. See [LICENSING.md](LICENSING.md). This is an independent RyujinWARE™ project, not an official Steam, Valve, Gamescope, MangoHud or LACT product. All third-party trademarks belong to their owners.

## Application emblem and portable user setup

The repository includes the original **RyuSCOPE dragon-crosshair emblem** under `assets/`, plus optional desktop-launcher and PyInstaller build scripts. The icon and packaging resources are **not a substitute for the real working v0.5.2 Python files**, which must be imported from the developer's local working checkout before publishing a runnable application.

No Steam libraries, drive mount paths, game installs, user directories, credentials or Proton prefixes are included. Every user uses their own Steam install and selects their game/library folder in RyuSCOPE. See [portable packaging and path support](docs/PORTABLE_PACKAGING.md).

