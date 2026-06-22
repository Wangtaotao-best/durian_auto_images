"""配置加载器 - 统一路径与超参数"""
from pathlib import Path
import yaml

_THIS_DIR = Path(__file__).parent
_PATHS_YAML = _THIS_DIR / "paths.yaml"


def _read_yaml() -> dict:
    with open(_PATHS_YAML, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_paths() -> dict:
    """加载路径配置,返回 {key: Path 对象}"""
    cfg = _read_yaml()
    root = Path(cfg["data_root"])
    out = {"data_root": root}
    for key, sub in cfg["subdirs"].items():
        out[key] = root / sub
    return out


def load_varieties() -> dict:
    """加载品种元信息"""
    return _read_yaml()["varieties"]


def load_training_defaults() -> dict:
    return _read_yaml()["training_defaults"]


def load_serve_defaults() -> dict:
    return _read_yaml()["serve_defaults"]
