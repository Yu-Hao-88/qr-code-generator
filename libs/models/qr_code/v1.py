"""QR code 產生器 API /qr_code/v1 的 schema 定義"""

from datetime import datetime, timezone
from typing import Annotated
from urllib.parse import urlparse, urlunparse

from fastapi import status
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, field_validator

from libs.models.general import (
    ResponseBadRequest,
    ResponseNotFound,
    ResponseOK,
    generate_response_examples,
)

ALLOWED_URL_SCHEMES = {"http", "https"}
DEFAULT_URL_SCHEME = "https"
MAX_URL_LENGTH = 2048
DEFAULT_PORTS = {"http": 80, "https": 443}


def validate_url(url: str) -> str:
    """
    檢查並正規化使用者輸入的 URL。

    驗證項目：去除前後空白、空字串檢查、補上預設 scheme、
    scheme 白名單、netloc 必填、長度上限。
    正規化項目：host 轉小寫、移除預設 port、移除 fragment。

    Args:
        url (str): 使用者輸入的 URL

    Raises:
        ValueError: URL 為空、scheme 不在白名單、缺少 host 或長度超過上限

    Returns:
        str: 正規化後的 URL
    """
    url = url.strip()
    if not url:
        raise ValueError("URL 不可為空")

    if "://" not in url:
        url = f"{DEFAULT_URL_SCHEME}://{url}"

    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_URL_SCHEMES:
        raise ValueError(f"URL scheme 必須為 {sorted(ALLOWED_URL_SCHEMES)} 之一")
    if not parsed.hostname:
        raise ValueError("URL 缺少 host")

    host = parsed.hostname.lower()
    netloc = host
    if parsed.port is not None and parsed.port != DEFAULT_PORTS[parsed.scheme]:
        netloc = f"{host}:{parsed.port}"

    normalized = urlunparse(
        (parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, "")
    )

    if len(normalized) > MAX_URL_LENGTH:
        raise ValueError(f"URL 長度不可超過 {MAX_URL_LENGTH} 字元")

    return normalized


ValidatedUrl = Annotated[str, AfterValidator(validate_url)]


class QRCreateRequest(BaseModel):
    url: ValidatedUrl = Field(..., title="要生成 QR code 的 URL")
    expires_at: datetime | None = Field(None, title="QR code 過期時間")

    @field_validator("expires_at")
    def check_expires_at(cls, expires_at: datetime | None) -> datetime | None:
        """
        檢查 QR code 過期時間是否晚於現在。

        若 expires_at 帶有時區資訊，以 UTC 當下時間比較；
        若為 naive datetime，則以本地時間比較，避免跨時區比較拋出 TypeError。

        Args:
            expires_at (datetime | None): 使用者輸入的過期時間

        Raises:
            ValueError: 過期時間不晚於現在

        Returns:
            datetime | None: 原始過期時間
        """
        if expires_at is None:
            return None
        now = datetime.now(timezone.utc) if expires_at.tzinfo else datetime.now()
        if expires_at <= now:
            raise ValueError("過期時間必須晚於現在")
        return expires_at

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "https://www.example.com/some/path?query=123",
                "expires_at": "2024-12-31T23:59:59Z",
            }
        }
    )


class QRCreateResponse(ResponseOK):
    qr_token: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "code": 200,
                "message": "操作成功",
                "data": {"qr_token": "example_token"},
            }
        }
    )


QR_CREATE_RESPONSE_EXAMPLES = generate_response_examples(
    [
        {
            "status_code": status.HTTP_200_OK,
            "response_name": "success",
            "example": QRCreateResponse.model_json_schema()["example"],
        },
        {
            "status_code": status.HTTP_400_BAD_REQUEST,
            "response_name": "bad_request",
            "example": ResponseBadRequest.model_json_schema()["example"],
        },
    ]
)


class QRInfoRequest(BaseModel):
    qr_token: str = Field(..., title="要查詢的 QR code 的 token")


class QRInfo(BaseModel):
    token: str
    original_url: str
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None
    is_deleted: bool


class QRInfoResponse(ResponseOK):
    data: QRInfo

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "code": 200,
                "message": "操作成功",
                "data": {
                    "token": "example_token",
                    "original_url": "https://www.example.com/some/path?query=123",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                    "expires_at": "2024-12-31T23:59:59Z",
                    "is_deleted": False,
                },
            }
        }
    )


QR_INFO_RESPONSE_EXAMPLES = generate_response_examples(
    [
        {
            "status_code": status.HTTP_200_OK,
            "response_name": "success",
            "example": QRInfoResponse.model_json_schema()["example"],
        },
        {
            "status_code": status.HTTP_404_NOT_FOUND,
            "response_name": "not_found",
            "example": ResponseNotFound.model_json_schema()["example"],
        },
    ]
)


class QRUpdatePathRequest(BaseModel):
    qr_token: str = Field(..., title="要修改的 QR code 的 token")


class QRUpdateBodyRequest(BaseModel):
    url: ValidatedUrl = Field(..., title="要生成 QR code 的 URL")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "https://www.google.com/",
            }
        }
    )


QR_UPDATE_RESPONSE_EXAMPLES = generate_response_examples(
    [
        {
            "status_code": status.HTTP_200_OK,
            "response_name": "success",
            "example": ResponseOK.model_json_schema()["example"],
        },
        {
            "status_code": status.HTTP_400_BAD_REQUEST,
            "response_name": "bad_request",
            "example": ResponseBadRequest.model_json_schema()["example"],
        },
        {
            "status_code": status.HTTP_404_NOT_FOUND,
            "response_name": "not_found",
            "example": ResponseNotFound.model_json_schema()["example"],
        },
    ]
)


class QRDeletePathRequest(BaseModel):
    qr_token: str = Field(..., title="要刪除的 QR code 的 token")


QR_DELETE_RESPONSE_EXAMPLES = generate_response_examples(
    [
        {
            "status_code": status.HTTP_200_OK,
            "response_name": "success",
            "example": ResponseOK.model_json_schema()["example"],
        },
        {
            "status_code": status.HTTP_404_NOT_FOUND,
            "response_name": "not_found",
            "example": ResponseNotFound.model_json_schema()["example"],
        },
    ]
)


class QRImageRequest(BaseModel):
    qr_token: str = Field(..., title="要查詢的 QR code 的 token")


QR_IMAGE_RESPONSE_EXAMPLES = generate_response_examples(
    [
        {
            "status_code": status.HTTP_404_NOT_FOUND,
            "response_name": "not_found",
            "example": ResponseNotFound.model_json_schema()["example"],
        },
    ]
)
