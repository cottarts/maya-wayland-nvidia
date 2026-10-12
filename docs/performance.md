# Performance and image fidelity

Measured on October 12, 2026, on the configuration in the README. These are short samples from one scene, not a general benchmark or a native-NVIDIA versus Zink comparison.

## Fidelity

The buffer contained exactly **2500 × 1406** pixels. The hidden native surface was **2628 × 1534**; the outer padding was removed at 1:1. Native render settings, image colors, sampling and resolution were not reduced. Fitting the visible canvas does not discard the stored full-resolution pixmap.

Offscreen Qt tests verify exact crop equality, edge colors, alpha preservation, changed-pixel propagation, and cursor anchoring. The optimization reuses the previous crop only if the complete framebuffer is exactly identical. It does not use an approximate image hash or similarity threshold.

## Measurements

A fixed 50 ms request interval was used for both paths in two alternating eight-second samples. CPU values use the Linux convention where 100% means one logical CPU core, not the whole machine.

| Sample | Previous full-resolution path | Optimized path |
| --- | ---: | ---: |
| First | 19.6% | 17.8% |
| Second | 18.9% | 19.0% |

All samples retained 2500 × 1406 buffer dimensions. The result is modest and variable; it does not justify a large percentage speedup claim. GPU readback and native painting remain significant costs. The active 50 ms and stable-image 250 ms request intervals are unchanged by this optimization pass.

## What changed

- Identical full framebuffers reuse their already cropped preview, avoiding another render-sized memory copy.
- Identical pixmaps are not uploaded again.
- The graphics scene extent is updated only when image dimensions change.
- No disk-export preview path, native-window reparenting, or repeated resize loop is used.

The adapter still performs GPU-to-CPU readback on Maya's UI thread. Higher resolutions cost more memory and transfer time. No claim is made that total Maya consumption equals or improves on native Maya. Tests did not quantify energy use or rendering throughput.
