# 🕹️ RyuSCOPE GS v0.5.2: easy SteamOS test for Jesse

Hey Jesse! Thanks for helping with a real-world compatibility test. RyuSCOPE is a Linux GUI for configuring Gamescope around Steam games. Reshii has already demonstrated **native Linux** and **Proton** game launch paths on CachyOS. We want to find out whether the same app launches on **your SteamOS desktop**.

**Only start after Reshii publishes the REAL working v0.5.2 application and gives you its GitHub link.** The documentation starter is **not** runnable yet. No one needs to send you their Steam games, saves, or account information.

## Step 1: Use Desktop Mode

Switch SteamOS to **Desktop Mode**. We won't test Gaming Mode first, since it already uses a special Gamescope session. Keep Steam running and pick any game already installed in *your* library.

## Step 2: Download and check

- Open Reshii's RyuSCOPE GitHub repository, click **Code → Download ZIP**, and extract it somewhere you can find again.
- Open a terminal inside that extracted folder.
- Copy this command, then press Enter:

```sh
bash scripts/check-environment.sh
```

This just checks which programs are installed. It doesn't change settings. If it reports missing Gamescope/Python, stop and ask Reshii; don't change SteamOS's protected system partitions or run unfamiliar `sudo` commands.

## Step 3: Install Python requirements and open the app

Once the verified application source is present, run:

```sh
bash scripts/setup-python.sh
bash scripts/run-local.sh
```

If either script says `main.py` or `requirements.txt` is missing, send the message to Reshii: the package is incomplete. Don't install random libraries to work around missing files.

## Step 4: Try one game

1. Start with a game that already works normally through Steam.
2. Open RyuSCOPE; check whether it detects Gamescope.
3. Follow the app's actual Steam launch option flow. If it offers **Copy Launch Options**, keep a copy of the game's original Steam launch options so you can restore them afterwards.
4. Launch your game, look for graphics/input issues, play briefly, and exit normally.
5. If the game fails, stop, note the exact error, and try launching directly through Steam without RyuSCOPE to compare.

A second game is optional. Don't try to modify Proton prefixes, game saves, GPU overclocking or SteamOS system files.

## Step 5: Send back a tiny report

Copy [this report](TEST_REPORT.md) and fill in: OS/SteamOS version, Desktop Mode, GPU model, the game's name, whether RyuSCOPE opened, whether Gamescope launched, whether the game ran and exited, and any visible error. **Redact your account name, home folder paths, tokens, Steam IDs, and private files from screenshots/logs.**

**That's it!** One safe, successful SteamOS game launch is valuable evidence. It does not need to prove every game or every GPU works. 🐉
