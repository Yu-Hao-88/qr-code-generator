"""
1. 將專案根目錄加入 sys.path，讓專案內的模組都能被正確 import。
2. 設定 logging 的 default 訊息。
"""

import logging
import sys
from pathlib import Path

# 設定 logging 的 default 訊息
logging.basicConfig(format="%(message)s", level=logging.INFO)

PROJECT_ROOT_PATH = str(Path(__file__).parents[1])

# Append ROOT_PATH_module to system path
if PROJECT_ROOT_PATH not in sys.path:
    # Avoid to append duplicated path to system path.
    sys.path.append(PROJECT_ROOT_PATH)

sys.path.append(str(Path(PROJECT_ROOT_PATH).joinpath("routes")))
