# Merge this documentation with your real v0.5.2 code

This ZIP is a GitHub publishing and research **starter**; it does **not** include the working v0.5.2 Python app. The older v0.2 code found elsewhere is deliberately excluded.

1. **Make a complete backup** of your local working `RyuSCOPE GS` directory before touching it.
2. Extract this ZIP and open its `RyuSCOPE-GS` folder.
3. Copy the documentation/support items (`README.md`, `docs/`, `scripts/`, `.github/`, `.gitignore`, `.gitattributes`, `CONTRIBUTING.md`, `LICENSING.md`, release notes) **into your actual source directory**. Do **not** replace or move `main.py`, `integrations.py`/integration modules, runtime assets or your settings before checking imports.
4. Review `.gitignore` before staging. If your app depends on a file it accidentally ignores, update the ignore rule first. Exclude personal Steam libraries, saved games, compatdata/pfx, private profiles and secrets.
5. Add a tested dependency manifest reflecting the exact imported code. Do not guess a package list solely from old v0.2 snippets.
6. Run all three scripts from that merged directory: `bash scripts/check-environment.sh`, `bash scripts/setup-python.sh`, `bash scripts/run-local.sh`.
7. Test at least one game. Keep the repo private until source, dependencies, instructions and licenses are reviewed, then follow [HOW_TO_PUBLISH.md](HOW_TO_PUBLISH.md).

**Important:** A GitHub repository created from this ZIP alone should be labelled **documentation/scaffold**, not `v0.5.2` executable release. Do not send that ZIP to Jesse as though it is an installer.
