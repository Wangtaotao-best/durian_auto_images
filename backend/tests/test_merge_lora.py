"""测试 merge_lora 的参数处理"""
import pytest
from pathlib import Path
from backend.tools.merge_lora import validate_paths


def test_validate_paths_existing(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    lora = tmp_path / "lora"
    lora.mkdir()
    output = tmp_path / "output"
    # 不应抛异常
    validate_paths(str(base), str(lora), str(output))


def test_validate_paths_missing_base(tmp_path):
    with pytest.raises(FileNotFoundError):
        validate_paths(str(tmp_path / "nonexistent"), str(tmp_path), str(tmp_path))
