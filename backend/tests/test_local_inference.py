"""测试本地推理脚本的辅助函数"""
from backend.local_inference import inject_trigger, build_output_name


def test_inject_trigger_prefixes():
    out = inject_trigger("musangking durian", "on a table")
    assert out.startswith("musangking durian")
    assert "on a table" in out


def test_inject_trigger_idempotent_if_already_present():
    out = inject_trigger("musangking durian", "musangking durian, on a table")
    # 不要重复加触发词
    assert out.count("musangking durian") == 1


def test_build_output_name_format():
    name = build_output_name("musang_king", 12345, 0)
    assert "musang_king" in name
    assert "12345" in name
    assert name.endswith("_0.png")
