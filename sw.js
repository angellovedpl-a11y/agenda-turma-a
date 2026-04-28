// Agenda Turma A — Service Worker para Web Push
// Versao 1.0 (2026-04-25)

const SW_VERSION = 'agenda-turma-a-sw-v1';

self.addEventListener('install', (e) => {
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(self.clients.claim());
});

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
