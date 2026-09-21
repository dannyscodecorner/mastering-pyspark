(() => {
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const staticView = new URLSearchParams(location.search).get('motion') === 'static';
  document.querySelectorAll('.boat-micro,.boat-whole').forEach(root => {
    const slide = root.closest('.slide');
    let animations = [], timers = [];
    function cancel() { animations.forEach(a => a.cancel()); timers.forEach(clearTimeout); animations=[];timers=[]; }
    const later = (fn, delay) => timers.push(setTimeout(fn, delay));
    function animate(el, frames, duration, delay=0) {
      if (reduced.matches || staticView) { Object.assign(el.style, frames[frames.length-1]); return; }
      const a=el.animate(frames,{duration,delay,easing:'cubic-bezier(.4,0,.2,1)',fill:'both'});
      animations.push(a);
    }
    function render() {
      cancel();
      if (!slide.classList.contains('active') && !staticView) return;
      const p=Number(root.dataset.point), instant=reduced.matches||staticView;
      if(root.classList.contains('boat-micro')) {
        const boat=root.querySelector('.record-barge');
        boat.style.transform='translateX(0px)';boat.style.opacity='1';
        if(p===1) animate(boat,[{transform:'translateX(0px)',opacity:1},{transform:'translateX(350px)',opacity:1}],1600);
        if(p===2) animate(boat,[{transform:'translateX(350px)',opacity:1},{transform:'translateX(350px)',opacity:1,offset:.4},{transform:'translateX(350px)',opacity:0}],1500);
        if(p===3) animate(boat,[{transform:'translateX(350px)',opacity:1},{transform:'translateX(470px)',opacity:1}],1500);
        return;
      }
      const boats=[...root.querySelectorAll('.record-barge')];
      const fromX=[420,210,0,315,105], toX=[1110,900,690,1005,795];
      const fromY=[85,85,85,185,185];
      const count=root.querySelector('.whole-count'), rule=root.querySelector('.whole-rule');
      count.textContent='';
      rule.textContent=p<2?'Same five sales. One unique product lookup.':p===2?'INNER · keep matching pairs':'LEFT · keep all sales';
      let output=0,total=0;
      boats.forEach((boat,i)=>{
        boat.style.left=fromX[i]+'px';boat.style.top=fromY[i]+'px';
        boat.style.transform='translateX(0px)';boat.style.opacity='1';
        boat.style.clipPath='inset(0 0 0% 0)';
        boat.querySelector('.barge-category').style.opacity=p===1?'1':'0';
        boat.querySelector('.barge-category').style.visibility=p===1?'visible':'hidden';
        if(p<2)return;
        const unmatched=boat.dataset.sale==='s4', keep=p===3||!unmatched;
        const dx=toX[i]-fromX[i], station=555-fromX[i];
        const duration=keep?2300:3000;
        const frames=keep
          ? [{transform:'translateX(0px)',opacity:1},{transform:`translateX(${station}px)`,opacity:1,offset:.48},{transform:`translateX(${dx}px)`,opacity:1}]
          : [
              {transform:'translateX(0px)',clipPath:'inset(0 0 0% 0)',opacity:1},
              {transform:`translateX(${station}px)`,clipPath:'inset(0 0 0% 0)',opacity:1,offset:.36},
              {transform:`translateX(${station}px) rotate(-5deg)`,clipPath:'inset(0 0 0% 0)',opacity:1,offset:.48},
              {transform:`translate(${station}px, 12px) rotate(10deg)`,clipPath:'inset(0 0 30% 0)',opacity:1,offset:.67},
              {transform:`translate(${station}px, 28px) rotate(17deg)`,clipPath:'inset(0 0 75% 0)',opacity:.85,offset:.86},
              {transform:`translate(${station}px, 40px) rotate(20deg)`,clipPath:'inset(0 0 100% 0)',opacity:0}
            ];
        animate(boat,frames,duration,i*800);
        const finished=()=>{
          if(keep){output++;total+=[25,40,15,10,10][i];boat.querySelector('.barge-category').style.opacity='1';boat.querySelector('.barge-category').style.visibility='visible';}
          count.textContent=`${output} rows · total ${total}`;
          if(i===4) rule.textContent='Same inputs. Different rules for unmatched rows.';
        };
        if(instant)finished();else later(finished,duration+i*800);
      });
    }
    new MutationObserver(render).observe(root,{attributes:true,attributeFilter:['data-point']});
    new MutationObserver(render).observe(slide,{attributes:true,attributeFilter:['class']});
    reduced.addEventListener('change',render);
    render();
  });
})();
// Make the skew long tail visible: light channels drain while the hot key remains.
(() => {
  const root=document.querySelector('.join-skew');if(!root)return;
  const slide=root.closest('.slide'), reduced=matchMedia('(prefers-reduced-motion: reduce)');
  const status=document.createElement('p');status.className='skew-live-status';status.setAttribute('aria-live','polite');
  root.querySelector('.join-skew-story .j1').append(status);
  let animations=[],timers=[];
  function render(){
    animations.forEach(a=>a.cancel());timers.forEach(clearTimeout);animations=[];timers=[];status.textContent='';
    if(root.dataset.point!=='1'||!slide.classList.contains('active'))return;
    if(reduced.matches){status.textContent='The light partitions finish first; the hot-key task takes longer.';return;}
    root.querySelectorAll('.waterways .cargo').forEach((g,i)=>{
      const r=g.querySelector('rect'),x=Number(r.getAttribute('x')),hot=Number(r.getAttribute('y'))<70;
      const delay=hot?(8-i)*800:(i-9)*170;
      animations.push(g.animate([{transform:'translateX(0px)',opacity:1},{transform:`translateX(${620-x}px)`,opacity:1,offset:.85},{transform:`translateX(${635-x}px)`,opacity:0}],{duration:1400,delay:Math.max(0,delay),fill:'both',easing:'linear'}));
    });
    timers.push(setTimeout(()=>status.textContent='P1–P3 have finished. The P0 task is still working.',2300));
    timers.push(setTimeout(()=>status.textContent='P0 finishes last. Only now can this stage complete.',7900));
  }
  new MutationObserver(render).observe(root,{attributes:true,attributeFilter:['data-point']});
  new MutationObserver(render).observe(slide,{attributes:true,attributeFilter:['class']});render();
})();
// Shuffle: show records taking their key's route before assembling each arrival group.
(() => {
  const root=document.querySelector('.join-shuffle'); if(!root)return;
  const slide=root.closest('.slide'), svg=root.querySelector('svg');
  const arrivals=root.querySelector('.river-arrivals');
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  const staticView=new URLSearchParams(location.search).get('motion')==='static';
  const ns='http://www.w3.org/2000/svg';
  const routes=[...svg.querySelectorAll('path.river')].map((path,i)=>{
    if(i<2)return path;
    const extended=document.createElementNS(ns,'path');
    extended.setAttribute('d',path.getAttribute('d')+` L1000 ${i===2?265:115}`);
    extended.setAttribute('fill','none');extended.setAttribute('stroke','none');extended.style.opacity='0';
    svg.append(extended);return extended;
  });
  const children=[...arrivals.children];
  const destinations=[0,1].map(i=>{
    const g=document.createElementNS(ns,'g');
    g.append(children[i*2],children[i*2+1]);arrivals.append(g);return g;
  });
  const packets=[
    ['B1 sales',0,0,0],['B1 books',3,500,0],
    ['G1 / M1 sales',2,1100,1],['G1 / X1 lookup',1,1600,1]
  ].map(([label,route,delay,dest],i)=>{
    const g=document.createElementNS(ns,'g');g.classList.add('shuffle-packet');
    const rect=document.createElementNS(ns,'rect');
    Object.entries({x:-92,y:-18,width:184,height:36,rx:7,fill:i%2?'#f6e5c4':'#deeff8',stroke:i%2?'#b08b4e':'#43899f','stroke-width':2}).forEach(([k,v])=>rect.setAttribute(k,v));
    const text=document.createElementNS(ns,'text');text.setAttribute('text-anchor','middle');text.setAttribute('y','7');text.setAttribute('class','shuffle-packet-label');text.textContent=label;
    g.append(rect,text);svg.append(g);g.style.opacity='0';
    return {g,path:routes[route],delay,dest};
  });
  let animations=[],timers=[];
  function render(){
    animations.forEach(a=>a.cancel());timers.forEach(clearTimeout);animations=[];timers=[];
    root.classList.remove('shuffle-routing');
    packets.forEach(({g})=>g.style.opacity='0');destinations.forEach(g=>g.style.opacity='1');
    if(root.dataset.point!=='2'||!slide.classList.contains('active')||reduced.matches||staticView)return;
    root.classList.add('shuffle-routing');destinations.forEach(g=>g.style.opacity='0');
    packets.forEach(({g,path,delay})=>{
      const length=path.getTotalLength();
      const samples=Array.from({length:121},(_,i)=>path.getPointAtLength(length*i/120));
      const start=samples.findIndex(p=>p.x>=350), end=samples.findIndex(p=>p.x>=970);
      const frames=samples.slice(start,end+1).map((p,i,a)=>({transform:`translate(${p.x}px,${p.y}px)`,opacity:i===a.length-1?0:1,offset:i/(a.length-1)}));
      animations.push(g.animate(frames,{duration:2400,delay,fill:'both',easing:'linear'}));
    });
    [2900,4000].forEach((delay,i)=>timers.push(setTimeout(()=>{
      destinations[i].style.opacity='1';
      animations.push(destinations[i].animate([{opacity:0,transform:'translateX(-12px)'},{opacity:1,transform:'translateX(0)'}],{duration:400,fill:'both'}));
      if(i===1)root.classList.remove('shuffle-routing');
    },delay)));
  }
  new MutationObserver(render).observe(root,{attributes:true,attributeFilter:['data-point']});
  new MutationObserver(render).observe(slide,{attributes:true,attributeFilter:['class']});
  reduced.addEventListener('change',render);render();
})();
