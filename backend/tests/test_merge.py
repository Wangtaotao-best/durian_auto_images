"""测试数据集合并"""
import pytest
from PIL import Image
from pathlib import Path
from backend.data_tools.merge_dataset import resize_image, merge_sources


@pytest.fixture
def make_img(tmp_path):
    def _f(name, w=800, h=800, color=(200, 150, 100)):
        p = tmp_path / name
        from PIL import ImageDraw
        im = Image.new("RGB", (w, h), color=color)
        draw = ImageDraw.Draw(im)
        # 画不同位置/大小的矩形以增加 pHash 区分度
        draw.rectangle([10, 10, w // 3, h // 3], fill=(color[1], color[2], color[0]))
        draw.rectangle([w // 2, h // 2, w - 20, h - 20], fill=(color[2], color[0], color[1]))
        im.save(p, "JPEG")
        return p
    return _f


def test_resize_image_short_side(tmp_path, make_img):
    src = make_img("orig.jpg", 1200, 800)
    out = resize_image(src, tmp_path / "out.jpg", target_short=512)
    with Image.open(out) as im:
        assert min(im.size) == 512


def test_merge_two_sources(tmp_path, make_img):
    crawl_dir = tmp_path / "crawl"
    crawl_dir.mkdir()
    personal_dir = tmp_path / "personal"
    personal_dir.mkdir()
    out_dir = tmp_path / "out"

    make_img("crawl/a.jpg", 700, 700, color=(200, 150, 100))
    make_img("crawl/b.jpg", 700, 700, color=(100, 200, 150))
    make_img("personal/x.jpg", 700, 700, color=(150, 100, 200))

    stats = merge_sources("musang_king", crawl_dir, personal_dir, out_dir)
    assert stats["total"] == 3
    assert len(list(out_dir.glob("*.jpg"))) == 3
