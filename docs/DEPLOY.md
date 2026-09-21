# Deployment

The installed evaluation uses `/home/aime/atelier-tryon` on `192.168.1.120`. Commands below describe a fresh, dedicated installation. Do not apply them to an existing merchant's shop. The supplied systemd unit explicitly selects the RTX PRO 6000 UUID; change that UUID and hostname for another machine.

## Python service and model

Python 3.12, an NVIDIA driver supporting CUDA 13, and approximately 40 GB free disk for weights plus environment are required. The tested GPU has 96 GB VRAM. Only one worker should own the model.

```sh
mkdir -p /home/aime/atelier-tryon
cd /home/aime/atelier-tryon
git clone git@github.com:sthamann/atelier-you.git repo
python3 -m venv .venv
.venv/bin/pip install torch==2.14.0 torchvision==0.29.0 --index-url https://download.pytorch.org/whl/cu130
.venv/bin/pip install -r repo/api/requirements.txt
.venv/bin/hf download Qwen/Qwen-Image-2.1 --revision b3179ad355be050328e483a9dfdd9e60cd62adfa --local-dir model
mkdir -p data/products
```

Review the model's license before downloading or using it. Generate the synthetic demo catalog before starting the resident API; both use the same GPU.

```sh
cd /home/aime/atelier-tryon/repo
CUDA_VISIBLE_DEVICES=GPU-c5489862-1768-0719-a514-b0f5ad58d976 \
MODEL_PATH=/home/aime/atelier-tryon/model DATA_DIR=/home/aime/atelier-tryon/data \
../.venv/bin/python scripts/generate_products.py
mkdir -p ~/.config/systemd/user
cp scripts/atelier-api.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now atelier-api
```

If an SSH shell cannot find the user bus, prefix systemctl with `XDG_RUNTIME_DIR=/run/user/$(id -u)`. Enable lingering for the service account if it must survive logout. The live machine has lingering enabled.

## Dedicated Shopware shop

Create a separate Dockware development container, bind to the LAN address only, and use persistent volumes on a fresh installation:

```sh
docker run -d --name atelier-shopware --restart unless-stopped \
  -p 192.168.1.120:8090:80 \
  -v atelier-shopware-html:/var/www/html \
  -v atelier-shopware-db:/var/lib/mysql \
  dockware/dev:6.6.10.6
```

Wait for Shopware to finish initializing. Store a random admin username/password as `admin.json` outside this repository, with mode 0600 and fields `username` and `password`. Never commit it. Disable or randomize Dockware's default admin password before providing access. The deployed demo has a random custom administrator and the default password was replaced.

`scripts/install_remote.py` is a **first-install** helper for this exact dedicated container. It creates the admin, copies and activates the plugin, installs assets and enables Apache's same-origin API proxy. It is not a general-purpose production deployer and user creation is not repeatable. The admin credential is supplied to the local container CLI as an argument during bootstrap; run in a trusted administrative environment.

```sh
cd /home/aime/atelier-tryon/repo
../.venv/bin/python scripts/install_remote.py
DATA_DIR=/home/aime/atelier-tryon/data \
SHOPWARE_ADMIN_FILE=/home/aime/atelier-tryon/admin.json \
../.venv/bin/python scripts/seed_shopware.py
```

The seed is repeatable: deterministic product/media/category IDs are upserted. It sets the dedicated channel's domain and navigation category and creates 17 real products. It does not delete unrelated records. The API catalog is a snapshot of these seeded products; changes made later in Shopware Admin require synchronization before the API reflects them.

## Updating and verification

```sh
docker cp shopware/AtelierYou/. atelier-shopware:/var/www/html/custom/plugins/AtelierYou/
docker exec atelier-shopware php bin/console assets:install
docker exec atelier-shopware php bin/console cache:clear
systemctl --user restart atelier-api
curl http://192.168.1.120:8090/tryon/health
../.venv/bin/pip install pytest
../.venv/bin/python -m pytest tests -q
```

Wait until health says `ready: true`. Interrupted jobs return to the queue on restart. Review `journalctl --user -u atelier-api` for service errors. The current demo container retains its data across restarts; do not remove it before exporting/backing up the database and media. The initial live container predates the named-volume example above.

## Session API

- `POST /tryon/session`: multipart `photo`; returns an HttpOnly cookie.
- `POST /tryon/jobs`: JSON `product_id`, or `product_ids` with up to five distinct slots; optional `view` = `front`, `side`, `back` and `priority`.
- `GET /tryon/session`: polling status and completed job IDs.
- `GET /tryon/results/{id}`: authenticated session-owned image.
- `DELETE /tryon/session`: deletes original, outputs, jobs and outfits.

Angles require a completed front view. Repeated requests are idempotent. A single worker serializes inference; queued background jobs do not preempt a running inference. Limits are 12 MB per photo, 32 live sessions and 256 queued/running jobs. This provides bounded demo admission, not production abuse protection.

For public deployment, replace Dockware with a supported production setup, enable TLS/Secure cookies, add authentication and per-user rate limits, and adapt the exact allowed origin. Keep personal media private and review model licensing.

## Demo movie

The editable HyperFrames composition is in `videos/atelier-you`. Its private `assets/` folder is delivered locally with the project and excluded from Git. It contains real browser captures, customer reference/outputs, fonts and generated demo music. With those assets present, Node 22+ and FFmpeg installed:

```sh
cd videos/atelier-you
npm run check
npm run render -- --quality delivery --output renders/atelier-you-demo.mp4
```

The movie shows recorded browser operation at normal speed, plus designed title and result shots. It does not simulate server completion or a 3D model.
