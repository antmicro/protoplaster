import hashlib
import hmac

_token: bytes = b""


def set_token(token: str):
    global _token
    _token = token.encode()


def sign(data: bytes) -> str:
    return hmac.new(_token, data, hashlib.sha256).hexdigest()


def verify(signature: str | None, data: bytes) -> bool:
    return signature is not None and hmac.compare_digest(sign(data), signature)
