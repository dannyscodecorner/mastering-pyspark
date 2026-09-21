/* Growing input: one synchronized timeline for continuous water and arriving rows.
 * The five named records run once; ellipses continue beyond the visible excerpt.
 * The other diagrams keep their existing step controller.
 */
(() => {
  'use strict';
  const root = document.querySelector('[data-stream-root]');
  if (!root) return;
  const slide = root.closest('.slide');
  const controls = root.querySelector('[data-motion-controls]');
  const status = root.querySelector('[data-motion-status]');
  const progress = root.querySelector('[data-stream-progress]');
  const rows = [...root.querySelectorAll('[data-arrival]')];
  const arrivals = rows.map(row => Number(row.dataset.arrival) + 240);
  const playbackRate = 1.3;
  const button = action => controls.querySelector(`[data-motion-action="${action}"]`);
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  const params = new URLSearchParams(location.search);
  const staticOverride = params.get('motion') === 'static' || document.documentElement.dataset.motion === 'static';
  const stepParam = params.get('step');
  const testStep = params.get('motion') === 'step' && /^\d+$/.test(stepParam || '') && Number(stepParam) <= rows.length ? Number(stepParam) : null;
  let animations = [];
  let clock;
  let timer = 0;
  let playing = false;
  let entered = false;
  let savedTime = 0;

  const elapsed = () => Number(clock?.currentTime || 0);
  const rowCount = () => arrivals.filter(time => time <= elapsed() + 1).length;

  function update() {
    clearTimeout(timer);
    const count = rowCount();
    root.dataset.rowCount = String(count);
    root.dataset.frame = count === rows.length ? 'end' : count === 0 ? 'start' : 'step';
    progress.textContent = count === rows.length ? '5 rows shown · stream continues' : `${count} ${count === 1 ? 'row' : 'rows'} received`;
    rows.forEach((row, index) => row.setAttribute('aria-hidden', String(index >= count)));
    button('prev').disabled = elapsed() < 1;
    button('next').disabled = count === rows.length;
    button('play').setAttribute('aria-pressed', String(playing));
    button('pause').setAttribute('aria-pressed', String(!playing));
    if (playing && count < rows.length) timer = setTimeout(update, Math.max(16, (arrivals[count] - elapsed()) / playbackRate + 16));
  }

  function pause(announce = false) {
    if (!clock) return;
    if (clock.currentTime !== null) savedTime = elapsed();
    playing = false;
    animations.forEach(animation => animation.pause());
    root.dataset.playback = 'paused';
    update();
    if (announce) status.textContent = `Paused. ${rowCount()} illustrated rows received.`;
  }

  function seek(time) {
    pause();
    animations.forEach(animation => { animation.currentTime = time; });
    update();
  }

  function play(announce = false) {
    if (!clock || !slide.classList.contains('active') || document.hidden) return;
    const time = elapsed();
    playing = true;
    root.dataset.playback = 'playing';
    animations.forEach(animation => {
      animation.currentTime = time;
      // Completed finite animations must stay complete when resuming the stream.
      if (time < animation.effect.getComputedTiming().endTime) animation.play();
    });
    update();
    if (announce) status.textContent = 'Stream playing. New records arrive automatically.';
  }

  function action(name) {
    if (!clock) return;
    if (name === 'pause') pause(true);
    if (name === 'play') play(true);
    if (name === 'replay') { seek(0); play(); status.textContent = 'Restarted with an empty stream and input table.'; }
    if (name === 'prev' || name === 'next') {
      const next = Math.max(0, Math.min(rows.length, rowCount() + (name === 'next' ? 1 : -1)));
      seek(next ? arrivals[next - 1] : 0);
      status.textContent = next ? `${next} illustrated ${next === 1 ? 'row' : 'rows'} received. Paused.` : 'Empty stream and input table. Paused.';
    }
  }

  function initialize() {
    clearTimeout(timer);
    animations.forEach(animation => animation.cancel());
    animations = [];
    clock = undefined;
    playing = false;
    root.classList.remove('motion-ready');
    delete root.dataset.motionState;
    if (staticOverride || reduce.matches) {
      root.dataset.motionState = reduce.matches ? 'reduced' : 'static';
      root.dataset.frame = 'static';
      root.dataset.rowCount = String(rows.length);
      root.dataset.playback = 'static';
      controls.hidden = true;
      rows.forEach(row => row.removeAttribute('aria-hidden'));
      status.textContent = 'Complete static view: five illustrated rows. Playback unavailable.';
      return;
    }
    // Hidden presentation slides have no CSS animation objects yet.
    if (!slide.classList.contains('active')) {
      controls.hidden = true;
      root.dataset.playback = 'waiting';
      return;
    }
    // The source remains complete if enhancement fails.
    try {
      root.classList.add('motion-ready');
      animations = root.getAnimations({subtree:true});
      clock = animations.find(animation => animation.animationName === 'sug-current');
      if (!clock) throw new Error('Stream clock is unavailable');
      animations.forEach(animation => { animation.pause(); animation.playbackRate = playbackRate; animation.currentTime = 0; });
      controls.hidden = testStep !== null;
      seek(testStep === null ? savedTime : testStep ? arrivals[testStep - 1] : 0);
      if (testStep !== null) { root.dataset.motionState = 'test'; entered = true; }
      else if (slide.classList.contains('active') && !entered) { entered = true; play(); status.textContent = 'Stream playing. The input starts empty.'; }
    } catch (error) {
      animations.forEach(animation => animation.cancel());
      root.classList.remove('motion-ready');
      controls.hidden = true;
      rows.forEach(row => row.removeAttribute('aria-hidden'));
      console.error('Input-stream illustration remained static:', error);
    }
  }

  controls.addEventListener('click', event => {
    const target = event.target.closest('[data-motion-action]');
    if (target && !target.disabled) action(target.dataset.motionAction);
  });
  root.addEventListener('keydown', event => {
    if (!clock || testStep !== null) return;
    if (event.ctrlKey || event.metaKey || event.altKey || event.target.closest('input,textarea,select,a')) return;
    const actions = {ArrowLeft:'prev', ArrowRight:'next', r:'replay', R:'replay'};
    let name = actions[event.key];
    if (event.code === 'Space' && !event.target.closest('button')) name = playing ? 'pause' : 'play';
    if (event.key === 'Home' || event.key === 'End') {
      event.preventDefault(); event.stopPropagation();
      seek(event.key === 'Home' ? 0 : arrivals.at(-1));
      return;
    }
    if (name) { event.preventDefault(); event.stopPropagation(); action(name); }
  });
  new MutationObserver(() => {
    if (!slide.classList.contains('active')) {
      // app.js pauses before hiding the slide. display:none then cancels CSS
      // animations; recreate them at the saved position on the next visit.
      if (clock?.currentTime !== null && clock) savedTime = elapsed();
      clearTimeout(timer);
      playing = false;
      animations = [];
      clock = undefined;
      root.classList.remove('motion-ready');
      root.dataset.playback = 'paused';
      controls.hidden = true;
    } else if (!clock) initialize();
  }).observe(slide, {attributes:true, attributeFilter:['class']});
  document.addEventListener('visibilitychange', () => { if (document.hidden) pause(); });
  reduce.addEventListener('change', () => { if (clock) savedTime = elapsed(); initialize(); });
  initialize();
})();
