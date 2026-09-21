# Verified on 2026-09-21

## Running system

- Dedicated Shopware 6.6.10.6 container on `192.168.1.120:8090`, with 17 seeded products, media and real product detail routes.
- FastAPI health reports ready with Qwen-Image-2.1 revision `b3179ad355be050328e483a9dfdd9e60cd62adfa`.
- NVIDIA process query matched the running systemd service PID to RTX PRO 6000 UUID `GPU-c5489862-1768-0719-a514-b0f5ad58d976`. Resident allocation was approximately 31.7 GB. Other GPUs were not used by this service.
- Restarted the service and confirmed readiness and retained session results afterwards.

## Functional evidence

- User-provided photo uploaded through the actual Storefront.
- All 17 individual product front views completed for the same private session.
- A five-product outfit completed with Heavy Tee, City Overshirt, Relaxed Chino, Court Sneaker and Everyday Cap.
- Its front, side and rear views were visually reviewed. The intended viewpoints and selected product categories were present.
- The original/current result switch, animated generation state and delayed crossfade were exercised in the real browser. The revised 20-second film includes a cached product/result switch at normal speed and an explicitly labelled accelerated outfit-generation capture.
- Mobile Outfit Studio tested at 390×844. Document width was 390 px, all five selectors were present. Navigation remains available and the small state label does not cover the face.

## Measured timings

These are single-session local measurements, not load tests. Model inference includes output encoding but excludes queue time, upload, browser polling and the approximately 0.78-second sequential image transition.

| Image | Seconds |
|---|---:|
| V3 Overshirt front | 8.437 |
| V3 five-item outfit front | 14.209 |
| V3 five-item outfit side | 6.118 |
| V3 five-item outfit rear | 6.152 |

These revised measurements use `atelier-v3-face-anchor-single-view-768x1024-28steps`. The earlier v1 six-product timings were 7.246–7.605 seconds; the v1 outfit was 12.856–13.669 seconds. They are historical comparisons, not a controlled speed benchmark.

In the initial v1 validation, five repeated requests for the completed outfit returned the identical job ID and kept the job count unchanged. Request round trips were 3.1–8.2 ms on the LAN; fetching its 41,464-byte output took 3.6 ms. These figures exclude browser decoding/rendering and say nothing about wider-network latency.

## Automated checks

`python -m pytest tests -q`: **8 passed**. The tests exercise invalid uploads, origin rejection, unauthenticated requests, session isolation, completed-image ownership, idempotent submissions, deletion, replacement, expiration, outfit slot conflicts, outfit permutation reuse and angle prerequisites, generation-version cache invalidation, absent/ambiguous face detections and reference-crop bounds. Two upstream test-client deprecation warnings remain.

The video composition passed HyperFrames checks with no runtime, layout or contrast errors. Seven structural lint warnings concern intentional single-file scene organization and reuse of the same result image in multiple scenes. Tight editorial line spacing was visually checked before marking its overlapping font boxes as intentional; actual glyphs remain separate.

## What this does not establish

No clothing-size estimation, physical fit accuracy, multi-view geometric ground truth, pixel-exact garment preservation, identity benchmark, production security audit or concurrent load benchmark is claimed. Feet/lower legs and unseen rear surfaces are generated from incomplete references. The synthetic catalog is a demo collection, not real inventory. A real commercial launch requires model rights and production deployment work.

## Identity revision

Visual review confirmed face drift in the first outfit output. Three controlled reference/prompt probes were compared with the supplied photo. Making a face crop the first reference and moving identity instructions to the start produced a closer likeness in the reviewed example. The deployed v2 pipeline derives that reference with a local face detector and skips ambiguous detections. No face recognition or biometric identity score is used. The initial v2 multi-reference angle outputs failed visual review: duplicate people and missing outerwear. The v3 angle path therefore rotates only the completed front image. Both regenerated views were visually checked: one person, the requested angle, and the jacket, trousers, shoes and cap retained. This is a qualitative adjustment, not proof of identity preservation.

The frontend now fades the old image out before revealing the new one, avoiding the additional morph-like effect of overlapping different face positions. A browser sampling check recorded 92 frames and zero frames with both layers above 3% opacity. After completion the base image was fully opaque and the incoming layer hidden. The reset explicitly disables the CSS waiting-state transition; otherwise it caused an unintended additional 8-second fade. Cache keys include the generation recipe so old results do not mask a changed pipeline.

## Media delivery

The main film is 20 seconds (1920×1080, 30 fps), with the first product-to-person reveal completed at 0.83 seconds. The private README embeds a short animated GIF. The MP4 and an editable project archive with the required media are release assets. Credentials, active sessions and model weights are excluded.
