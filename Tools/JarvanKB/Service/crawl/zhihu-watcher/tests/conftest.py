import logging
import pytest


@pytest.fixture(autouse=True)
def _quiet_logging():
    logging.getLogger("zhihu_watcher").setLevel(logging.CRITICAL)
