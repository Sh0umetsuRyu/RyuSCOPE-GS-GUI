# RyuFG v1.1 local test report

Tested November 5, 2026 with AFMF-Linux 1.3.1 at
`e738127530ebf4a8b070b9fb38469377958120a7`. The x86-64 Linux host had
Gamescope 3.17.0 and a Vulkan loader but no `/dev/dri` device. Vulkan
present tests used Mesa lavapipe with llvmpipe. The Vulkan validation layer
was unavailable on this host.

| Check | Result |
| --- | --- |
| Upstream CMake/Ninja Release build | Passed with GCC, Vulkan headers 1.3.296, glslang and SPIR-V validation. The layer links against glibc and does not link the Vulkan loader. |
| Python integration smoke | Passed. Executed direct and Steam-generated commands with a stand-in compositor and Proton wrapper. Verified environment scope, arguments and paths with spaces, MangoApp plus FSR flags, off by default, conflict rejection, one-game Steam writes and restoration, and idempotent staging. |
| Packaged implicit layer, relocated path | Passed. With no explicit layer request, the package produced 119 generated companions from 120 software-rendered presents. Both sampled output frames passed upstream's moving-square position and optical-flow checks. |
| Packaged implicit layer, Steam-style XDG discovery | Passed on the host Vulkan loader, with no custom Vulkan layer path. The registered copy produced 119 companions from 120 presents, passed the same pixel checks, and requested five extra swapchain images. |
| Packaged implicit layer, negative controls | Passed. Setting only upstream's enable variable produced no AFMF activity without the RyuFG gate. Setting `DISABLE_AFMF=1` suppressed activation even with both gates set. |
| Upstream default headless checks | Gamescope process pass-through passed. The first quality and Gamescope-mode runs generated 105 and 106 companions respectively and missed required early frame dumps. The quality, performance and Gamescope-mode checks also failed with only the governor disabled. |
| Upstream controlled headless checks | Quality, performance, Gamescope mode and compositor pass-through all passed after disabling both the governor and minimum-FPS floor for the synthetic test. The app retains upstream's normal runtime defaults. |
| Portable app | Built the PyInstaller onedir bundle with both MIT notices and the layer. The bundle started under Qt offscreen after moving it to a path containing spaces. |
| Real game session | Unverified for hardware Vulkan, Steam Runtime and Proton, and Gamescope presentation with MangoApp and FSR. The stand-ins exercise launch wiring. The Vulkan probe exercises generated pixels in software. |

## Reproduce

```sh
bash scripts/build-ryufg.sh
python3 -m unittest discover -s tests -v
python3 -m tests.smoke_ryufg_vulkan build/afmf-linux
AFMF_GOVERNOR=0 AFMF_MIN_FPS=0 ctest --test-dir build/afmf-linux-build \
  -R '^headless(_gamescope|_gamescope_passive|_performance)?$' --output-on-failure
```

The packaged Vulkan smoke test requires `VK_EXT_headless_surface`. Set
`VK_DRIVER_FILES` to a suitable ICD manifest when the default ICD lacks it.
For separately installed headers, pass `--headers /path/to/include` to
the smoke test and `-DVulkan_INCLUDE_DIR=/path/to/include` to the build
script. The packaged probe writes logs under `build/ryufg-smoke-logs`.

The release test still requires an upstream-supported GPU and a real game
session for each intended launch route. Compare on and off in the same
scene, check generated and skipped presents and capture the resulting
output. Check Gamescope scaling and MangoApp in the same session.
