"""QR code 資料庫操作類別"""

from fastapi import Depends
from sqlalchemy import Result, RowMapping, select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.database.models.url_mapping_model import UrlMapping
from libs.database.rds_config import RDSConfig
from libs.database.session_provider import SessionProvider


class QRCodeRepository:
    """QR code 資料庫操作類別"""

    def __init__(
        self,
        session: AsyncSession = Depends(SessionProvider(RDSConfig.QR_CODE)),
    ) -> None:
        self.__session = session

    async def check_token_exists(self, token: str) -> bool:
        """
        檢查 QR code token 是否存在於資料庫中

        Args:
            token (str): QR code token

        Returns:
            bool: 是否存在
        """
        stmt = select(UrlMapping).where(UrlMapping.token == token)
        result: Result = await self.__session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create(self, url: str, token: str, expires_at: str) -> None:
        """
        根據提供的 URL 生成 QR code，並可選擇設定過期時間

        Args:
            url (str): 要生成 QR code 的 URL
            token (str): QR code token
            expires_at (str): QR code 過期時間
        """
        new_mapping = UrlMapping(
            token=token,
            original_url=url,
            expires_at=expires_at,
        )
        self.__session.add(new_mapping)

    async def get_info(self, qr_token: str) -> RowMapping | None:
        """
        根據提供的 QR code token 查詢 QR code 資訊

        Args:
            qr_token (str): QR code token

        Returns:
            RowMapping | None: QR code 資訊，若找不到則回傳 None
        """
        stmt = select(
            UrlMapping.token,
            UrlMapping.original_url,
            UrlMapping.created_at,
            UrlMapping.updated_at,
            UrlMapping.expires_at,
            UrlMapping.is_deleted,
        ).where(UrlMapping.token == qr_token)
        result: Result = await self.__session.execute(stmt)
        return result.mappings().one_or_none()

    async def update(self, qr_token: str, url: str) -> bool:
        """
        根據提供的 QR code token 更新 QR code 資訊

        Args:
            qr_token (str): QR code token
            url (str): 要修改的新 URL

        Returns:
            bool: 更新是否成功
        """
        # 使用 SELECT ... FOR UPDATE 鎖定資料列，確保在更新過程中不會有其他交易修改同一筆資料
        stmt = select(UrlMapping).where(UrlMapping.token == qr_token).with_for_update()
        result: Result = await self.__session.execute(stmt)
        url_mapping: UrlMapping | None = result.scalar_one_or_none()

        if url_mapping is None:
            return False

        # 更新 URL 和 updated_at 欄位
        url_mapping.original_url = url
        await self.__session.flush()

        return True
