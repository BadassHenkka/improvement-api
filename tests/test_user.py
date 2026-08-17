from fastapi.testclient import TestClient
from requests.structures import CaseInsensitiveDict  # type: ignore

from app.models.user import User

user_data_keys = User.schema().get("properties").keys()


def test_should_return_user_data(user_in_db, test_client):
    response = test_client.post("/api/auth/access-token", data=user_in_db)
    assert response.status_code == 200

    data = response.json()
    token = data.get("accessToken")

    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Authorization"] = f"Bearer {token}"

    response = test_client.get("/api/user/me", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert user_data_keys == data.keys()
    assert user_in_db.get("username") == data.get("username")
