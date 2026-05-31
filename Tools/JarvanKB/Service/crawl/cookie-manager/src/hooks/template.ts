export interface HookContext {
  uuid: string;
  domain: string;
  cookie_json: string;
  encrypted: string;
  crypto_type: string;
  update_time: string;
  ts: string;
}

export interface HookMatch {
  uuid: string;
  domain?: string;
}

export function interpolate(template: string, ctx: HookContext): string {
  return template.replace(/\{\{(\w+)\}\}/g, (_, key: string) => {
    const v = (ctx as unknown as Record<string, unknown>)[key];
    return v === undefined || v === null ? '' : String(v);
  });
}

export function matchHook(match: HookMatch, ctx: HookContext, domains: string[]): boolean {
  if (match.uuid !== '*' && match.uuid !== ctx.uuid) return false;
  if (match.domain && !domains.includes(match.domain)) return false;
  return true;
}
