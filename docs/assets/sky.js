// Spatium Flow — calm, professional starfield + scroll reveal
// Quiet field of faint stars, very slow drift, gentle twinkle. No streaks, no green.
(function(){
  const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const cv = document.getElementById('sky'); if(!cv) return;
  const ctx = cv.getContext('2d');
  let w,h,dpr,stars=[];
  function size(){
    dpr=Math.min(window.devicePixelRatio||1,2);
    w=cv.width=innerWidth*dpr; h=cv.height=innerHeight*dpr;
    cv.style.width=innerWidth+'px'; cv.style.height=innerHeight+'px';
    // far fewer stars than before — quiet, not busy
    const n=Math.round((innerWidth*innerHeight)/26000);
    stars=Array.from({length:n},()=>{
      const z=Math.random();
      return {x:Math.random()*w,y:Math.random()*h,z:z,
        r:(z*0.9+0.35)*dpr,                 // small, restrained sizes
        tw:Math.random()*Math.PI*2,
        tws:0.15+Math.random()*0.4,         // slow, subtle twinkle
        vx:(z*0.022+0.004)*dpr,             // barely-there drift
        warm:Math.random()<0.07};           // a rare faint warm star, no green
    });
  }
  function draw(t){
    ctx.clearRect(0,0,w,h);
    for(const s of stars){
      if(!reduce){s.x-=s.vx; if(s.x<-2)s.x=w+2;}
      const tw=reduce?0.6:(0.45+0.3*(0.5+0.5*Math.sin(t*0.001*s.tws+s.tw)));
      const a=tw*(0.30+s.z*0.45);           // dimmer overall
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
// scroll reveal
(function(){
  const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const els = document.querySelectorAll('.reveal');
  if(reduce){ els.forEach(el=>el.classList.add('in')); return; }
  const io=new IntersectionObserver((es)=>{es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);}});},{threshold:.12});
  els.forEach(el=>io.observe(el));
})();
