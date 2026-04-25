"""實作 API 介面"""

import asyncio
import json
import logging
import traceback

import uvicorn
import uvloop
from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

import context
import libs.models.general as general_models
import libs.utils.exceptions as custom_exc
from libs.utils.api_config import ApiConfig
from libs.utils.limiter import RateLimiter
from routes.qr_code.v1 import router as qr_code_router
from routes.redirect.v1 import router as redirect_router

# 改用 uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
policy = asyncio.get_event_loop_policy()
logging.basicConfig(level=logging.INFO)
logging.info("Current asyncio event loop policy: %s", policy)

# 新增 router 只需要加在這裡即可，swagger 顯示的順序會和這邊一樣
all_routers = [qr_code_router, redirect_router]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


app = FastAPI(
    title="QR Code Generator API",
    docs_url=ApiConfig.DOCS_URL,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.state.limiter = RateLimiter.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Override fastapi 422 response"""
    reasons = []
    for error in exc.errors():
        match error["type"]:
            case "value_error":
                # 自訂的一些 value error 直接回傳 msg
                reasons.append(f"loc {error['loc']} {error['msg']}")
            case "json_invalid":
                reasons.append("請提供合法的 json")
            case "missing":
                reasons.append(f"少了 {error['loc']} 欄位")
            case "float_type" | "float_parsing":
                reasons.append(f"loc {error['loc']} 需為浮點數")
            case "int_type" | "int_parsing" | "int_from_float":
                reasons.append(f"loc {error['loc']} 需為整數")
            case "bool_type" | "bool_parsing":
                reasons.append(f"loc {error['loc']} 需為布林值")
            case "string_type":
                reasons.append(f"loc {error['loc']} 需為字串")
            case "greater_than_equal":
                reasons.append(
                    f"loc {error['loc']} 必須是大於等於 {error['ctx']['ge']}"
                )
            case "string_too_long":
                reasons.append(
                    f"loc {error['loc']} 字串長度必須是小於等於 {error['ctx']['max_length']}"
                )
            case "enum":
                reasons.append(
                    f"loc {error['loc']} 需為 {error['ctx']['expected']} 中的值"
                )
    if reasons:
        message = ", ".join(reasons)
    else:
        message = "沒有抓取到的錯誤，請提供 data 中的 request body 以便解析"
        logging.error("抓取不到的錯誤：%s", exc.errors())

    # 取得並解析 request body
    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8")
    try:
        body_json = json.loads(body_str) if body_str else {}
        logging.info("RequestValidationError Body: %s", body_json)
    except json.JSONDecodeError:
        body_json = {}
        logging.info("RequestValidationError Body: %s", body_str)

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=general_models.ResponseBadRequest(
            message=message,
            data=body_json,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def internal_server_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """捕捉所有非預期例外，統一回傳 HTTP 500"""
    logging.error(traceback.format_exc())
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=general_models.ResponseInternalServerError().model_dump(),
    )


@app.exception_handler(custom_exc.DataNotFoundError)
async def data_not_found_error_handler(
    request: Request,
    exc: custom_exc.DataNotFoundError,
) -> JSONResponse:
    """捕捉共用例外 DataNotFoundError，統一回傳 HTTP 404"""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=general_models.ResponseNotFound(
            message=exc.message,
            code=exc.code,
        ).model_dump(),
    )


@app.exception_handler(custom_exc.DataGoneError)
async def data_gone_error_handler(
    request: Request,
    exc: custom_exc.DataGoneError,
) -> JSONResponse:
    """捕捉共用例外 DataGoneError，統一回傳 HTTP 410"""
    return JSONResponse(
        status_code=status.HTTP_410_GONE,
        content=general_models.ResponseGone(
            message=exc.message,
            code=exc.code,
        ).model_dump(),
    )


@app.get("/")
def homepage(response: Response):
    """Homepage"""
    response.status_code = status.HTTP_200_OK
    return response.status_code


# add router
for route in all_routers:
    # /receiveSale 為服務名稱 固定在最前面
    app.include_router(route)


if __name__ == "__main__":
    # start web API service
    uvicorn.run(
        "main:app",
        host=ApiConfig.HOST,
        port=ApiConfig.PORT,
        reload=ApiConfig.RELOAD,
        workers=ApiConfig.WORKERS,
        http="httptools",
    )
