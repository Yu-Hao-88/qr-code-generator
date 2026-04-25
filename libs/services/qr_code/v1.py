""" "QR code 相關服務"""

from datetime import datetime

from fastapi import Depends

from libs.models.qr_code.v1 import QRInfo
from libs.repositories.qr_code_repository import QRCodeRepository
from libs.utils.exceptions import DataNotFoundError
from libs.utils.generate_token import generate_token

MAX_TRIES = 5


class QRCodeService:
    def __init__(
        self,
        qr_code_repository: QRCodeRepository = Depends(QRCodeRepository),
    ) -> None:
        self.__qr_code_repository = qr_code_repository

    async def create(self, url: str, expires_at: datetime = None) -> str:
        """
        根據提供的 URL 生成 QR code，並可選擇設定過期時間

        Args:
            url (str): 要生成 QR code 的 URL
            expires_at (datetime, optional): QR code 過期時間

        Returns:
            str: qr_token
        """
        # 產生 QR code token
        token = generate_token(url)

        # 確保 token 不重複，最多嘗試 MAX_TRIES 次
        count = 0
        while (
            await self.__qr_code_repository.check_token_exists(token)
            and count < MAX_TRIES
        ):
            token = generate_token(url)
            count += 1

        if count == MAX_TRIES:
            raise RuntimeError(
                "Failed to generate a unique QR code token after maximum retries"
            )

        # 將 QR code 資訊存入資料庫
        await self.__qr_code_repository.create(url, token, expires_at)

        return token

    async def get_info(self, qr_token: str) -> QRInfo:
        """
        根據提供的 QR code token 查詢 QR code 資訊

        Args:
            qr_token (str): QR code token

        Returns:
            QRInfo: QR code 資訊
        """
        result = await self.__qr_code_repository.get_info(qr_token)

        if result is None:
            raise DataNotFoundError(message="QR code not found")

        return QRInfo(**result)
