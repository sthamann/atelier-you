# Installation and operation

Run ATELIER / YOU on your own infrastructure. No access to the original demo server is needed. This guide uses a dedicated Linux GPU machine, a new Shopware development container and local browser access. It is a manual prototype setup, not a one-command production installer.

The existing `scripts/install_remote.py` and `scripts/atelier-api.service` preserve the original installation’s fixed paths, network addresses and GPU selection. **Do not run or copy them unchanged on another machine.** The commands below replace that bootstrap with explicit configuration. The application and catalog scripts also have original deployment defaults; always set the variables shown here.

## Prerequisites

- Access to this repository, Git, Python 3.12 and Docker Engine on Linux.
- An NVIDIA GPU with sufficient VRAM and a driver compatible with the pinned CUDA 13 PyTorch build. The reference installation used an RTX PRO 6000 with 96 GB VRAM and approximately 31.7 GB resident allocation. This is not a verified minimum; smaller GPUs and other configurations have not been tested.
- Approximately 40 GB free disk for model weights and the Python environment, plus space for generated media.
- Access to the pinned Qwen weights under their applicable license; see [third-party terms](THIRD_PARTY.md).

A GPU workstation or rented GPU server can supply inference. The example below puts Shopware and the API on the same Linux host. If they run on separate hosts, change the proxy destination to an internally reachable API address and configure the network accordingly. macOS/Windows Docker networking is outside this tested topology.

## 1. Choose your configuration

Run the shell blocks in the same Bash session. Use an installation path without spaces for the optional systemd unit below.

```bash
export ATELIER_ROOT="$HOME/atelier-you-runtime"
export MODEL_PATH="$ATELIER_ROOT/model"
export DATA_DIR="$ATELIER_ROOT/data"
export PUBLIC_ORIGIN="http://localhost:8090"
export SHOPWARE_URL="$PUBLIC_ORIGIN"
export SHOPWARE_ADMIN_FILE="$ATELIER_ROOT/admin.json"

# Inspect available GPUs, then choose one you have available for this service.
nvidia-smi --query-gpu=index,name,memory.total,uuid --format=csv
export CUDA_VISIBLE_DEVICES="0"

mkdir -p "$ATELIER_ROOT"
git clone git@github.com:sthamann/atelier-you.git "$ATELIER_ROOT/repo"
cd "$ATELIER_ROOT"
python3 -m venv .venv
.venv/bin/pip install torch==2.14.0 torchvision==0.29.0 --index-url https://download.pytorch.org/whl/cu130
.venv/bin/pip install -r repo/api/requirements.txt
.venv/bin/hf download Qwen/Qwen-Image-2.1 \
  --revision b3179ad355be050328e483a9dfdd9e60cd62adfa --local-dir "$MODEL_PATH"
mkdir -p "$DATA_DIR/products"
```

`PUBLIC_ORIGIN` must match the browser’s exact storefront origin, including scheme and port. `SHOPWARE_URL` must reach the same shop from the seed process; it is also written into the seeded sales-channel domain. This example uses `http://localhost:8090` consistently. On a remote GPU host, an SSH forward such as `ssh -L 8090:127.0.0.1:8090 user@your-gpu-host` lets your local browser use that same origin.

| Setting | Purpose |
|---|---|
| `CUDA_VISIBLE_DEVICES` | The GPU index or UUID selected for inference. |
| `MODEL_PATH` | Your downloaded model directory. |
| `DATA_DIR` | Persistent catalog, queue, photos and generated results. Keep outside the repository. |
| `PUBLIC_ORIGIN` | Exact storefront origin permitted for browser uploads and mutations. |
| `SHOPWARE_URL` | Shopware URL used by the catalog seed and sales-channel domain. |
| `SHOPWARE_ADMIN_FILE` | Private JSON file containing `username` and `password` for bootstrap/seeding. |
| `COOKIE_SECURE` | Set to `1` when the browser accesses the storefront over HTTPS. Leave unset for this local HTTP example. |

## 2. Generate the demo catalog

```bash
cd "$ATELIER_ROOT/repo"
"$ATELIER_ROOT/.venv/bin/python" scripts/generate_products.py
```

This creates synthetic garment references and `catalog.json` in `DATA_DIR`. Generate them before starting the resident API so both processes do not compete for GPU memory. The seed later creates 17 real Shopware product records from this catalog.

