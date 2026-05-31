import CryptoJS from 'crypto-js';
const endpoint = process.env.ENDPOINT ?? 'http://127.0.0.1:8088';
const uuid = process.argv[2], password = process.argv[3];
const theKey = CryptoJS.MD5(uuid + '-' + password).toString().substring(0, 16);
const payload = { cookie_data: { '.zhihu.com': [{ name: 'z_c0', value: 'SMOKE', domain: '.zhihu.com' }] }, local_storage_data: {}, update_time: new Date().toISOString() };
const encrypted = CryptoJS.AES.encrypt(JSON.stringify(payload), theKey).toString();
const res = await fetch(`${endpoint}/update`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ uuid, encrypted }) });
console.log('status', res.status, await res.json());
