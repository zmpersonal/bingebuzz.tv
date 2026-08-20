
document.querySelector('.menu')?.addEventListener('click',()=>{
 const n=document.querySelector('nav');n.style.display=n.style.display==='flex'?'none':'flex';
 n.style.position='absolute';n.style.top='76px';n.style.left='0';n.style.right='0';
 n.style.background='#090909';n.style.padding='22px';n.style.flexDirection='column';n.style.borderBottom='1px solid #292929';
});
document.querySelectorAll('[data-share]').forEach(b=>b.addEventListener('click',async()=>{
 const u=b.dataset.share||location.href,t=b.dataset.title||document.title;
 if(navigator.share){try{await navigator.share({title:t,url:u});return}catch(e){}}
 await navigator.clipboard.writeText(u); b.textContent='Copied';
}));
document.querySelectorAll('[data-embed]').forEach(el=>el.addEventListener('click',()=>{
 const id=el.dataset.embed;el.innerHTML='<iframe loading="lazy" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen src="https://www.youtube-nocookie.com/embed/'+id+'?autoplay=1"></iframe>';
}));
document.querySelectorAll('.battle-card .vote').forEach(b=>b.addEventListener('click',()=>{
 localStorage.setItem('bb_vote_'+b.closest('.battle-card').dataset.id,'1');b.textContent='😂 Your pick';
}));
