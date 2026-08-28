const q=(s,p=document)=>p.querySelector(s), qa=(s,p=document)=>[...p.querySelectorAll(s)];
q('.menu')?.addEventListener('click',()=>{const n=q('nav');n.style.display=n.style.display==='flex'?'none':'flex';n.style.position='absolute';n.style.top='76px';n.style.left='0';n.style.right='0';n.style.background='#090909';n.style.padding='22px';n.style.flexDirection='column';n.style.borderBottom='1px solid #292929';});

async function shareUrl(button,title,url){
  if(navigator.share){try{await navigator.share({title,url});return}catch(e){}}
  try{await navigator.clipboard.writeText(url);button.textContent='Copied ✓';setTimeout(()=>button.textContent=button.dataset.original||'Share',1600)}catch(e){}
}
qa('[data-share]').forEach(b=>{b.dataset.original=b.textContent;b.addEventListener('click',()=>shareUrl(b,b.dataset.title||document.title,b.dataset.share||location.href));});

qa('[data-embed]').forEach(el=>el.addEventListener('click',()=>{const id=el.dataset.embed;el.innerHTML='<iframe loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen src="https://www.youtube-nocookie.com/embed/'+id+'?autoplay=1"></iframe>';}));

qa('[data-take-panel]').forEach(panel=>{
  const vid=panel.dataset.video, key='bb_take_'+vid, result=q('[data-take-result]',panel), buttons=qa('[data-take]',panel);
  function render(val){buttons.forEach(b=>b.classList.toggle('selected',b.dataset.take===val));result.hidden=false;result.textContent=val==='funny'?'Your take: 😂 Funny. Share it or challenge the ranking.':'Your take: 😐 Nope. Think another clip deserves the spot? Challenge it.';}
  const old=localStorage.getItem(key); if(old) render(old);
  buttons.forEach(b=>b.addEventListener('click',()=>{localStorage.setItem(key,b.dataset.take);render(b.dataset.take);}));
  q('[data-share-take]')?.addEventListener('click',e=>{
    const val=localStorage.getItem(key); if(val){e.currentTarget.dataset.title=(val==='funny'?'😂 I voted this funny on BingeBuzz: ':'😐 I voted nope on BingeBuzz: ')+panel.dataset.title;}
  });
});

function wireBattle(root=document){
  qa('[data-battle-once]',root).forEach(battle=>{
    if(battle.dataset.wired)return; battle.dataset.wired='1';
    const votes=qa('[data-battle-vote]',battle), result=battle.nextElementSibling?.matches('[data-battle-result]')?battle.nextElementSibling:q('[data-battle-result]',battle.parentElement||document);
    votes.forEach(btn=>btn.addEventListener('click',()=>{
      votes.forEach(x=>x.classList.toggle('selected',x===btn));
      const id=btn.dataset.battleVote; localStorage.setItem('bb_battle_last',id);
      const total=Number(localStorage.getItem('bb_battle_count')||0)+1; localStorage.setItem('bb_battle_count',String(total));
      const counter=q('[data-battle-count]'); if(counter)counter.textContent=total;
      if(result){result.hidden=false;result.textContent='Your pick is locked on this device. Keep judging to build your BingeBuzz taste record.';}
    }));
  });
}
wireBattle();
const counter=q('[data-battle-count]'); if(counter)counter.textContent=localStorage.getItem('bb_battle_count')||'0';

const poolNode=q('#battle-pool'), arena=q('#battle-arena');
if(poolNode&&arena){
  let pool=[];try{pool=JSON.parse(poolNode.textContent)}catch(e){}
  let cursor=0;
  function battleCard(v){return `<div class="battle-card" data-id="${v.video_id}"><a class="battle-thumb" href="/videos/${v.video_id}/"><img src="${v.thumbnail}" alt=""><span>#${v.rank||'—'}</span></a><div class="battle-body"><div class="kicker">Buzz ${Math.round(v.buzz_score||0)}</div><h3>${String(v.title||'').replace(/[&<>"']/g,s=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[s]))}</h3><p>${String(v.creator||'').replace(/[&<>"']/g,s=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[s]))}</p><button class="vote" data-battle-vote="${v.video_id}">😂 This one wins</button></div></div>`}
  function nextBattle(){if(pool.length<2)return;cursor=(cursor+2)%pool.length;const a=pool[cursor],b=pool[(cursor+1)%pool.length];arena.innerHTML=`<div class="battle" data-battle-once>${battleCard(a)}<div class="vs">VS</div>${battleCard(b)}</div><div class="battle-result" data-battle-result hidden></div>`;wireBattle(arena);arena.scrollIntoView({behavior:'smooth',block:'center'});}
  q('[data-next-battle]')?.addEventListener('click',nextBattle);
}
