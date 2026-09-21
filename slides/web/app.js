(() => {
  'use strict';
  const slides = [...document.querySelectorAll('.slide')];
  const el = id => document.getElementById(id);
  let current = 0;
  function resize() { document.documentElement.style.setProperty('--scale', Math.max(.1, Math.min(innerWidth / 1440, (innerHeight - 54) / 810))); }
  function render(index, updateHash = true) {
    const previous = slides[current];
    previous.querySelector('[data-motion-action="pause"]')?.click();
    current = Math.max(0, Math.min(slides.length - 1, index));
    slides.forEach((s,i) => { s.classList.toggle('active', i === current); s.inert = i !== current; });
    if (previous !== slides[current] && previous.contains(document.activeElement)) document.activeElement.blur();
    const nextHistory = slides[current].dataset.historyIndex;
    const previousHistory = previous.dataset.historyIndex;
    if (nextHistory !== undefined && previousHistory !== undefined && previous !== slides[current]
        && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
      const track = slides[current].querySelector('.history-track');
      track.getAnimations().forEach(animation => animation.cancel());
      track.animate([
        {transform: `translateY(${234 - Number(previousHistory) * 218}px)`},
        {transform: `translateY(${234 - Number(nextHistory) * 218}px)`}
      ], {duration: 1000, easing: 'cubic-bezier(.4,0,.2,1)'});
    }

    el('position').textContent = `${current + 1} / ${slides.length}`;
    el('previous').disabled = current === 0;
    el('next').disabled = current === slides.length - 1;
    el('notes-text').textContent = slides[current].querySelector('.speaker-notes').textContent || 'No notes yet.';
    document.querySelectorAll('[data-slide-index]').forEach(b => b.setAttribute('aria-current', String(+b.dataset.slideIndex === current)));
    document.title = `${slides[current].getAttribute('aria-label')} — DCC`;
    if (updateHash) history.replaceState(null,'', '#' + slides[current].id);
  }
  function fromHash() { const aliases = {'#pyspark-functions':'#pyspark-cleaning','#pyspark-python-functions':'#pyspark-cleaning','#pyspark-rejections':'#pyspark-types','#pyspark-streaming-reader':'#pyspark-streaming-query','#pyspark-streaming-arrivals':'#pyspark-streaming-query','#execution-stages-zoom':'#execution-stages','#dataset-context':'#api-overview','#rdd-reuse':'#rdd-foundation','#data-views':'#dataframe-meaning','#mapreduce-jobs':'#hadoop-mapreduce','#rdd-why':'#rdd-foundation','#dataframe-why':'#dataframe-meaning','#history-apis':'#history-apache','#spark-foundations':'#pyspark-code','#python-spark':'#pyspark-code','#python-workers':'#classic-pyspark'}; const hash = aliases[location.hash] || location.hash; const found = slides.findIndex(s => '#' + s.id === hash); render(found < 0 ? 0 : found, false); }
  function showDialog(id) { if (!el(id).open) el(id).showModal(); }
  function toggleNotes() { el('notes-panel').hidden = !el('notes-panel').hidden; el('notes-toggle').setAttribute('aria-expanded', String(!el('notes-panel').hidden)); }
  async function fullscreen() {
    try { if(document.fullscreenElement) await document.exitFullscreen(); else await document.documentElement.requestFullscreen(); }
    catch { showDialog('help-dialog'); }
  }
  slides.forEach((s,i) => {
    const button = document.createElement('button');
    button.dataset.slideIndex = i;
    button.style.setProperty('--item-accent', getComputedStyle(s).getPropertyValue('--accent'));
    const number = document.createElement('small'); number.textContent = String(i+1).padStart(2,'0');
    button.append(number, document.createTextNode(s.getAttribute('aria-label').replace(/<br>/g,' ')));
    button.addEventListener('click', () => { el('overview').close(); render(i); });
    el('overview-list').append(button);
  });
  el('previous').onclick = () => render(current - 1);
  el('next').onclick = () => render(current + 1);
  el('contents').onclick = () => showDialog('overview');
  el('notes-toggle').onclick = toggleNotes;
  el('fullscreen').onclick = fullscreen;
  el('help').onclick = () => showDialog('help-dialog');
  document.querySelectorAll('[data-close]').forEach(b => b.onclick = () => el(b.dataset.close).close());
  el('unblank').onclick = () => { el('blank').hidden = true; };
  addEventListener('keydown', e => {
    if(e.metaKey || e.ctrlKey || e.altKey || e.target.closest('input,textarea,select,[contenteditable]')) return;
    if(!el('blank').hidden) { if(['b','B','Escape',' '].includes(e.key)){e.preventDefault();el('blank').hidden = true;} return; }
    if(document.querySelector('dialog[open]')) return;
    if(e.target.closest('[data-motion-root]') && ['ArrowLeft','ArrowRight',' ','Home','End','r','R'].includes(e.key)) return;
    if(e.target.closest('button,a') && [' ','Enter'].includes(e.key)) return;
    const actions = {ArrowRight:()=>render(current+1),PageDown:()=>render(current+1),' ':()=>render(current+1),ArrowLeft:()=>render(current-1),PageUp:()=>render(current-1),Home:()=>render(0),End:()=>render(slides.length-1),o:()=>showDialog('overview'),n:toggleNotes,f:fullscreen,'?':()=>showDialog('help-dialog'),b:()=>{slides[current].querySelector('[data-motion-action="pause"]')?.click();el('blank').hidden=false;},Escape:()=>{el('notes-panel').hidden=true;}};
    const action = actions[e.key] || actions[e.key.toLowerCase()];
    if(action){e.preventDefault();action();}
  });
  addEventListener('hashchange', fromHash);
  addEventListener('resize', resize);
  resize(); fromHash(); document.documentElement.classList.add('enhanced');
})();
