"""初始化 sqlalchemy rds 連線，並回傳 connection 相關變數"""

import logging
import traceback
from collections import defaultdict
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

import context
from libs.database.rds_config import RDSConfig

DATABASE_URL = f"sqlite:///{context.PROJECT_ROOT_PATH}/data/qr_code.db"


class SQLAlchemyConnection:
    """SQLAlchemy 連線管理類別"""

    __engines = defaultdict(dict)

    @classmethod
    @contextmanager
    def session_scope(cls, rds_config: RDSConfig) -> Generator[Session, None, None]:
        """
        提供一個上下文管理器，用於管理 SQLAlchemy 的 Session。

        使用方式：
        ```
        with SQLAlchemyConnection.session_scope(RDSConfig.QR_CODE) as session:
            session.execute("SELECT * FROM some_table")
        ```

        Args:
            rds_config (RDSConfig): 指定資料庫設定，從 RDSConfig 中選擇。

        Yields:
            Session: SQLAlchemy 的資料庫 Session。
        """
        session = cls.get_session(rds_config)
        try:
            yield session
            session.commit()  # 自動提交
        except Exception as e:
            session.rollback()  # 發生異常時回滾
            logging.error(
                "RDS Session error: %s\n Traceback:\n%s",
                e,
                traceback.format_exc(),
            )
            raise
        finally:
            session.close()  # 確保 Session 被正確關閉

    @classmethod
    def get_session(cls, rds_config: RDSConfig) -> Session:
        """
        取得 sqlalchemy Session

        Session 是 ORM 的工作單位，應在每次操作後立即關閉或釋放。

        Args:
            rds_config (RDSConfig): 指定資料庫設定，從 RDSConfig 中選擇。

        Returns:
            Session: SQLAlchemy 的資料庫 Session。
        """
        return sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=cls.get_engine(rds_config),
        )()

    @classmethod
    def get_engine(cls, rds_config: RDSConfig) -> Engine:
        """
        讀取 rds 設定並建立 sqlalchemy Engine

        Engine 為連線池, 建立後可長期持有、重複使用

        Args:
            rds_config (RDSConfig): 指定資料庫設定，從 RDSConfig 中選擇。

        Returns:
            Engine: SQLAlchemy 的資料庫 Engine。
        """
        # 若已建立過連線就直接回傳
        if rds_config.value in cls.__engines:
            return cls.__engines[rds_config.value]

        # 建立連線
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,  # 每次 checkout 時測試連線的可用性。
            pool_recycle=3600,  # 每 1 小時回收一次連線，避免 MySQL 連線過期
        )

        # 儲存連線
        cls.__engines[rds_config.value] = engine

        return engine
