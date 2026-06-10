"""CLI entrypoint: `python -m zhihu_watcher [--once] [--config PATH]`.

Default (no --once): start a BlockingScheduler interval job (max_instances=1) and run forever.
--once: run a single cycle and exit (used by the smoke test + CI).
"""
from __future__ import annotations

import argparse
import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from .config import load_config
from .watcher import build_watcher


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="zhihu_watcher")
    parser.add_argument("--config", default="config/zhihu-watcher.yaml",
                        help="path to the YAML config")
    parser.add_argument("--once", action="store_true",
                        help="run a single poll cycle and exit (smoke / CI)")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    config = load_config(args.config)
    watcher = build_watcher(config)

    if args.once:
        watcher.run_cycle()
        return

    scheduler = BlockingScheduler()
    scheduler.add_job(
        watcher.run_cycle,
        trigger="interval",
        minutes=config.poll_interval_minutes,
        max_instances=1,
        coalesce=True,
    )
    logging.getLogger("zhihu_watcher").info(
        "starting scheduler: every %d min, %d target(s)",
        config.poll_interval_minutes, len(config.targets),
    )
    # run once immediately, then APScheduler fires every interval
    watcher.run_cycle()
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    main()
