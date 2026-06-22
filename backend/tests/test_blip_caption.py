"""测试 caption 拼接逻辑(不真实加载 BLIP 模型)"""
from backend.data_tools.blip_caption import build_full_caption


def test_build_caption_prefixes_trigger():
    cap = build_full_caption("musangking durian", "a fruit on a table")
    assert cap.startswith("musangking durian")
    assert "a fruit on a table" in cap
    assert "high quality" in cap


def test_build_caption_no_double_period():
    cap = build_full_caption("musangking durian", "a fruit.")
    assert cap.count("..") == 0
