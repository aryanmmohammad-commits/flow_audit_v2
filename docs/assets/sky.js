// Spatium Flow — calm night sky: slow, gentle drift + soft twinkle. No fast stars, no streaks.
(function(){
  const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const cv = document.getElementById('sky'); if(!cv) return;
  const ctx = cv.getContext('2d');
  let w,h,dpr,stars=[];
  function size(){
    dpr=Math.min(window.devicePixelRatio||1,2);
    w=cv.width=innerWidth*dpr; h=cv.height=innerHeight*dpr;
    cv.style.width=innerWidth+'px'; cv.style.height=innerHeight+'px';
    const n=Math.round((innerWidth*innerHeight)/15000);   // gentle density
    stars=Array.from({length:n},()=>{
      const z=Math.random();
      return {x:Math.random()*w,y:Math.random()*h,z:z,
        r:(z*1.0+0.4)*dpr, base:0.3+z*0.45,
        tw:Math.random()*Math.PI*2, tws:0.18+Math.random()*0.5,
        vx:(z*0.035+0.012)*dpr,        // calm, slow drift — no fast stars
        warm:Math.random()<0.07};
    });
  }
  function draw(t){
    ctx.clearRect(0,0,w,h);
    for(const s of stars){
      if(!reduce){s.x-=s.vx; if(s.x<-2){s.x=w+2; s.y=Math.random()*h;}}
      const tw=reduce?0.7:(s.base*(0.72+0.28*Math.sin(t*0.001*s.tws+s.tw)));
      const a=Math.max(0.05,tw);
      ctx.beginPath(); ctx.arc(s.x,s.y,s.r,0,6.2832);
      ctx.fillStyle=(s.warm?'rgba(255,196,140,':'rgba(220,230,245,')+a+')';
      ctx.fill();
    }
    if(!reduce) requestAnimationFrame(draw);
  }
  size();
  if(reduce){draw(0);} else {requestAnimationFrame(draw);}
  let to; addEventListener('resize',()=>{clearTimeout(to);to=setTimeout(size,150)});
})();
(function(){
  const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const els = document.querySelectorAll('.reveal');
  if(reduce){ els.forEach(el=>el.classList.add('in')); return; }
  const io=new IntersectionObserver((es)=>{es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);}});},{threshold:.12});
  els.forEach(el=>io.observe(el));
})();
