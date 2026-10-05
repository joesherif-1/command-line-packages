#!/bin/bash
# xxd 2026-06-16 (from Vim; free to use and distribute, see the header of xxd.c): hex dumps.
cd "$(dirname "$0")"
source ../common.sh
WORK="$CACHE/xxd"; mkdir -p "$WORK"; cd "$WORK"
fetch https://raw.githubusercontent.com/vim/vim/6d862f58dd6d51b292dd26ae658b02fb1e691ca5/src/xxd/xxd.c \
  f4f9812f9b83651e30040c83bd722651cc4656eb95b86a852edd1cd60e9b2fcd xxd.c
$CC -O2 -D_WASI_EMULATED_SIGNAL xxd.c -lwasi-emulated-signal -o "$OUT/xxd.wasm"
echo "$OUT/xxd.wasm"
