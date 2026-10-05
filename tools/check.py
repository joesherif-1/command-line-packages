#!/usr/bin/env python3
"""Checks index.json: every file downloads, matches its sha256 and size, and every program
(bin/...) is a WebAssembly module the app can run: it imports only WASI preview 1
(wasi_snapshot_preview1) and doesn't use wasm exception handling (the app's interpreter,
WAMR's fast interpreter, can't run it yet).

  tools/check.py                 check everything
  tools/check.py jq rg           check some packages
  tools/check.py --fill          also write missing sha256/size values into index.json
"""
import hashlib, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "index.json")
CACHE = os.path.join(os.path.expanduser("~/Library/Caches/command-line-packages"), "files")


def fetch(url):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, hashlib.sha256(url.encode()).hexdigest())
    if not os.path.exists(path):
        # curl rather than urllib: it uses the system's certificates everywhere.
        result = subprocess.run(["curl", "-fsSL", "-o", path + ".tmp", url], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"curl failed ({result.returncode})")
        os.rename(path + ".tmp", path)
    return open(path, "rb").read()


def leb(data, i):
    result = shift = 0
    while True:
        byte = data[i]; i += 1
        result |= (byte & 0x7F) << shift; shift += 7
        if byte < 0x80:
            return result, i


def wasm_problems(data):
    """Why the app couldn't run this module (empty when it can)."""
    if data[:4] != b"\0asm":
        return ["not a WebAssembly module"]
    problems, i = [], 8
    while i < len(data):
        section = data[i]; i += 1
        size, i = leb(data, i)
        end = i + size
        if section == 13:
            problems.append("uses wasm exception handling (tag section)")
        if section == 2:
            count, j = leb(data, i)
            for _ in range(count):
                n, j = leb(data, j); module = data[j:j + n].decode(); j += n
                n, j = leb(data, j); name = data[j:j + n].decode(); j += n
                kind = data[j]; j += 1
                if kind == 0: _, j = leb(data, j)
                elif kind == 1:
                    j += 1; flags, j = leb(data, j); _, j = leb(data, j)
                    if flags & 1: _, j = leb(data, j)
                elif kind == 2:
                    flags, j = leb(data, j); _, j = leb(data, j)
                    if flags & 1: _, j = leb(data, j)
                elif kind == 3: j += 2
                elif kind == 4: j += 1; _, j = leb(data, j)
                if module != "wasi_snapshot_preview1":
                    problems.append(f"imports {module}.{name}")
        i = end
    return problems


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    fill = "--fill" in sys.argv
    index = json.load(open(INDEX))
    failures = 0
    for name in sorted(index["packages"]):
        if args and name not in args:
            continue
        package = index["packages"][name]
        for key in ("version", "description", "license", "files"):
            if key not in package:
                print(f"FAIL {name}: missing {key}"); failures += 1
        for file in package["files"]:
            label = f"{name} {file['path']}"
            if ".." in file["path"].split("/") or file["path"].startswith("/"):
                print(f"FAIL {label}: path must stay inside /usr"); failures += 1; continue
            try:
                data = fetch(file["url"])
            except Exception as error:
                print(f"FAIL {label}: {error}"); failures += 1; continue
            digest = hashlib.sha256(data).hexdigest()
            if fill and not file.get("sha256"):
                file["sha256"], file["size"] = digest, len(data)
            if file.get("sha256") != digest:
                print(f"FAIL {label}: sha256 is {digest}"); failures += 1
            if file.get("size") not in (None, len(data)):
                print(f"FAIL {label}: size is {len(data)}"); failures += 1
            if file["path"].startswith("bin/"):
                for problem in wasm_problems(data):
                    print(f"FAIL {label}: {problem}"); failures += 1
    if fill:
        with open(INDEX, "w") as out:
            json.dump(index, out, indent=2, sort_keys=True)
            out.write("\n")
    total = len(args) or len(index["packages"])
    print(f"{total} packages checked, {failures} problems")
    sys.exit(1 if failures else 0)


main()
