# v1.0 distribution assets

The runnable `RyuSCOPE-GS-v1.0-linux-x86_64.{tar.gz,zip}` and checksum file are uploaded **as GitHub Release assets**, not committed into the source repository.

Build on the tested developer workstation via `scripts/build-linux.sh`, smoke-test the PyInstaller executable, package its complete onedir folder plus launcher and README, then create the `v1.0` tag and GitHub Release.

**Hardware testing:** AMD Radeon RX 7800 XT on CachyOS only. No general NVIDIA/Intel support claims. Host Gamescope, mangoapp, Vulkan drivers, Steam and Proton remain external.
