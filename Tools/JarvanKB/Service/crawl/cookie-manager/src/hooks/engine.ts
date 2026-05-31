import type { EventEmitter } from 'node:events';
import type { Config, HookConfig } from '../config.js';
import { passwordFor } from '../config.js';
import type { Store } from '../store.js';
import { cookieDecrypt } from '../crypto.js';
import { matchHook, type HookContext } from './template.js';
import { runExec, runWriteFile } from './actions.js';
import { scheduleCron, type CronHandle } from './triggers.js';

export interface CookieUpdateEvent { uuid: string; encrypted: string; crypto_type: 'legacy' | 'aes-128-cbc-fixed'; }

export interface Engine { start(): void; stop(): void; }

function nowIso(): string { return new Date().toISOString(); }

export function createEngine(cfg: Config, store: Store, bus: EventEmitter): Engine {
  const crons: CronHandle[] = [];

  async function runHook(hook: HookConfig, ctx: HookContext): Promise<void> {
    try {
      if (hook.action === 'exec') {
        const res = await runExec(hook, ctx);
        if (res.code !== 0) console.error(`[hook ${hook.id}] exec exited ${res.code}: ${res.stderr}`);
      } else {
        await runWriteFile(hook, ctx);
      }
    } catch (err) {
      console.error(`[hook ${hook.id}] failed:`, err);
    }
  }

  function buildContext(uuid: string, encrypted: string, cryptoType: 'legacy' | 'aes-128-cbc-fixed'): { ctx: HookContext; domains: string[] } | null {
    const pw = passwordFor(cfg, uuid);
    let domains: string[] = [];
    let cookieJson = '';
    if (pw) {
      try {
        const payload = cookieDecrypt(uuid, encrypted, pw, cryptoType);
        domains = Object.keys(payload.cookie_data ?? {});
        cookieJson = JSON.stringify(payload.cookie_data ?? {});
      } catch (err) {
        console.error(`[engine] decrypt failed for uuid=${uuid}:`, err);
      }
    } else {
      console.warn(`[engine] no password configured for uuid=${uuid}; domain-matched hooks will be skipped`);
    }
    const ctx: HookContext = {
      uuid, domain: '', cookie_json: cookieJson, encrypted, crypto_type: cryptoType,
      update_time: '', ts: nowIso(),
    };
    return { ctx, domains };
  }

  async function onCookieUpdate(evt: CookieUpdateEvent): Promise<void> {
    const built = buildContext(evt.uuid, evt.encrypted, evt.crypto_type);
    if (!built) return;
    for (const hook of cfg.hooks) {
      if (hook.on !== 'cookie-update') continue;
      const domain = hook.match.domain;
      if (!matchHook(hook.match, built.ctx, built.domains)) continue;
      const ctx = { ...built.ctx, domain: domain ?? (built.domains[0] ?? '') };
      if (domain && built.domains.includes(domain)) {
        const pw = passwordFor(cfg, evt.uuid);
        if (pw) {
          const payload = cookieDecrypt(evt.uuid, evt.encrypted, pw, evt.crypto_type);
          ctx.cookie_json = JSON.stringify(payload.cookie_data[domain] ?? []);
        }
      }
      void runHook(hook, ctx);
    }
  }

  function runCronHook(hook: HookConfig): void {
    for (const meta of store.list()) {
      const rec = store.load(meta.uuid);
      if (!rec) continue;
      const built = buildContext(meta.uuid, rec.encrypted, rec.crypto_type);
      if (!built) continue;
      if (!matchHook(hook.match, built.ctx, built.domains)) continue;
      const domain = hook.match.domain;
      const ctx = { ...built.ctx, domain: domain ?? (built.domains[0] ?? '') };
      if (domain && built.domains.includes(domain)) {
        const pw = passwordFor(cfg, meta.uuid);
        if (pw) ctx.cookie_json = JSON.stringify(cookieDecrypt(meta.uuid, rec.encrypted, pw, rec.crypto_type).cookie_data[domain] ?? []);
      }
      void runHook(hook, ctx);
    }
  }

  return {
    start() {
      bus.on('cookie-update', (evt: CookieUpdateEvent) => void onCookieUpdate(evt));
      for (const hook of cfg.hooks) {
        if (hook.on === 'cron') crons.push(scheduleCron(hook.schedule, () => runCronHook(hook)));
      }
    },
    stop() {
      bus.removeAllListeners('cookie-update');
      crons.forEach((c) => c.stop());
      crons.length = 0;
    },
  };
}
