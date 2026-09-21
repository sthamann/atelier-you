"""Generate original synthetic demo merchandise, with reproducible prompts."""
import json, os, time, uuid
from pathlib import Path
import torch
from diffusers import QwenImage21Pipeline
root=Path(os.environ.get('DATA_DIR','data'))
(root/'products').mkdir(parents=True,exist_ok=True)
items=[
 ('The City Overshirt','Outerwear',149,'Olive','olive green heavyweight cotton twill overshirt jacket, classic collar, two large chest flap pockets, matte dark buttons, relaxed fit, long sleeves','A clean silhouette. Heavy cotton twill, distinctive pockets and an easy olive shade for every day.'),
 ('The Soft Knit','Knitwear',119,'Sand','sand beige textured cable knit wool crew neck sweater, ribbed cuffs and hem, long sleeves, premium minimalist menswear','Soft knitwear in warm sand. An effortless companion for cool mornings and long evenings.'),
 ('The Everyday Blazer','Outerwear',229,'Midnight','navy blue unstructured single breasted mens blazer, two buttons, notch lapels, premium wool texture, tailored casual fit','Relaxed enough for every day. Sharp enough for your next meeting. Your blazer in deep midnight blue.'),
 ('The Oxford Shirt','Essentials',89,'Cloud','crisp light blue Oxford cotton button down mens shirt, white buttons, long sleeves, subtle cotton texture','A lightweight classic. Oxford cotton in cloud blue with a relaxed, precise silhouette.'),
 ('The Studio Hoodie','Essentials',99,'Terracotta','muted terracotta rust orange premium heavyweight cotton hoodie, no logo, kangaroo pocket, matching drawstrings, ribbed cuffs','Heavyweight cotton, a soft lining and a warm colour. For everything between the studio and the weekend.'),
 ('The Merino Polo','Knitwear',109,'Forest','dark forest green fine merino wool short sleeved knit polo shirt, three buttons, ribbed hem, luxury minimal menswear','Fine merino knitwear in deep forest green. A quiet alternative between a T-shirt and a shirt.'),
]
items += [
 ('The Straight Denim','Trousers',129,'Washed Black','washed black straight leg denim jeans, five pocket design, matte silver hardware, full length mens trousers','A clean cut, authentic denim and washed black. Your everyday favourite.'),
 ('The Relaxed Chino','Trousers',99,'Stone','stone beige relaxed tapered cotton chino trousers for men, full length, minimal flat front','Light, relaxed and versatile. A chino in pale stone for every day.'),
 ('The Tailored Trouser','Trousers',139,'Navy','navy blue tailored mens wool trousers with subtle front crease, full length, straight fit','A clean line in navy. For a look that needs no special occasion.'),
 ('The Court Sneaker','Footwear',149,'White','pair of clean white leather low top court sneakers, white laces, warm off-white rubber sole, no logos, three quarter product view','Stripped back to the essentials. White sneakers with a quiet, timeless silhouette.'),
 ('The Suede Runner','Footwear',159,'Taupe','pair of taupe and cream suede running inspired sneakers, mesh panels, gum rubber outsole, no logos, three quarter product view','Taupe, cream and soft suede. A sporty touch for relaxed combinations.'),
 ('The Chelsea Boot','Footwear',189,'Espresso','pair of dark espresso brown suede Chelsea ankle boots, elastic side panels, brown rubber sole, three quarter product view','Soft suede in espresso. A Chelsea boot with effortless presence.'),
 ('The Everyday Cap','Headwear',39,'Olive','olive green cotton six panel baseball cap, curved brim, adjustable strap, no logo, three quarter product view','An easy finishing touch for your look. A cotton cap in understated olive.'),
 ('The Studio Cap','Headwear',39,'Black','black cotton six panel baseball cap, curved brim, adjustable strap, no logo, three quarter product view','A black cap. A clear statement. No logo, no fuss.'),
 ('The Heavy Tee','T-Shirts',49,'Chalk','chalk white heavyweight cotton mens crew neck T-shirt, short sleeves, boxy relaxed fit, no logo','Heavyweight jersey, clean lines. The white T-shirt your outfit is built on.'),
 ('The Night Tee','T-Shirts',49,'Black','jet black heavyweight cotton mens crew neck T-shirt, short sleeves, relaxed fit, no logo','Deep black and soft jersey. An everyday essential.'),
 ('The Breton Tee','T-Shirts',59,'Navy / Ecru','ecru cotton mens crew neck T-shirt with thin horizontal navy blue Breton stripes, short sleeves','A nautical classic. Fine navy stripes on warm ecru.'),
]

catalog=[]
pipe=None
for i,(name,cat,price,color,desc,copy) in enumerate(items):
    pid=uuid.uuid5(uuid.NAMESPACE_URL,'atelier-you/'+name).hex
    file=pid+'.webp'
    slot={'Outerwear':'outer','Trousers':'bottom','Footwear':'shoes','Headwear':'head'}.get(cat,'top')
    catalog.append(dict(slot=slot,id=pid,name=name,category=cat,price=price,color=color,prompt=desc,description=copy,file=file,image='/tryon/products/'+pid+'/image',url='/detail/'+pid))
    if (root/'products'/file).exists(): continue
    if pipe is None:
        pipe=QwenImage21Pipeline.from_pretrained(os.environ['MODEL_PATH'],torch_dtype=torch.bfloat16).to('cuda')
    start=time.monotonic()
    presentation='Single item or matching pair centered' if cat in ('Footwear','Headwear') else 'Single garment on an invisible ghost mannequin, front view, full garment centered'
    prompt='Premium e-commerce product photography of '+desc+'. '+presentation+', warm light grey studio background, soft natural shadows, highly detailed fabric texture. No person, no hands, no face, no hanger, no text, no logo. Editorial luxury fashion catalog, vertical composition.'
    with torch.inference_mode():
        image=pipe(prompt=prompt,width=768,height=1024,num_inference_steps=28,generator=torch.Generator('cuda').manual_seed(100+i)).images[0]
    image.convert('RGB').save(root/'products'/file,'WEBP',quality=94)
    print(json.dumps(dict(product=name,seconds=round(time.monotonic()-start,2))),flush=True)
    (root/'catalog.json').write_text(json.dumps(catalog,indent=2,ensure_ascii=False))
(root/'catalog.json').write_text(json.dumps(catalog,indent=2,ensure_ascii=False))
