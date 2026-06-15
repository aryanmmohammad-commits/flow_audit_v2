// Spatium Flow — quiet night-sky field. Static stars, gentle twinkle only. No drift, no streaks.
(function(){
  const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const cv = document.getElementById('sky'); if(!cv) return;
  const ctx = cv.getContext('2d');
  let w,h,dpr,stars=[];
  function size(){
    dpr=Math.min(window.devicePixelRatio||1,2);
    w=cv.width=innerWidth*dpr; h=cv.height=innerHeight*dpr;
    cv.style.width=innerWidth+'px'; cv.style.height=innerHeight+'px';
    const n=Math.round((innerWidth*innerHeight)/30000);   // sparse, calm
    stars=Array.from({length:n},()=>{
      const z=Math.random();
      return {x:Math.random()*w,y:Math.random()*h,
        r:(z*0.8+0.35)*dpr,
        base:0.22+z*0.4,
        tw:Math.random()*Math.PI*2,
        tws:0.12+Math.random()*0.3,          // very slow twinkle
        warm:Math.random()<0.06};            // a rare faint warm star
    });
  }
  function draw(t){
    ctx.clearRect(0,0,w,h);
    for(const s of stars){
      // stars do NOT move; only a gentle brightness twinkle
      const tw = reduce ? 0.6 : (s.base + 0.18*Math.sin(t*0.001*s.tws + s.tw));
      const a = Math.max(0.06, tw);
      ctx.beginPath(); ctx.arc(s.x,s.y,s.r,0,6.2832);
      ctx.fillStyle=(s.warm?'rgba(255,196,140,':'rgba(216,226,242,')+a+')';
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
