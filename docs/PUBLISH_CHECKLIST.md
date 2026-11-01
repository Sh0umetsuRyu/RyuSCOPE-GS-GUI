# Before publishing v0.5.2

- [ ] **Copy actual local working v0.5.2 source** (`main.py`, integration modules, assets) into this repository tree. Do not substitute the older v0.2 library source.
- [ ] Preserve a complete separate backup of the known-working project first.
- [ ] Confirm the source imports, launch entry point and Python dependencies; include a verified `requirements.txt` or equivalent manifest.
- [ ] Run `bash scripts/check-environment.sh` and `bash scripts/setup-python.sh` and `bash scripts/run-local.sh` on the intended system.
- [ ] Run one native Linux and one Proton game end-to-end from the packaged source.
- [ ] Inspect `git status --short`, `git diff --cached`, and `bash scripts/preflight.sh` plus manually review files for paths, credentials, personal profiles or game data. `gitignore` alone is not a security audit.
- [ ] Choose a source license or clearly document restrictions before public release.
- [ ] Set GitHub repo visibility intentionally; source repository and downloadable app are different deliverables.
- [ ] Only after all the above, tag the complete working snapshot `v0.5.2`.
- [ ] Send Jesse the **complete runnable package**, not this documentation scaffold; no SteamOS system-level changes required for first trial.
- [ ] Track driver/GPU environment in every test report; do not claim NVIDIA/Intel support until validated.
