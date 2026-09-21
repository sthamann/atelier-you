"""Private-session virtual try-on API. SQLite queue survives service restarts."""
import hashlib
import io
import json
import logging
import os
import secrets
import shutil
import sqlite3
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from PIL import Image, ImageOps, UnidentifiedImageError
from .engine import Engine, MODEL_ID, REVISION, RECIPE

ROOT = Path(os.getenv('DATA_DIR', 'data')).resolve()
ROOT.mkdir(parents=True, exist_ok=True)
(ROOT / 'sessions').mkdir(exist_ok=True)
DB = ROOT / 'queue.sqlite'
COOKIE = 'atelier_session'
TTL = 86400
MAX_UPLOAD = 12 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 24_000_000
state = {'ready': False, 'error': None, 'active': None}
wake = threading.Event()
mutation = threading.RLock()

def connection():
    con = sqlite3.connect(DB, timeout=30)
    con.row_factory = sqlite3.Row
    return con

def initialize():
    with connection() as db:
        db.executescript('''
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, created REAL, photo_hash TEXT);
        CREATE TABLE IF NOT EXISTS outfits (id TEXT, session TEXT, products TEXT, PRIMARY KEY(id,session));
        CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, session TEXT, product TEXT,
        status TEXT, priority INTEGER, created REAL, seconds REAL, error TEXT,
        UNIQUE(session,product));
        ''')
        if 'view' not in {r['name'] for r in db.execute('PRAGMA table_info(jobs)')}:
            db.executescript('''
            ALTER TABLE jobs RENAME TO jobs_v1;
            CREATE TABLE jobs (id TEXT PRIMARY KEY, session TEXT, product TEXT,
            status TEXT, priority INTEGER, created REAL, seconds REAL, error TEXT,
            view TEXT NOT NULL DEFAULT 'front', UNIQUE(session,product,view));
            INSERT INTO jobs SELECT *, 'front' FROM jobs_v1;
            DROP TABLE jobs_v1;
            ''')
        if 'recipe' not in {r['name'] for r in db.execute('PRAGMA table_info(jobs)')}:
            db.executescript("""
            ALTER TABLE jobs RENAME TO jobs_v2;
            CREATE TABLE jobs (id TEXT PRIMARY KEY, session TEXT, product TEXT,
            status TEXT, priority INTEGER, created REAL, seconds REAL, error TEXT,
            view TEXT NOT NULL DEFAULT 'front', recipe TEXT NOT NULL,
            UNIQUE(session,product,view,recipe));
            INSERT INTO jobs SELECT *, 'atelier-v1-768x1024-28steps' FROM jobs_v2;
            DROP TABLE jobs_v2;
            """)
        db.execute("UPDATE jobs SET status='queued' WHERE status='running' AND recipe=?", (RECIPE,))

def catalog():
    path = ROOT / 'catalog.json'
    return json.loads(path.read_text()) if path.exists() else []

def get_session(request):
    token = request.cookies.get(COOKIE, '')
    sid = hashlib.sha256(token.encode()).hexdigest()
    with connection() as db:
        row = db.execute('SELECT * FROM sessions WHERE id=? AND created>?', (sid, time.time()-TTL)).fetchone()
    if not row:
        raise HTTPException(401, 'Please upload your photo first.')
    return dict(row)

def session_dir(sid):
    return ROOT / 'sessions' / sid

def remove_session(sid):
    with connection() as db:
        db.execute('DELETE FROM jobs WHERE session=?', (sid,))
        db.execute('DELETE FROM outfits WHERE session=?', (sid,))
        db.execute('DELETE FROM sessions WHERE id=?', (sid,))
    shutil.rmtree(session_dir(sid), ignore_errors=True)

def sweep():
    with connection() as db:
        stale = db.execute('SELECT id FROM sessions WHERE created<?', (time.time()-TTL,)).fetchall()
    for row in stale:
        remove_session(row['id'])

