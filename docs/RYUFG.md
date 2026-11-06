# RyuFG in RyuSCOPE GS v1.1

RyuFG is the frame-generation provider in RyuSCOPE’s launch pipeline. It uses
AFMF-Linux v1.3.1, pinned to
[`e738127530ebf4a8b070b9fb38469377958120a7`](https://github.com/serialexperimentslainnnn/afmf-linux/tree/e738127530ebf4a8b070b9fb38469377958120a7).
The AFMF layer and the AMD FidelityFX shader code both carry MIT terms. The
bundle includes both license texts and upstream provenance. The upstream C
code and shaders are built unmodified. RyuFG adapts the Vulkan manifest to
use a relative library path and a RyuSCOPE-specific activation gate.
[AFMF license](https://github.com/serialexperimentslainnnn/afmf-linux/blob/e738127530ebf4a8b070b9fb38469377958120a7/LICENSE) ·
[FidelityFX license](https://github.com/serialexperimentslainnnn/afmf-linux/blob/e738127530ebf4a8b070b9fb38469377958120a7/shaders/fidelityfx/LICENSE.txt)

## Build and use

- Build dependencies are x86-64 Linux, Git, Python 3, CMake 3.28+, Ninja, a
  C11 compiler, Vulkan headers 1.3.250+ and loader development files, and
  glslang. Install SPIRV-Tools to validate the compiled shaders. The shared
  library produced on this host requires glibc 2.34 or newer. The portable
  app has separate Python, Qt and system library compatibility requirements.
- Run `bash scripts/build-ryufg.sh` for the source checkout. An existing clean
  checkout at the pinned revision can be supplied via `AFMF_SOURCE_DIR`.
  Run `bash scripts/build-linux.sh` with the app's PyInstaller environment
  to build the portable app, which includes the payload at
  `plugins/ryufg` beside its executable. Keep the onedir bundle together when
  moving it.
- In **Performance**, enable **RyuFG (AFMF-Linux)** for the launch profile.
  The setting defaults off, including in profiles saved before v1.1.
  For Steam, select the game and apply its profile, or use **Copy Steam
  launch options** and paste into that game's properties. To turn it off for
  a Steam game, apply or paste options with the checkbox cleared, or restore
  that game's original options.
- The target is 64-bit Vulkan, including Direct3D translated by DXVK or
  vkd3d-proton. Use native Steam and an upstream-tested GPU/driver where
  possible. Standalone native Ryujinx can also use the layer. OpenGL, WineD3D,
  32-bit Vulkan and Flatpak delivery are outside this integration's scope.
  [Upstream installation and usage](https://afmf-linux.digitalexperiments.dev/install/)
- Disable any in-game frame generation or injector before opting in. RyuFG
  checks for known conflicting layer manifests, launch options, environment
  settings and recognizable injector filenames at the game directory root.
  It cannot inspect in-game settings, renamed injectors or overrides added
  after Steam options are saved. Gamescope FSR is a spatial upscaler and its
  flags coexist with RyuFG.

## Layer discovery and diagnostics

Direct launches add the plugin directory to the game's
`VK_ADD_IMPLICIT_LAYER_PATH`. Steam Apply and Copy stage a private copy under
`${XDG_DATA_HOME:-$HOME/.local/share}/ryuscope/ryufg` and register its gated
manifest at `vulkan/implicit_layer.d/ryuscope-ryufg.json` under the same data
home. This uses Steam Runtime's host-layer discovery and keeps saved Steam
options independent of the portable app's location. Use the same account
and XDG data home for Steam and RyuSCOPE. The manifest is staged once and
remains dormant without the per-game gate. Close games and Steam before
removing that manifest and its corresponding private payload if you want
to unregister it or replace an older staged RyuFG build.
[Valve Steam Runtime layer discovery](https://github.com/ValveSoftware/steam-runtime/issues/808)

The compositor receives `DISABLE_AFMF=1`. RyuFG removes that value only in
the enabled game command and supplies `AFMF_ENABLE=1`, its private
`RYUSCOPE_RYUFG=1` gate and, when nested, upstream's `AFMF_GAMESCOPE=1`.
The last option allows extra swapchain images under Gamescope.
[Upstream configuration](https://afmf-linux.digitalexperiments.dev/configuration/)

Performance shows package readiness or the detected conflict. To diagnose
runtime behavior, start RyuSCOPE from a terminal with `AFMF_LOG=3`, or add
`AFMF_LOG=3` before the generated Steam launch options and capture Steam's
output. Look for the game's swapchain decision and generated/skipped counts
at teardown. Compare with RyuFG off in the same scene. A layer listing or
“layer active” line only verifies discovery or activation. Use generated
present counts and an on/off visual or capture comparison to verify actual
in-game frame generation.

See [the RyuFG test report](RYUFG_TEST_REPORT.md) for this build's coverage.
