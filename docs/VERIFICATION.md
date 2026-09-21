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

## English storefront and media (v0.3.0)

The README, custom storefront, all 17 product descriptions, upload/privacy controls, generation states and API error messages were translated into English. The Shopware sales channel, domain snippets and product translation context use `en-GB`. EUR prices use English decimal formatting. The catalog generator can update product copy without loading the image model when all product images already exist.

Fresh browser recordings replace both previous German captures. A new session uploaded the chosen photo through the English dialog and generated the five-item outfit, its additional views and the single-product result. The 20-second MP4, 12-second README GIF and labelled view overview were rendered again with English titles and captions.

English verification: all 17 live product detail pages returned their English catalog descriptions and `lang="en-GB"`, with no matches for the checked German UI strings. The fresh session completed 22 image jobs (17 product fronts, two extra overshirt views and three outfit views). At 390×844 the English Outfit Studio kept a 390 px document width and all five selectors. All 8 API/reference tests passed; the final English composition passed runtime, layout and contrast checks. The generated GIF decodes to 144 frames at 960×540 over 12 seconds.

## One upload across products (v0.4.0)

A fresh browser session uploaded the selected photo exactly once through the live English homepage. All 17 front-view jobs completed. The collection was captured before upload and after generation at the same viewport and scroll position. Four real product pages were then recorded: The Heavy Tee, The Studio Hoodie, The City Overshirt and The Soft Knit. Their completed front-view job IDs remained unchanged across the page visits; no second upload was performed. IDs and session cookies are kept out of the repository.

The 20-second cut prioritizes these four different garments, with four side-by-side looks visible within the first second, one upload, the collection before/after and four 2.5-second product-page sequences. The README GIF condenses it to 12 seconds. The omitted generation wait and previously generated results are labelled. Runtime, layout and contrast checks passed before rendering.
