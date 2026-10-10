#!/usr/bin/env bash
set -euo pipefail
# Temporary environment for this launch only. Existing LD_LIBRARY_PATH and
# renderer-specific flags are inherited; nothing is written to Maya.env.
MAYA_BIN="${MAYA_BIN:-/usr/autodesk/maya2026/bin/maya}"
if [[ ! -x "$MAYA_BIN" ]]; then
  printf 'Maya executable not found: %s\nSet MAYA_BIN to your executable.\n' "$MAYA_BIN" >&2
  exit 1
fi
exec env QT_QPA_PLATFORM=xcb __GLX_VENDOR_LIBRARY_NAME=mesa \
  MAYA_VP2_DEVICE_OVERRIDE=VirtualDeviceGLCore "$MAYA_BIN" "$@"
