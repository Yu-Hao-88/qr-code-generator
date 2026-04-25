"""實作 API 通用型的 model"""

from collections import defaultdict

from pydantic import BaseModel, ConfigDict, Field


class GeneralModel(BaseModel):
    status: str = Field(..., title="狀態")
    code: int = Field(..., title="狀態碼")
    message: str = Field(..., title="訊息")
    data: dict = Field(..., title="回應資料")


class ResponseOK(GeneralModel):
    status: str = "success"
    code: int = 200
    message: str = ""
    data: dict = {}
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "code": 200,
                "message": "",
                "data": {},
            }
        }
    )


class ResponseBadRequest(GeneralModel):
    status: str = "fail"
    code: int = 400
    message: str = "參數錯誤說明"
    data: dict = {}
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "fail",
                "code": 400,
                "message": "參數錯誤說明",
                "data": {},
            }
        }
    )


class ResponseForbidden(GeneralModel):
    status: str = "fail"
    code: int = 403
    message: str = "禁止存取"
    data: dict = {}
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "fail",
                "code": 403,
                "message": "禁止存取",
                "data": {},
            }
        }
    )


class ResponseNotFound(GeneralModel):
    status: str = "fail"
    code: int = 404
    message: str = "找不到資源"
    data: dict = {}
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "fail",
                "code": 404,
                "message": "找不到資源",
                "data": {},
            }
        }
    )


class ResponseTooManyRequests(GeneralModel):
    status: str = "fail"
    code: int = 429
    message: str = "請求過於頻繁，請稍後再試"
    data: dict = {}
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "fail",
                "code": 429,
                "message": "請求過於頻繁，請稍後再試",
                "data": {},
            }
        }
    )


class ResponseInternalServerError(GeneralModel):
    status: str = "fail"
    code: int = 500
    message: str = "執行失敗，請通知相關人員"
    data: dict = {}
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "fail",
                "code": 500,
                "message": "執行失敗，請通知相關人員",
                "data": {},
            }
        }
    )


class ResponseBadGatewayError(GeneralModel):
    status: str = "fail"
    code: int = 502
    message: str = "上游伺服器傳回了無效回應"
    data: dict = {}
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "fail",
                "code": 502,
                "message": "上游伺服器傳回了無效回應",
                "data": {},
            }
        }
    )


def generate_response_examples(api_response_examples: list) -> dict:
    """
    將一組包含 status_code、response_name、example 的定義清單，轉換成 FastAPI 可用的 response_model examples 格式。

    註：此函式會自動補上公版的 internal_server_error response

    Args:
        api_response_examples (list[dict]): 每個 dict 需包含以下鍵：
            - status_code (int): HTTP status code
            - response_name (str): response example 名稱（e.g. "success"）
            - example (dict): 該 response 的實際內容

    Returns:
        dict: FastAPI router 中 responses 參數可用的 dict 格式。
    """
    # 補上公版 internal_server_error response
    api_response_examples.append(
        {
            "status_code": 500,
            "response_name": "internal_server_error",
            "example": ResponseInternalServerError.model_json_schema()["example"],
        },
    )

    responses = defaultdict(lambda: {"content": {"application/json": {"examples": {}}}})
    for item in api_response_examples:
        status_code = item["status_code"]
        name = item["response_name"]
        example = item["example"]

        responses[status_code]["content"]["application/json"]["examples"][name] = {
            "value": example
        }
    return dict(responses)
