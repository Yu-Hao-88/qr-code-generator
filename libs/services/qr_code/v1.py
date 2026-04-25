""" "QR code 相關服務"""

import base64
import io
import logging
from datetime import datetime

import qrcode
from fastapi import Depends

from libs.database.redis import RedisClient
from libs.models.qr_code.v1 import QRInfo
from libs.repositories.qr_code_repository import QRCodeRepository
from libs.utils.api_config import ApiConfig
from libs.utils.exceptions import DataNotFoundError
from libs.utils.generate_token import generate_token

REDIRECT_URL_TEMPLATE = "{base_url}/api/redirect/v1/{qr_token}"

MAX_TRIES = 5
QR_INFO_CACHE_TTL = 300
QR_IMAGE_CACHE_TTL = 3600


class QRCodeService:
    def __init__(
        self,
        qr_code_repository: QRCodeRepository = Depends(QRCodeRepository),
        redis_client: RedisClient = Depends(RedisClient),
    ) -> None:
        self.__qr_code_repository = qr_code_repository
        self.__redis = redis_client

    @staticmethod
    def __info_cache_key(qr_token: str) -> str:
        """
        產生 QR code 資訊的 Redis cache key

        Args:
            qr_token (str): QR code token

        Returns:
            str: Redis cache key
        """
        return f"qr_info:{qr_token}"

    @staticmethod
    def __image_cache_key(qr_token: str) -> str:
        """
        產生 QR code 圖片的 Redis cache key

        Args:
            qr_token (str): QR code token

        Returns:
            str: Redis cache key
        """
        return f"qr_image:{qr_token}"

    async def create(self, url: str, expires_at: datetime = None) -> str:
        """
        根據提供的 URL 生成 QR code，並可選擇設定過期時間

        Args:
            url (str): 要生成 QR code 的 URL
            expires_at (datetime, optional): QR code 過期時間

        Returns:
            str: qr_token
        """
        token = generate_token(url)

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

        await self.__qr_code_repository.create(url, token, expires_at)

        return token

    async def get_info(self, qr_token: str) -> QRInfo:
        """
        根據提供的 QR code token 查詢 QR code 資訊，優先從 Redis cache 取得

        Args:
            qr_token (str): QR code token

        Returns:
            QRInfo: QR code 資訊
        """
        # QR code 資訊的 Redis cache key 與圖片不同，分開儲存以避免互相覆蓋
        cache_key = self.__info_cache_key(qr_token)
        cached = await self.__redis.get(cache_key)
        if cached:
            logging.info(f"QR code info cache hit for token: {qr_token}")
            return QRInfo.model_validate_json(cached)

        # 從資料庫查詢 QR code 資訊，若找不到則會拋出 DataNotFoundError
        result = await self.__qr_code_repository.get_data_for_info(qr_token)
        if result is None:
            raise DataNotFoundError(message="QR code not found")

        # 將查詢結果轉換為 QRInfo 物件，並儲存到 Redis cache，設定過期時間
        info = QRInfo(**result)
        await self.__redis.set(cache_key, info.model_dump_json(), ex=QR_INFO_CACHE_TTL)
        return info

    async def update(self, qr_token: str, url: str) -> None:
        """
        根據提供的 QR code token 更新 QR code 資訊

        Args:
            qr_token (str): QR code token
            url (str): 要修改的新 URL
        """
        result = await self.__qr_code_repository.update(qr_token, url)

        if not result:
            raise DataNotFoundError(message="QR code not found")

        await self.__redis.delete(self.__info_cache_key(qr_token))

    async def delete(self, qr_token: str) -> None:
        """
        根據提供的 QR code token 刪除 QR code 資訊

        Args:
            qr_token (str): QR code token
        """
        result = await self.__qr_code_repository.delete(qr_token)

        if not result:
            raise DataNotFoundError(message="QR code not found")

        await self.__redis.delete(self.__info_cache_key(qr_token))
        await self.__redis.delete(self.__image_cache_key(qr_token))

    async def get_image(self, qr_token: str) -> bytes:
        """
        根據提供的 QR code token 產生 QR code 圖片，優先從 Redis cache 取得

        Args:
            qr_token (str): QR code token

        Returns:
            bytes: QR code PNG 圖片的 bytes
        """
        # 圖片的 Redis cache key 與資訊不同，分開儲存以避免互相覆蓋
        cache_key = self.__image_cache_key(qr_token)
        cached = await self.__redis.get(cache_key)
        if cached:
            logging.info(f"QR code image cache hit for token: {qr_token}")
            return base64.b64decode(cached)

        # 產生 QR code 圖片前先確認 QR code 資訊存在，避免產生無效圖片
        await self.get_info(qr_token)

        # QR code 圖片內容為重定向 URL，使用 qrcode 套件生成 PNG 圖片
        redirect_url = REDIRECT_URL_TEMPLATE.format(
            base_url=ApiConfig.BASE_URL, qr_token=qr_token
        )
        qr = qrcode.QRCode()
        qr.add_data(redirect_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # 將 PIL Image 物件轉換為 PNG 圖片的 bytes
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        image_bytes = buf.getvalue()

        # 將圖片 bytes 以 base64 編碼後儲存到 Redis，並設定過期時間
        await self.__redis.set(
            cache_key,
            base64.b64encode(image_bytes).decode(),
            ex=QR_IMAGE_CACHE_TTL,
        )
        return image_bytes