## 3. Create a dedicated development shop

```bash
docker run -d --name atelier-shopware --restart unless-stopped \
  -p 127.0.0.1:8090:80 \
  -v atelier-shopware-html:/var/www/html \
  -v atelier-shopware-db:/var/lib/mysql \
  dockware/dev:6.6.10.6
```

Wait for initialization to finish. Create `SHOPWARE_ADMIN_FILE` outside the repository with fields `username` and `password`, using a new admin name and a strong random password. Set its file mode to `0600`. Disable or randomize Dockware’s default administrator before granting access to the shop.

The following creates your administrator once. The password is supplied to the container CLI during bootstrap, so run it in a trusted administrative environment.

```bash
chmod 600 "$SHOPWARE_ADMIN_FILE"
"$ATELIER_ROOT/.venv/bin/python" - <<'PY'
import json, os, subprocess
from pathlib import Path
credentials = json.loads(Path(os.environ['SHOPWARE_ADMIN_FILE']).read_text())
result = subprocess.run([
    'docker', 'exec', 'atelier-shopware', 'php', 'bin/console',
    'user:create', credentials['username'], '--admin',
    '--email=atelier@example.invalid', '--password=' + credentials['password'], '-n',
])
if result.returncode:
    raise SystemExit('Admin bootstrap failed; check the container output.')
PY

docker exec atelier-shopware php bin/console sales-channel:update:domain \
  "$PUBLIC_ORIGIN" --previous-domain=http://localhost
docker exec -u root atelier-shopware mkdir -p /var/www/html/custom/plugins/AtelierYou
docker cp "$ATELIER_ROOT/repo/shopware/AtelierYou/." \
  atelier-shopware:/var/www/html/custom/plugins/AtelierYou/
docker exec atelier-shopware php bin/console plugin:refresh
docker exec atelier-shopware php bin/console plugin:install --activate AtelierYou
docker exec atelier-shopware php bin/console assets:install
docker exec atelier-shopware php bin/console cache:clear
```

## 4. Connect Shopware to the image API

The browser calls `/tryon/` on the storefront origin. Apache forwards these requests to the API; the GPU address is never a browser-facing link.

For this same-host Linux Docker example, bind the API to the host’s Docker bridge gateway, which the Shopware container can reach:

```bash
export ATELIER_API_BIND="$(docker network inspect bridge --format '{{(index .IPAM.Config 0).Gateway}}')"
test -n "$ATELIER_API_BIND"
cat > "$ATELIER_ROOT/atelier-proxy.conf" <<PROXY
ProxyPass /tryon/ http://${ATELIER_API_BIND}:8091/tryon/
ProxyPassReverse /tryon/ http://${ATELIER_API_BIND}:8091/tryon/
PROXY

docker cp "$ATELIER_ROOT/atelier-proxy.conf" \
  atelier-shopware:/etc/apache2/conf-available/atelier-proxy.conf
docker exec -u root atelier-shopware a2enmod proxy proxy_http
docker exec -u root atelier-shopware a2enconf atelier-proxy
docker exec -u root atelier-shopware apachectl -k graceful

cd "$ATELIER_ROOT/repo"
"$ATELIER_ROOT/.venv/bin/python" scripts/seed_shopware.py
"$ATELIER_ROOT/.venv/bin/uvicorn" api.app:app \
  --host "$ATELIER_API_BIND" --port 8091 --workers 1
```

Keep that terminal running while trying the shop. Only one API worker should own the model. On a split-host installation, replace the bind address and proxy destination with your own internal network configuration. Do not expose the API directly to the public internet.

The seed upserts deterministic product/media/category IDs, sets the dedicated channel’s English language and domain, and creates 17 products. It changes the first Storefront channel’s navigation and domain settings: **use a fresh development shop, not an existing merchant store.** It does not delete unrelated records. The API catalog is a snapshot; later Shopware Admin edits need synchronization before inference reflects them.

## 5. Open your shop and verify

After model loading, `http://localhost:8090/tryon/health` should report `ready: true`. Open `http://localhost:8090/` and upload a photo. Outfit Studio is at `http://localhost:8090/?outfit=1`. These URLs point to your installation (or SSH-forwarded installation), not a hosted demo.

