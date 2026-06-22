"""测试爬虫模块的纯函数部分(不真实联网)"""
import pytest
from backend.data_tools.scraper import build_keywords, sanitize_output_dir
from pathlib import Path


def test_build_keywords_for_known_variety():
    keywords = build_keywords("musang_king")
    assert len(keywords) >= 2
    assert any("musang" in k.lower() for k in keywords)


def test_build_keywords_unknown_variety_raises():
    with pytest.raises(KeyError):
        build_keywords("nonexistent_variety")


def test_sanitize_output_dir_creates_path(tmp_path):
    out = sanitize_output_dir(tmp_path / "raw" / "musang_king")
    assert out.exists()
    assert out.is_dir()
