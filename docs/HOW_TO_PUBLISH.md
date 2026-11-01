# Publish a **real** RyuSCOPE GS v0.5.2 GitHub repository

**Goal:** upload *the real current working v0.5.2 source* along with these docs. Do not publish an older source snapshot or declare this documentation-only ZIP runnable.

See the [source merge checklist](MERGE_INTO_WORKING_SOURCE.md) and [publication checklist](PUBLISH_CHECKLIST.md) before final release.

## 1. Back up your known-working application

Copy your entire current RyuSCOPE GS project directory to a safe location outside the future repository. Keep its layout unchanged. Confirm you can still run the original application.

## 2. Merge this documentation starter into the application folder

Copy `README.md`, `docs/`, `scripts/`, `.gitignore`, `.gitattributes`, `.github/` etc into the *same folder* as the real source. Preserve the relative paths of `main.py`, its integration modules and assets. Do **not** replace the known-working source with the earlier v0.2 snapshot.

Review the README, release notes and `docs/INSTALL_AND_USE.md` before release to ensure all "source pending" wording is updated **after** the source/requirements actually exist and have been tested.

## 3. Verify the install/use workflow

In a new terminal from the actual project directory:

```sh
bash scripts/check-environment.sh
bash scripts/setup-python.sh
bash scripts/run-local.sh
```

The dependency setup requires `requirements.txt` matching the real v0.5.2 source, which must be added by the maintainer. Confirm that the app opens and launches at least one game. For SteamOS testers, do **not** assume CachyOS packages/commands are appropriate.

## 4. Check private data before commit

```sh
git init
git branch -M main
bash scripts/preflight.sh
git status --short --untracked-files=all
```

Review all candidate files and source for hard-coded local paths, account credentials, keys, tokens, Steam IDs, game files, logs, saves and prefix folders. `.gitignore` is not a security scanner. Fix/omit anything personal *before* staging.

## 5. Create GitHub repository

Go to https://github.com/new and create an empty repository named `RyuSCOPE-GS` under your account. Keep it **Private** until you verify contents. Do not check "Initialize README/license/.gitignore" since these files are local already.

## 6. First commit and push

```sh
git add -A
git diff --cached --stat
git diff --cached --check
git commit -m "RyuSCOPE GS v0.5.2: native Linux and Proton launch checkpoint"
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/RyuSCOPE-GS.git
git push -u origin main
```

Replace the username with your actual account. If a remote already exists, inspect `git remote -v` rather than adding another. GitHub password is not used for Git HTTP pushes; use supported Git credential authentication.

## 7. Tag the real application source snapshot

After the complete v0.5.2 source and tested run instructions are pushed:

```sh
git tag -a v0.5.2 -m "Native Linux and Proton Gamescope launch checkpoint"
git push origin v0.5.2
```

Optional: create a GitHub **pre-release** tied to the tag. List verified games and current AMD-only GPU monitoring, plus honest scaling/SteamOS caveats. Do not attach a fictional binary or a docs-only archive advertised as an installer.

## 8. External testing

Send Jesse **the actual verified package/repository link**, [the beginner instructions](JESSE_TEST_GUIDE.md) and [the test form](TEST_REPORT.md). Keep private config, game assets, and Proton prefixes off GitHub.
