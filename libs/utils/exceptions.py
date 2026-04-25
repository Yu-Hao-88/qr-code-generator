"""存放客製化 exception"""

from fastapi import status as http_status

# -- General Exception -- #
# 所有 General Exception 都可以直接交由 main 中的 handler 抓取處理


class DataNotFoundError(Exception):
    def __init__(
        self,
        code: int = http_status.HTTP_404_NOT_FOUND,
        message: str = "",
    ) -> None:
        """查無資料時拋出的 Error"""
        super().__init__(message)
        self.message = message
        self.code = code


class DataGoneError(Exception):
    def __init__(
        self,
        code: int = http_status.HTTP_410_GONE,
        message: str = "",
    ) -> None:
        """資料已被刪除時拋出的 Error"""
        super().__init__(message)
        self.message = message
        self.code = code
