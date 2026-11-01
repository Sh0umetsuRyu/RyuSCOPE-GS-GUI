# GPU monitoring: AMD-only baseline and v0.6.2 LACT integration plan

## Support statement for the v0.5.2 checkpoint

**Current RyuSCOPE GPU telemetry support is AMD-only.** NVIDIA and Intel monitoring have not been implemented or verified in the v0.5.2 checkpoint. The exact current AMD collection backend must be confirmed against the working local source before naming it as a required dependency. Do not confuse *monitoring* support with *game-launching* support. The starter archive does not include the app source.

## Planned v0.6.2 implementation: read-only LACT telemetry adapter

[LACT](https://github.com/ilya-zlobintsev/LACT) monitors AMD, NVIDIA and Intel GPUs and provides historical GPU data. It also has a documented local daemon JSON API, see [LACT API](https://github.com/ilya-zlobintsev/LACT/blob/master/docs/API.md). Unlike LACT's own charts, its API is suitable for a separate RyuSCOPE GUI to consume.

Proposed data flow:

```text
LACT daemon (optional, installed by user)
  -> local Unix socket /run/lactd.sock (JSON requests/responses)
    -> RyuSCOPE read-only telemetry adapter
      -> validated samples + bounded in-memory history
        -> RyuSCOPE Qt graph components
```

Implementation guidelines:

1. Check if `lactd` is available and whether the user can read the socket. Never request elevated access or change daemon configuration automatically.
2. Query available devices, then query supported metrics using the documented read-only API; discover exact command and response schemas from the installed LACT version.
3. Normalize supported metric names and units (GPU utilization, VRAM, clocks, temperatures, power, fan) with timestamps and explicit missing/unsupported values. Vendor, card and driver can change metric availability.
4. Sample at a measured, reasonable polling rate without blocking the Qt event loop. Keep a bounded ring buffer for graph history.
5. Draw RyuSCOPE graphs in Qt, preserving project appearance. LACT's GTK graph widgets do **not** embed directly into a Qt GUI.
6. Gracefully fall back to the existing AMD telemetry backend where available, or display `Monitoring unavailable` on unsupported hardware. No fabricated readings, synthetic history, or false cross-vendor support claims.
7. **No tuning commands:** no calls to set power caps, clocks, voltage, fans or profiles. Monitoring must stay read-only.
8. Test independently on AMD, NVIDIA and Intel before broadening the README support statement.

LACT also has an [OpenTelemetry exporter](https://github.com/ilya-zlobintsev/LACT/blob/master/docs/EXPORTER.md); it is useful for remote dashboards/metrics collectors but would generally add unnecessary setup to a simple local desktop graph. The local API is the first integration candidate.

## Compatibility notes

- Users do not need LACT to run Gamescope through RyuSCOPE unless a future specific feature explicitly requires LACT.
- LACT support varies by hardware, driver and software version.
- `AMD-only` accurately describes **the RyuSCOPE v0.5.2 monitoring feature**. It does **not** describe LACT's own GPU support.
- This document describes the v0.6.2 target, **not** a claim that LACT integration currently works.