API documentation is at `http://<your-internal-api-address>:8091/docs` from a machine with access to that internal interface. It is not exposed through the storefront proxy.

In another shell, set `ATELIER_ROOT` to the same installation directory and run:

```bash
curl --fail http://localhost:8090/tryon/health
cd "$ATELIER_ROOT/repo"
"$ATELIER_ROOT/.venv/bin/pip" install pytest
"$ATELIER_ROOT/.venv/bin/python" -m pytest tests -q
```

The automated tests do not validate your GPU’s performance. Test a real photo upload and generated result in your deployment. See [reference measurements and limits](VERIFICATION.md).

## Optional: keep the API running with systemd

Stop the foreground API before starting a service. With the configuration variables from steps 1 and 4 still set, generate a unit for your own installation:

```bash
mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/atelier-api.service" <<UNIT
[Unit]
Description=ATELIER YOU image API
After=network-online.target
[Service]
Type=simple
WorkingDirectory=${ATELIER_ROOT}/repo
Environment=CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES}
Environment=MODEL_PATH=${MODEL_PATH}
Environment=DATA_DIR=${DATA_DIR}
Environment=PUBLIC_ORIGIN=${PUBLIC_ORIGIN}
Environment=COOKIE_SECURE=${COOKIE_SECURE:-0}
Environment=PYTHONUNBUFFERED=1
ExecStart=${ATELIER_ROOT}/.venv/bin/uvicorn api.app:app --host ${ATELIER_API_BIND} --port 8091 --workers 1
Restart=on-failure
RestartSec=5
UMask=0077
[Install]
WantedBy=default.target
UNIT
systemctl --user daemon-reload
systemctl --user enable --now atelier-api
```

If an SSH shell cannot find the user bus, prefix `systemctl` with `XDG_RUNTIME_DIR=/run/user/$(id -u)`. Enable lingering for the service account if the service must survive logout. Inspect errors with `journalctl --user -u atelier-api`. Interrupted jobs return to the queue after restart; completed results remain usable until session expiry.

## Updates and storage

After updating the source, copy the plugin contents into the same container, install assets and clear the cache:

```bash
docker cp "$ATELIER_ROOT/repo/shopware/AtelierYou/." \
  atelier-shopware:/var/www/html/custom/plugins/AtelierYou/
docker exec atelier-shopware php bin/console assets:install
docker exec atelier-shopware php bin/console cache:clear
systemctl --user restart atelier-api
```

If using a foreground API, restart that process instead. Back up the database, Shopware media and persistent API data before replacing containers or changing storage. Never commit credentials, customer uploads or session data.

## Session API

- `POST /tryon/session`: multipart `photo`; returns an HttpOnly cookie.
- `POST /tryon/jobs`: JSON `product_id`, or `product_ids` with up to five distinct slots; optional `view` = `front`, `side`, `back` and `priority`.
- `GET /tryon/session`: polling status and completed job IDs.
- `GET /tryon/results/{id}`: authenticated session-owned image.
- `DELETE /tryon/session`: deletes original, outputs, jobs and outfits.

Angles require a completed front view. Repeated requests are idempotent. A single worker serializes inference; queued background jobs do not preempt a running inference. Limits are 12 MB per photo, 32 live sessions and 256 queued/running jobs. These are bounded prototype limits, not production abuse protection.

## Before public operation

Replace Dockware with a supported production Shopware setup, enable TLS and `COOKIE_SECURE=1`, set the exact `PUBLIC_ORIGIN`, and provide authentication, per-user quotas and rate limits. Keep API connectivity internal. Review model rights, product-reference quality, storage retention and privacy requirements for your deployment. The recorded prototype does not establish production security, multi-user capacity or physical fit accuracy.

## Demo movie

You can watch the README GIF and release video without running the app or owning a GPU. To edit the video, use the media project archive from [the demo release](https://github.com/sthamann/atelier-you/releases/tag/v0.4.0). It restores the assets excluded from Git. The archive is a source snapshot for that video; use the current repository and this guide for application setup.

With the media assets restored, Node 22+ and FFmpeg installed:

```bash
cd videos/atelier-you
npm run check
npm run render -- --quality delivery --output renders/atelier-you-demo.mp4
```

The movie contains real browser captures and designed result shots. Generation waiting time is omitted and labelled; product-page sequences use previously generated results. See [media details](MEDIA.md).
