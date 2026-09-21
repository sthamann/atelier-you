import json, os, uuid
from pathlib import Path
import httpx
root=Path(os.getenv('DATA_DIR','data'))
base=os.getenv('SHOPWARE_URL','http://192.168.1.120:8090')
auth=json.loads(Path(os.environ['SHOPWARE_ADMIN_FILE']).read_text())
c=httpx.Client(base_url=base,timeout=90)
r=c.post('/api/oauth/token',json={'grant_type':'password','client_id':'administration',**auth});r.raise_for_status()
c.headers['Authorization']='Bearer '+r.json()['access_token']

def call(method,path,**kwargs):
 r=c.request(method,'/api/'+path,**kwargs)
 if r.is_error: print(r.text[:3000]);r.raise_for_status()
 return r.json() if r.content else None

def search(entity,**body):
 return call('POST','search/'+entity,json={'limit':100,**body})['data']
channels=search('sales-channel',filter=[{'type':'equals','field':'typeId','value':'8a243080f92e4c719546314b577cf82b'}])
channel=channels[0];cid=channel['id'];currency=channel['attributes']['currencyId']
for domain in search('sales-channel-domain',filter=[{'type':'equals','field':'salesChannelId','value':cid}]):
 call('PATCH','sales-channel-domain/'+domain['id'],json={'url':base})
tax=next(x for x in search('tax') if x['attributes']['taxRate']==19)['id']
category=uuid.uuid5(uuid.NAMESPACE_URL,'atelier-you/category').hex
call('POST','_action/sync',json={'category':{'entity':'category','action':'upsert','payload':[{'id':category,'name':'ATELIER / YOU','active':True,'type':'page'}]}})
call('PATCH','sales-channel/'+cid,json={'name':'ATELIER / YOU','navigationCategoryId':category})
products=json.loads((root/'catalog.json').read_text())
for i,p in enumerate(products):
 mid=uuid.uuid5(uuid.NAMESPACE_URL,'atelier-you/media/'+p['id']).hex
 pmid=uuid.uuid5(uuid.NAMESPACE_URL,'atelier-you/productmedia/'+p['id']).hex
 call('POST','_action/sync',json={'media':{'entity':'media','action':'upsert','payload':[{'id':mid}]}})
 call('POST','_action/media/'+mid+'/upload',params={'extension':'webp','fileName':'atelier-'+p['id']},content=(root/'products'/p['file']).read_bytes(),headers={'Content-Type':'image/webp'})
 payload={'id':p['id'],'name':p['name'],'productNumber':'AY-'+str(i+1).zfill(3),'description':p['description'],'active':True,'stock':100,'taxId':tax,'price':[{'currencyId':currency,'gross':p['price'],'net':round(p['price']/1.19,2),'linked':True}],'visibilities':[{'id':uuid.uuid5(uuid.NAMESPACE_URL,'atelier-you/visibility/'+p['id']).hex,'salesChannelId':cid,'visibility':30}],'categories':[{'id':category}],'media':[{'id':pmid,'mediaId':mid,'position':0}],'coverId':pmid}
 call('POST','_action/sync',json={'products':{'entity':'product','action':'upsert','payload':[payload]}})
 print('Seeded',p['name'],p['id'],flush=True)
(root/'shopware-evidence.json').write_text(json.dumps({'sales_channel':cid,'category':category,'product_ids':[p['id'] for p in products],'shopware_url':base},indent=2))
print('Verified product count:',len(search('product',filter=[{'type':'prefix','field':'productNumber','value':'AY-'}])))
