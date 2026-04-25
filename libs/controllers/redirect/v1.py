"""redirect controller v1"""

from datetime import datetime, timezone

from fastapi import Depends, status
from fastapi.responses import RedirectResponse

from libs.services.qr_code.v1 import QRCodeService
from libs.utils.exceptions import DataGoneError


class RedirectController:
    """redirect controller"""

    def __init__(self, qr_code_service: QRCodeService = Depends(QRCodeService)) -> None:
        self.__qr_code_service = qr_code_service

    async def redirect(self, qr_token: str) -> RedirectResponse:
        """
        根據 QR code token 查詢對應的 URL，並回傳 302 導轉

        Args:
            qr_token (str): QR code token

        Returns:
            RedirectResponse: 302 導轉回應
        """
        # 查詢 QR code 資訊
        qr_info = await self.__qr_code_service.get_info(qr_token)

        # 檢查 QR code 是否被刪除或過期
        if qr_info.is_deleted:
            raise DataGoneError(message="QR code has been deleted")
        if qr_info.expires_at:
            now = (
                datetime.now(timezone.utc)
                if qr_info.expires_at.tzinfo
                else datetime.now()
            )
            if qr_info.expires_at <= now:
                raise DataGoneError(message="QR code has expired")

        return RedirectResponse(qr_info.original_url, status_code=status.HTTP_302_FOUND)
