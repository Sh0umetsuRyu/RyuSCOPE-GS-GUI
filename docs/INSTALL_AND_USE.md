# Installing and using RyuSCOPE GS (v0.5.2)

> **Publication gate:** The current documentation ZIP does **not** include v0.5.2's real Python application. These instructions become runnable only **after** the developer imports `main.py`, its integration modules/assets, and a verified Python dependency manifest. A broken or misleading install guide is worse than a clearly labeled checkpoint. The helper scripts here tell you when these pieces are missing.

## First-time Linux user: what you need

- A Linux desktop with working Steam and at least one game already installed (for the Steam launch path).
- Gamescope installed and usable on *your* Linux environment.
- The complete RyuSCOPE v0.5.2 application source/verified build, **not** just this documentation starter.
- Python 3 and the Python packages the actual source requires (to be enumerated once the source is imported).
- Optional: a compatible Proton installation managed by Steam for Windows titles. Native Linux games do not require Proton.

**SteamOS:** Start in **Desktop Mode**. SteamOS is not identical to a regular Arch/CachyOS installation; do **not** run generic `sudo pacman -S` instructions or disable SteamOS protections based on this guide. Ask the developer for a suitable packaged build if dependencies are missing.

## Easy setup once the actual release has been published

1. Open the RyuSCOPE repository in GitHub. Click **Code → Download ZIP** and extract it to a folder, or clone it using Git. You do not need to download anyone else's games.
2. Open a terminal in the extracted project folder (the folder containing `README.md` and `scripts/`).
3. Check your system, with **no changes** to your PC:

   ```sh
   bash scripts/check-environment.sh
   ```

4. If the repository contains the real app and a verified `requirements.txt`, create a local isolated Python environment:

   ```sh
   bash scripts/setup-python.sh
   ```

   The setup script **does not** install system packages, use `sudo`, or edit Steam. It will stop and explain what is missing if no dependency manifest has been published.

5. Launch the included application once the source and dependencies are in place:

   ```sh
   bash scripts/run-local.sh
   ```

   If it reports `main.py missing`, you downloaded the **documentation-only scaffold**, not the application. Do not replace it with the old v0.2 source.

## Your first game test

1. Ensure Steam starts normally and your chosen game already launches **without RyuSCOPE**.
2. Open RyuSCOPE, confirm Gamescope detection, and select a game or use its Steam launch-command workflow **as documented by the complete app's GUI**. Do not assume the project has already implemented automatic scanning of every Steam library.
3. For the first test, keep the game's resolution and output resolution at a familiar, supported setting. Do not enable unverified features.
4. If the GUI provides a button to **copy Steam launch options**, make a backup of any existing launch options before replacing them. In Steam: right-click the game → **Properties → General → Launch Options**; paste the complete command the GUI generated, retaining `%command%` if present. Launch through Steam as usual. The exact v0.5.2 workflow must be checked against the imported source before publication.
5. Check that the game opens and plays; quit normally. For support, record the OS/GPU, selected resolutions, and whether the game opened/exited cleanly.
6. **Do not copy Steam game files or Proton prefixes** into the RyuSCOPE folder. You use your own Steam library on your machine.

## Does it support native Linux and Proton?

**Yes: both launch paths were demonstrated on the developer's system.** Half-Life 2 used `hl2.sh` through Steam Linux Runtime without Proton; Galactic Racer, Sleeping Dogs: Definitive Edition, and Expedition 33 used Proton launch paths. These are game-launch observations, not a guarantee that every game or GPU works.

## If something goes wrong

- `gamescope: command not found`: Gamescope is missing from the environment; follow your distribution's official packaging guidance. Do not run unreviewed privileged commands.
- `main.py missing`: Real v0.5.2 source has not been included yet.
- `requirements.txt missing`: Python dependency list has not been verified/published; do not guess dependencies.
- Gamescope opens but the game doesn't: Test the game directly through Steam, check chosen Steam compatibility tool, try a normal resolution, then capture a *redacted* error report.
- SteamOS Gaming Mode issues: Retry the first test in Desktop Mode; Gaming Mode uses its own Gamescope session and is a separate validation target.

Send a [test report](TEST_REPORT.md) if you get stuck. See [verification commands](VERIFY_GAMESCOPE.md) for an optional read-only process check.

## Optional desktop app shortcut

Once the actual `main.py` and `requirements.txt` exist and the app starts correctly, install a per-user launcher with the official RyuSCOPE emblem:

```bash
bash scripts/install-desktop.sh
```

Find **RyuSCOPE GS** in your application menu. It uses the local extracted project's path, not the developer's computer paths. If you move the folder later, run the script again.

An optional Linux executable bundle can be built by a maintainer using `scripts/build-linux.sh` once the complete verified source is present. See [Portable packaging](PORTABLE_PACKAGING.md).
