// Agenda Turma A — Service Worker
// v2 (2026-08-17): + app shell cache (splash instantanea, sem esperar o Render acordar)
// v1 (2026-04-25): Web Push

const SW_VERSION = 'agenda-turma-a-sw-v2';
const SHELL_CACHE = 'agenda-shell-v2';   // casca do app (index/splash) — navegacao
const ASSET_CACHE = 'agenda-assets-v2';  // css/js/imagens/manifest

// Casca minima pra pintar a splash e o app na hora, mesmo com o servidor dormindo.
// Falha em qualquer item nao aborta o install (allSettled).
const SHELL_URLS = [
  '/',
  '/static/style.css',
  '/static/app.js',
  '/manifest.webmanifest',
  '/vale_symbol_color.png?v=2',
  '/vale_symbol_white.png?v=2',
  '/icon.svg',
  '/icon-192-v2.png?v=3',
  '/icon-512-v2.png?v=3',
];

self.addEventListener('install', (e) => {
  e.waitUntil((async () => {
    const shell = await caches.open(SHELL_CACHE);
    const assets = await caches.open(ASSET_CACHE);
    // '/' vai pro SHELL_CACHE; o resto (assets) pro ASSET_CACHE.
    await Promise.allSettled([
      shell.add(new Request('/', { cache: 'reload' })),
      ...SHELL_URLS.filter((u) => u !== '/').map((u) =>
        assets.add(new Request(u, { cache: 'reload' }))
      ),
    ]);
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    // Limpa caches de versoes antigas
    const keys = await caches.keys();
    await Promise.all(
      keys
        .filter((k) => k !== SHELL_CACHE && k !== ASSET_CACHE)
        .map((k) => caches.delete(k))
    );
    await self.clients.claim();
  })());
});

// ---- Estrategias de fetch ----

// Navegacao (abrir o app pelo icone): casca-primeiro -> splash aparece na hora.
// Atualiza o index em segundo plano pra proxima abertura.
async function shellFirst(event) {
  const url = new URL(event.request.url);
  const cache = await caches.open(SHELL_CACHE);

  // Paginas separadas (termos, politica, etc): rede primeiro, cache so de reserva.
  // So a raiz do app usa casca-primeiro pra nao servir o app no lugar dessas paginas.
  if (url.pathname !== '/' && url.pathname !== '/index.html') {
    try {
      return await fetch(event.request);
    } catch (_) {
      return (await cache.match(event.request)) || cache.match('/');
    }
  }

  const cached = await cache.match('/');
  const network = fetch(event.request)
    .then((res) => {
      if (res && res.ok) cache.put('/', res.clone());
      return res;
    })
    .catch(() => null);

  if (cached) {
    event.waitUntil(network); // revalida sem travar o usuario
    return cached;
  }
  // Primeira abertura de todas (nada em cache ainda): depende da rede.
  const net = await network;
  return net || new Response('Offline', { status: 503, statusText: 'Offline' });
}

// Assets (css/js/imagens): serve do cache na hora e atualiza em segundo plano.
async function staleWhileRevalidate(event) {
  const cache = await caches.open(ASSET_CACHE);
  const cached = await cache.match(event.request);
  const network = fetch(event.request)
    .then((res) => {
      if (res && res.ok) cache.put(event.request, res.clone());
      return res;
    })
    .catch(() => cached);
  event.waitUntil(network.catch(() => {}));
  return cached || network;
}

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return; // POST/PUT/etc: deixa passar

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return; // fontes/CDN externos: rede
  if (url.pathname.startsWith('/api/')) return;     // API: SEMPRE rede (dados/login)
  if (url.pathname === '/manual_agenda_turma_a.pdf') return; // PDF grande: rede

  if (req.mode === 'navigate') {
    event.respondWith(shellFirst(event));
    return;
  }
  event.respondWith(staleWhileRevalidate(event));
});

// ---- Web Push (inalterado) ----

self.addEventListener('push', (event) => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (_) {
    data = { title: 'Agenda Turma A', body: event.data ? event.data.text() : 'Nova notificacao' };
  }

  const title = data.title || 'Agenda Turma A';
  const options = {
    body: data.body || '',
    icon: '/icon-192-v2.png?v=3',
    badge: '/icon-192-v2.png?v=3',
    tag: data.tag || 'agenda-turma',
    renotify: true,
    requireInteraction: false,
    vibrate: [200, 100, 200, 100, 200],
    data: {
      url: data.url || '/',
      kind: data.kind || 'generico'
    }
  };

  event.waitUntil(
    Promise.all([
      self.registration.showNotification(title, options),
      // Avisar todas as abas/janelas abertas para tocar a buzina e atualizar UI
      self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clients) => {
        clients.forEach((c) => {
          c.postMessage({ type: 'push', payload: data });
        });
      })
    ])
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || '/';

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clients) => {
      // Se ja existe uma janela aberta, foca e navega
      for (const c of clients) {
        if ('focus' in c) {
          c.postMessage({ type: 'notification_click', url: url });
          return c.focus();
        }
      }
      // Senao abre uma nova
      if (self.clients.openWindow) {
        return self.clients.openWindow(url);
      }
    })
  );
});
