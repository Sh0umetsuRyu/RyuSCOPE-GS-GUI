# RyuSCOPE GS development roadmap

The milestones below are **planned implementation goals**, not claims that these features work today.

## v0.5.2: Working source checkpoint and early external testing

- Gamescope activation / game launch observed working on the developer's CachyOS system. One game confirmed tested at the time of this checkpoint.
- Current built-in GPU monitoring: **AMD-only**. NVIDIA/Intel monitoring not implemented or verified.
- Preserve the real working source unchanged before further implementation. A documentation starter alone is not a runnable application.
- After verified installation/run instructions are written, offer a sanitized v0.5.2 build/source package to an external tester such as Jesse (SteamOS desktop). Try Desktop Mode first. Treat Gaming Mode as a distinct integration challenge.

## v0.6: Complete Gamescope and Steam/Proton foundation

- Test two or three additional games and resolution paths; verify 720p → 1080p upscaling, not merely that Gamescope launches.
- Validate launch/exit, windowed/fullscreen settings and useful error messages.
- Detect users' own Steam libraries and game AppIDs; identify individual Proton prefix paths read-only and avoid mixing different games' data.

## v0.6.1: Gamescope MangoHud and optional Steam Overlay control

- Run the performance HUD **through Gamescope `--mangoapp`**, **not** through direct game-level MangoHud injection.
- `mangoapp` must exist on the tester's system as a separate installed dependency; Gamescope does not bundle the program. RyuSCOPE detects it, configures the launch and handles missing dependencies gracefully.
- Wire RyuSCOPE's clickable metrics/presets, position and size/font scaling controls to confirmed working mangoapp settings; confirm real game output.
- **If feasible**, add a reversible per-game Steam Overlay preference (`Follow Steam` / `Request disabled`), and test whether it truly suppresses the overlay without breaking Steam Input or game launches. Do not claim dynamic in-game toggling until that behavior is demonstrated.

## v0.6.2: LACT-powered GPU monitoring

- Add an **optional, read-only** LACT daemon adapter using its documented local socket/API and permission checks; no automatic installation or privilege changes.
- Graph real sampled data inside RyuSCOPE's own Qt UI; do not embed or duplicate LACT's GTK graph widgets.
- Continue to report v0.5.2 as **AMD-only** until the adapter is developed and verified on AMD, NVIDIA and Intel hardware separately.
- Support appropriate fallbacks for unavailable LACT/metrics. **No GPU tuning** (clocks/voltage/power/fans) is included in this milestone.

See [GPU_MONITORING.md](GPU_MONITORING.md).

## v0.6.3: Frame generation

- Evaluate a real frame-generation backend (afmf-linux is one candidate, **not** a preselected guaranteed dependency).
- Integrate backend detection, launch options, compatibility guards and graceful disabling if unsupported.
- Verify generated frames, pacing, responsiveness and interaction with Gamescope and mangoapp; don't advertise multipliers that the backend cannot actually deliver.

## v1.0: Public release

- Fix regressions and document which GPUs, distributions and games have actually been tested.
- Provide repeatable installation, clear missing-dependency prompts, accurate release notes and suitable package artifacts.
- Enlist more testers after early hardware results. Hardware support claims must be evidence-based.
