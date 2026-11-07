from app.services.security import (
    hash_password,
    verify_password,
    create_access_token,
    verify_access_token,
)


def test_password_hashing():
    password = "TestPassword@123"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)


def test_wrong_password_rejected():
    hashed = hash_password("CorrectPassword@123")

    assert not verify_password("WrongPassword@123", hashed)


def test_jwt_token_creation_and_validation():
    token = create_access_token("123")

    assert isinstance(token, str)
    assert verify_access_token(token) == "123"


def test_invalid_jwt_rejected():
    assert verify_access_token("invalid.test.token") is None
