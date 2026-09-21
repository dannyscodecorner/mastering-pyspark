(() => {
  const staticView = new URLSearchParams(location.search).get('motion') === 'static';
  document.querySelectorAll('[data-lesson]').forEach(root => {
    const cues = [...root.querySelectorAll('[data-cue]')];
    const rail = [...root.querySelectorAll('.lesson-rail li')];
    let point = staticView ? cues.length - 1 : 0;
    function render(next) {
      point = Math.max(0,Math.min(cues.length-1,next));
      root.dataset.point = String(point);
      cues.forEach((cue,i) => cue.classList.toggle('active',i===point));
      rail.forEach((item,i) => { item.classList.toggle('past',i<point); if(i===point)item.setAttribute('aria-current','step');else item.removeAttribute('aria-current'); });
      root.querySelector('[data-lesson-prev]').disabled = point===0;
      root.querySelector('[data-lesson-next]').disabled = point===cues.length-1;
      root.querySelector('.lesson-position').textContent = `${point+1} / ${cues.length}`;
    }
    root.classList.add('live');
    root.classList.toggle('static-view',staticView);
    root.querySelector('[data-lesson-prev]').addEventListener('click',()=>render(point-1));
    root.querySelector('[data-lesson-next]').addEventListener('click',()=>render(point+1));
    root.querySelector('[data-lesson-reset]').addEventListener('click',()=>render(0));
    render(point);
  });
})();
