"""测试图像过滤逻辑"""
import pytest
from PIL import Image
from pathlib import Path
from backend.data_tools.filter import (
    check_resolution,
    check_aspect_ratio,
    check_file_size,
    compute_phash,
    filter_image,
)


@pytest.fixture
def tmp_image(tmp_path):
    def _make(w=600, h=600, fmt="JPEG"):
        p = tmp_path / f"img_{w}x{h}.{fmt.lower()}"
        Image.new("RGB", (w, h), color=(255, 200, 100)).save(p, fmt)
        return p
    return _make


def test_resolution_pass(tmp_image):
    assert check_resolution(tmp_image(600, 600), min_size=512) is True


def test_resolution_fail(tmp_image):
    assert check_resolution(tmp_image(400, 400), min_size=512) is False


def test_aspect_ratio_pass(tmp_image):
    assert check_aspect_ratio(tmp_image(600, 800)) is True


def test_aspect_ratio_fail_too_wide(tmp_image):
    assert check_aspect_ratio(tmp_image(2000, 500)) is False


def test_file_size_ok(tmp_image):
    assert check_file_size(tmp_image(), max_mb=10) is True


def test_phash_returns_string(tmp_image):
    h = compute_phash(tmp_image())
    assert isinstance(h, str)
    assert len(h) == 16


def test_filter_image_passes_good(tmp_image):
    ok, reason = filter_image(tmp_image(800, 800))
    assert ok is True
    assert reason == "ok"


def test_filter_image_rejects_small(tmp_image):
    ok, reason = filter_image(tmp_image(300, 300))
    assert ok is False
    assert "resolution" in reason
