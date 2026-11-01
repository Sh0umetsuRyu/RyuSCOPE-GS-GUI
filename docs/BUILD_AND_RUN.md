# Build/run status for v0.5.2

**Status:** Documentation is prepared. Real local v0.5.2 application source has not been provided in this packaging environment. The files here are safe repository scaffolding, **not an executable application release**.

## What the project maintainer must add before release

1. Preserve the exact working v0.5.2 project tree, including Python entry point (`main.py` if it remains the entry point), integration modules, icon/assets and all relative files it imports.
2. Provide a verified `requirements.txt`, or clearly document the actual dependency source if Python packages are installed differently. **Do not use old v0.2's imports to claim v0.5.2 dependencies.**
3. Confirm the project's app launch from a clean shell on the developer machine with `bash scripts/run-local.sh` and record interpreter version.
4. Verify the `bash scripts/setup-python.sh` workflow in a fresh virtualenv on a comparable Linux system. Keep system-wide Gamescope/Steam installation under users' control.
5. Confirm the GUI steps for importing an installed game, generating Steam launch options, native Linux and Proton launch handling, and app shutdown. Replace any tentative wording in [INSTALL_AND_USE.md](INSTALL_AND_USE.md) with observed details.
6. Scan for local absolute paths, credentials, Steam account details, proprietary assets and user profiles. Run `bash scripts/preflight.sh` inside the git repo and manually inspect all staged files.
7. Publish actual source with test evidence; **only then** create a `v0.5.2` Git tag and optional downloadable package.

## Provided helpers

- `bash scripts/check-environment.sh`: read-only tool and version availability (all users).
- `bash scripts/setup-python.sh`: creates `.venv`, installs from `requirements.txt` **only when present**, and refuses to guess missing dependencies.
- `bash scripts/run-local.sh`: runs `main.py` using `.venv/bin/python` when available, or `python3` otherwise; fails with helpful message if source is missing.
- `bash scripts/preflight.sh`: Git candidate-file review (not a secret scanner).

No helper uses `sudo`, copies game content, changes Steam library settings, or writes Proton prefixes.
