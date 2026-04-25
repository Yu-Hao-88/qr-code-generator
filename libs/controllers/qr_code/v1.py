"""實作 QR code 相關的 controller"""

from datetime import datetime

from fastapi import Depends, status

from libs.models.general import ResponseOK
from libs.models.qr_code.v1 import QRCreateResponse, QRInfoResponse
from libs.services.qr_code.v1 import QRCodeService


class QRCodeController:
    def __init__(self, qr_code_service: QRCodeService = Depends(QRCodeService)) -> None:
        self.__qr_code_service = qr_code_service

    async def create(self, url: str, expires_at: datetime = None) -> tuple[int, dict]:
        """
        根據提供的 URL 生成 QR code，並可選擇設定過期時間

        Args:
            url (str): 要生成 QR code 的 URL
            expires_at (datetime, optional): QR code 過期時間

        Returns:
            tuple[int, dict]: HTTP 狀態碼和回應資料
        """
        qr_token = await self.__qr_code_service.create(url, expires_at)
        return status.HTTP_200_OK, QRCreateResponse(qr_token=qr_token)

    async def get_info(self, qr_token: str) -> tuple[int, dict]:
        """
        根據提供的 QR code token 查詢 QR code 資訊

        Args:
            qr_token (str): QR code token

        Returns:
            tuple[int, dict]: HTTP 狀態碼和回應資料
        """
        qr_info = await self.__qr_code_service.get_info(qr_token)

        return status.HTTP_200_OK, QRInfoResponse(data=qr_info)

    async def update(self, qr_token: str, url: str) -> tuple[int, dict]:
        """
        根據提供的 QR code token 更新 QR code 資訊

        Args:
            qr_token (str): QR code token
            url (str): 要修改的新 URL

        Returns:
            tuple[int, dict]: HTTP 狀態碼和回應資料
        """
        await self.__qr_code_service.update(qr_token, url)

        return status.HTTP_200_OK, ResponseOK(message="更新成功")
