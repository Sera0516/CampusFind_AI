
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES


# Password hashing configuration
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# JWT configuration
ALGORITHM = "HS256"


# Hash user password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# Verify user password
def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


# Generate JWT access token
def create_access_token(subject: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": subject,
        "exp": expires
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token


# Validate JWT access token
def verify_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        subject = payload.get("sub")

        if subject is None:
            print("JWT ERROR: Missing subject")
            return None

        return subject

    except JWTError as exc:
        print("JWT VALIDATION ERROR:", repr(exc))
        return None
