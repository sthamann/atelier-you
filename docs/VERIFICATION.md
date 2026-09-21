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
- The original/current result switch, animated generation state and delayed crossfade were exercised in the real browser. Two recordings used for the film preserve original playback speed.
- Mobile Outfit Studio tested at 390×844. Document width was 390 px, all five selectors were present. Navigation remains available and the small state label does not cover the face.

## Measured timings

These are single-session local measurements, not load tests. Model inference includes output encoding but excludes queue time, upload, browser polling and the 1.6-second crossfade.

| Image | Seconds |
|---|---:|
| Original six single-product front views | 7.246–7.605 |
| Overshirt side | 9.136 |
| Overshirt rear | 8.416 |
| Five-item outfit front | 12.856 |
| Five-item outfit side | 13.609 |
| Five-item outfit rear | 13.669 |

Five repeated requests for the completed outfit returned the identical job ID and kept the job count unchanged. Request round trips were 3.1–8.2 ms on the LAN; fetching its 41,464-byte output took 3.6 ms. These figures exclude browser decoding/rendering and say nothing about wider-network latency.

## Automated checks

`python -m pytest tests -q`: **4 passed**. The tests exercise invalid uploads, origin rejection, unauthenticated requests, session isolation, completed-image ownership, idempotent submissions, deletion, replacement, expiration, outfit slot conflicts, outfit permutation reuse and angle prerequisites. Two upstream test-client deprecation warnings remain.

The video composition passed HyperFrames checks with no runtime, layout or contrast errors. Seven structural lint warnings concern intentional single-file scene organization and reuse of the same result image in multiple scenes. Tight editorial line spacing was visually checked before marking its overlapping font boxes as intentional; actual glyphs remain separate.

## What this does not establish

No clothing-size estimation, physical fit accuracy, multi-view geometric ground truth, pixel-exact garment preservation, identity benchmark, production security audit or concurrent load benchmark is claimed. Feet/lower legs and unseen rear surfaces are generated from incomplete references. The synthetic catalog is a demo collection, not real inventory. A real commercial launch requires model rights and production deployment work.