def worker():
    try:
        engine = Engine()
        state['ready'] = True
    except Exception:
        logging.exception('Model initialization failed')
        state['error'] = 'The image model could not be loaded.'
        return
    while True:
        with mutation:
            sweep()
            with connection() as db:
                job = db.execute("SELECT * FROM jobs WHERE status='queued' AND recipe=? ORDER BY priority DESC, created LIMIT 1", (RECIPE,)).fetchone()
                if job:
                    db.execute("UPDATE jobs SET status='running' WHERE id=?", (job['id'],))
        if not job:
            wake.wait(5)
            wake.clear()
            continue
        state['active'] = job['id']
        folder = session_dir(job['session'])
        temp = ROOT / ('render-' + job['id'] + '.webp')
        try:
            if job['product'].startswith('outfit-'):
                with connection() as db:
                    outfit = db.execute('SELECT products FROM outfits WHERE id=? AND session=?',(job['product'],job['session'])).fetchone()
                ids = json.loads(outfit['products'])
                products = [p for p in catalog() if p['id'] in ids]
            else:
                products = [next(p for p in catalog() if p['id'] == job['product'])]
            front = None
            if job['view'] != 'front':
                with connection() as db:
                    ref = db.execute("SELECT id FROM jobs WHERE session=? AND product=? AND view='front' AND status='done' AND recipe=?", (job['session'],job['product'],RECIPE)).fetchone()
                if not ref:
                    raise RuntimeError('Front reference not ready')
                front = folder / (ref['id'] + '.webp')
            seconds = engine.generate(folder / 'photo.jpg', [ROOT / 'products' / p['file'] for p in products], temp, [p['prompt'] for p in products], view=job['view'], front=front)
            with mutation:
                with connection() as db:
                    alive = db.execute('SELECT 1 FROM sessions WHERE id=? AND created>?', (job['session'],time.time()-TTL)).fetchone()
                    if alive:
                        temp.replace(folder / (job['id'] + '.webp'))
                        db.execute("UPDATE jobs SET status='done', seconds=? WHERE id=?", (seconds,job['id']))
        except Exception:
            logging.exception('Generation failed: %s', job['id'])
            with connection() as db:
                db.execute("UPDATE jobs SET status='failed', error=? WHERE id=?", ('Try-on failed. Please try again.',job['id']))
        finally:
            temp.unlink(missing_ok=True)
            state['active'] = None

@asynccontextmanager
async def lifespan(app):
    initialize()
    if os.getenv('ATELIER_TEST') != '1':
        threading.Thread(target=worker, daemon=True).start()
        def cleanup():
            while True:
                with mutation:
                    sweep()
                time.sleep(30)
        threading.Thread(target=cleanup, daemon=True).start()
    yield

app = FastAPI(title='ATELIER / YOU — private try-on', lifespan=lifespan)

@app.middleware('http')
async def private_headers(request, call_next):
    if request.method == 'POST':
        try:
            length = int(request.headers.get('content-length', '0'))
        except ValueError:
            return Response(status_code=400)
        if length > MAX_UPLOAD + 1024 * 1024:
            return Response(status_code=413)
    if request.method in ('POST','DELETE'):
        origin = request.headers.get('origin')
        allowed = os.getenv('PUBLIC_ORIGIN', 'http://192.168.1.120:8090')
        if origin and origin != allowed:
            return Response(status_code=403)
        if request.headers.get('sec-fetch-site') == 'cross-site':
            return Response(status_code=403)
    response = await call_next(request)
    response.headers['Cache-Control'] = 'private, no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

@app.get('/tryon/health')
def health():
    return {**state, 'model': MODEL_ID, 'revision': REVISION, 'recipe': RECIPE, 'device': 'RTX PRO 6000', 'evaluation_only': True}

@app.get('/tryon/catalog')
def get_catalog():
    return catalog()

@app.get('/tryon/products/{pid}/image')
def product_image(pid: str):
    product = next((p for p in catalog() if p['id'] == pid), None)
    if not product:
        raise HTTPException(404)
    return FileResponse(ROOT / 'products' / product['file'])

