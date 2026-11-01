# RyuSCOPE GS: comparison with existing Linux gaming GUIs

**Research date:** October 31, 2026. This is an outside-project review, **not** a claim that RyuSCOPE is superior. Verify each external project's current release before repeating comparisons in public marketing.

## Executive summary

Many RyuSCOPE feature ideas overlap with established Linux tools. **Native Linux and Proton support, Gamescope profiles, MangoHud customization, Steam integration, and even some frame-generation configuration are *not novel on their own*.** This is good news: these are important user expectations, and we can learn from existing UX patterns without copying code or branding.

The opportunity is a **focused, beginner-friendly Gamescope launch/verification experience** that owns the complete workflow: select game, configure output vs render resolution, generate a safe Steam launch command, detect real launch behavior, customize the Gamescope-native MangoHud, integrate optional LACT telemetry, and report which functions are supported on this GPU/driver/session.

## Relevant projects

| Project | Currently documented strengths | Overlap with RyuSCOPE | Lessons/opportunity |
|---|---|---|---|
| **ScopeBuddy** | Steam Overlay and Steam Input workarounds for nested Gamescope, per-game/default args/environment, display auto-detection and Gamescope session avoidance | Direct overlap with Steam launch and Gamescope profile work | Test nested/embedded session detection; prefer well-tested workarounds to invented overlay toggles |
| **ScopeBuddy GUI** | Python/Qt GUI for Gamescope resolution, aspect ratio, HDR/Adaptive Sync profiles; can apply via ScopeBuddy | Very close to the current Gamescope configuration GUI idea | RyuSCOPE must differentiate on launch diagnostics, polished first-run help, measured verification, and integrated telemetry, rather than merely being another checkbox wrapper |
| **GOverlay** | Qt6 MangoHud/vkBasalt/vkSumi/OptiScaler/proton tweak configurations, per-game settings, lsfg-vk/OptiScaler-related functionality | Strong overlap with HUD customization and later frame-generation milestone | Frame generation is **not** a unique feature; focus on compatibility validation, unified per-game state, and safety. Don't market these features as 'first-ever' |
| **SteamTinkerLaunch** | Native Linux and Proton Steam launch wrapper with Gamescope, MangoHud, Proton customization and extensive third-party tool integration | Broad overlap with native+Proton claims and Steam integration | Smaller scope and simpler UX could differentiate, but less functionality is not inherently better; benchmark setup steps and discoverability |
| **LACT** | AMD/NVIDIA/Intel monitoring with GPU charts and hardware data, optional power/thermal tuning | Overlap with RyuSCOPE's planned GPU monitoring | Use an optional read-only telemetry adapter and original Qt graphs; avoid reimplementing GPU driver access or promising uniform metrics across vendors |
| **Gamescope** | Provides compositor and filters; documents AMD/Intel Mesa support and NVIDIA driver requirements | The actual foundation for RyuSCOPE | Detect supported features from installed Gamescope rather than hard-code availability or confuse Gamescope's compatibility with RyuSCOPE's validated platforms |

## How RyuSCOPE can differentiate (proposals, not completed features)

1. **Evidence-based compatibility panel:** show *detected / launch-tested / feature-verified* separately for each component; export anonymized diagnostic reports with user consent.
2. **Launch pipeline visualizer:** clearly distinguish game resolution, Gamescope output resolution, physical monitor mode, frame cap, scaling algorithm, and (future) generated FPS.
3. **One game, one coherent profile:** native Linux and Proton launch flow with read-only Steam library/AppID/prefix identification, while preserving user Steam options and not touching game files.
4. **Unified but modular backends:** Gamescope + `--mangoapp` (if installed), optional LACT telemetry, optional frame-gen adapter; never silently install drivers or need root for core launch.
5. **Cross-vendor quality gates:** AMD/NVIDIA/Intel matrix with driver variants, X11/Wayland, standalone desktop vs gamescope-session, multi-GPU handling. Public claims only after tests.
6. **Beginner experience:** copy/paste Steam commands; plain-English missing dependency and incompatibility explanations; reproducible install and one-page tester guide.

## Competitive cautions

- ScopeBuddy already addresses some **Steam Overlay** and **Steam Input** issues; disabling Steam Overlay via process environment is not reliably identical to the official Steam game setting. Test reversible per-game control rather than promise a working switch today.
- GOverlay already has frame-generation and per-game tools. Its existence means a RyuSCOPE v0.6.3 feature would be part of an existing ecosystem, not a brand-new invention.
- LACT's advertised support for AMD/NVIDIA/Intel does **not** mean every control, metric or driver is universal. RyuSCOPE v0.5.2 is AMD-monitoring-only; other vendors remain a test goal.
- Gamescope supports multiple GPU vendors in documented configurations. This alone does **not** verify RyuSCOPE on NVIDIA or Intel.
- A different feature set is not proof of better performance, better UX, or stronger compatibility. We need tester evidence before making such claims.

## Primary sources reviewed

- Valve Gamescope, official repository: https://github.com/ValveSoftware/gamescope
- ScopeBuddy: https://github.com/OpenGamingCollective/ScopeBuddy
- ScopeBuddy GUI: https://github.com/rfrench3/scopebuddy-gui
- GOverlay: https://github.com/benjamimgois/goverlay
- GOverlay releases: https://github.com/benjamimgois/goverlay/releases
- SteamTinkerLaunch: https://github.com/sonic2kk/steamtinkerlaunch
- LACT: https://github.com/ilya-zlobintsev/LACT

This document is comparative planning research, not a license to reuse third-party code. Check project licenses before importing code, artwork or substantial text.
