from jose import jwt
from starlette.testclient import TestClient

from app.core.config import settings

access_res_dict = {"accessToken": 1, "tokenType": 2}


def check_access_token_response(response, test_user):
    assert response.status_code == 200

    data = response.json()

    assert data.keys() >= access_res_dict.keys()

    token = data.get("accessToken")
    payload_sub = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]).get("sub")

    assert payload_sub.find(test_user.get("username")) != -1


def test_should_register_a_new_user_and_return_token(test_user, test_client: TestClient):
    response = test_client.post("/api/auth/register", data=test_user)
    check_access_token_response(response, test_user)


def test_register_should_fail_with_existing_username(test_user, test_client: TestClient):
    response = test_client.post("/api/auth/register", data=test_user)
    assert response.status_code == 400

    data = response.json()

    assert data.get("detail") == "This username is already taken."


def test_should_create_access_token(test_user, test_client: TestClient):
    response = test_client.post("/api/auth/access-token", data=test_user)
    check_access_token_response(response, test_user)
