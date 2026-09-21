(() => {
  const root = document.querySelector('.workbench-walk');
  if (!root) return;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const staticView = new URLSearchParams(location.search).get('motion') === 'static';
  if (staticView) root.classList.add('workbench-static');
  let timers = [], animations = [];
  const later = (fn, delay) => timers.push(setTimeout(fn, delay));
  const allTasks = [...root.querySelectorAll('.wb-ticket')];
  const finalCue = root.querySelectorAll('[data-cue]')[4];
  const originalCue = finalCue.innerHTML;
  const reports = [...root.querySelectorAll('.wb-report')];
  const received = root.querySelector('.wb-received');
  function render() {
    timers.forEach(clearTimeout); timers = [];
    animations.forEach(a => a.cancel()); animations = [];
    allTasks.forEach(t => { t.classList.remove('wb-done'); t.querySelector('small').textContent = t.classList.contains('wb-task-b') ? 'Final aggregate' : 'Running'; });
    finalCue.innerHTML = originalCue;
    reports.forEach(r => r.hidden = true);
    root.classList.remove('wb-all-reported','wb-query-complete');
    received.textContent = '0 / 3 reported';
    const point = Number(root.dataset.point);
    const instant = reduced.matches || staticView;
    root.querySelectorAll('.wb-launch-state').forEach(e => e.textContent = point === 1 && !instant ? 'Starting executor…' : 'Executor ready');
    if (point === 1 && !instant) later(() => root.querySelectorAll('.wb-launch-state').forEach(e => e.textContent = 'Executor ready'), 1300);
    if (point !== 3 && point !== 4) return;
    const isFinal = point === 4;
    const tasks = [...root.querySelectorAll(isFinal ? '.wb-task-b' : '.wb-task-a')];
    received.textContent = `0 / ${tasks.length} reported`;
    root.querySelector('.wb-complete').textContent = isFinal ? 'Stage B complete' : 'Stage A complete';
    let count = 0;
    tasks.forEach((task, i) => {
      const finish = () => {
        task.classList.add('wb-done');
        task.querySelector('small').textContent = 'Completed';
        const report = reports[i];
        report.textContent = isFinal ? `Task ${i + 3} result` : `Task ${i} complete`;
        const arrive = () => {
          report.hidden = true;
          count += 1;
          received.textContent = `${count} / ${tasks.length} reported`;
          if (count === tasks.length) {
            root.classList.add('wb-all-reported');
            if (isFinal) {
              root.classList.add('wb-query-complete');
              finalCue.innerHTML = '<strong>Both Stage B tasks have finished. The totals are ready.</strong><span>books: 50 · games: 40 · music: 10. The executors remain available for more work.</span>';
            }
          }
        };
        if (instant) { arrive(); return; }
        later(() => {
          report.hidden = false;
          const x = (isFinal ? [491,919] : [491,649,919])[i];
          const a = report.animate([
            {transform:`translate(${x}px, 180px)`,opacity:0},
            {transform:`translate(${x}px, 310px)`,opacity:1,offset:.22},
            {transform:'translate(155px, 310px)',opacity:1,offset:.70},
            {transform:'translate(155px, 117px)',opacity:1}
          ], {duration:1900,fill:'forwards',easing:'ease-in-out'});
          animations.push(a);
          a.onfinish = arrive;
        }, 450);
      };
      if (instant) finish(); else later(finish, (isFinal ? 4700 : 650) + i * 2100);
    });
  }
  new MutationObserver(render).observe(root,{attributes:true,attributeFilter:['data-point']});
  reduced.addEventListener('change',render);
  render();
})();