@app.post('/tryon/session')
async def upload(request: Request, response: Response, photo: UploadFile = File(...)):
    data = await photo.read(MAX_UPLOAD + 1)
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, 'Please choose a photo smaller than 12 MB.')
    try:
        im = Image.open(io.BytesIO(data))
        if im.format not in ('JPEG','PNG','WEBP'):
            raise ValueError()
        im = ImageOps.exif_transpose(im).convert('RGB')
        im.thumbnail((1536,1536))
        if min(im.size) < 256:
            raise ValueError()
    except (ValueError, UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise HTTPException(400, 'Please use a valid JPG, PNG or WebP image with at least 256 pixels on each side.')
    with mutation:
        sweep()
        with connection() as db:
            count = db.execute('SELECT count(*) FROM sessions').fetchone()[0]
        if count >= 32:
            raise HTTPException(429, 'The demo is busy. Please try again later.')
        old = request.cookies.get(COOKIE)
        if old:
            remove_session(hashlib.sha256(old.encode()).hexdigest())
        token = secrets.token_urlsafe(32)
        sid = hashlib.sha256(token.encode()).hexdigest()
        folder = session_dir(sid)
        folder.mkdir(mode=0o700)
        im.save(folder / 'photo.jpg', quality=94)
        with connection() as db:
            db.execute('INSERT INTO sessions VALUES (?,?,?)', (sid,time.time(),hashlib.sha256((folder/'photo.jpg').read_bytes()).hexdigest()))
    response.set_cookie(COOKIE,token,max_age=TTL,httponly=True,samesite='strict',secure=os.getenv('COOKIE_SECURE')=='1',path='/tryon')
    return {'active':True,'expires_in':TTL}

@app.get('/tryon/session')
def session(request: Request):
    try:
        row = get_session(request)
    except HTTPException:
        return {'active':False}
    with connection() as db:
        jobs = [dict(r) for r in db.execute('SELECT id,product,status,seconds,error,view FROM jobs WHERE session=? AND recipe=?', (row['id'],RECIPE))]
    return {'active':True,'jobs':jobs,'expires_in':max(0,int(row['created']+TTL-time.time()))}

@app.delete('/tryon/session')
def delete(request: Request, response: Response):
    row = get_session(request)
    with mutation:
        remove_session(row['id'])
    response.delete_cookie(COOKIE,path='/tryon')
    return {'deleted':True}

@app.get('/tryon/photo')
def photo(request: Request):
    row = get_session(request)
    return FileResponse(session_dir(row['id']) / 'photo.jpg')

class JobRequest(BaseModel):
    product_id: str | None = None
    product_ids: list[str] = Field(default_factory=list, max_length=5)
    priority: bool = True
    view: Literal['front','side','back'] = 'front'

@app.post('/tryon/jobs')
def submit(body: JobRequest, request: Request):
    row = get_session(request)
    if body.product_ids:
        ids = sorted(set(body.product_ids))
        chosen = [p for p in catalog() if p['id'] in ids]
        if len(chosen) != len(ids):
            raise HTTPException(404,'Product not found.')
        slots = [p.get('slot','top') for p in chosen]
        if len(slots) != len(set(slots)):
            raise HTTPException(400,'Please choose at most one item per outfit category.')
        body.product_id = 'outfit-' + hashlib.sha256('|'.join(ids).encode()).hexdigest()[:24]
        with mutation, connection() as db:
            db.execute('INSERT OR IGNORE INTO outfits VALUES (?,?,?)',(body.product_id,row['id'],json.dumps(ids)))
    elif body.product_id and body.product_id.startswith('outfit-'):
        with connection() as db:
            if not db.execute('SELECT 1 FROM outfits WHERE id=? AND session=?',(body.product_id,row['id'])).fetchone():
                raise HTTPException(404,'Outfit not found.')
    elif body.product_id not in {p['id'] for p in catalog()}:
        raise HTTPException(404,'Product not found.')
    if state['error']:
        raise HTTPException(503,state['error'])
    with mutation, connection() as db:
        if body.view != 'front' and not db.execute("SELECT 1 FROM jobs WHERE session=? AND product=? AND view='front' AND status='done' AND recipe=?",(row['id'],body.product_id,RECIPE)).fetchone():
            raise HTTPException(409,'Your front view needs to be created first.')
        prior = db.execute('SELECT * FROM jobs WHERE session=? AND product=? AND view=? AND recipe=?',(row['id'],body.product_id,body.view,RECIPE)).fetchone()
        if prior:
            if prior['status'] == 'failed':
                db.execute("UPDATE jobs SET status='queued',error=NULL,priority=? WHERE id=?",(int(body.priority),prior['id']))
            elif body.priority:
                db.execute('UPDATE jobs SET priority=1 WHERE id=?',(prior['id'],))
            wake.set()
            return dict(db.execute('SELECT id,product,status,seconds,error,view FROM jobs WHERE id=?',(prior['id'],)).fetchone())
        queued = db.execute("SELECT count(*) FROM jobs WHERE status IN ('queued','running') AND recipe=?",(RECIPE,)).fetchone()[0]
        if queued >= 256:
            raise HTTPException(429,'The fitting room is busy.')
        jid = secrets.token_hex(16)
        db.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?)',(jid,row['id'],body.product_id,'queued',int(body.priority),time.time(),None,None,body.view,RECIPE))
    wake.set()
    return {'id':jid,'product':body.product_id,'status':'queued','view':body.view}

@app.get('/tryon/results/{jid}')
def result(jid: str, request: Request):
    row = get_session(request)
    with connection() as db:
        job = db.execute("SELECT * FROM jobs WHERE id=? AND session=? AND status='done' AND recipe=?",(jid,row['id'],RECIPE)).fetchone()
    if not job:
        raise HTTPException(404)
    return FileResponse(session_dir(row['id']) / (jid + '.webp'),media_type='image/webp')
