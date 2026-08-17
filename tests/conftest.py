import asyncio
from datetime import datetime
from datetime import timedelta

import asyncpg
import pytest
from asyncpg import PostgresError
from starlette.testclient import TestClient

from app.api.utils import user_token_sub
from app.core.config import settings
from app.core.security import create_access_token
from app.core.security import get_password_hash
from app.db.init_db_schema_and_functions import init_db_schema_and_functions
from app.main import app
from app.models.user import User

test_user_in_db = {
    "user_uuid": "1088292a-46cc-4258-85b6-9611f09e1830",
    "username": "testuser_in_db",
    "email": "testuser_in_db@mail.com",
    "is_active": True,
    "created_at": datetime.now(),
    "updated_at": datetime.now(),
}


TEST_USER_IN_DB_PASSWORD = "superstrongpassword"


test_board_in_db = {
    "board_uuid": "a4264b97-df71-442f-b3ca-b018d473a803",
    "board_name": "test board",
    "column_order": [],
    "owner_uuid": test_user_in_db.get("user_uuid"),
}


test_access_token = create_access_token(
    data={"sub": user_token_sub(User(**test_user_in_db))}, expires_delta=timedelta(settings.ACCESS_TOKEN_EXPIRE_MINUTES)
)


def init_test_db():
    # create user in db matching the user_in_db fixture below
    async def create_existing_test_user():
        conn = await asyncpg.connect(settings.TEST_DATABASE_URL)

        hashed_pwd = get_password_hash(TEST_USER_IN_DB_PASSWORD)
        test_user_uuid = test_user_in_db.get("user_uuid")
        test_user_username = test_user_in_db.get("username")
        test_user_email = test_user_in_db.get("email")

        test_board_uuid = test_board_in_db.get("board_uuid")
        test_board_name = test_board_in_db.get("board_name")
        test_board_owner_uuid = test_board_in_db.get("owner_uuid")

        insert_existing_test_user = """
            INSERT INTO users (user_uuid, username, email, is_active, password)
            VALUES ($1, $2, $3, true, $4);
        """
        insert_existing_test_board = """
            INSERT INTO boards (board_uuid, board_name, column_order, owner_uuid)
            VALUES ($1, $2, NULL, $3);
        """

        try:
            await conn.execute(
                insert_existing_test_user, test_user_uuid, test_user_username, test_user_email, hashed_pwd
            )
            await conn.execute(insert_existing_test_board, test_board_uuid, test_board_name, test_board_owner_uuid)
        except PostgresError as err:
            print(err)
        finally:
            await conn.close()

    asyncio.get_event_loop().run_until_complete(init_db_schema_and_functions(test=True))
    asyncio.get_event_loop().run_until_complete(create_existing_test_user())


def clean_up():
    async def clear_test_db():
        print("\n\nClearing test pg db and redis...")
        conn = await asyncpg.connect(settings.TEST_DATABASE_URL)
        redis = settings.REDIS

        # drop schema
        # this clears all the data, types and functions from public schema
        drop_schema = """
            DROP SCHEMA public CASCADE;
            CREATE SCHEMA public;
        """

        try:
            await conn.execute(drop_schema)
            await redis.flushdb(asynchronous=True)
        except PostgresError as err:
            print(err)
        finally:
            await conn.close()

    asyncio.get_event_loop().run_until_complete(clear_test_db())


def pytest_sessionstart():
    """whole test run starts."""
    settings.DATABASE_URL = settings.TEST_DATABASE_URL
    settings.REDIS_URL = settings.TEST_REDIS_URL
    init_test_db()


def pytest_sessionfinish():
    """whole test run finishes."""
    clean_up()


@pytest.fixture
def test_user():
    return {"username": "testuser", "password": "verystrongpassword"}


# user created during test db init
@pytest.fixture
def user_in_db():
    return {"username": test_user_in_db.get("username"), "password": TEST_USER_IN_DB_PASSWORD}


@pytest.fixture
def test_client():
    with TestClient(app) as client:
        yield client
