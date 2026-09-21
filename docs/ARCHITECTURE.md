# ATELIER / YOU

A real Shopware 6.6.10.6 Storefront with a Twig plugin and 17 actual DAL product records. The API's catalog is a deployment snapshot of those same seeded product IDs, not a replacement commerce database. Product detail navigation uses Shopware's SEO URLs and product page loader.

The browser uploads one image to the same-origin `/tryon/session` endpoint. The service stores a normalized image with EXIF removed under a random session, sets an HttpOnly SameSite=Strict cookie, and creates idempotent SQLite jobs. A single resident QwenImage21Pipeline executes on the NVIDIA GPU selected through `CUDA_VISIBLE_DEVICES`. Configure the model and data paths with `MODEL_PATH` and `DATA_DIR`, and set `PUBLIC_ORIGIN` to your storefront origin. The browser never needs the GPU server’s address. Visible products and requested angles take priority over background front-view prefetch.

Every result is authorized against the session before delivery; images are not in Shopware's public media system. Upload replacement and deletion remove the entire session's originals, jobs and results. Expired sessions cannot retrieve results after 24 hours, and a cleanup thread removes files on a 30-second cadence. Restart requeues interrupted jobs; completed sessions remain usable until expiry.

Front views use customer photo + garment reference. Side/rear use only the completed front view as their image reference to improve consistency and avoid duplicate people. These are inferred views; invisible garment details and body geometry are not measurements or evidence of physical fit. Front views for the 17 catalog items prefetch globally. Side/rear views prefetch for the currently opened product after its front view is ready.

Outfit Studio accepts up to five products, one each in top, outerwear, trousers, shoes and headwear. The sorted product IDs form a stable outfit key, but the outfit definition and results remain session scoped. Qwen receives all selected references together. Side/rear shots use only that outfit's completed front view as their image reference. Reordering the same selection reuses the existing job. Empty selections and conflicting garment slots are rejected.

The transition keeps the product image visible during the actual job and animates a light sweep. The new image is decoded before a sequential reveal: the old image fades out over 180 ms, then the new image fades in over 550 ms. No synthetic progress percentage or fake ready state is used. Reduced-motion settings suppress the effects.

The prototype has no ordering UI. Hardening before public operation: HTTPS and Secure cookies, authenticated/rate-limited admission, CSRF/origin policy for the deployed hostname, per-user quotas, production Shopware deployment, monitored storage retention, product-reference review, and commercial model authorization. Do not expose Dockware development containers publicly.
