"""QR code 資料庫操作類別"""

from fastapi import Depends
from sqlalchemy import Result, select
from sqlalchemy.orm import Session

from libs.database.models.url_mapping_model import UrlMapping
from libs.database.rds_config import RDSConfig
from libs.database.session_provider import SessionProvider


class QRCodeRepository:
    """QR code 資料庫操作類別"""

    def __init__(
        self,
        session: Session = Depends(SessionProvider(RDSConfig.QR_CODE)),
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
        result: Result = self.__session.execute(stmt)
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
