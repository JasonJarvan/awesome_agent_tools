import cron from 'node-cron';

export interface CronHandle { stop(): void; }

export function scheduleCron(expr: string, fn: () => void): CronHandle {
  let running = false;
  const task = cron.schedule(expr, async () => {
    if (running) return; // skip overlapping ticks
    running = true;
    try { await fn(); } finally { running = false; }
  });
  return { stop: () => task.stop() };
}
