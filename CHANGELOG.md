# Changelog

## v0.1.0 — 2026-10-12

First packaged experimental release.

- Keep full render resolution when the image exceeds the visible window; validated at 2500 × 1406.
- Retain Arnold's original hidden native container at fixed dimensions, with the visible Qt canvas managed separately by the splitter.
- Preserve wheel-zoom cursor anchoring after other navigation gestures.
- Forward mesh picking and press-held native highlighting.
- Back off copies of stable images; keep the existing active refresh cadence.
- Avoid padding-copy and pixmap work for exactly identical frames, and avoid redundant scene-extent updates.
- Add optional offscreen Qt fidelity and cursor-zoom checks plus performance notes.

Image resolution, render sampling and colors are not reduced. Graphics compatibility is currently validated on one configuration; consult the limitations before installing.
