# RyuSCOPE GS v0.5.2: actual game compatibility observations

**Testing environment:** One developer machine running CachyOS KDE, Ryzen 9 7900X, AMD Radeon RX 7800 XT, 1920×1080 / 180 Hz monitor. The process command excerpts below came from in-session `ps --forest` output, not from independently measured graphics output.

**Summary:** Five titles have been reported as successfully launching under the v0.5.2 workflow; **four have provided process-tree evidence in this conversation** and Fallout: New Vegas was reported working without a process-tree capture shown. Gamescope was observed wrapping both Steam/Proton and native Linux runtime paths.

| Test | Game | Path shown | Steam AppID | Gamescope options observed | Evidence strength |
|---|---|---|---|---|---|
| 1 | Fallout: New Vegas | Legacy Windows game through Proton (developer report) | Not recorded | Not recorded | Developer success report only |
| 2 | STAR WARS: Galactic Racer | Steam → Proton 11.0 → game executable | `4078430` | `-w 1920 -h 1080 -W 2560 -H 1440 -r 180 -f` | Gamescope process tree and game binary present |
| 3 | Sleeping Dogs: Definitive Edition | Steam → Proton 11.0 → `sdhdship.exe` launch target | `307690` | `-w 1600 -h 900 -W 1920 -H 1080 -r 180 -f` | Gamescope and Proton chain present; game UI/playability reported by developer; executable process not separately shown by filtered output |
| 4 | Clair Obscur: Expedition 33 | Steam → Proton Experimental → `Expedition33_Steam.exe` launch target | `1903340` | `-w 1920 -h 1080 -W 2560 -H 1440 -r 180 -f` | Gamescope and Proton chain present; playability reported by developer; game executable process not separately shown by filtered output |
| 5 | Half-Life 2 | Steam Linux Runtime (Soldier/Scout) → **native `hl2.sh`** | `220` | `-w 1280 -h 720 -W 1920 -H 1080 -r 180 -f` | Gamescope + native launch-script path present; developer confirms native launch; separate game process not captured by the filter |

## Native Linux: Half-Life 2

The command explicitly used a native entry point, not Proton:

```text
gamescope -w 1280 -h 720 -W 1920 -H 1080 -r 180 -f -- [Steam launch wrapper] ... [Steam Linux Runtime] ... Half-Life 2/hl2.sh -steam -game hl2_complete
```

This verifies that RyuSCOPE's Gamescope configuration can accompany a Steam native Linux launch path. As always, the title's running/playable result was confirmed by the developer and may need independent reproduction.

## Proton: modern and older games

Example from Galactic Racer:

```text
gamescope -w 1920 -h 1080 -W 2560 -H 1440 -r 180 -f -- [Steam launch wrapper] ... Proton 11.0/proton waitforexitandrun ... Launcher.exe
```

Example from Expedition 33:

```text
gamescope -w 1920 -h 1080 -W 2560 -H 1440 -r 180 -f -- [Steam launch wrapper] ... Proton - Experimental/proton waitforexitandrun ... Expedition33_Steam.exe
```

**Privacy:** Real home-directory paths, Steam folders, and other identifying data have been replaced here with neutral placeholders. Do not upload original unredacted process dumps as bug reports.

## What this does NOT establish yet

1. Gamescope's `-w/-h` (game resolution) and `-W/-H` (output resolution) were passed correctly, **not** proof that the game rendered at the exact expected internal resolution throughout gameplay.
2. `-r 180` requests a **Gamescope frame-rate limit**; it does not by itself establish actual delivered 180 FPS or verify the monitor's refresh rate.
3. No `-F fsr` or `-F nis` was observed in these command lines. Filter use and image quality must be checked separately. Upscaling configuration is not proof of the selected algorithm.
4. On a physical 1080p display, `-W 2560 -H 1440` is a logical output test, not proof of native 1440p scan-out.
5. `--mangoapp` was not observed. In some Proton sessions Steam Overlay renderer preloads were present; **neither** Gamescope-native MangoHud integration nor Steam Overlay suppression is verified yet.
6. All evidence is from **one** AMD/CachyOS system. SteamOS, NVIDIA, Intel, additional AMD generations and varied desktop sessions still need testing.
7. GPU monitoring remains AMD-only in this checkpoint.

## Next reproducibility step

Once the real v0.5.2 source and installation instructions are packaged, ask a second tester (for example, Jesse on SteamOS Desktop Mode) to repeat a basic native or Proton launch and send the [safe compatibility report](TEST_REPORT.md). Do not report outside-platform support until demonstrated.
