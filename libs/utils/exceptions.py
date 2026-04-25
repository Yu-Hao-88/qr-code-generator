"""存放客製化 exception"""

# -- General Exception -- #
# 所有 General Exception 都可以直接交由 main 中的 handler 抓取處理


class DataNotFoundError(Exception):
    def __init__(self, code: int = 404, message: str = "") -> None:
        """查無資料時拋出的 Error"""
        super().__init__(message)
        self.message = message
        self.code = code
