"""提供資料庫連線的類別，使用 SQLAlchemy 來管理資料庫連線"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from libs.database.rds_config import RDSConfig
from libs.database.sqlalchemy_connection import SQLAlchemyConnection


class SessionProvider:
    def __init__(self, rds_config: RDSConfig) -> None:
        self.__rds_config = rds_config

    async def __call__(self) -> AsyncGenerator[AsyncSession, None]:
        async with SQLAlchemyConnection.session_scope(self.__rds_config) as session:
            yield session
