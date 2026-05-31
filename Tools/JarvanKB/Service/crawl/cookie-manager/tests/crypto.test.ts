import { describe, it, expect } from 'vitest';
import crypto from 'node:crypto';
import CryptoJS from 'crypto-js';
import { deriveKey, cookieDecrypt, cookieEncrypt } from '../src/crypto.js';

const sample = {
  cookie_data: { '.zhihu.com': [{ name: 'z_c0', value: 'X', domain: '.zhihu.com' }] },
  local_storage_data: {},
  update_time: '2026-05-31T00:00:00Z',
};

// --- Independent OpenSSL oracle (node:crypto), DIFFERENT impl than crypto-js ---
function evpKDF(passphrase: string, salt: Buffer, keyLen: number, ivLen: number) {
  let data = Buffer.alloc(0);
  let prev = Buffer.alloc(0);
  while (data.length < keyLen + ivLen) {
    prev = crypto.createHash('md5').update(Buffer.concat([prev, Buffer.from(passphrase, 'utf8'), salt])).digest();
    data = Buffer.concat([data, prev]);
  }
  return { key: data.subarray(0, keyLen), iv: data.subarray(keyLen, keyLen + ivLen) };
}
function nodeDecryptLegacy(theKey: string, b64: string): string {
  const raw = Buffer.from(b64, 'base64');
  if (raw.subarray(0, 8).toString('utf8') !== 'Salted__') throw new Error('not Salted__');
  const salt = raw.subarray(8, 16);
  const ct = raw.subarray(16);
  const { key, iv } = evpKDF(theKey, salt, 32, 16);
  const d = crypto.createDecipheriv('aes-256-cbc', key, iv);
  return Buffer.concat([d.update(ct), d.final()]).toString('utf8');
}

describe('deriveKey', () => {
  it('is the first 16 hex chars of md5(uuid + "-" + password)', () => {
    expect(deriveKey('a', 'b')).toMatch(/^[0-9a-f]{16}$/);
    expect(deriveKey('u', 'pw')).toBe(CryptoJS.MD5('u-pw').toString().substring(0, 16));
  });
});

describe('round-trip legacy', () => {
  it('encrypts then decrypts back to the payload, with Salted__ envelope', () => {
    const enc = cookieEncrypt('u', sample, 'pw', 'legacy');
    expect(enc.startsWith('U2FsdGVkX1')).toBe(true); // base64 of "Salted__"
    expect(cookieDecrypt('u', enc, 'pw', 'legacy')).toEqual(sample);
  });
});

describe('round-trip aes-128-cbc-fixed', () => {
  it('encrypts then decrypts back to the payload, no Salted__ wrapper', () => {
    const enc = cookieEncrypt('u', sample, 'pw', 'aes-128-cbc-fixed');
    expect(enc.startsWith('U2FsdGVkX1')).toBe(false);
    expect(cookieDecrypt('u', enc, 'pw', 'aes-128-cbc-fixed')).toEqual(sample);
  });
});

describe('INDEPENDENT oracle: crypto-js legacy output decodes under node:crypto OpenSSL', () => {
  it('a crypto-js Salted__ blob decrypts via hand-rolled EVP_BytesToKey + node aes-256-cbc', () => {
    const theKey = deriveKey('u', 'pw');
    const enc = cookieEncrypt('u', sample, 'pw', 'legacy');
    const plain = nodeDecryptLegacy(theKey, enc);
    expect(JSON.parse(plain)).toEqual(sample);
  });
});

describe('decrypt failure', () => {
  it('throws on wrong password', () => {
    const enc = cookieEncrypt('u', sample, 'pw', 'legacy');
    expect(() => cookieDecrypt('u', enc, 'WRONG', 'legacy')).toThrow();
  });
});
