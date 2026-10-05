#!/bin/bash
# jq 1.8.2 (MIT): command-line JSON processor. Built without Oniguruma (no regex functions:
# test/match/capture/sub/gsub/splits).
cd "$(dirname "$0")"
source ../common.sh
WORK="$CACHE/jq"; mkdir -p "$WORK"; cd "$WORK"
fetch https://github.com/jqlang/jq/releases/download/jq-1.8.2/jq-1.8.2.tar.gz \
  71b8d6e8f5fe81f6c6d0d110e3892251f6ce76ed095abd315e26e6e1193af3af jq.tar.gz
rm -rf jq-1.8.2 && tar xzf jq.tar.gz && cd jq-1.8.2
CC="$CC" AR="$AR" RANLIB="$RANLIB" \
  CFLAGS="-O2 -D_WASI_EMULATED_SIGNAL -D_WASI_EMULATED_PROCESS_CLOCKS" \
  LDFLAGS="-lwasi-emulated-signal -lwasi-emulated-process-clocks" \
  ./configure --host=wasm32-wasi --without-oniguruma --disable-docs --disable-shared --enable-static \
  --disable-maintainer-mode > configure.log
make src/builtin.inc > /dev/null
make -j"$(getconf _NPROCESSORS_ONLN)" jq > make.log
cp jq "$OUT/jq.wasm"
echo "$OUT/jq.wasm"
