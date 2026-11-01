# RyuSCOPE GS testing plan: v0.5.2 → v0.6

## Baseline now established

Five games have reported successful launches, with four process-tree captures spanning three distinct requested Gamescope resolution configurations. See [COMPATIBILITY_RESULTS.md](COMPATIBILITY_RESULTS.md). We do **not** need to re-label these as untested.

## Remaining tests

| Test | Requested game → output | Goal |
|---|---|---|
| Baseline | 1920×1080 → 1920×1080 | Compare without scaling |
| Low-resolution scale | 1280×720 → 1920×1080 | Verify *actual* scaling filter effect, not just arguments |
| Non-integer scale | 1600×900 → 1920×1080 | Verify correct aspect/visual quality |
| Virtual higher output | 1920×1080 → 2560×1440 | Verify logical Gamescope output; no native 1440p claim on 1080p monitor |
| Native Linux | Half-Life 2 (native) | Input, playable window, exit, chosen scaling mode |
| Steam/Proton | One or two known working Windows titles | Launch, input, exit and error handling |

Further work: FSR/NIS filter tests (`-F ...` when supported), stable full-screen/windowed operation, game-input behavior, multiple user-owned Steam library locations, per-game Proton prefix discovery (read-only), log redaction, and packaging reliability.

## External hardware

Jesse's SteamOS desktop is a potential first independent tester, exact GPU unconfirmed. First test in **Desktop Mode**. The actual runnable source/verified package must be supplied first. Use [the beginner test guide](JESSE_TEST_GUIDE.md) and [report template](TEST_REPORT.md).

## Result log

| Date | Commit | OS/session | GPU | Game | Native/Proton | Game → output | Gameplay? | Filter verified? | Notes |
|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | |
