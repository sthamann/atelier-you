import io, json, importlib, sys, time
import pytest
from PIL import Image
from fastapi.testclient import TestClient

@pytest.fixture
def api(tmp_path,monkeypatch):
 monkeypatch.setenv('DATA_DIR',str(tmp_path));monkeypatch.setenv('ATELIER_TEST','1')
 sys.modules.pop('api.app',None)
 module=importlib.import_module('api.app')
 (tmp_path/'catalog.json').write_text(json.dumps([{'id':'product-a','file':'a.webp'}]))
 with TestClient(module.app) as c:
  yield module,c

def upload(c):
 buffer=io.BytesIO();Image.new('RGB',(512,768),'grey').save(buffer,'JPEG')
 return c.post('/tryon/session',files={'photo':('test.jpg',buffer.getvalue(),'image/jpeg')})

def test_reject_invalid_upload_and_foreign_origin(api):
 m,c=api
 assert c.post('/tryon/session',files={'photo':('x.jpg',b'not an image','image/jpeg')}).status_code==400
 assert c.post('/tryon/jobs',headers={'Origin':'https://evil.example'},json={'product_id':'product-a'}).status_code==403
 assert c.post('/tryon/jobs',json={'product_id':'product-a'}).status_code==401

def test_job_idempotence_and_private_results(api):
 m,c=api
 assert upload(c).status_code==200
 a=c.post('/tryon/jobs',json={'product_id':'product-a'}).json()
 b=c.post('/tryon/jobs',json={'product_id':'product-a'}).json()
 assert a['id']==b['id']
 with m.connection() as db:
  row=db.execute('SELECT * FROM sessions').fetchone()
  db.execute("UPDATE jobs SET status='done' WHERE id=?",(a['id'],))
 out=m.session_dir(row['id'])/(a['id']+'.webp');Image.new('RGB',(10,10)).save(out)
 assert c.get('/tryon/results/'+a['id']).status_code==200
 with TestClient(m.app) as other:
  assert upload(other).status_code==200
  assert other.get('/tryon/results/'+a['id']).status_code==404
 assert c.delete('/tryon/session').status_code==200
 assert not out.exists()
 assert c.get('/tryon/results/'+a['id']).status_code==401

def test_photo_replacement_removes_prior_results_and_expiry(api):
 m,c=api
 upload(c);c.post('/tryon/jobs',json={'product_id':'product-a'})
 with m.connection() as db: old=db.execute('SELECT id FROM sessions').fetchone()['id']
 upload(c)
 assert not m.session_dir(old).exists()
 assert c.get('/tryon/session').json()['jobs']==[]
 with m.connection() as db:db.execute('UPDATE sessions SET created=?',(time.time()-m.TTL-1,))
 assert c.get('/tryon/session').json()['active'] is False
 m.sweep()
 with m.connection() as db:assert db.execute('SELECT count(*) FROM sessions').fetchone()[0]==0

def test_outfits_validate_slots_and_angles_require_front(api):
 m,c=api
 (m.ROOT/'catalog.json').write_text(json.dumps([{'id':'shirt','slot':'top'},{'id':'tee','slot':'top'},{'id':'pants','slot':'bottom'}]))
 upload(c)
 assert c.post('/tryon/jobs',json={'product_ids':['shirt','tee']}).status_code==400
 assert c.post('/tryon/jobs',json={'product_ids':['missing']}).status_code==404
 first=c.post('/tryon/jobs',json={'product_ids':['shirt','pants']}).json()
 same=c.post('/tryon/jobs',json={'product_ids':['pants','shirt']}).json()
 assert first['id']==same['id']
 assert c.post('/tryon/jobs',json={'product_id':first['product'],'view':'side'}).status_code==409
 with m.connection() as db:db.execute("UPDATE jobs SET status='done' WHERE id=?",(first['id'],))
 side=c.post('/tryon/jobs',json={'product_id':first['product'],'view':'side'})
 assert side.status_code==200 and side.json()['id']!=first['id']
 assert c.post('/tryon/jobs',json={'product_id':first['product'],'view':'invalid'}).status_code==422
 with TestClient(m.app) as other:
  upload(other)
  assert other.post('/tryon/jobs',json={'product_id':first['product']}).status_code==404
 c.delete('/tryon/session')
 with m.connection() as db:assert db.execute('SELECT count(*) FROM outfits').fetchone()[0]==0

def test_recipe_change_never_reuses_old_face_or_angle_reference(api, monkeypatch):
 m,c=api
 upload(c)
 first=c.post('/tryon/jobs',json={'product_id':'product-a'}).json()
 with m.connection() as db:
  sid=db.execute('SELECT id FROM sessions').fetchone()['id']
  db.execute("UPDATE jobs SET status='done' WHERE id=?",(first['id'],))
 Image.new('RGB',(10,10)).save(m.session_dir(sid)/(first['id']+'.webp'))
 monkeypatch.setattr(m,'RECIPE','a-new-identity-recipe')
 assert c.get('/tryon/session').json()['jobs']==[]
 assert c.get('/tryon/results/'+first['id']).status_code==404
 assert c.post('/tryon/jobs',json={'product_id':'product-a','view':'side'}).status_code==409
 new=c.post('/tryon/jobs',json={'product_id':'product-a'}).json()
 assert new['id']!=first['id']
 assert c.post('/tryon/jobs',json={'product_id':'product-a'}).json()['id']==new['id']
 # Rollback can still use its own cache; no destructive migration of personal media.
 with m.connection() as db:assert db.execute('SELECT count(*) FROM jobs').fetchone()[0]==2
