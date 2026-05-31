import { EventEmitter } from 'node:events';
import type { Server } from 'node:http';
import { loadConfig, type Config } from './config.js';
import { createStore } from './store.js';
import { createServer } from './server.js';
import { createEngine, type Engine } from './hooks/engine.js';

export interface RunningApp { server: Server; engine: Engine; stop(): Promise<void>; }

export async function startApp(cfg: Config): Promise<RunningApp> {
  const store = createStore(cfg.server.data_dir);
  const bus = new EventEmitter();
  const engine = createEngine(cfg, store, bus);
  engine.start();
  const app = createServer(store, bus, {
    body_limit: cfg.server.body_limit,
    auth_token: cfg.server.auth_token,
    auth_header: cfg.server.auth_header,
  });

  const server = await new Promise<Server>((resolve) => {
    const s = app.listen(cfg.server.port, cfg.server.host, () => resolve(s));
  });

  return {
    server,
    engine,
    stop: () =>
      new Promise<void>((resolve) => {
        engine.stop();
        server.close(() => resolve());
      }),
  };
}

const isMain = process.argv[1] && (process.argv[1].endsWith('index.ts') || process.argv[1].endsWith('index.js'));
if (isMain) {
  const cfgPath = process.env.COOKIE_MANAGER_CONFIG ?? 'config/cookie-manager.yaml';
  const cfg: Config = loadConfig(cfgPath);
  startApp(cfg).then((app) => {
    console.log(`cookie-manager listening on ${cfg.server.host}:${cfg.server.port}`);
    const shutdown = () => { void app.stop().then(() => process.exit(0)); };
    process.on('SIGTERM', shutdown);
    process.on('SIGINT', shutdown);
  });
}
