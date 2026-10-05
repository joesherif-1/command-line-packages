# Shared by the recipes: wasi-sdk 34 (the same toolchain and C library as the app's own clang),
# downloaded once into ~/Library/Caches/command-line-packages. Sourced, not run.
set -euo pipefail
WASI_SDK_VERSION=34.0
CACHE="${CACHE:-$HOME/Library/Caches/command-line-packages}"
case "$(uname -s)-$(uname -m)" in
  Darwin-arm64) SDK_NAME="wasi-sdk-$WASI_SDK_VERSION-arm64-macos" ;;
  Darwin-x86_64) SDK_NAME="wasi-sdk-$WASI_SDK_VERSION-x86_64-macos" ;;
  Linux-x86_64) SDK_NAME="wasi-sdk-$WASI_SDK_VERSION-x86_64-linux" ;;
  Linux-aarch64) SDK_NAME="wasi-sdk-$WASI_SDK_VERSION-arm64-linux" ;;
  *) echo "unsupported build machine" >&2; exit 1 ;;
esac
WASI_SDK="$CACHE/$SDK_NAME"
if [ ! -x "$WASI_SDK/bin/clang" ]; then
  mkdir -p "$CACHE"
  curl -sSL "https://github.com/WebAssembly/wasi-sdk/releases/download/wasi-sdk-${WASI_SDK_VERSION%%.*}/$SDK_NAME.tar.gz" | tar xz -C "$CACHE"
fi
CC="$WASI_SDK/bin/clang --target=wasm32-wasip1"
AR="$WASI_SDK/bin/llvm-ar"
RANLIB="$WASI_SDK/bin/llvm-ranlib"
OUT="${OUT:-$PWD/out}"
mkdir -p "$OUT"

# fetch <url> <sha256> <file>: downloads a source and checks it.
fetch() {
  curl -sSL "$1" -o "$3"
  echo "$2  $3" | shasum -a 256 -c - > /dev/null || { echo "checksum mismatch: $1" >&2; exit 1; }
}
