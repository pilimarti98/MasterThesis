import tomllib
from pathlib import Path

CONFIG_PATH = Path(__file__).parent/"configuration.toml"

with open(CONFIG_PATH, "rb") as f:
    CONFIG = tomllib.load(f)