const CACHE_NAME = 'swarabharat-v2.4.0';
const OFFLINE_URL = '/offline.html';
const SUBMIT_ENDPOINTS = [
  'https://backend-swarabharat.onrender.com/submit',
  '/submit',
  'http://localhost:5000/submit'
];

const CRITICAL_ASSETS = [
  '/',
  '/index1.html',
  '/admin/admin.html',
  '/medical-center-admin.html',
  '/runtime-config.html',
  '/js/script.js',
  '/admin/admin.js',
  '/manifest.json',
  OFFLINE_URL
];

// Install - cache critical assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(CRITICAL_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate - clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch - network first, fallback to cache
self.addEventListener('fetch', (event) => {
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => {
        return caches.match(OFFLINE_URL);
      })
    );
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        const responseClone = response.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, responseClone);
        });
        return response;
      })
      .catch(() => {
        return caches.match(event.request);
      })
  );
});

// Background sync for offline submissions
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-reports') {
    event.waitUntil(syncReports());
  }
});

async function syncReports() {
  const reports = await getAllPendingReports();

  for (const report of reports) {
    const payload = report.payload || report;
    try {
      await submitToAnyEndpoint(payload);
      await deletePendingReport(report.id);
    } catch (e) {
      console.error('Sync failed:', e);
    }
  }
}

async function submitToAnyEndpoint(payload) {
  let lastError = null;
  for (const endpoint of SUBMIT_ENDPOINTS) {
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        return;
      }

      lastError = new Error(`HTTP ${response.status}`);
    } catch (e) {
      lastError = e;
    }
  }

  throw lastError || new Error('No submit endpoint succeeded');
}

async function getAllPendingReports() {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('pending-reports', 'readonly');
    const store = tx.objectStore('pending-reports');
    const request = store.getAll();

    request.onsuccess = () => {
      const result = request.result || [];
      db.close();
      resolve(result);
    };

    request.onerror = () => {
      db.close();
      reject(request.error || new Error('Failed to read queued reports'));
    };
  });
}

async function deletePendingReport(id) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction('pending-reports', 'readwrite');
    const store = tx.objectStore('pending-reports');
    store.delete(id);

    tx.oncomplete = () => {
      db.close();
      resolve();
    };
    tx.onerror = () => {
      db.close();
      reject(tx.error || new Error('Failed to delete queued report'));
    };
  });
}

function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('swarabharat-db', 1);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('pending-reports')) {
        db.createObjectStore('pending-reports', { keyPath: 'id', autoIncrement: true });
      }
    };
  });
}
