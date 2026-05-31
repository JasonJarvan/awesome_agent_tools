import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mkdtempSync, rmSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createStore } from '../src/store.js';

let dir: string;
beforeEach(() => { dir = mkdtempSync(join(tmpdir(), 'cm-store-')); });
afterEach(() => { rmSync(dir, { recursive: true, force: true }); });

describe('store', () => {
  it('saves and loads a record', () => {
    const store = createStore(dir);
    store.save('uuid-1', { encrypted: 'BLOB', crypto_type: 'legacy' });
    expect(store.load('uuid-1')).toEqual({ encrypted: 'BLOB', crypto_type: 'legacy' });
  });

  it('returns null for a missing uuid', () => {
    expect(createStore(dir).load('nope')).toBeNull();
  });

  it('lists stored uuids with metadata', () => {
    const store = createStore(dir);
    store.save('a', { encrypted: 'X', crypto_type: 'legacy' });
    store.save('b', { encrypted: 'Y', crypto_type: 'aes-128-cbc-fixed' });
    const ids = store.list().map((m) => m.uuid).sort();
    expect(ids).toEqual(['a', 'b']);
  });

  it('neutralizes path traversal in uuid', () => {
    const store = createStore(dir);
    store.save('../evil', { encrypted: 'X', crypto_type: 'legacy' });
    expect(existsSync(join(dir, 'evil.json'))).toBe(true);
    expect(existsSync(join(dir, '..', 'evil.json'))).toBe(false);
  });
});
