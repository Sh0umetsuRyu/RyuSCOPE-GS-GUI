# RyuSCOPE GS v1.0 | Gamescope + MangoApp + FSR

**First major RyujinWARE RyuSCOPE GS release candidate, promoted from the developer's working v0.6 MangoApp branch.**

## Verified in the developer environment

- Gamescope GUI and Steam/Proton launch workflow.
- Gamescope's `--mangoapp` overlay, visibly working in Left 4 Dead 2.
- Gamescope FSR scaling toggle, with observable visual change in Left 4 Dead 2.
- Working native Linux and Proton launches across the documented test matrix.

## Installation

Download **RyuSCOPE-GS-v1.0-linux-x86_64.tar.gz** (preferred on Linux) or **RyuSCOPE-GS-v1.0-linux-x86_64.zip** below. Extract the archive and execute `./run.sh` in its directory. You do **not** have to compile Python source. The external Gamescope, MangoHud/mangoapp, Steam/Proton and Vulkan/driver components are not bundled.

## Testing limitations

**TESTED ON AMD HARDWARE ONLY: RX 7800 XT on CachyOS.** NVIDIA/Intel and other distros are not verified. Builds created on CachyOS may need newer Linux libraries than older distributions provide. Features such as frame generation, full LACT control and CPU telemetry are *future releases*, not features of this package.

See README and docs/COMPATIBILITY_v1.0.md in the repository for details. ZIP/TAR downloads are application bundles; GitHub's automatic Source code downloads are not.
