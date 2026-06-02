def test_public_surface():
    import bilibili
    for name in [
        "BilibiliEngine", "BilibiliCredential", "EngineConfig", "RenderOptions",
        "BilibiliResult", "transcribe", "BilibiliEngineError",
    ]:
        assert hasattr(bilibili, name), f"missing public export: {name}"
