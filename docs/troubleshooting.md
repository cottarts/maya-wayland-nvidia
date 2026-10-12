# Troubleshooting

## Mesa selects llvmpipe

Do not mistake software rendering for working Zink acceleration. Check `__GLX_VENDOR_LIBRARY_NAME=mesa glxinfo -B`. Confirm Vulkan support for the NVIDIA driver and your distribution's Mesa/Zink packages before using the launcher. This repository deliberately does not change system drivers.

Disabling Kopper with `LIBGL_KOPPER_DISABLE=true` fell back to llvmpipe on the tested machine. It was not retained as a fix.

## Maya is still black

Confirm that the launched process receives `QT_QPA_PLATFORM=xcb`, `__GLX_VENDOR_LIBRARY_NAME=mesa`, and `MAYA_VP2_DEVICE_OVERRIDE=VirtualDeviceGLCore`. Check for overrides in your existing `Maya.env` and desktop launcher. A clean Qt test window does not establish that Maya's viewport will work with the same vendor.

## Arnold keeps the original canvas

Run in Maya's Python Script Editor:

```python
import arnold_qt_canvas_auto
arnold_qt_canvas_auto.start()
```

Check the Script Editor for exceptions. MtoA must be loaded and Arnold RenderView must be open. The watcher does not load plugins. If your Maya uses a custom user scripts directory, install with `--scripts-dir` pointing to that directory.

## Border or incorrect crop

v0.1.0 uses a hidden fixed-size native container and full-resolution Qt pixmap. Press **F** in the Qt canvas to frame all pixels. Check that Arnold's **Test Resolution** is 100% and **3D Manipulation** is disabled. The tested layout uses device pixel ratio 1.

If upgrading from the earlier centered-crop or safety-zoom versions, restart Maya after replacing the runtime; an already attached canvas keeps its loaded Python implementation. Do not reparent Arnold's native OpenGL window or repeatedly resize it while IPR runs. The shipped adapter retains that window's original owner.

If the crop still differs, compare the selected render camera and resolution gate, inspect Script Editor errors, and report the configuration without scene or account data. See [capture limitations](limitations.md).

## IPR does not update

Start IPR with Arnold's original controls. Ensure its `Scene Updates` option is enabled. The Qt adapter requests display updates; it cannot force Arnold to produce frames while Maya or the rendering engine is blocked.

Copies pause only during interactions in the Qt canvas, for 80 ms after the last gesture. They should not pause while dragging the camera in Maya. A scene with high rendering cost can still update slowly.

## Disable the adapter

Close Maya and run the uninstaller. Restart to restore the original canvas. To temporarily stop automatic attachment inside Maya:

```python
import arnold_qt_canvas_auto
arnold_qt_canvas_auto.stop()
```

Stopping the watcher does not remove a canvas already attached. Restart Maya after uninstalling for a complete rollback.

## Redshift licensing is a separate issue

A separate Redshift issue on the original machine involved a modified local library and was investigated independently. The graphics workaround does not bypass, assign, release or alter any renderer license. No Redshift binaries, personal subscription identifiers, executable-stack overrides or local licensing fixes are distributed here.
