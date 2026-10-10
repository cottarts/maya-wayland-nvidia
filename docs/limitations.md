# Known limitations

## Scope

This is an experimental display adapter validated on one machine. Maya runs with the Qt `xcb` backend under XWayland. There is no native Wayland port, replacement rendering engine, or per-window GLX vendor switch.

The exact underlying driver or Qt defect has not been established. Reading a clean framebuffer while the window showed trails suggested a presentation problem, but forcing XDamage notifications did not resolve it.

## Cropping

The adapter crops a centered rectangle using `defaultResolution.width` and `.height`, assuming the native Arnold image is centered at **1:1 scale**. This was verified for 1920 × 1080 on a canvas larger than the image.

Native zoom/pan, cropped regions, high-DPI scaling, render-size overrides and different snapshot dimensions may invalidate that assumption. If the requested dimensions exceed the framebuffer, the implementation keeps the full framebuffer. Large renders can therefore retain the native background or lose the expected framing. The adapter does not read raw Arnold beauty/AOV buffers directly.

## Rendering and responsiveness

The 50 ms timer is an update request interval, not a guaranteed 20 FPS. Capture includes a GPU-to-CPU readback and Qt pixmap upload on Maya's main thread. On the tested scene, a recent update took about 6 ms; performance is scene-, resolution- and hardware-dependent.

While panning/zooming in the Qt viewer, image copying pauses briefly to keep navigation responsive. Camera movement in Maya does not intentionally pause copying. Maya or Arnold can still defer scene updates if their own threads are busy.

## Arnold features

Image controls are implemented separately from the native canvas. Native image-click tools, pixel inspection, region picking, shape picking, AOV switching, snapshots, color-management edge cases and multiple RenderView instances have not all been verified. Toolbar commands that affect native image positioning can conflict with the crop assumption.

The adapter explicitly enables `Scene Updates`. Uninstalling the startup hook does not restore Arnold option values that Maya may have persisted; restore that preference manually if needed.

## Internal API and lifecycle

The runtime identifies `CRenderViewWindow`, `CRenderGLWidget` and `QWindowContainer`. These are internal class names and may change between releases. It invokes hidden-window painting, which is not an official MtoA integration API.

Only Python syntax and installer tests are covered by CI. The initial startup watcher was activated and verified in an existing session. Repeated restarts, destroy/recreate cycles, multi-monitor changes and different MtoA versions need more coverage. If automatic attachment fails, stop the watcher in Maya, close RenderView, and use the troubleshooting guide.

No changes to shared OpenGL libraries or proprietary application binaries are part of this repository.
