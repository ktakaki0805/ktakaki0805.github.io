const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const test = require('node:test');

const script = fs.readFileSync('assets/language.js', 'utf8');

function visit({ href = 'https://example.test/blog/', language = 'ja',
  pages = { ja: './', en: 'en/' }, languages = ['ja-JP'], saved = null,
  blocked = false, links = [] } = {}) {
  const redirects = [];
  const events = {};
  const location = { href, replace: (url) => redirects.push(url) };
  const storage = new Map(saved === null ? [] : [['blog-language', saved]]);
  const access = () => { if (blocked) throw new Error('Storage denied'); };
  vm.runInNewContext(script, {
    URL,
    navigator: { languages, language: languages[0] },
    window: {
      location,
      addEventListener: (name, fn) => { events[name] = fn; },
      localStorage: {
        getItem: (key) => { access(); return storage.get(key) || null; },
        setItem: (key, value) => { access(); storage.set(key, value); },
        removeItem: (key) => { access(); storage.delete(key); },
      },
    },
    document: {
      getElementById: () => ({ textContent: JSON.stringify({ language, pages }) }),
      addEventListener: (name, fn) => { events[name] = fn; },
      querySelectorAll: (selector) => selector === 'a[data-language]'
        ? links.filter((link) => link.dataset.language) : links,
    },
  });
  if (events.DOMContentLoaded) events.DOMContentLoaded();
  return { redirects, storage, changeHash: (hash) => {
    const current = new URL(location.href);
    current.hash = hash;
    location.href = current.href;
    events.hashchange?.();
  } };
}

test('regional language tags, preference order, and English fallback', () => {
  for (const languages of [['ja-JP'], ['ja-jp', 'en-US'], ['fr-FR', 'ja-JP', 'en']]) {
    assert.deepEqual(visit({ languages }).redirects, []);
  }
  for (const languages of [['en-GB', 'ja'], ['EN-us'], ['fr', 'de'], []]) {
    assert.deepEqual(visit({ languages }).redirects, ['https://example.test/blog/en/']);
  }
});

test('saved choice overrides browser language in both directions', () => {
  assert.deepEqual(visit({ languages: ['en'], saved: 'ja' }).redirects, []);
  assert.deepEqual(visit({ saved: 'en' }).redirects, ['https://example.test/blog/en/']);
  assert.deepEqual(visit({ saved: 'invalid' }).redirects, []);
  assert.deepEqual(visit({ href: 'https://example.test/blog/en/', language: 'en',
    pages: { ja: '../', en: './' } }).redirects, ['https://example.test/blog/']);
});

test('explicit choice wins, persists, and preserves query and fragment', () => {
  const result = visit({ href: 'https://example.test/blog/?utm_source=rss&lang=en#sec-intro', saved: 'ja' });
  assert.equal(result.storage.get('blog-language'), 'en');
  assert.deepEqual(result.redirects, ['https://example.test/blog/en/?utm_source=rss&lang=en#sec-intro']);
});

test('automatic mode clears preference and uses browser settings', () => {
  const result = visit({ href: 'https://example.test/blog/?lang=auto', saved: 'en' });
  assert.equal(result.storage.has('blog-language'), false);
  assert.deepEqual(result.redirects, []);
});

test('untranslated articles remain readable without redirects', () => {
  assert.deepEqual(visit({ languages: ['en'], pages: { ja: './' } }).redirects, []);
});

test('blocked storage still allows an explicit choice', () => {
  assert.deepEqual(visit({ blocked: true, href: 'https://example.test/blog/?lang=ja', languages: ['en'] }).redirects, []);
  assert.deepEqual(visit({ blocked: true, href: 'https://example.test/blog/?lang=en' }).redirects,
    ['https://example.test/blog/en/?lang=en']);
});

test('redirect target settles without a language loop', () => {
  const result = visit({ languages: ['en'] });
  assert.deepEqual(visit({ href: result.redirects[0], language: 'en',
    pages: { ja: '../', en: './' }, languages: ['en'] }).redirects, []);
});

function link(href, dataset = {}) {
  return { href, dataset,
    hasAttribute: (name) => name === 'data-language' && Boolean(dataset.language) };
}

test('internal navigation retains choice without modifying feeds or external links', () => {
  const links = [link('https://example.test/blog/en/tags/'),
    link('https://example.test/blog/index.xml'), link('https://other.test/'),
    link('https://example.test/blog/?lang=ja', { language: 'ja', translated: 'true' })];
  visit({ href: 'https://example.test/blog/en/?lang=en', language: 'en',
    blocked: true, links });
  assert.equal(links[0].href, 'https://example.test/blog/en/tags/?lang=en');
  assert.equal(links[1].href, 'https://example.test/blog/index.xml');
  assert.equal(links[2].href, 'https://other.test/');
  assert.equal(links[3].href, 'https://example.test/blog/?lang=ja');
});

test('switch preserves article anchor and query, but drops anchor on index fallback', () => {
  for (const translated of ['true', 'false']) {
    const switcher = link('https://example.test/blog/en/?lang=en', { language: 'en', translated });
    visit({ href: 'https://example.test/blog/?ref=feed#sec-model', links: [switcher] });
    assert.equal(switcher.href, 'https://example.test/blog/en/?ref=feed&lang=en'
      + (translated === 'true' ? '#sec-model' : ''));
  }
});

test('switch follows anchors selected after the page has loaded', () => {
  const switcher = link('https://example.test/blog/en/?lang=en', { language: 'en', translated: 'true' });
  const page = visit({ links: [switcher] });
  page.changeHash('#sec-conclusion');
  assert.equal(switcher.href, 'https://example.test/blog/en/?lang=en#sec-conclusion');
  page.changeHash('');
  assert.equal(switcher.href, 'https://example.test/blog/en/?lang=en');
});
