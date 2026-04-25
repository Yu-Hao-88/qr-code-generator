"""Rate limiter 封裝"""

from functools import cached_property

from configobj import ConfigObj
from slowapi import Limiter
from slowapi.util import get_remote_address

import context


class RateLimiter:
    """Rate limiter 封裝，使用 Redis 作為計數器儲存"""

    @cached_property
    def limiter(self) -> Limiter:
        """
        建立並回傳 Limiter 實例，使用 Redis 作為儲存後端

        Returns:
            Limiter: Limiter 實例
        """
        config = ConfigObj(
            f"{context.PROJECT_ROOT_PATH}/configs/redis.ini",
            encoding="utf-8",
        )["REDIS"]
        return Limiter(
            key_func=get_remote_address,
            storage_uri=f"redis://{config['host']}:{config['port']}",
        )


RATE_LIMITER = RateLimiter()
