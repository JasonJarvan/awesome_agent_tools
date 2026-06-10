import logging
import pytest


@pytest.fixture(autouse=True)
def _quiet_logging():
    logging.getLogger("bilibili_watcher").setLevel(logging.CRITICAL)
