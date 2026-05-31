import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mkdtempSync, rmSync, readFileSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { runExec, runWriteFile } from '../src/hooks/actions.js';
import type { HookContext } from '../src/hooks/template.js';

const ctx: HookContext = {
  uuid: 'u1', domain: '.zhihu.com', cookie_json: '[{"name":"a"}]',
  encrypted: 'BLOB', crypto_type: 'legacy', update_time: 'T', ts: 'TS',
};

let dir: string;
beforeEach(() => { dir = mkdtempSync(join(tmpdir(), 'cm-act-')); });
afterEach(() => { rmSync(dir, { recursive: true, force: true }); });

describe('runWriteFile', () => {
  it('renders template + path and writes the file', async () => {
    await runWriteFile(
      { action: 'write_file', path: join(dir, '{{uuid}}.json'), template: '{"c":{{cookie_json}}}' } as any,
      ctx,
    );
    const out = join(dir, 'u1.json');
    expect(existsSync(out)).toBe(true);
    expect(readFileSync(out, 'utf8')).toBe('{"c":[{"name":"a"}]}');
  });
});

describe('runExec', () => {
  it('runs the command with interpolated args + env and resolves on success', async () => {
    const outFile = join(dir, 'echoed.txt');
    const res = await runExec(
      { action: 'exec', command: 'sh', args: ['-c', `printf '%s' "$COOKIE_JSON" > ${outFile}`],
        env: { COOKIE_JSON: '{{cookie_json}}' }, timeout_ms: 5000 } as any,
      ctx,
    );
    expect(res.code).toBe(0);
    expect(readFileSync(outFile, 'utf8')).toBe('[{"name":"a"}]');
  });

  it('rejects/returns nonzero on a failing command', async () => {
    const res = await runExec(
      { action: 'exec', command: 'sh', args: ['-c', 'exit 3'], env: {}, timeout_ms: 5000 } as any,
      ctx,
    );
    expect(res.code).toBe(3);
  });
});
