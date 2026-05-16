import yaml
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
CFG_DIR = ROOT_DIR / "cfg"


def deep_merge(base, override):
    for (
        k,
        v,
    ) in override.items():
        if isinstance(v, dict) and isinstance(cur := base.get(k), dict):
            deep_merge(cur, v)
        else:
            base[k] = v
    return base


def read_config(path=CFG_DIR / "default.yaml", override=None):
    with open(path) as config_path:
        config = yaml.safe_load(config_path)

    if override:
        config_override = read_config(CFG_DIR / override)
        config = deep_merge(config, config_override)
    return config


print(read_config(override="colab.yaml"))
