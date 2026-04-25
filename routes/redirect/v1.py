"""讀取 QR code 導轉"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response

from libs.controllers.redirect.v1 import RedirectController
from libs.models.redirect.v1 import REDIRECT_RESPONSE_EXAMPLES, RedirectRequest

# router object
router = APIRouter(prefix="/api/redirect/v1", tags=["redirect"])


@router.get("/{qr_token}", responses=REDIRECT_RESPONSE_EXAMPLES)
async def get_qr_info(
    response: Response,
    redirect_request: Annotated[RedirectRequest, Path()],
    redirect_controller: RedirectController = Depends(RedirectController),
):
    """
    QR code 導轉 API

    根據提供的 QR code token 查詢 QR code 資訊

    Request:
    - **object** data: QR code 查詢請求資料
      - **str** qr_token: 要查詢的 QR code 的 token (必填)


    Response:
    - **str** status: 執行狀態 (success / fail)
    - **int** code: 狀態碼
    - **str** message: 訊息
    - **object** data: 生成的 QR code 資料
        - **str** token: QR code token
        - **str** original_url: QR code 對應的原始 URL
        - **datetime** created_at: QR code 生成時間
        - **datetime** updated_at: QR code 最後更新時間
        - **Optional[datetime]** expires_at: QR code 過期時間 (若有設定)
        - **bool** is_deleted: QR code 是否已刪除
    """
    return await redirect_controller.redirect(redirect_request.qr_token)
