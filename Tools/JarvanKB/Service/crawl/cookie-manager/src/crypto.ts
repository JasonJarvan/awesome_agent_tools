import CryptoJS from 'crypto-js';

export type CryptoType = 'legacy' | 'aes-128-cbc-fixed';

export interface CookieObject {
  name: string;
  value: string;
  domain?: string;
  path?: string;
  [k: string]: unknown;
}

export interface InnerPayload {
  cookie_data: Record<string, CookieObject[]>;
  local_storage_data?: Record<string, unknown>;
  update_time?: string;
}

const FIXED_IV = CryptoJS.enc.Hex.parse('0'.repeat(32)); // 16 zero bytes

export function deriveKey(uuid: string, password: string): string {
  return CryptoJS.MD5(uuid + '-' + password).toString().substring(0, 16);
}

export function cookieEncrypt(
  uuid: string,
  payload: InnerPayload,
  password: string,
  cryptoType: CryptoType = 'legacy',
): string {
  const theKey = deriveKey(uuid, password);
  const plaintext = JSON.stringify(payload);
  if (cryptoType === 'legacy') {
    return CryptoJS.AES.encrypt(plaintext, theKey).toString();
  }
  const key = CryptoJS.enc.Utf8.parse(theKey);
  const enc = CryptoJS.AES.encrypt(plaintext, key, {
    iv: FIXED_IV,
    mode: CryptoJS.mode.CBC,
    padding: CryptoJS.pad.Pkcs7,
  });
  return enc.ciphertext.toString(CryptoJS.enc.Base64);
}

export function cookieDecrypt(
  uuid: string,
  encrypted: string,
  password: string,
  cryptoType: CryptoType = 'legacy',
): InnerPayload {
  const theKey = deriveKey(uuid, password);
  let text: string;
  if (cryptoType === 'legacy') {
    text = CryptoJS.AES.decrypt(encrypted, theKey).toString(CryptoJS.enc.Utf8);
  } else {
    const key = CryptoJS.enc.Utf8.parse(theKey);
    text = CryptoJS.AES.decrypt(encrypted, key, {
      iv: FIXED_IV,
      mode: CryptoJS.mode.CBC,
      padding: CryptoJS.pad.Pkcs7,
    }).toString(CryptoJS.enc.Utf8);
  }
  if (!text) throw new Error('cookieDecrypt: empty result (wrong password or corrupt payload)');
  return JSON.parse(text) as InnerPayload;
}
