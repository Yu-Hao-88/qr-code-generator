"""使用 SHA256 + base62 生成 token"""

import hashlib
import secrets
import string

BASE62_CHARS = string.ascii_letters + string.digits


def __to_base62(n: int) -> str:
    """
    將整數轉換為 Base62 字串

    Args:
        n (int): 非負整數

    Returns:
        str: Base62 編碼字串
    """
    if n == 0:
        return BASE62_CHARS[0]
    digits = []
    while n:
        digits.append(BASE62_CHARS[n % 62])
        n //= 62
    return "".join(reversed(digits))


def generate_token(url: str, length: int = 8) -> str:
    """
    產生 token

    Args:
        url (str): 網址
        length (int): token 長度，預設 8

    Returns:
        str: Base62 編碼的 token
    """
    salt = secrets.token_bytes(16)
    digest = hashlib.sha256(salt + url.encode()).digest()
    token = __to_base62(int.from_bytes(digest, byteorder="big"))
    return token[:length]
