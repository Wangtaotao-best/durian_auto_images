"""测试训练辅助函数"""
from backend.lora_trainer import resolve_output_dir, resolve_data_dir
from pathlib import Path


def test_resolve_data_dir_from_variety(tmp_path):
    paths = {"training": tmp_path}
    (tmp_path / "musang_king").mkdir()
    result = resolve_data_dir("musang_king", None, paths)
    assert result == tmp_path / "musang_king"


def test_resolve_data_dir_explicit_override(tmp_path):
    explicit = tmp_path / "custom"
    explicit.mkdir()
    paths = {"training": tmp_path / "default"}
    result = resolve_data_dir("musang_king", explicit, paths)
    assert result == explicit
