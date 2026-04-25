"""API 設定讀取工具"""

from configobj import ConfigObj

import context

_config = ConfigObj(
    f"{context.PROJECT_ROOT_PATH}/configs/api.ini",
    encoding="utf-8",
)["API"]


class ApiConfig:
    """API 設定類別"""

    BASE_URL: str = _config["base_url"]
    HOST: str = _config["host"]
    PORT: int = int(_config["port"])
    RELOAD: bool = _config.as_bool("reload")
    WORKERS: int = int(_config.get("workers", 1))
    DOCS_URL: str = _config["docs_url"]
