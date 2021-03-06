from typing import List
from typing import Optional

from asyncpg import PostgresError
from asyncpg.connection import Connection
from fastapi import HTTPException
from pydantic.types import UUID4

from app.crud.card import update_card_and_order_in_columns
from app.db.decorators import dbconn
from app.models.card import CardAndOrderInColumns
from app.models.column import Column
from app.models.column import ColumnCreate


@dbconn
async def create_column_and_update_board_column_order(
    conn: Connection, column: ColumnCreate, column_order: Optional[List[UUID4]]
):
    try:
        column_and_board_column_order = await conn.fetchrow(
            "SELECT * FROM create_column_and_update_board_column_order($1,$2,$3);",
            column.column_name,
            column.board_uuid,
            column_order,
        )

        return column_and_board_column_order
    except PostgresError:
        raise HTTPException(status_code=500, detail="Error while trying to create a column.")


@dbconn
async def update_column_and_update_board_column_order(
    conn: Connection, column: Column, column_order: Optional[List[UUID4]]
):
    try:
        column_and_board_column_order = await conn.fetchrow(
            "SELECT * FROM update_column_and_update_board_column_order($1,$2,$3,$4);",
            column.column_uuid,
            column.column_name,
            column.board_uuid,
            column_order,
        )

        return column_and_board_column_order
    except PostgresError:
        raise HTTPException(status_code=500, detail="Error while trying to update a column.")


@dbconn
async def delete_column_and_update_board_column_order(
    conn: Connection, board_uuid: UUID4, column_uuid: UUID4, column_order: List[UUID4]
):
    try:
        deleted_column_response = await conn.fetchrow(
            "SELECT * FROM delete_column_and_update_board_column_order($1,$2,$3);",
            board_uuid,
            column_uuid,
            column_order,
        )

        return deleted_column_response
    except PostgresError:
        raise HTTPException(status_code=500, detail="Error while trying to delete the column.")


@dbconn
async def update_single_column_card_order(conn: Connection, column_uuid: UUID4, card_order: List[UUID4]):
    try:
        column_card_order = await conn.fetchrow(
            "SELECT * FROM update_single_column_card_order($1,$2);",
            column_uuid,
            card_order,
        )

        return column_card_order
    except PostgresError:
        raise HTTPException(status_code=500, detail="Error while trying to update a column's card order.")


async def handle_column_crud(board_uuid: str, crud_type: str, data: dict):
    column_order = data.get("column_order")

    if crud_type == "create":
        new_col_data = data.get("new_column")
        return await create_column_and_update_board_column_order(ColumnCreate(**new_col_data), column_order)  # type: ignore

    if crud_type == "update":
        updated_col_data = data.get("updated_column")
        return await update_column_and_update_board_column_order(Column(**updated_col_data), column_order)  # type: ignore

    if crud_type == "delete":
        return await delete_column_and_update_board_column_order(board_uuid, data.get("column_uuid"), column_order)

    if crud_type == "update-card-order":
        card_order = data.get("card_order")
        return await update_single_column_card_order(data.get("column_uuid"), card_order)

    if crud_type == "update-card-and-order-in-columns":
        return await update_card_and_order_in_columns(CardAndOrderInColumns(**data))  # type: ignore


async def get_board_columns(conn: Connection, board_uuid: UUID4):
    try:
        board_columns = await conn.fetch("SELECT * FROM get_board_columns($1);", board_uuid)

        return board_columns
    except PostgresError:
        raise HTTPException(status_code=500, detail="Error while fetching the board columns.")
