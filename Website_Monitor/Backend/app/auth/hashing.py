from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

MAX_BCRYPT_BYTES = 72

def _safe_password(password: str) -> str:
    """
    bcrypt supports only 72 BYTES.
    This prevents runtime crash.
    """
    raw = password.encode("utf-8")
    if len(raw) > MAX_BCRYPT_BYTES:
        return raw[:MAX_BCRYPT_BYTES].decode("utf-8", errors="ignore")
    return password

def hash_password(password: str) -> str:
    password = _safe_password(password)
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    plain = _safe_password(plain)
    return pwd_context.verify(plain, hashed)
