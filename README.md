# RyuSCOPE GS v1.0

> **v1.1.0 development snapshot · WIP · Development ON HOLD**
>
> RyuFG is experimental and real-game frame generation remains unverified. Development is paused while reported RX 7800 XT junction temperatures up to 110°C and an approximately 45°C junction-to-edge delta are investigated. A hardware thermal-contact issue is suspected and remains unverified. See the [release notes](RELEASE_NOTES_v1.1.0.md) for test coverage and the hardware hold.

**RyujinWARE™ | Gamescope GUI for Linux**

> **TESTED ON AMD HARDWARE ONLY**: development and game-launch testing have been performed on a **Radeon RX 7800 XT** running CachyOS Linux. NVIDIA and Intel GPUs have **not been validated**. These results do not establish compatibility with all AMD GPUs, distros, display servers or drivers.

## Download the real executable

Use the ZIP or TAR.GZ files attached to the [v1.0 GitHub Release](https://github.com/Sh0umetsuRyu/RyuSCOPE-GS-GUI/releases/tag/v1.0). **Do not use GitHub's automatically generated “Source code” links if you want a ready-to-run application.**

Extract one archive, open the extracted folder and execute `./run.sh` (or `./RyuSCOPE-GS/RyuSCOPE-GS`). There is **no need to compile source, install PyInstaller or set up a Python environment** to run the packaged application.

**External dependencies:** Linux x86_64 desktop session with compatible graphics drivers and Vulkan runtime, `gamescope`, and `mangoapp` (provided by MangoHud for the integrated overlay). Steam and Proton are separately required for Steam/Proton games. Game files are not included.

The portable build is assembled on the developer's CachyOS environment. Other Linux distributions, especially those with older glibc or Qt compatibility, are not yet verified. The executable is not an AppImage or universal distribution package.

## Verified development results

- Gamescope launcher and Steam/Proton game launching demonstrated on the developer's AMD setup.
- Gamescope-integrated MangoApp overlay observed while playing **Left 4 Dead 2** (native Linux).
- Gamescope FSR on/off visual difference demonstrated in **Left 4 Dead 2**.
- Other reported launch tests: **Half-Life 2**, **Fallout: New Vegas**, **Sleeping Dogs: Definitive Edition**, and **Clair Obscur: Expedition 33**.

For specific test caveats see [compatibility details](docs/COMPATIBILITY_v1.0.md).

**Not in v1.0:** AFMF/other frame generation backends, full LACT GPU tuning and telemetry integration, or CPU tuning. Some overview graphs in v1.0 use demonstration data, not live measurements.

## Roadmap

- **v1.1:** AFMF-Linux frame generation exploration and validation; later investigate lsfg-vk as an alternate backend.
- **v2.0:** Full LACT integration, including real GPU telemetry, graphs, and supported GPU tuning controls.
- **v3.0:** CPU telemetry and monitoring, the final planned major feature milestone (without CPU overclocking controls).

See [release notes](RELEASE_NOTES_v1.0.md) and [version roadmap](docs/ROADMAP_v1.0.md).

## Source and project

The Python source and integration modules remain in this repository. For contributions and build instructions, see `docs/` and `scripts/`. The binaries in GitHub Releases are distinct from the repository's source archive.

RyuSCOPE GS is an independent RyujinWARE project, not an official Valve, Gamescope, Steam or MangoHud release. The repository's source license status is documented separately in `LICENSING.md`.
