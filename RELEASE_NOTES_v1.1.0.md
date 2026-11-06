# RyuSCOPE GS v1.1.0 | RyuFG development snapshot

**WIP prerelease · Development ON HOLD**

[v1.0 remains the stable release](https://github.com/Sh0umetsuRyu/RyuSCOPE-GS-GUI/releases/tag/v1.0).

## Upstream credits

**RyuFG-AFMF** is RyuSCOPE’s opt-in launcher integration for [AFMF-Linux v1.3.1](https://github.com/serialexperimentslainnnn/afmf-linux/tree/e738127530ebf4a8b070b9fb38469377958120a7), developed by Lain and upstream contributors. AFMF-Linux supplies the frame-generation implementation and includes AMD FidelityFX shader code. RyuSCOPE builds the upstream code and shaders as-is and adapts the Vulkan manifest for per-game activation. Packaged builds include [AFMF-Linux’s MIT notice](https://github.com/serialexperimentslainnnn/afmf-linux/blob/e738127530ebf4a8b070b9fb38469377958120a7/LICENSE) and the [AMD FidelityFX notice](https://github.com/serialexperimentslainnnn/afmf-linux/blob/e738127530ebf4a8b070b9fb38469377958120a7/shaders/fidelityfx/LICENSE.txt).

## Integration

RyuFG-AFMF is experimental and defaults off, including for existing profiles. The development code wires RyuFG into direct launches, Steam launch options and native Ryujinx. Steam Apply and Copy can stage a gated Vulkan layer in the user's local data directory. RyuFG targets 64-bit Vulkan, including games using DXVK or VKD3D-Proton. See the [RyuFG guide](https://github.com/Sh0umetsuRyu/RyuSCOPE-GS-GUI/blob/v1.1.0/docs/RYUFG.md) for scope and build instructions.

## Validation and remaining work

- Five local integration smoke tests passed, covering direct and Steam command wiring, conflict checks, legacy profile defaults, and Steam profile apply and restore with test fixtures.
- The [November 5 test report](https://github.com/Sh0umetsuRyu/RyuSCOPE-GS-GUI/blob/v1.1.0/docs/RYUFG_TEST_REPORT.md) records a successful layer build and portable app startup. It also records 119 generated companion frames from 120 presents in each of two software Vulkan probes, with sampled pixel checks. Some upstream headless checks missed their expected frame dumps at default settings and passed under controlled settings with the governor and minimum FPS floor disabled.
- Hardware Vulkan and real-game frame generation still need validation. Steam Runtime, Proton, native Ryujinx, and Gamescope presentation with MangoApp and FSR need real-session checks. Frame pacing, image quality, skipped frames and title-specific behavior, including Clair Obscur, remain open.

## Hardware hold

Development is on hold while the RX 7800 XT thermal issue is investigated. The reported GPU junction temperature reached **110°C**, with a reported junction-to-edge delta of **approximately 45°C**. A hardware thermal-contact problem is suspected. The root cause remains unverified, and the reported readings do not establish that RyuSCOPE or RyuFG caused the issue.

GitHub provides source archives for this snapshot. This prerelease has no attached binaries.
