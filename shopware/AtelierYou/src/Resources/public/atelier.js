(() => {
  'use strict';
  const $ = s => document.querySelector(s);
  const dialog = $('#ay-upload');
  if (!dialog) return;
  let current = $('.ay-main')?.dataset.productId || '';
  const studio = $('.ay-main')?.dataset.outfit === 'true';
  let products = [], active = false, jobs = [], personalURL = '', originalURL = '', showOriginal = false, previewURL, currentView = 'front', swapTimer, swapToken = 0;
  const angleRequests = new Set();
  const money = n => new Intl.NumberFormat('de-DE',{style:'currency',currency:'EUR'}).format(n);
  const toast = text => {$('#ay-toast').textContent=text;$('#ay-toast').hidden=false;setTimeout(()=>$('#ay-toast').hidden=true,6000);};
  async function api(path, options={}) {
    const r = await fetch('/tryon/'+path,{credentials:'same-origin',...options});
    if(!r.ok){let d;try{d=await r.json();}catch{}throw new Error(d?.detail||'Die Anprobe ist gerade nicht erreichbar.');}
    return r.json();
  }
  const jobFor = (id,view='front') => jobs.find(j=>j.product===id && (j.view||'front')===view && j.status==='done');
  function displayImage(url) {
    const base=$('#ay-main-image'), incoming=$('#ay-incoming-image');
    if(!base)return;
    if(base.getAttribute('src')===url){if(incoming.dataset.target&&incoming.dataset.target!==url){++swapToken;clearTimeout(swapTimer);incoming.style.transition='none';incoming.style.opacity='0';incoming.dataset.target='';}return;}
    if(incoming.dataset.target===url)return;
    const token=++swapToken;clearTimeout(swapTimer);incoming.dataset.target=url;incoming.style.transition='none';incoming.style.opacity='0';
    incoming.onload=()=>{if(token!==swapToken)return;requestAnimationFrame(()=>requestAnimationFrame(()=>{incoming.style.transition='opacity 1.6s cubic-bezier(.22,1,.36,1)';incoming.style.opacity='1';swapTimer=setTimeout(()=>{if(token!==swapToken)return;base.src=url;incoming.style.transition='none';incoming.style.opacity='0';incoming.dataset.target='';},1650);}));};incoming.src=url;
  }
  async function requestAngles(){
    if(!current||!jobFor(current))return;
    for(const view of ['side','back']){const key=current+view;if(angleRequests.has(key))continue;angleRequests.add(key);try{await api('jobs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product_id:current,view,priority:true})});}catch(e){angleRequests.delete(key);}}
  }
  function draw(filter='all') {
    const grid = $('#ay-products'); if(!grid)return;
    grid.replaceChildren();
    const list=products.filter(p=>p.id!==current && (filter==='all'||p.category===filter));
    for(const p of list){
      const card=document.createElement('a');card.className='ay-card';card.href=p.url;
      const visual=document.createElement('div');visual.className='ay-card-visual';
      const img=document.createElement('img');img.alt=p.name;img.loading='lazy';img.dataset.pid=p.id;
      const done=jobFor(p.id);img.src=done?'/tryon/results/'+done.id:p.image;
      const tag=document.createElement('span');tag.className='ay-card-tag';tag.textContent=done?'DEIN LOOK':p.category.toUpperCase();
      const arrow=document.createElement('span');arrow.className='ay-card-arrow';arrow.textContent='↗';
      visual.append(img,tag,arrow);
      const info=document.createElement('div');info.className='ay-card-info';
      const text=document.createElement('div');const title=document.createElement('h3');title.textContent=p.name;
      const color=document.createElement('p');color.textContent=p.color+' / ATELIER ESSENTIALS';text.append(title,color);
      const price=document.createElement('span');price.textContent=money(p.price);info.append(text,price);card.append(visual,info);grid.append(card);
    }
  }
  function outfitIds(){return [...document.querySelectorAll('[data-slot]')].map(x=>x.value).filter(Boolean);}
  function outfitSelectors(){
    const host=$('#ay-outfit-selectors');if(!host)return;
    let saved={};try{saved=JSON.parse(localStorage.getItem('atelier-outfit')||'{}');}catch{}
    const defaults={top:'The Heavy Tee',outer:'The City Overshirt',bottom:'The Relaxed Chino',shoes:'The Court Sneaker',head:'The Everyday Cap'};
    for(const [slot,label] of Object.entries({top:'OBERTEIL',outer:'JACKE',bottom:'HOSE',shoes:'SCHUHE',head:'CAP'})){
      const row=document.createElement('div');row.className='ay-outfit-select';const img=document.createElement('img');img.alt=label;
      const wrap=document.createElement('div'),lab=document.createElement('label');lab.textContent=label;lab.htmlFor='slot-'+slot;
      const select=document.createElement('select');select.id='slot-'+slot;select.dataset.slot=slot;select.add(new Option('Ohne '+label.toLowerCase(),''));
      const candidates=products.filter(p=>p.slot===slot);for(const p of candidates)select.add(new Option(p.name+' · '+p.color+' · '+money(p.price),p.id));
      select.value=saved[slot]!==undefined?saved[slot]:(candidates.find(p=>p.name===defaults[slot])?.id||candidates[0]?.id||'');
      const update=()=>{const p=products.find(p=>p.id===select.value);img.src=p?.image||products[0].image;img.style.opacity=p?'1':'.2';saved[slot]=select.value;localStorage.setItem('atelier-outfit',JSON.stringify(saved));$('#ay-outfit-price').textContent=money(products.filter(p=>outfitIds().includes(p.id)).reduce((a,p)=>a+p.price,0));$('#ay-outfit-generate').disabled=!outfitIds().length;};
      select.addEventListener('change',update);wrap.append(lab,select);row.append(img,wrap);host.append(row);update();
    }
  }
  async function generateOutfit(){
    if(!active){dialog.showModal();return;}
    const button=$('#ay-outfit-generate');button.disabled=true;
    try{const job=await api('jobs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product_ids:outfitIds(),priority:true,view:'front'})});current=job.product;currentView='front';showOriginal=false;angleRequests.clear();await refresh();}
    catch(e){toast(e.message);}finally{button.disabled=false;}
  }
  function paint(){
    $('[data-profile-label]').textContent=active?'Dein Look ist aktiv':'Deine Anprobe';
    $('#ay-delete').hidden=!active;
    if($('#ay-try-label'))$('#ay-try-label').textContent=active?'Deine persönliche Ansicht':'An mir ansehen';
    for(const p of products){const done=jobFor(p.id);document.querySelectorAll('img[data-pid="'+p.id+'"]').forEach(img=>{const next=done?'/tryon/results/'+done.id:p.image;if(img.getAttribute('src')!==next)img.src=next;img.parentElement.querySelector('.ay-card-tag').textContent=done?'DEIN LOOK':p.category.toUpperCase();});}
    const hero=$('#ay-hero-image');if(hero&&products[0]){const done=jobFor(products[0].id);const src=done?'/tryon/results/'+done.id:products[0].image;if(hero.getAttribute('src')!==src)hero.src=src;}
    if(studio&&!current){if(originalURL)displayImage(originalURL);return;}
    if(!current)return;
    const done=jobFor(current,currentView), job=jobs.find(j=>j.product===current&&(j.view||'front')===currentView);
    const visual=$('.ay-product-visual');
    $('#ay-angles').hidden=!active;
    document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('selected',b.dataset.view===currentView));
    if(done){personalURL='/tryon/results/'+done.id;displayImage(showOriginal?originalURL:personalURL);$('#ay-image-state').textContent=showOriginal?'THE ORIGINAL':({front:'DEIN PERSÖNLICHER LOOK',side:'DEIN LOOK · SEITENANSICHT',back:'DEIN LOOK · RÜCKANSICHT'}[currentView]);$('#ay-compare').hidden=false;$('#ay-render-state').hidden=true;visual.classList.remove('is-generating');$('#ay-personal-note').textContent='Für dich generiert · '+Math.round(done.seconds)+' s · gespeichert für deine Sitzung';}
    else{personalURL='';if(!active)displayImage(originalURL);$('#ay-compare').hidden=true;$('#ay-image-state').textContent=active?'DEIN LOOK ENTSTEHT':'THE ORIGINAL';$('#ay-render-state').hidden=!active||job?.status==='failed';visual.classList.toggle('is-generating',active&&job?.status!=='failed');if(active&&job?.status==='failed')$('#ay-personal-note').textContent=job.error;else if(active)$('#ay-render-state span:last-child').textContent=job?.status==='running'?'Ein bisschen Magie. Dein Look entsteht …':'Dein Look wird vorbereitet …';}
    if(active&&jobFor(current))requestAngles();
  }

  async function refresh(){const s=await api('session');active=s.active;jobs=s.jobs||[];paint();}
  async function queue(){
    if(studio){await generateOutfit();return;}
    const ordered=[...products].sort((a,b)=>(a.id===current?-1:b.id===current?1:0));
    for(const p of ordered)await api('jobs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product_id:p.id,priority:p.id===current})});
    await refresh();
  }
  document.querySelectorAll('[data-upload-open]').forEach(b=>b.addEventListener('click',()=>dialog.showModal()));
  $('.ay-close').addEventListener('click',()=>dialog.close());
  $('#ay-file').addEventListener('change',()=>{const file=$('#ay-file').files[0];if(!file)return;if(previewURL)URL.revokeObjectURL(previewURL);previewURL=URL.createObjectURL(file);$('#ay-preview').src=previewURL;$('#ay-preview').hidden=false;$('#ay-start').disabled=false;$('#ay-upload-error').textContent='';});
  $('#ay-start').addEventListener('click',async()=>{
    const file=$('#ay-file').files[0];if(!file)return;
    $('#ay-start').disabled=true;$('#ay-upload-error').textContent='';
    try{const form=new FormData();form.append('photo',file);await api('session',{method:'POST',body:form});active=true;jobs=[];showOriginal=false;currentView='front';angleRequests.clear();if(studio){current='';originalURL='/tryon/photo';}paint();dialog.close();toast('Dein Foto ist bereit. Wir erstellen deine persönlichen Looks.');await queue();}
    catch(e){$('#ay-upload-error').textContent=e.message;toast(e.message);}finally{$('#ay-start').disabled=false;}
  });
  $('#ay-delete').addEventListener('click',async()=>{try{await api('session',{method:'DELETE'});active=false;jobs=[];showOriginal=false;currentView='front';angleRequests.clear();if(studio){current='';originalURL=products[0].image;}$('#ay-file').value='';$('#ay-preview').hidden=true;$('#ay-start').disabled=true;paint();dialog.close();toast('Dein Foto und deine Looks wurden gelöscht.');}catch(e){toast(e.message);}});
  $('#ay-compare')?.addEventListener('click',()=>{showOriginal=!showOriginal;$('#ay-compare').textContent=showOriginal?'Meinen Look ansehen ↔':'Original ansehen ↔';paint();});
  document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',async()=>{currentView=b.dataset.view;showOriginal=false;paint();if(!jobFor(current,currentView)){try{await api('jobs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({product_id:current,view:currentView,priority:true})});await refresh();}catch(e){toast(e.message);}}}));
  document.querySelectorAll('[data-filter]').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('[data-filter]').forEach(x=>x.classList.toggle('active',x===b));draw(b.dataset.filter);}));
  document.querySelectorAll('.ay-sizes button').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('.ay-sizes button').forEach(x=>x.classList.toggle('selected',x===b));}));
  (async()=>{try{products=await api('catalog');originalURL=products.find(p=>p.id===current)?.image||$('#ay-main-image')?.getAttribute('src');if(studio){outfitSelectors();$('#ay-outfit-generate').addEventListener('click',generateOutfit);}draw();await refresh();if(studio){originalURL=active?'/tryon/photo':products[0].image;displayImage(originalURL);}if(active)await queue();setInterval(()=>{if(active)refresh().catch(()=>{});},2000);}catch(e){toast(e.message);}})();
})();
