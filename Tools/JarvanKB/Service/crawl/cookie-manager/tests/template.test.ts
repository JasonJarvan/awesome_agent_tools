import { describe, it, expect } from 'vitest';
import { interpolate, matchHook, type HookContext } from '../src/hooks/template.js';

const ctx: HookContext = {
  uuid: 'u1', domain: '.zhihu.com', cookie_json: '[{"name":"a"}]',
  encrypted: 'BLOB', crypto_type: 'legacy', update_time: 'T', ts: '2026-05-31T00:00:00Z',
};

describe('interpolate', () => {
  it('substitutes known vars', () => {
    expect(interpolate('u={{uuid}} d={{domain}}', ctx)).toBe('u=u1 d=.zhihu.com');
  });
  it('injects raw json for cookie_json (no quotes added)', () => {
    expect(interpolate('{"c":{{cookie_json}}}', ctx)).toBe('{"c":[{"name":"a"}]}');
  });
  it('resolves unknown vars to empty string', () => {
    expect(interpolate('x={{nope}}', ctx)).toBe('x=');
  });
});

describe('matchHook', () => {
  it('matches uuid glob "*"', () => {
    expect(matchHook({ uuid: '*' }, ctx, ['.zhihu.com'])).toBe(true);
  });
  it('matches exact uuid', () => {
    expect(matchHook({ uuid: 'u1' }, ctx, ['.zhihu.com'])).toBe(true);
    expect(matchHook({ uuid: 'other' }, ctx, ['.zhihu.com'])).toBe(false);
  });
  it('matches when domain present in the cookie domains', () => {
    expect(matchHook({ uuid: '*', domain: '.zhihu.com' }, ctx, ['.zhihu.com', '.bilibili.com'])).toBe(true);
    expect(matchHook({ uuid: '*', domain: '.weibo.com' }, ctx, ['.zhihu.com'])).toBe(false);
  });
  it('matches any update when no domain filter', () => {
    expect(matchHook({ uuid: '*' }, ctx, [])).toBe(true);
  });
});
