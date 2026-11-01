# Steam libraries and Proton-prefix discovery

**Design goal:** associate each user-owned Steam game with the right library, AppID and prefix, while keeping the tool read-only and keeping all game/user data outside Git.

## Common locations (not guaranteed)

- Steam library metadata commonly uses `steamapps/libraryfolders.vdf` associated with a Steam installation.
- Library game manifests are usually `<library>/steamapps/appmanifest_<AppID>.acf`.
- A typical Proton prefix uses `<library>/steamapps/compatdata/<AppID>/pfx/`.
- Steam can use multiple library roots, compatibility prefixes can be moved, absent, symlinked, or overridden; e.g., `STEAM_COMPAT_DATA_PATH` may select a different compatdata root for a specific launch.
- Linux desktop and SteamOS layouts vary. Do **not** hardcode the developer's home path.

## Proposed read-only algorithm

1. Discover configured Steam installations and parse their `libraryfolders.vdf` paths safely. Do not write to VDF files.
2. Discover `appmanifest_<AppID>.acf` files at each library root; parse AppID and install directory metadata.
3. Store a *logical* game record `{appid, library_root, manifest_path, install_dir, prefix_path_or_null}` without storing any private absolute path in shared defaults or reports.
4. For each game, check typical `steamapps/compatdata/<AppID>/pfx` locations and relevant explicitly configured overrides. Do not assume a prefix exists just because a game is installed.
5. Distinguish multiple installed copies and conflicting or duplicate AppIDs. Prefer Steam-provided associations, and surface ambiguity rather than guessing.
6. Treat an absent, unreadable or alternate prefix as a normal diagnostic status, **not** a reason to create, delete, merge, copy or repair a prefix.
7. Before logging/exporting, strip usernames, full local paths, Steam IDs, session tokens and save/config contents.

## Safety rules

- Read-only scan by default, no registry edits.
- Do not infer compatibility tools solely from prefix directory names.
- Do not redistribute Steam libraries, appmanifest files, installed games, prefixes, save data or proprietary assets.
- Use synthetic fixture data for future parser tests; never commit a user's real `libraryfolders.vdf`.
- Test default library, nondefault mounted drive, missing prefix, unreadable path, symlink, duplicates and case sensitivity.
