(() => {
  'use strict';

  const config = JSON.parse(document.getElementById('blog-language').textContent);
  const supported = ['ja', 'en'];
  const storageKey = 'blog-language';
  const url = new URL(window.location.href);
  const requested = url.searchParams.get('lang');
  let saved;
  try {
    saved = window.localStorage.getItem(storageKey);
    if (supported.includes(requested)) {
      window.localStorage.setItem(storageKey, requested);
    } else if (requested === 'auto') {
      window.localStorage.removeItem(storageKey);
    }
  } catch {
    // Private browsing can disable storage. The URL still remembers a choice.
  }
  if (requested === 'auto') saved = null;

  const browserLanguage = (navigator.languages?.length ? navigator.languages : [navigator.language])
    .map((language) => String(language || '').toLowerCase().split(/[-_]/)[0])
    .find((language) => supported.includes(language)) || 'en';
  const preferred = supported.includes(requested) ? requested
    : supported.includes(saved) ? saved : browserLanguage;
  const target = config.pages[preferred];

  if (preferred !== config.language && target) {
    const destination = new URL(target, url);
    destination.search = url.search;
    destination.hash = url.hash;
    window.location.replace(destination.href);
    return;
  }

  document.addEventListener('DOMContentLoaded', () => {
    const choice = supported.includes(requested) ? requested : saved;
    // Keep an explicit choice on internal navigation even if storage is blocked.
    if (supported.includes(choice)) {
      document.querySelectorAll('a[href]').forEach((link) => {
        const destination = new URL(link.href, url);
        if (link.hasAttribute('data-language') || destination.origin !== url.origin
            || destination.searchParams.has('lang') || link.hasAttribute('download')
            || !(/\/$|\.html$/.test(destination.pathname))) return;
        destination.searchParams.set('lang', choice);
        link.href = destination.href;
      });
    }

    const updateLanguageLinks = () => {
      const current = new URL(window.location.href);
      document.querySelectorAll('a[data-language]').forEach((link) => {
        const destination = new URL(link.href, current);
        destination.search = current.search;
        destination.searchParams.set('lang', link.dataset.language);
        // Matching article anchors are shared; an index fallback has no anchor.
        destination.hash = link.dataset.translated === 'true' ? current.hash : '';
        link.href = destination.href;
      });
    };
    updateLanguageLinks();
    window.addEventListener('hashchange', updateLanguageLinks);
  });
})();
