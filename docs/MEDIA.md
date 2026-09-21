# One photo, every look — demo media

The private README directly embeds `docs/media/atelier-you-demo.gif`. The 12-second preview focuses on a single upload personalizing different products. Click it for the private [v0.4.0 release](https://github.com/sthamann/atelier-you/releases/tag/v0.4.0).

The release contains:

- `atelier-you-one-photo-every-look.mp4`: 20 seconds, 1920×1080, 30 fps, music, English.
- `atelier-you-wardrobe-project.zip`: the versioned source and required images, recordings, music, fonts and licenses.
- `atelier-you-four-looks.png`: the customer wearing a T-shirt, hoodie, jacket and sweater.
- `atelier-you-personal-catalog.png`: the actual personalized collection after one upload.
- `SHA256SUMS.txt`: release checksums.

Unzip the project archive, enter `videos/atelier-you`, run `npm run check`, then `npm run render`. Node/npm and network access for the pinned HyperFrames package and GSAP are required. The repository contains the composition and inline media; the release archive restores all required larger assets at their relative paths. Credentials, runtime sessions and model weights are excluded.

## Sequence

| Time | Content |
|---|---|
| 0–2 s | Four products become four personal looks, all revealed by 0.64 s. |
| 2–4 s | Real upload of the chosen photo, once. |
| 4–7 s | Real collection before and after generation in that session. |
| 7–9.5 s | T-shirt: The Heavy Tee. |
| 9.5–12 s | Hoodie: The Studio Hoodie. |
| 12–14.5 s | Jacket: The City Overshirt. |
| 14.5–17 s | Sweater: The Soft Knit. |
| 17–20 s | Four looks together: Upload once. See yourself everywhere. |

All four product pages use the same session and completed results. The catalog before/after transition is an editorial cut across omitted generation time, not an unchanged real-time capture. Captions disclose this. There is no repeated photo upload between products. Single-product latency is documented in [VERIFICATION.md](VERIFICATION.md).

Personal media are included at the user's explicit request in a private repository/release. Applicable model, audio and font terms are in [THIRD_PARTY.md](THIRD_PARTY.md).
