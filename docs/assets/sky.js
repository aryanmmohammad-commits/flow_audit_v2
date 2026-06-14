// Spatium Flow — shared starfield (white/amber/green stars + shooting light-paths) + scroll reveal
(function(){
  const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const cv = document.getElementById('sky'); if(!cv) return;
  const ctx = cv.getContext('2d');
  let w,h,dpr,stars=[],shoot=[],lastShoot=0;
  const COL={white:'rgba(234,242,255,',warm:'rgba(255,184,105,',green:'rgba(150,232,172,'};
  function pick(){const r=Math.random();return r<0.10?'warm':(r<0.19?'green':'white');}
  function size(){
    dpr=Math.min(window.devicePixelRatio||1,2);
    w=cv.width=innerWidth*dpr; h=cv.height=innerHeight*dpr;
    cv.style.width=innerWidth+'px'; cv.style.height=innerHeight+'px';
    const n=Math.round((innerWidth*innerHeight)/8000);
    stars=Array.from({length:n},()=>{
      const z=Math.random();
      return {x:Math.random()*w,y:Math.random()*h,z:z,
        r:(Math.pow(z,1.5)*2.0+0.25)*dpr,
        tw:Math.random()*Math.PI*2, tws:0.4+Math.random()*1.8,
        vx:(Math.pow(z,2)*0.24+0.01)*dpr,
        c:pick()};
    });
  }
  function spawnShoot(){
    const r=Math.random();
    const col = r<0.5?'green':(r<0.72?'warm':'white');
    const dir = Math.random()<0.5?1:-1;
    const ang = (0.18+Math.random()*0.34);
    const sp = (5.5+Math.random()*5)*dpr;
    shoot.push({x:Math.random()*w, y:Math.random()*h*0.55,
      vx:Math.cos(ang)*sp*dir, vy:Math.sin(ang)*sp+sp*0.35,
      life:0, max:55+Math.random()*45, col});
  }
  function draw(t){
    ctx.clearRect(0,0,w,h);
    for(const s of stars){
      if(!reduce){s.x-=s.vx; if(s.x<-2)s.x=w+2;}
      const tw=reduce?0.7:(0.4+0.5*(0.5+0.5*Math.sin(t*0.001*s.tws+s.tw)));
      const a=tw*(0.35+s.z*0.65);
      ctx.beginPath(); ctx.arc(s.x,s.y,s.r,0,6.2832);
      ctx.fillStyle=COL[s.c]+a+')';
      if(s.z>0.72){ctx.shadowBlur=6*dpr; ctx.shadowColor=COL[s.c]+'0.8)';} else ctx.shadowBlur=0;
      ctx.fill();
    }
    ctx.shadowBlur=0;
    if(!reduce){
      if(t-lastShoot > 2000+Math.random()*2800){lastShoot=t; spawnShoot();}
      for(let i=shoot.length-1;i>=0;i--){
        const p=shoot[i]; p.life++; p.x+=p.vx; p.y+=p.vy;
        const k=1-p.life/p.max; if(k<=0){shoot.splice(i,1);continue;}
        const tx=p.x-p.vx*6, ty=p.y-p.vy*6;
        const g=ctx.createLinearGradient(tx,ty,p.x,p.y); const b=COL[p.col];
        g.addColorStop(0,b+'0)'); g.addColorStop(1,b+(k*0.9)+')');
        ctx.strokeStyle=g; ctx.lineWidth=1.4*dpr; ctx.lineCap='round';
        ctx.beginPath(); ctx.moveTo(tx,ty); ctx.lineTo(p.x,p.y); ctx.stroke();
        ctx.beginPath(); ctx.arc(p.x,p.y,1.5*dpr,0,6.2832); ctx.fillStyle=b+k+')';
        ctx.shadowBlur=8*dpr; ctx.shadowColor=b+'0.9)'; ctx.fill(); ctx.shadowBlur=0;
      }
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
