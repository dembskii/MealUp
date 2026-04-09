import pytest
from fastapi import HTTPException

from src.api.routes import get_user_id


def test_get_user_id_prefers_header_over_token_sub():
    user_id = get_user_id("gateway-id", {"sub": "jwt-sub"})
    assert user_id == "gateway-id"


def test_get_user_id_falls_back_to_token_sub():
    user_id = get_user_id(None, {"sub": "jwt-sub"})
    assert user_id == "jwt-sub"


def test_get_user_id_raises_401_when_identity_missing():
    with pytest.raises(HTTPException) as exc:
        get_user_id(None, {})

    assert exc.value.status_code == 401
    assert exc.value.detail == "Unable to determine user identity"
