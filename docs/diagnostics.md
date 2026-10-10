# Read-only diagnostics

Run these manually and review output before posting it. Do not publish full environment dumps, account information, license files or scene paths.

```bash
printf 'Session: %s\n' "${XDG_SESSION_TYPE:-unknown}"
uname -r
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
__GLX_VENDOR_LIBRARY_NAME=mesa glxinfo -B
```

On Debian/Ubuntu, package versions can be read with:

```bash
dpkg-query -W -f='${Package} ${Version}\n' libglx-mesa0 mesa-vulkan-drivers xwayland
```

In Maya's Python Script Editor:

```python
import maya.cmds as cmds
from PySide6 import QtCore
print('Maya:', cmds.about(version=True))
print('Qt:', QtCore.qVersion())
if cmds.pluginInfo('mtoa', query=True, loaded=True):
    print('MtoA:', cmds.pluginInfo('mtoa', query=True, version=True))
```

When reporting behavior, distinguish the speed of generating render samples from the speed of moving an already displayed image. Test camera navigation in Maya separately from pan/zoom in Arnold's canvas.
