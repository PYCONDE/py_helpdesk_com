"""

"""
from pathlib import Path
from omegaconf import OmegaConf
import logging


private_conf = OmegaConf.load(Path(__file__).parents[1].resolve() / "_private/config.yaml")
base_conf = OmegaConf.load(Path(__file__).parent.resolve() / "config.yaml")
CONFIG = OmegaConf.merge(base_conf, private_conf)


# It's useful to cache some docs like team IDs as they are needed for params
CONFIG["docs_cache_path"] = Path(__file__).parents[1] / CONFIG.docs_cache
CONFIG["docs_cache_path"].mkdir(parents=True, exist_ok=True)

# Optional for archive / backups
if CONFIG.archive:
    CONFIG["archive_path"] = Path(__file__).parents[1] / CONFIG.archive
    CONFIG["archive_path"].mkdir(parents=True, exist_ok=True)

CONFIG["log_path"] = Path(__file__).parents[1] / "_logs" / CONFIG.log
CONFIG["log_path"].parent.mkdir(parents=True, exist_ok=True)

# Create a custom logger
logger = logging.getLogger("py_helpdesk")

# Create handlers
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler(str(CONFIG["log_path"].resolve()))
c_handler.setLevel(logging.INFO)
f_handler.setLevel(logging.INFO)

# Create formatters and add it to handlers
c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

# Add handlers to the logger
logger.addHandler(c_handler)
logger.addHandler(f_handler)

logger.info("logger initiated")

__all__ = ["CONFIG", "logger"]
