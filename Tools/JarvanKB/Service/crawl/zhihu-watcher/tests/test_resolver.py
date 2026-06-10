from zhihu_watcher.config import CollectionConfig, UserTarget
from zhihu_watcher.favorites_client import UserCollection
from zhihu_watcher.resolver import TargetResolver


class _FakeFC:
    def __init__(self, *, cols=None, token="zhao", boom=False):
        self._cols = cols or []
        self._token = token
        self._boom = boom
    def get_current_url_token(self, cookies):
        return self._token
    def list_user_collections(self, url_token, cookies):
        if self._boom:
            raise RuntimeError("listing failed")
        return self._cols


def test_collection_passthrough():
    r = TargetResolver(_FakeFC())
    out = r.resolve([CollectionConfig(id="1", name="A")], {})
    assert [(c.id, c.name) for c in out] == [("1", "A")]

def test_user_expansion_skips_default_and_empty_and_prefixes():
    cols = [UserCollection("721", "我的收藏", is_default=True, item_count=109),
            UserCollection("865", "技术-AI生成", is_default=False, item_count=94),
            UserCollection("999", "产品思维", is_default=False, item_count=0)]
    r = TargetResolver(_FakeFC(cols=cols))
    out = r.resolve([UserTarget(url_token="me", name_prefix="zhao/")], {})
    assert [(c.id, c.name) for c in out] == [("865", "zhao/技术-AI生成")]   # default + empty skipped

def test_include_default_true_keeps_default():
    cols = [UserCollection("721", "我的收藏", is_default=True, item_count=109)]
    r = TargetResolver(_FakeFC(cols=cols))
    out = r.resolve([UserTarget(url_token="me", include_default=True)], {})
    assert [(c.id, c.name) for c in out] == [("721", "我的收藏")]

def test_me_resolution_calls_token():
    cols = [UserCollection("865", "技术-AI生成", is_default=False, item_count=5)]
    r = TargetResolver(_FakeFC(cols=cols, token="resolved-token"))
    # literal token bypasses /me; "me" uses it — both reach the same fake list
    assert r.resolve([UserTarget(url_token="me")], {})[0].id == "865"
    assert r.resolve([UserTarget(url_token="literal")], {})[0].id == "865"

def test_dedup_explicit_name_wins_over_discovered():
    cols = [UserCollection("865", "技术-AI生成", is_default=False, item_count=5)]
    r = TargetResolver(_FakeFC(cols=cols))
    out = r.resolve([UserTarget(url_token="me"), CollectionConfig(id="865", name="MyName")], {})
    assert [(c.id, c.name) for c in out] == [("865", "MyName")]   # explicit processed first, wins

def test_failing_user_target_degrades_explicit_survives():
    r = TargetResolver(_FakeFC(boom=True))
    out = r.resolve([CollectionConfig(id="1", name="A"), UserTarget(url_token="me")], {})
    assert [(c.id, c.name) for c in out] == [("1", "A")]   # user target failure skipped, collection kept
