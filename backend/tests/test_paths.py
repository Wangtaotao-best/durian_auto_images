"""测试路径配置加载"""
from pathlib import Path
import pytest
from backend.configs.loader import load_paths


def test_load_paths_returns_dict():
    paths = load_paths()
    assert isinstance(paths, dict)


def test_paths_has_required_keys():
    paths = load_paths()
    required = ["data_root", "raw", "candidates", "training", "models_lora",
                "models_merged", "models_openvino", "outputs"]
    for key in required:
        assert key in paths, f"missing key: {key}"


def test_paths_are_path_objects():
    paths = load_paths()
    assert isinstance(paths["data_root"], Path)


def test_data_root_is_durian_data():
    paths = load_paths()
    assert paths["data_root"].name == "durian-data"
