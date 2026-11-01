# RyuSCOPE GS v0.5.2: working Gamescope launch checkpoint

> **Release candidate documentation.** Do not publish/tag until the developer's real v0.5.2 application source, dependency list and tested installation flow are included.

## Headline: Native Linux **and** Steam/Proton support demonstrated! 🎮🐉

Five game launches have been reported successful on the developer's CachyOS AMD machine. Four include process-tree evidence in the conversation. The test set spans native Steam Linux Runtime and different Proton versions:

- **Half-Life 2:** native Linux `hl2.sh` via Steam Linux Runtime, 720p → 1080p Gamescope options.
- **STAR WARS: Galactic Racer:** Proton 11.0, 1080p → logical 1440p.
- **Sleeping Dogs: Definitive Edition:** Proton 11.0, 900p → 1080p.
- **Clair Obscur: Expedition 33:** Proton Experimental, 1080p → logical 1440p.
- **Fallout: New Vegas:** developer-confirmed legacy Proton game launch (process details not recorded).

These are game-launch results, **not** proof of FSR filter output, universal compatibility, 1440p physical scan-out or measured 180 FPS. See [full test evidence](docs/COMPATIBILITY_RESULTS.md).

## Current compatibility limits

- **GPU monitoring: AMD only.** NVIDIA and Intel telemetry are not available/verified.
- Other GPU vendors, distributions and SteamOS desktop setups need testers.
- Game libraries, game binaries and Proton prefixes are *not* part of the repository.
- `--mangoapp` through Gamescope, per-game Steam Overlay disable, LACT telemetry and frame generation are future implementation targets. None is claimed working in v0.5.2.

## Installation & testing

See [Quick Start](docs/QUICKSTART.md), [Install & Use](docs/INSTALL_AND_USE.md) and [Jesse's beginner test guide](docs/JESSE_TEST_GUIDE.md). These only become executable instructions after real v0.5.2 application code is added to this starter; the included helper scripts deliberately fail clearly if source/dependencies are missing.

## Next milestones

- v0.6: Steam/Proton groundwork and Gamescope scaling verification.
- v0.6.1: MangoHud through Gamescope + optional Steam Overlay disable.
- v0.6.2: LACT integration.
- v0.6.3: frame generation.
- v1.0: stabilized public release.
