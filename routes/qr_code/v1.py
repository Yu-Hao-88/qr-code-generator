"""實作計算委刊單價 route"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request, Response

from libs.controllers.qr_code.v1 import QRCodeController
from libs.models.qr_code.v1 import (
    QR_CREATE_RESPONSE_EXAMPLES,
    QR_DELETE_RESPONSE_EXAMPLES,
    QR_IMAGE_RESPONSE_EXAMPLES,
    QR_INFO_RESPONSE_EXAMPLES,
    QR_UPDATE_RESPONSE_EXAMPLES,
    QRCreateRequest,
    QRDeletePathRequest,
    QRImageRequest,
    QRInfoRequest,
    QRUpdateBodyRequest,
    QRUpdatePathRequest,
)
from libs.utils.limiter import RATE_LIMITER

# router object
router = APIRouter(prefix="/api/qr_code/v1", tags=["qr_code"])


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


@router.get(
    "/{qr_token}",
    responses=QR_INFO_RESPONSE_EXAMPLES,
)
@RATE_LIMITER.limiter.limit("30/minute")
async def get_qr_info(
    request: Request,
    response: Response,
    qr_info_request: Annotated[QRInfoRequest, Path()],
    qr_code_controller: QRCodeController = Depends(QRCodeController),
):
    """
    QR code 查詢 API

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
    response.status_code, return_response = await qr_code_controller.get_info(
        qr_info_request.qr_token
    )
    return return_response


@router.put(
    "/{qr_token}",
    responses=QR_UPDATE_RESPONSE_EXAMPLES,
)
async def update_qr_code(
    response: Response,
    qr_update_path_request: Annotated[QRUpdatePathRequest, Path()],
    qr_update_body_request: QRUpdateBodyRequest,
    qr_code_controller: QRCodeController = Depends(QRCodeController),
):
    """
    QR code 更新 API

    根據提供的 QR code token 更新 QR code 資訊

    Request:
    - **object** data: QR code 更新請求資料
      - **str** qr_token: 要更新的 QR code 的 token (必填)
      - **str** url: 要修改的新 URL (必填)


    Response:
    - **str** status: 執行狀態 (success / fail)
    - **int** code: 狀態碼
    - **str** message: 訊息
    """
    response.status_code, return_response = await qr_code_controller.update(
        qr_update_path_request.qr_token,
        qr_update_body_request.url,
    )
    return return_response


@router.delete(
    "/{qr_token}",
    responses=QR_DELETE_RESPONSE_EXAMPLES,
)
async def delete_qr_code(
    response: Response,
    qr_delete_path_request: Annotated[QRDeletePathRequest, Path()],
    qr_code_controller: QRCodeController = Depends(QRCodeController),
):
    """
    QR code 刪除 API

    根據提供的 QR code token 刪除 QR code 資訊

    Request:
    - **object** data: QR code 刪除請求資料
      - **str** qr_token: 要刪除的 QR code 的 token (必填)


    Response:
    - **str** status: 執行狀態 (success / fail)
    - **int** code: 狀態碼
    - **str** message: 訊息
    """
    response.status_code, return_response = await qr_code_controller.delete(
        qr_delete_path_request.qr_token
    )
    return return_response


@router.get(
    "/{qr_token}/image",
    responses=QR_IMAGE_RESPONSE_EXAMPLES,
)
@RATE_LIMITER.limiter.limit("30/minute")
async def get_qr_image(
    request: Request,
    response: Response,
    qr_image_request: Annotated[QRImageRequest, Path()],
    qr_code_controller: QRCodeController = Depends(QRCodeController),
):
    """
    QR code 圖片查詢 API

    根據提供的 QR code token 查詢 QR code 圖片

    Request:
    - **object** data: QR code 查詢請求資料
      - **str** qr_token: 要查詢的 QR code 的 token (必填)

    Response:
    - **bytes** 圖片二進位資料 (Content-Type: image/png)
    """
    response.status_code, return_response = await qr_code_controller.get_image(
        qr_image_request.qr_token
    )
    return return_response
