import { z } from 'zod';
import { readFileSync } from 'node:fs';
import yaml from 'js-yaml';

const MatchSchema = z.object({
  uuid: z.string().default('*'),
  domain: z.string().optional(),
}).default({ uuid: '*' });

const ExecAction = z.object({
  action: z.literal('exec'),
  command: z.string(),
  args: z.array(z.string()).default([]),
  env: z.record(z.string()).default({}),
  timeout_ms: z.number().int().positive().default(30000),
});

const WriteFileAction = z.object({
  action: z.literal('write_file'),
  path: z.string(),
  template: z.string(),
  mode: z.string().optional(),
});

const TriggerCookieUpdate = z.object({ on: z.literal('cookie-update') });
const TriggerCron = z.object({ on: z.literal('cron'), schedule: z.string() });

const HookSchema = z.intersection(
  z.object({ id: z.string(), match: MatchSchema }),
  z.intersection(
    z.discriminatedUnion('on', [TriggerCookieUpdate, TriggerCron]),
    z.discriminatedUnion('action', [ExecAction, WriteFileAction]),
  ),
);

export const ConfigSchema = z.object({
  server: z.object({
    host: z.string().default('0.0.0.0'),
    port: z.number().int().default(8088),
    data_dir: z.string().default('./data'),
    body_limit: z.string().default('50mb'),
  }).default({}),
  accounts: z.array(z.object({ uuid: z.string(), password: z.string() })).default([]),
  hooks: z.array(HookSchema).default([]),
});

export type Config = z.infer<typeof ConfigSchema>;
export type HookConfig = z.infer<typeof HookSchema>;

export function parseConfig(raw: unknown): Config {
  return ConfigSchema.parse(raw);
}

export function loadConfig(path: string): Config {
  return parseConfig(yaml.load(readFileSync(path, 'utf8')));
}

export function passwordFor(cfg: Config, uuid: string): string | undefined {
  return cfg.accounts.find((a) => a.uuid === uuid)?.password;
}
