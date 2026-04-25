"""redis"""

from functools import cached_property

import redis.asyncio as aioredis
from configobj import ConfigObj

import context


class RedisClient:
    """Redis 操作封裝，內部共用 module-level 單例連線。"""

    @cached_property
    def __client(self) -> aioredis.Redis:
        """Redis 連線，使用 cached_property 確保只建立一次連線"""
        config = ConfigObj(f"{context.PROJECT_ROOT_PATH}/configs/redis.ini")["REDIS"]
        return aioredis.Redis(
            host=config["host"],
            port=int(config["port"]),
            db=0,
            decode_responses=True,
        )

    async def set(self, key: str, value: str, ex: int = None) -> None:
        """
        設定 Redis key-value，可選設定過期秒數

        Args:
            key (str): Redis key
            value (str): 要儲存的字串值
            ex (int, optional): 過期秒數
        """
        await self.__client.set(key, value, ex=ex)

    async def get(self, key: str) -> str | None:
        """
        取得 Redis key 對應的值

        Args:
            key (str): Redis key

        Returns:
            str | None: 對應的值，若不存在則回傳 None
        """
        return await self.__client.get(key)

    async def delete(self, key: str) -> None:
        """
        刪除 Redis key

        Args:
            key (str): Redis key
        """
        await self.__client.delete(key)
