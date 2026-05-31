import { createStore } from './store.js';
import { cookieDecrypt } from './crypto.js';
import { loadConfig, passwordFor, type Config } from './config.js';

type Printer = (s: string) => void;

function dataDir(cfg: Config): string { return cfg.server.data_dir; }

export function runCli(argv: string[], cfg: Config, print: Printer = console.log): number {
  const [cmd, ...rest] = argv;
  const store = createStore(dataDir(cfg));

  if (cmd === 'list') {
    for (const meta of store.list()) {
      const pw = passwordFor(cfg, meta.uuid);
      let domains = 0, updateTime = '?';
      if (pw) {
        const rec = store.load(meta.uuid)!;
        try {
          const p = cookieDecrypt(meta.uuid, rec.encrypted, pw, rec.crypto_type);
          domains = Object.keys(p.cookie_data ?? {}).length;
          updateTime = p.update_time ?? '?';
        } catch { /* keep defaults */ }
      }
      print(`${meta.uuid}\t${meta.crypto_type}\tdomains=${domains}\tupdated=${updateTime}`);
    }
    return 0;
  }

  if (cmd === 'show') {
    const domainArg = rest.find((a) => a.startsWith('domain='))?.slice('domain='.length);
    if (!domainArg) { print('usage: show domain=<x>'); return 2; }
    let best: { cookies: unknown; uuid: string } | null = null;
    for (const meta of store.list()) {
      const pw = passwordFor(cfg, meta.uuid);
      if (!pw) continue;
      const rec = store.load(meta.uuid)!;
      try {
        const p = cookieDecrypt(meta.uuid, rec.encrypted, pw, rec.crypto_type);
        if (p.cookie_data[domainArg]) best = { cookies: p.cookie_data[domainArg], uuid: meta.uuid };
      } catch { /* skip */ }
    }
    if (!best) { print(`no cookies for domain ${domainArg}`); return 1; }
    print(JSON.stringify(best.cookies, null, 2));
    return 0;
  }

  if (cmd === 'dump') {
    const onlyUuid = rest.find((a) => a.startsWith('--uuid='))?.slice('--uuid='.length);
    const result: Record<string, unknown> = {};
    for (const meta of store.list()) {
      if (onlyUuid && meta.uuid !== onlyUuid) continue;
      const pw = passwordFor(cfg, meta.uuid);
      if (!pw) continue;
      const rec = store.load(meta.uuid)!;
      try { result[meta.uuid] = cookieDecrypt(meta.uuid, rec.encrypted, pw, rec.crypto_type).cookie_data; } catch { /* skip */ }
    }
    print(JSON.stringify(result, null, 2));
    return 0;
  }

  print('usage: cookie-manager <list|show domain=<x>|dump [--uuid=<u>]>');
  return 2;
}

const invokedFile = process.argv[1] ?? '';
if (invokedFile.endsWith('cli.ts') || invokedFile.endsWith('cli.js')) {
  const cfgPath = process.env.COOKIE_MANAGER_CONFIG ?? 'config/cookie-manager.yaml';
  process.exit(runCli(process.argv.slice(2), loadConfig(cfgPath)));
}
