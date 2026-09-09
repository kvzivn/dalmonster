import sizes from './asset-sizes.json';

// A fixed byte budget avoids the backwards jumps caused by sequentially
// discovered LoadingManager items. Images count when decoded; GLBs also report
// their download progress. Reserve the last 5% for scene/GPU preparation.
export function createLoadingProgress(element) {
  const total = Object.values(sizes).reduce((sum, size) => sum + size, 0);
  const loaded = new Map();
  let progress = 0;
  const paint = (value) => {
    progress = Math.max(progress, Math.min(100, value));
    element.style.setProperty('--progress', progress / 100);
    element.setAttribute('aria-valuenow', String(Math.floor(progress)));
  };
  const report = (url, bytes) => {
    if (!sizes[url]) return;
    loaded.set(url, Math.max(loaded.get(url) || 0, Math.min(bytes, sizes[url])));
    paint(95 * [...loaded.values()].reduce((sum, size) => sum + size, 0) / total);
  };
  return {
    track(loader) {
      const load = loader.loadAsync.bind(loader);
      loader.loadAsync = async (url) => {
        const result = await load(url, event => report(url, event.loaded));
        report(url, sizes[url]);
        return result;
      };
    },
    async json(url) {
      const response = await fetch(url);
      if (!response.ok) throw new Error(`Could not load ${url}: ${response.status}`);
      const value = await response.json();
      report(url, sizes[url]);
      return value;
    },
    finish() { paint(100); },
  };
}
