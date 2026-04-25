""" "重定向相關的資料模型"""

from fastapi import status
from pydantic import BaseModel, Field

from libs.models.general import (
    ResponseGone,
    generate_response_examples,
)


class RedirectRequest(BaseModel):
    """
    重定向請求資料模型

    Attributes:
    - **str** url: 要重定向的目標 URL (必填)
    """

    qr_token: str = Field(..., title="QR code token")


REDIRECT_RESPONSE_EXAMPLES = generate_response_examples(
    [
        {
            "status_code": status.HTTP_410_GONE,
            "response_name": "gone",
            "example": ResponseGone.model_json_schema()["example"],
        },
    ]
)
