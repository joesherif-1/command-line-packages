# command-line-packages

The package list for **Command Line**, a terminal for iPad. In the app:

```
pkg search            list what you can install
pkg install jq rg     download and install packages
jq '.name' data.json  installed commands run like any other command
pkg list / info / remove / update / upgrade
```

Every package is a **WebAssembly (WASI) program**. iPadOS doesn't let an app run native code it
downloads, so the app runs these in its built-in WebAssembly interpreter
([WAMR](https://github.com/bytecodealliance/wasm-micro-runtime)). Programs see the
user's files (`/` is the terminal's top folder, mounted folders are `/<name>`) and their
package's files at `/usr`, and nothing else.

## index.json

The app downloads [`index.json`](index.json) (at most once a day, or with `pkg update`) and also
ships a copy of it for when it's offline.

```json
{
  "version": 1,
  "packages": {
    "jq": {
      "version": "1.8.2",
      "description": "command-line JSON processor",
      "license": "MIT",
      "homepage": "https://jqlang.org",
      "source": "command-line-packages (recipes/jq)",
      "files": [
        { "path": "bin/jq", "url": "https://.../jq.wasm", "sha256": "833c...", "size": 1048176 }
      ]
    }
  }
}
```

- `files[].path` is where the file goes inside `/usr`. Each file in `bin/` is a command
  (`bin/jq` → `jq`); other files (for example `share/<name>/...`) are data the program reads at
  `/usr/share/...`. Paths can't leave `/usr`.
- `sha256` is required. The app checks every file before installing anything, so a changed
  download is refused.
- `version` is compared as text: when it changes, `pkg upgrade` installs the new files.

## Where the programs come from

- **Built here** (`recipes/<name>/build.sh`): compiled with
  [wasi-sdk 34](https://github.com/WebAssembly/wasi-sdk), which uses the same LLVM and C library as
  the app's own `cc`. Each recipe pins its source by SHA-256, and the builds are reproducible
  (the same recipe gives byte-identical files). They're published as this repository's release
  files (one release per `name-version`).
- **a-Shell**: most of the catalog points at the WebAssembly builds that
  [a-Shell](https://github.com/holzschu/a-shell) publishes in
  [a-Shell-commands](https://github.com/holzschu/a-Shell-commands). They're plain WASI programs, so
  they run unchanged. Each was checked to load and run in the app's interpreter, and each is
  pinned by SHA-256. The files are downloaded from a-Shell's own releases, not copied here. The
  `license` field is the license of the program each one was built from.

## Adding a package

1. Write `recipes/<name>/build.sh` (see `recipes/jq` and `recipes/xxd`; `recipes/common.sh`
   downloads wasi-sdk and has `fetch <url> <sha256> <file>`). Build for `wasm32-wasip1`.
2. Check what the app can't run yet:
   - **no wasm exception handling** (C++ exceptions, `setjmp`/`longjmp`);
   - **no threads and no sockets**;
   - **no `fork`/`exec`/`system`**;
   - **no raw terminal mode**: full-screen programs like editors don't work yet.

   Programs start in the shell's folder. Their output goes to the screen live; programs can't
   tell they're on a terminal yet (`isatty` is false).
3. Add the entry to `index.json` with an empty `"sha256": ""`, then run `tools/check.py --fill
   <name>`. It downloads each file, fills in `sha256` and `size`, and checks the program only
   imports `wasi_snapshot_preview1` and doesn't use exception handling.
4. Open a pull request with the recipe and the index entry. The release file is uploaded when
   it's merged.

`tools/check.py` with no arguments checks the whole index.
