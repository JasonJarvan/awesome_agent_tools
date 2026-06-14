def test_public_surface():
    import bilibili
    for name in [
        "BilibiliEngine", "BilibiliCredential", "EngineConfig", "RenderOptions",
        "BilibiliResult", "transcribe", "BilibiliEngineError",
    ]:
        assert hasattr(bilibili, name), f"missing public export: {name}"


def test_configure_is_exported_and_contract_intact():
    import bilibili
    assert hasattr(bilibili, "configure") and callable(bilibili.configure)
    assert "configure" in bilibili.__all__
    # additive: the v1 frozen contract symbols are all still exported
    for name in ("BilibiliEngine", "transcribe", "BilibiliCredential", "EngineConfig",
                 "RenderOptions", "RenderedOutput", "BilibiliResult", "BilibiliMetadata",
                 "Transcript", "TranscriptSegment"):
        assert hasattr(bilibili, name), f"frozen contract symbol missing: {name}"
