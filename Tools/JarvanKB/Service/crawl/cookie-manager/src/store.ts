import { mkdirSync, writeFileSync, readFileSync, existsSync, readdirSync } from 'node:fs';
import { join, basename } from 'node:path';
import type { CryptoType } from './crypto.js';

export interface StoredRecord {
  encrypted: string;
  crypto_type: CryptoType;
}

export interface StoredMeta {
  uuid: string;
  crypto_type: CryptoType;
}

export interface Store {
  save(uuid: string, record: StoredRecord): void;
  load(uuid: string): StoredRecord | null;
  list(): StoredMeta[];
}

export function createStore(dataDir: string): Store {
  mkdirSync(dataDir, { recursive: true });
  const fileFor = (uuid: string) => join(dataDir, basename(uuid) + '.json');

  return {
    save(uuid, record) {
      writeFileSync(fileFor(uuid), JSON.stringify(record));
    },
    load(uuid) {
      const f = fileFor(uuid);
      if (!existsSync(f)) return null;
      return JSON.parse(readFileSync(f, 'utf8')) as StoredRecord;
    },
    list() {
      if (!existsSync(dataDir)) return [];
      return readdirSync(dataDir)
        .filter((f) => f.endsWith('.json'))
        .map((f) => {
          const rec = JSON.parse(readFileSync(join(dataDir, f), 'utf8')) as StoredRecord;
          return { uuid: f.replace(/\.json$/, ''), crypto_type: rec.crypto_type };
        });
    },
  };
}
