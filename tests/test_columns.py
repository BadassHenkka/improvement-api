from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

from .conftest import test_access_token
from .conftest import test_board_in_db
from app.main import app


client = TestClient(app)

test_board_uuid = test_board_in_db.get("board_uuid")
test_board_websocket_url = f"api/board/ws/{test_board_uuid}"


def handle_ws_auth(websocket: WebSocket):
    websocket.send_json({"type": "authenticate", "data": test_access_token})


def test_connecting_to_board_websocket():
    with client.websocket_connect(test_board_websocket_url) as websocket:
        handle_ws_auth(websocket)
        data = websocket.receive_json()

        column_order = data.get("column_order")
        columns = data.get("columns")

        # should be empty when first connecting
        assert column_order == []
        assert columns == []


def test_creating_columns():
    with client.websocket_connect(test_board_websocket_url) as websocket:
        handle_ws_auth(websocket)
        for i in range(1, 6):
            data = websocket.receive_json()
            column_order = data.get("column_order")

            new_column = {"column_name": f"test column {i}", "board_uuid": test_board_uuid}

            column_creation_data = {"new_column": new_column, "column_order": column_order}

            websocket.send_json({"crud": "create", "data": column_creation_data})

    with client.websocket_connect(test_board_websocket_url) as websocket:
        handle_ws_auth(websocket)
        data = websocket.receive_json()

        column_order = data.get("column_order")
        columns = data.get("columns")

        assert len(column_order) == 5
        assert len(columns) == 5
        assert columns[2].get("column_name") == "test column 3"

        last_col_uuid = columns[4].get("column_uuid")

        assert column_order[4] == last_col_uuid


def test_updating_columns():
    col_id_1 = ""
    col_id_2 = ""

    with client.websocket_connect(test_board_websocket_url) as websocket:
        handle_ws_auth(websocket)
        for i in range(1, 3):
            data = websocket.receive_json()
            columns = data.get("columns")
            column_order = data.get("column_order")

            updated_column_order = [*column_order]

            if i == 1:
                col_id_1 = columns[i].get("column_uuid")
                updated_column_order.pop(column_order.index(col_id_1))

                # insert to the end of column_order
                updated_column_order.insert(len(column_order), col_id_1)

            if i == 2:
                col_id_2 = columns[i].get("column_uuid")
                updated_column_order.pop(column_order.index(col_id_2))

                # insert on the third spot
                updated_column_order.insert(2, col_id_2)

            updated_col_name = "test column with updated name" if i == 2 else "test column 1"

            updated_column = {
                "column_uuid": col_id_1 if i == 1 else col_id_2,
                "column_name": updated_col_name,
                "board_uuid": test_board_uuid,
            }

            updated_column_data = {"updated_column": updated_column, "column_order": updated_column_order}

            websocket.send_json({"crud": "update", "data": updated_column_data})

    with client.websocket_connect(test_board_websocket_url) as websocket:
        handle_ws_auth(websocket)
        data = websocket.receive_json()
        columns = data.get("columns")
        column_order = data.get("column_order")

        last_col_id = columns[len(columns) - 1].get("column_uuid")

        assert last_col_id == col_id_1
        assert column_order.index(col_id_2) == 2

        col_with_updated_name = next(
            (col for col in columns if col["column_name"] == "test column with updated name"), None
        )
        assert col_with_updated_name


def test_deleting_columns():
    col_id_1 = ""
    col_id_2 = ""

    with client.websocket_connect(test_board_websocket_url) as websocket:
        handle_ws_auth(websocket)
        data = websocket.receive_json()

        columns = data.get("columns")
        column_order = data.get("column_order")

        col_id_1 = columns[0].get("column_uuid")

        updated_column_order = [*column_order]
        updated_column_order.pop(column_order.index(col_id_1))

        column_deletion_data = {"column_uuid": col_id_1, "column_order": updated_column_order}

        websocket.send_json({"crud": "delete", "data": column_deletion_data})

    with client.websocket_connect(test_board_websocket_url) as websocket:
        handle_ws_auth(websocket)
        data = websocket.receive_json()

        columns = data.get("columns")
        column_order = data.get("column_order")

        col_id_2 = columns[2].get("column_uuid")

        updated_column_order = [*column_order]
        updated_column_order.pop(column_order.index(col_id_2))

        column_deletion_data = {"column_uuid": col_id_2, "column_order": updated_column_order}

        websocket.send_json({"crud": "delete", "data": column_deletion_data})

    with client.websocket_connect(test_board_websocket_url) as websocket:
        handle_ws_auth(websocket)
        data = websocket.receive_json()
        columns = data.get("columns")
        column_order = data.get("column_order")

        assert len(columns) == 3
        assert len(column_order) == 3

        deleted_col_1 = next((col for col in columns if col["column_uuid"] == col_id_1), None)
        deleted_col_2 = next((col for col in columns if col["column_uuid"] == col_id_2), None)

        assert deleted_col_1 is None
        assert deleted_col_2 is None

        assert col_id_1 not in column_order
        assert col_id_2 not in column_order
