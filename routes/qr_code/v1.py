"""實作計算委刊單價 route"""

from fastapi import APIRouter, Depends, Response

from libs.controllers.qr_code.v1 import QRCodeController
from libs.models.qr_code.v1 import QR_CREATE_RESPONSE_EXAMPLES, QRCreateRequest

# router object
router = APIRouter(prefix="/api/qr_code/v1")


@router.post(
    "",
    responses=QR_CREATE_RESPONSE_EXAMPLES,
)
async def create_qr_code(
    response: Response,
    qr_create_request: QRCreateRequest,
    qr_code_controller: QRCodeController = Depends(QRCodeController),
):
    """
    QR code 產生器 API

    根據提供的 URL 生成 QR code，並可選擇設定過期時間

    Request:
    - **object** data: QR code 生成請求資料
      - **str** url: 要生成 QR code 的 URL (必填)
      - **Optional[datetime]** expires_at: QR code 過期時間 (選填)


    Response:
    - **str** status: 執行狀態 (success / fail)
    - **int** code: 狀態碼
    - **str** message: 訊息
    - **object** data: 生成的 QR code 資料
      - **str** qr_token: 生成的 QR code 圖片的 base64 編碼字符串
    """
    response.status_code, return_response = await qr_code_controller.create(
        qr_create_request.url, qr_create_request.expires_at
    )
    return return_response
