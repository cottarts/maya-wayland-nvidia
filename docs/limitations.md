# Known limitations

## Scope

This is an experimental display adapter validated on one machine. Maya runs with the Qt `xcb` backend under XWayland. There is no native Wayland port, replacement rendering engine, or per-window GLX vendor switch.

The exact underlying driver or Qt defect has not been established. Reading a clean framebuffer while the window showed trails suggested a presentation problem, but forcing XDamage notifications did not resolve it.

## Full-resolution capture

The original hidden `QWindowContainer` remains attached to Arnold. It is removed from the visible splitter layout by hiding it; only the Qt image view moves into that layout. The hidden container stays fixed at `defaultResolution` plus 128 pixels. Its native image is initialized at 1:1, and the 64-pixel outer padding is cropped. No safety zoom-out or preview downsampling is applied.

This is still a native-framebuffer copy, not a direct Arnold output-driver API. The implementation was verified at 2500 × 1406 with device pixel ratio 1 and 100% test resolution. Non-square pixels, high-DPI scaling, test-resolution overrides, snapshots of other sizes, native region/zoom tools and multiple RenderView instances need further validation. Keep Arnold's 3D Manipulation disabled: its native Frame All action can move the camera in that mode.

The adapter expects a QSplitter-based Arnold layout. Internal widget hierarchy changes may prevent attachment. Very large render dimensions increase GPU surface memory and readback cost; this release does not claim a tested 4K/8K ceiling or zero overhead.

## Rendering and responsiveness

The 50 ms timer is an update request interval, not a guaranteed 20 FPS. Capture includes a GPU-to-CPU readback and Qt pixmap upload on Maya's main thread. Performance is scene-, resolution- and hardware-dependent. See [measured results](performance.md). A 50 ms request interval is not guaranteed 20 FPS.

While panning/zooming in the Qt viewer, image copying pauses briefly to keep navigation responsive. Camera movement in Maya does not intentionally pause copying. Maya or Arnold can still defer scene updates if their own threads are busy.

## Arnold features

Image controls are implemented separately from the native canvas. Mesh picking by left click and press-held native highlighting were verified. Pixel inspection, region picking, AOV switching, snapshots, color-management edge cases and multiple RenderView instances have not all been verified. Toolbar commands that affect native image positioning can invalidate the 1:1 positioning assumption.

The adapter explicitly enables `Scene Updates`. Uninstalling the startup hook does not restore Arnold option values that Maya may have persisted; restore that preference manually if needed.

## Internal API and lifecycle

The runtime identifies `CRenderViewWindow`, `CRenderGLWidget` and `QWindowContainer`. These are internal class names and may change between releases. It invokes hidden-window painting, which is not an official MtoA integration API.

Python syntax, installer tests and offscreen Qt checks are covered by CI. These do not replace live Maya graphics validation. The initial startup watcher was activated and verified in an existing session. Repeated restarts, destroy/recreate cycles, multi-monitor changes and different MtoA versions need more coverage. If automatic attachment fails, stop the watcher in Maya, close RenderView, and use the troubleshooting guide.

No changes to shared OpenGL libraries or proprietary application binaries are part of this repository.
