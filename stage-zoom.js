(() => {
  const root = document.querySelector('.stages-zoom');
  if (!root) return;
  let previous = root.dataset.point;
  let timer;
  new MutationObserver(() => {
    const next = root.dataset.point;
    if (next === previous) return;
    clearTimeout(timer);
    root.classList.remove('is-docking');
    if (previous === '1' && next === '2') {
      root.classList.add('is-docking');
      timer = setTimeout(() => root.classList.remove('is-docking'), 1550);
    }
    previous = next;
  }).observe(root, {attributes: true, attributeFilter: ['data-point']});
})();
