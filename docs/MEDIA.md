# Demo media and reproduction

The private README embeds `docs/media/atelier-you-demo.gif` directly. It is an animated preview, not a download-only link. Click it to open the private [v0.2.0 release](https://github.com/sthamann/atelier-you/releases/tag/v0.2.0).

The release includes:

- `atelier-you-demo-v2.mp4`: 20 seconds, 1920×1080, 30 fps, music.
- `atelier-you-projekt-v2.zip`: the source tree for this version, required video assets, fonts and font licenses. No credentials, runtime customer sessions or model weights.
- `SHA256SUMS.txt`: checksums for the two files.

Unzip the project package, enter `videos/atelier-you`, run `npm run check`, then `npm run render`. Node/npm and network access for the pinned HyperFrames package and GSAP are required. The repository alone contains the composition but intentionally omits large source media; the release package restores the media at the expected relative paths.

## Edit structure

- 0–3 s: product image to personal result; first reveal completes at 0.83 s.
- 3–7 s: actual Shopware product detail page, cached original/result toggle.
- 7–12 s: actual five-item outfit generation, wait shortened and labelled on screen.
- 12–16 s: generated front, side and rear views.
- 16–20 s: closing result.

The GIF condenses this sequence for fast inline playback. Model latency is documented separately in [VERIFICATION.md](VERIFICATION.md). Editing playback speed does not change generation latency.

Personal demo media are included by the user's explicit request in this private repository/release. Keep that in mind before changing repository visibility. Upstream model, audio and font terms are documented in [THIRD_PARTY.md](THIRD_PARTY.md).
