const CACHE_NAME = 'samplesplit-v1';
const OFFLINE_URL = '/static/offline.html';

const PRECACHE_URLS = [
    '/',
    '/static/offline.html',
    '/static/style.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js',
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => cache.addAll(PRECACHE_URLS))
            .then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name !== CACHE_NAME)
                    .map((name) => caches.delete(name))
            );
        }).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    if (request.method !== 'GET') return;
    if (url.pathname.startsWith('/static/uploads/')) return;
    if (url.pathname.startsWith('/admin/')) return;
    if (url.pathname.startsWith('/group/')) return;

    event.respondWith(
        (async () => {
            try {
                const networkResponse = await fetch(request);
                if (networkResponse.ok) {
                    const cache = await caches.open(CACHE_NAME);
                    if (request.method === 'GET' && networkResponse.status === 200) {
                        cache.put(request, networkResponse.clone());
                    }
                }
                return networkResponse;
            } catch (error) {
                const cachedResponse = await caches.match(request);
                if (cachedResponse) return cachedResponse;

                if (request.mode === 'navigate') {
                    const offlinePage = await caches.match(OFFLINE_URL);
                    if (offlinePage) return offlinePage;
                }

                throw error;
            }
        })()
    );
});
