import asyncio
from typing import List

from fastapi import APIRouter
from fastapi import Depends
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from pydantic.types import UUID4
from starlette.responses import Response
from starlette.status import HTTP_404_NOT_FOUND

from app.api.dependancies import get_current_active_user
from app.core.config import settings
from app.crud.board import create_board
from app.crud.board import delete_board
from app.crud.board import get_board_column_order
from app.crud.board import get_user_board
from app.crud.board import get_user_boards
from app.crud.board import update_board
from app.crud.card import get_board_cards
from app.crud.card import handle_card_crud
from app.crud.column import get_board_columns
from app.crud.column import handle_column_crud
from app.models.board import Board
from app.models.board import BoardCreate
from app.models.user import User
from app.redis.pub import publish
from app.redis.sub import subscribe_and_read
from app.utils.board import transform_and_sort_column_cards
from app.utils.board import transform_column
from app.websocket import ConnectionManager

board_router = APIRouter()


@board_router.post("/create", dependencies=[Depends(get_current_active_user)], response_model=Board)
async def create_new_board(board_data: BoardCreate):
    new_board = await create_board(board_data)

    return Board(**new_board)


@board_router.get("/list", response_model=List[Board])
async def list_user_boards(current_user: User = Depends(get_current_active_user)):
    user_boards = await get_user_boards(current_user.user_uuid)

    return user_boards


@board_router.get("/list/{board_uuid}", response_model=Board)
async def get_one_user_board(board_uuid: UUID4, current_user: User = Depends(get_current_active_user)):
    user_board = await get_user_board(current_user.user_uuid, board_uuid)

    return Board(**user_board) if user_board else Response(status_code=HTTP_404_NOT_FOUND)


@board_router.put("/update", response_model=Board)
async def update_user_board(updated_board_data: Board, current_user: User = Depends(get_current_active_user)):
    new_board = await update_board(updated_board_data, current_user.user_uuid)

    return Board(**new_board)


@board_router.delete("/delete/{board_uuid}")
async def delete_user_board(board_uuid: UUID4, current_user: User = Depends(get_current_active_user)):
    delete_board_response = await delete_board(board_uuid, current_user.user_uuid)

    return delete_board_response


async def get_board_data(board_uuid: UUID4):
    conn_pool = settings.CONN_POOL

    async with conn_pool.acquire() as conn:
        board_column_records = await get_board_columns(conn, board_uuid)

        if not board_column_records:
            return {"column_order": [], "columns": {}, "cards": {}}

        board_column_order_record = await get_board_column_order(conn, board_uuid)
        board_card_records = await get_board_cards(conn, board_uuid)

        board_columns = {str(column.get("column_uuid")): transform_column(column) for column in board_column_records}

        column_order = [str(col_uuid) for col_uuid in board_column_order_record[0]] if board_column_order_record else []

        # {"col-uuid-1": [card1, card2], "col-uuid-2": [card4, card3]}
        sorted_board_cards = (
            {column[0]: transform_and_sort_column_cards(board_card_records, column) for column in board_columns.items()}
            if board_card_records
            else {}
        )

        board_data = {"column_order": column_order, "columns": board_columns, "cards": sorted_board_cards}

        return board_data


@board_router.websocket("/ws/{board_uuid}")
async def board_ws_endpoint(websocket: WebSocket, board_uuid: UUID4):
    board_ws_manager = ConnectionManager()

    init_board_data = await get_board_data(board_uuid)

    await board_ws_manager.connect(websocket, init_board_data)
    ws_conn_open = websocket in board_ws_manager.active_connections

    async def handle_update_board_data():
        updated_board_data = await get_board_data(board_uuid)
        await board_ws_manager.send_json_data(updated_board_data, websocket)

    board_pubsub_channel = f"board:{board_uuid}"

    board_pubsub_task = asyncio.create_task(subscribe_and_read(board_pubsub_channel, handle_update_board_data))

    try:
        while ws_conn_open:
            data_dict = await websocket.receive_json()
            crud_target = data_dict.get("target")
            crud_type = data_dict.get("crud")

            if crud_target == "column":
                await handle_column_crud(board_uuid, crud_type, data_dict.get("data"))

            if crud_target == "card":
                await handle_card_crud(board_uuid, crud_type, data_dict.get("data"))

            if crud_target:
                # trigger all board subscribers to fetch updated data
                await publish(board_pubsub_task, board_pubsub_channel, "get_board_data")

    except WebSocketDisconnect:
        board_ws_manager.disconnect(websocket)

        board_pubsub_task.cancel()
        if settings.REDIS:
            await settings.REDIS.close()
