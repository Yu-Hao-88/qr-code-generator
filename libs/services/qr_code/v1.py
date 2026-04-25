""" "QR code 相關服務"""

import io
from datetime import datetime

import qrcode
from fastapi import Depends

from libs.models.qr_code.v1 import QRInfo
from libs.repositories.qr_code_repository import QRCodeRepository
from libs.utils.api_config import ApiConfig
from libs.utils.exceptions import DataNotFoundError
from libs.utils.generate_token import generate_token

REDIRECT_URL_TEMPLATE = "{base_url}/api/redirect/v1/{qr_token}"

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
        result = await self.__qr_code_repository.get_data_for_info(qr_token)

        if result is None:
            raise DataNotFoundError(message="QR code not found")

        return QRInfo(**result)

    async def update(self, qr_token: str, url: str) -> None:
        """
        根據提供的 QR code token 更新 QR code 資訊

        Args:
            qr_token (str): QR code token
            url (str): 要修改的新 URL
        """
        # 更新 QR code 資訊
        result = await self.__qr_code_repository.update(qr_token, url)

        if not result:
            raise DataNotFoundError(message="QR code not found")

    async def delete(self, qr_token: str) -> None:
        """
        根據提供的 QR code token 刪除 QR code 資訊

        Args:
            qr_token (str): QR code token
        """
        # 刪除 QR code 資訊
        result = await self.__qr_code_repository.delete(qr_token)

        if not result:
            raise DataNotFoundError(message="QR code not found")

    async def get_image(self, qr_token: str) -> bytes:
        """
        根據提供的 QR code token 產生 QR code 圖片

        Args:
            qr_token (str): QR code token

        Returns:
            bytes: QR code PNG 圖片的 bytes
        """
        # 查詢 QR code 資訊，確認 QR code 是否存在
        result = await self.__qr_code_repository.get_data_for_info(qr_token)
        if result is None:
            raise DataNotFoundError(message="QR code not found")

        # 產生 QR code 圖片
        redirect_url = REDIRECT_URL_TEMPLATE.format(
            base_url=ApiConfig.BASE_URL, qr_token=qr_token
        )
        qr = qrcode.QRCode()
        qr.add_data(redirect_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # 產生 PNG 圖片的 bytes
        buf = io.BytesIO()
        img.save(buf, format="PNG")

        return buf.getvalue()
