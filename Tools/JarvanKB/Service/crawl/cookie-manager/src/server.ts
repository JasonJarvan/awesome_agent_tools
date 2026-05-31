import express, { type Express } from 'express';
import type { EventEmitter } from 'node:events';
import type { Store } from './store.js';
import type { CryptoType } from './crypto.js';

export interface ServerOptions { body_limit?: string; auth_token?: string; auth_header?: string; }

export function createServer(store: Store, bus: EventEmitter, opts: ServerOptions = {}): Express {
  const app = express();
  const limit = opts.body_limit ?? '50mb';

  // Optional shared-secret header auth. When auth_token is set, every request except
  // /health must carry the matching header (rejected BEFORE body parsing so unauthorized
  // large uploads are dropped cheaply). The extension sets it via its "request header" field.
  const authToken = opts.auth_token;
  if (authToken) {
    const headerName = (opts.auth_header ?? 'X-CookieCloud-Token').toLowerCase();
    app.use((req, res, next) => {
      if (req.path === '/health') { next(); return; }
      if (req.get(headerName) !== authToken) { res.status(401).send('Unauthorized'); return; }
      next();
    });
  }

  app.use(express.json({ limit }));
  app.use(express.urlencoded({ extended: true, limit }));

  app.get('/health', (_req, res) => { res.json({ status: 'ok' }); });

  app.post('/update', (req, res) => {
    const { uuid, encrypted } = req.body ?? {};
    const rawCryptoType = req.body?.crypto_type;
    if (rawCryptoType != null && rawCryptoType !== 'legacy' && rawCryptoType !== 'aes-128-cbc-fixed') {
      res.status(400).send('Bad Request'); return;
    }
    const crypto_type: CryptoType = (rawCryptoType as CryptoType) ?? 'legacy';
    if (!uuid || !encrypted) { res.status(400).send('Bad Request'); return; }
    try {
      store.save(uuid, { encrypted, crypto_type });
    } catch (err) {
      console.error('[server] store failed:', err);
      res.status(500).send('Internal Server Error');
      return;
    }
    res.json({ action: 'done' });
    setImmediate(() => bus.emit('cookie-update', { uuid, encrypted, crypto_type }));
  });

  const handleGet = (req: express.Request, res: express.Response) => {
    const rec = store.load(req.params.uuid);
    if (!rec) { res.status(404).send('Not Found'); return; }
    res.json(rec);
  };
  app.get('/get/:uuid', handleGet);
  app.post('/get/:uuid', handleGet);

  return app;
}
