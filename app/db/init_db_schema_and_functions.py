import asyncio
from os import listdir
from os import path
from typing import Optional

import asyncpg

from app.core.config import settings

dir_path = path.dirname(path.abspath(__file__).replace("db", ""))


SCHEMA_DIR = f"{dir_path}/db/schema"
FUNCTION_DIR = f"{dir_path}/db/functions"


def read_sql_file(file_path):
    with open(file_path, "r") as f:
        content = f.read()
        return f"{content}\n"


def create_db_schema():
    schema = ""
    for file in sorted(listdir(SCHEMA_DIR)):
        if file.endswith(".sql"):
            file_path = f"{SCHEMA_DIR}/{file}"
            file_content = read_sql_file(file_path)
            schema += f"{file_content}\n"
    return schema


def create_db_functions():
    functions = ""
    for file in sorted(listdir(FUNCTION_DIR)):
        if file.endswith(".sql"):
            file_path = f"{FUNCTION_DIR}/{file}"
            file_content = read_sql_file(file_path)
            functions += f"{file_content}\n"
    return functions


async def init_db_schema_and_functions(test: Optional[bool] = False):
    if test:
        print("Using test db url...")
        conn = await asyncpg.connect(settings.TEST_DATABASE_URL)
    else:
        conn = await asyncpg.connect(settings.DATABASE_URL)

    try:
        schema = create_db_schema()
        functions = create_db_functions()

        await conn.execute(f"{schema} {functions}")
    except Exception as err:
        print(err)
    finally:
        await conn.close()

    return print("DB schema and functions initialized")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init_db_schema_and_functions())
