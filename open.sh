#!/usr/bin/env bash
# Abre un circuito en Logisim Evolution 5.0.0 con la ruta de Questa ya configurada.
# Uso: bash open.sh                  -> circuit/smips.circ
#      bash open.sh otro.circ        -> otro circuito
set -euo pipefail
dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
circ="$(realpath "${1:-$dir/circuit/smips.circ}")"
jar="${LOGISIM_JAR:-/snap/logisim-evolution-snapcraft/current/jar/logisim-evolution.jar}"
questa="${QUESTA_BIN:-$HOME/altera/25.1std/questa_fse/bin}"
java="java"
[ -x "$HOME/.local/jdk-21/bin/java" ] && java="$HOME/.local/jdk-21/bin/java"
exec "$java" --class-path "$jar" "$dir/tools/OpenCircuit.java" "$circ" "$questa"
