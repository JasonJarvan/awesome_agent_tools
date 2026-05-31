import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname } from 'node:path';
import { interpolate, type HookContext } from './template.js';
import type { HookConfig } from '../config.js';

export interface ExecResult { code: number; stdout: string; stderr: string; }

export async function runExec(hook: Extract<HookConfig, { action: 'exec' }>, ctx: HookContext): Promise<ExecResult> {
  const args = hook.args.map((a) => interpolate(a, ctx));
  const env: Record<string, string> = { ...process.env as Record<string, string> };
  for (const [k, v] of Object.entries(hook.env)) env[k] = interpolate(v, ctx);

  return new Promise((resolve) => {
    const child = spawn(interpolate(hook.command, ctx), args, { env });
    let stdout = '', stderr = '';
    const timer = setTimeout(() => child.kill('SIGKILL'), hook.timeout_ms);
    child.stdout?.on('data', (d) => (stdout += d));
    child.stderr?.on('data', (d) => (stderr += d));
    child.on('close', (code) => { clearTimeout(timer); resolve({ code: code ?? -1, stdout, stderr }); });
    child.on('error', (err) => { clearTimeout(timer); resolve({ code: -1, stdout, stderr: String(err) }); });
  });
}

export async function runWriteFile(hook: Extract<HookConfig, { action: 'write_file' }>, ctx: HookContext): Promise<void> {
  const outPath = interpolate(hook.path, ctx);
  mkdirSync(dirname(outPath), { recursive: true });
  writeFileSync(outPath, interpolate(hook.template, ctx), hook.mode ? { mode: parseInt(hook.mode, 8) } : undefined);
}
