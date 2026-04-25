"""初始化 sqlalchemy rds 連線，並回傳 connection 相關變數"""

import logging
import traceback
from collections import defaultdict
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

import context
from libs.database.rds_config import RDSConfig

DATABASE_URL = f"sqlite+aiosqlite:///{context.PROJECT_ROOT_PATH}/data/qr_code.db"


class SQLAlchemyConnection:
    """SQLAlchemy 連線管理類別"""

    __engines: dict[str, AsyncEngine] = defaultdict(dict)

    @classmethod
    @asynccontextmanager
    async def session_scope(cls, rds_config: RDSConfig) -> AsyncGenerator[AsyncSession, None]:
        """
        提供一個非同步上下文管理器，用於管理 SQLAlchemy 的 AsyncSession。

        使用方式：
        ```
        async with SQLAlchemyConnection.session_scope(RDSConfig.QR_CODE) as session:
            await session.execute("SELECT * FROM some_table")
        ```

        Args:
            rds_config (RDSConfig): 指定資料庫設定，從 RDSConfig 中選擇。

        Yields:
            AsyncSession: SQLAlchemy 的非同步資料庫 Session。
        """
        session = cls.get_session(rds_config)
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logging.error(
                "RDS Session error: %s\n Traceback:\n%s",
                e,
                traceback.format_exc(),
            )
            raise
        finally:
            await session.close()

    @classmethod
    def get_session(cls, rds_config: RDSConfig) -> AsyncSession:
        """
        取得 sqlalchemy AsyncSession

        Args:
            rds_config (RDSConfig): 指定資料庫設定，從 RDSConfig 中選擇。

        Returns:
            AsyncSession: SQLAlchemy 的非同步資料庫 Session。
        """
        return async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=cls.get_engine(rds_config),
            class_=AsyncSession,
        )()

    @classmethod
    def get_engine(cls, rds_config: RDSConfig) -> AsyncEngine:
        """
        讀取 rds 設定並建立 sqlalchemy AsyncEngine

        Engine 為連線池，建立後可長期持有、重複使用

        Args:
            rds_config (RDSConfig): 指定資料庫設定，從 RDSConfig 中選擇。

        Returns:
            AsyncEngine: SQLAlchemy 的非同步資料庫 Engine。
        """
        if rds_config.value in cls.__engines:
            return cls.__engines[rds_config.value]

        engine = create_async_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=3600,
        )

        cls.__engines[rds_config.value] = engine

        return engine
