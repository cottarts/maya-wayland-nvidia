# Known limitations

## Scope

This is an experimental display adapter validated on one machine. Maya runs with the Qt `xcb` backend under XWayland. There is no native Wayland port, replacement rendering engine, or per-window GLX vendor switch.

The exact underlying driver or Qt defect has not been established. Reading a clean framebuffer while the window showed trails suggested a presentation problem, but forcing XDamage notifications did not resolve it.

## Cropping

The adapter fits the hidden native image and applies a safety zoom-out when the canvas size or `defaultResolution` changes. It detects the outer background along the horizontal and vertical center lines and caches a crop rectangle only when its aspect ratio matches the configured resolution. A 2500 × 1406 render larger than the native canvas was checked in Maya after this change.

This remains a framebuffer-copy adapter, not direct access to raw Arnold beauty/AOV pixels. Fitting and the safety zoom-out reduce preview pixel resolution; zooming the Qt canvas enlarges that preview rather than fetching additional render pixels. Saved renders still use Arnold's render settings.

Background detection is heuristic. Render content matching the border color along the scan lines, cropped regions, non-square pixels, high-DPI scaling, render-size overrides and snapshots of different dimensions need further validation. If a valid rectangle cannot be found, the full framebuffer is retained. Native positioning tools may invalidate the cached rectangle; resize RenderView to force it to be recalculated.

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
