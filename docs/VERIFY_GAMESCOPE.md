# Verifying Gamescope launches (read-only)

Use these checks *while a game is open*. They work from a second terminal and **do not** kill games or change Steam settings.

## Quick check (Bash or fish)

```sh
ps -e -o pid,ppid,comm,args --forest | grep -Ei 'gamescope|proton|wine|hl2|Expedition|SWGR|sdhdship' | grep -v grep
```

**Caution:** Full process trees contain local paths, game install locations and sometimes account identifiers. Remove usernames, home folders, Steam IDs and other personal data before posting on GitHub.

## Show the Gamescope command more clearly (fish shell)

```fish
pgrep -af 'gamescope -'
```

The important flags are:

- `-w`, `-h`: Gamescope's *requested game resolution*.
- `-W`, `-H`: Gamescope's *requested output resolution*.
- `-r`: Gamescope frame-rate **limit**; **not** proof of actual FPS or monitor refresh.
- `-f`: fullscreen.
- `-F fsr` / `-F nis`: explicitly select scaling filters when supported by installed Gamescope.

Example verified for the **native Linux Half-Life 2 launch**:

```text
gamescope -w 1280 -h 720 -W 1920 -H 1080 -r 180 -f -- ... hl2.sh -steam -game hl2_complete
```

Example verified for **Expedition 33 under Proton Experimental**:

```text
gamescope -w 1920 -h 1080 -W 2560 -H 1440 -r 180 -f -- ... proton waitforexitandrun ... Expedition33_Steam.exe
```

## Important distinction

A command line proves which options were requested, and the process tree shows the Linux/Steam/Proton launch path. It **does not** independently verify FSR filter quality, rendered FPS or 1440p physical scan-out on a 1080p monitor. See the [test results](COMPATIBILITY_RESULTS.md).

Documentation: [Gamescope official README](https://github.com/ValveSoftware/gamescope/blob/master/README.md).
