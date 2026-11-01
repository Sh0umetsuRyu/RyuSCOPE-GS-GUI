# AMD, Intel and NVIDIA: planned RyuSCOPE support

**Current status: v0.5.2**. RyuSCOPE's existing GPU monitoring is **AMD-only**. All observed launches came from a **single AMD RX 7800 XT system running CachyOS KDE**. There is no demonstrated Intel or NVIDIA RyuSCOPE compatibility yet.

## Separate these capabilities

| Capability | v0.5.2 status | Planned design/verification |
|---|---|---|
| Gamescope game launch | Evidence on AMD RX 7800 XT; native Linux and Proton | Test AMD / NVIDIA / Intel, driver versions, X11 and Wayland, nested sessions and game launch behavior |
| Gamescope resolution/scaling flags | Multiple resolution requests documented on AMD | Validate output mode, filter activation, scaling result and frame pacing on all three vendor stacks |
| RyuSCOPE GPU telemetry | **AMD only** | Optional, **read-only** LACT integration (v0.6.2), with per-metric availability and driver-specific fallbacks |
| Gamescope `--mangoapp` and UI-controlled HUD | Not verified in v0.5.2 | v0.6.1 check `mangoapp` availability and user-selected config behavior without direct game injection |
| Frame generation | Not implemented | v0.6.3 backend capability/driver validation, explicitly limited to working combinations |
| Steam Overlay disable | Not implemented | Optional v0.6.1 if reliable; allow 'Follow Steam' fallback |

## Suggested outside tests

- **AMD:** developer RDNA3 (7800 XT), another AMD generation (Jesse's GPU model to confirm), and an integrated Radeon if available.
- **NVIDIA:** dedicated desktop NVIDIA GPU with its installed proprietary driver, including explicit Gamescope startup check and relevant driver/DRM requirements; avoid assuming all NVIDIA configurations work.
- **Intel:** Arc and/or integrated Intel GPU with supported Mesa; report each separately.
- **Session:** KDE Plasma Wayland, other Wayland compositor, X11, SteamOS Desktop Mode; Gaming Mode evaluated independently because Gamescope already manages the session.
- **Game path:** native Linux and Steam Proton, checking input, overlay, clean shutdown, scaling and actual monitor output.
- **Multiple GPUs:** report actual renderer and compositor GPU separately where possible; don't infer from GPU vendor name alone.

## Ship gate

A feature can be marked **planned**, **detected**, **launch-tested**, or **verified**. Make no universal GPU-vendor claims in the public README until real NVIDIA/Intel test reports exist. Missing telemetry is not a game-launch failure. No unrequested driver installs, kernel parameters, service changes or privileged GPU tuning.

Official references:
- Gamescope: https://github.com/ValveSoftware/gamescope
- LACT: https://github.com/ilya-zlobintsev/LACT
