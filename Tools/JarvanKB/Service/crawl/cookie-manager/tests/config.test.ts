import { describe, it, expect } from 'vitest';
import { ConfigSchema, parseConfig } from '../src/config.js';

const valid = {
  server: { host: '0.0.0.0', port: 48088, data_dir: './data', body_limit: '50mb' },
  accounts: [{ uuid: 'u1', password: 'p1' }],
  hooks: [
    { id: 'h1', on: 'cookie-update', match: { uuid: '*', domain: '.zhihu.com' },
      action: 'exec', command: '/bin/true', args: ['{{uuid}}'], timeout_ms: 1000 },
    { id: 'h2', on: 'cron', schedule: '*/15 * * * *', match: { uuid: '*' },
      action: 'write_file', path: './out/{{uuid}}.json', template: '{{cookie_json}}' },
  ],
};

describe('config', () => {
  it('parses a valid config and applies defaults', () => {
    const cfg = parseConfig(valid);
    expect(cfg.server.port).toBe(48088);
    expect(cfg.hooks).toHaveLength(2);
  });

  it('rejects a cron hook without schedule', () => {
    const bad = { ...valid, hooks: [{ id: 'x', on: 'cron', action: 'exec', command: 'x' }] };
    expect(() => parseConfig(bad)).toThrow();
  });

  it('rejects an exec hook without command', () => {
    const bad = { ...valid, hooks: [{ id: 'x', on: 'cookie-update', action: 'exec' }] };
    expect(() => parseConfig(bad)).toThrow();
  });

  it('rejects a write_file hook without path/template', () => {
    const bad = { ...valid, hooks: [{ id: 'x', on: 'cookie-update', action: 'write_file' }] };
    expect(() => parseConfig(bad)).toThrow();
  });

  it('exposes a zod schema', () => {
    expect(ConfigSchema.safeParse(valid).success).toBe(true);
  });
});
