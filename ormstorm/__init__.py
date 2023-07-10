import sqlite3

from .orm.column import Column, ColumnType
from .orm.constants import Types
from .orm.table import Table, DynamicTable

from typing import Callable


class Session(object):
    def __init__(self, path: str, tables: list[type[Table] | DynamicTable] = None, **kwargs) -> None:

        """
        Creates a new session to work with the database.

        :param path: Path to the database
        :param tables: List of tables to be created during session initialization
        :param kwargs: Other options for opening a database [ More details in `sqlite3.connect(...)` ]
        """

        self._database = sqlite3.connect(path, **kwargs)
        self._tables = tables or []

        for table in self._tables:
            self.create(table)

    def create(self, table: type[Table] | DynamicTable) -> None:

        """
        Creates a new table in the database.

        :param table: Table or dynamic table
        :return: Nothing
        """

        self._database.execute(f"CREATE TABLE IF NOT EXISTS {table.__tablename__} "
                               f"({', '.join([column.serialize() for column in table.columns().values()])})")
        self._database.commit()

    def clear(self, table: type[Table] | DynamicTable) -> None:

        """
        Clears the selected table.

        :param table: Table or dynamic table
        :return: Nothing
        """

        self._database.execute(
            f"DELETE FROM {table.__tablename__}"
        )
        self._database.commit()

    def drop(self, table: type[Table] | DynamicTable) -> None:

        """
        Completely removes the table from the database.

        :param table: Table or dynamic table
        :return: Nothing
        """

        self._database.execute(
            f"DROP TABLE IF EXISTS {table.__tablename__}"
        )
        self._database.commit()

    def insert(self, table: Table, replace: bool = False) -> None:

        """
        Adds a new row to the table.

        :param table: Initialized table object
        :param replace: Will replace an existing row
        :return: Nothing
        """

        values = table.values

        self._database.execute(
            f"INSERT {'OR REPLACE' if replace else ''} INTO {table.__tablename__} ({', '.join(values.keys())}) "
            f"VALUES ({', '.join(['?'] * len(values))})", list(values.values())
        )
        self._database.commit()

    def delete(self, column: Column | ColumnType, value: object) -> None:

        """
        Deletes the selected row in the table.

        :param column: The column for which you want to delete the row
        :param value: The value by which to delete the row
        :return: Nothing
        """

        self._database.execute(
            f"DELETE FROM {column.table} WHERE {column.name} = ?", (value, )
        )
        self._database.commit()

    def exists(self, column: Column | ColumnType, value: object) -> bool:

        """
        Checks for the existence of a row in tables.

        :param column: Column on which to check
        :param value: Value on which to check
        :return: Boolean
        """

        return not not self._database.execute(
            f"SELECT EXISTS(SELECT {column.name} FROM {column.table} WHERE {column.name} = {value})"
        ).fetchone()[0]

    def get(self, column: Column | ColumnType, value: object) -> list[tuple]:

        """
        Returns all rows that meet the conditions.

        :param column: Column on which to get
        :param value: Value on which to get
        :return: List of rows
        """

        return self._database.execute(
            f"SELECT * FROM {column.table} WHERE {column.name} = ?", (value, )
        ).fetchall()

    def count(self, column: Column | ColumnType, value: object) -> int:

        """
        Count the number of rows that meet the conditions.

        :param column: Column on which to count
        :param value: Value on which to count
        :return: Integer
        """

        return self._database.execute(
            f"SELECT COUNT({column.name}) FROM {column.table} WHERE {column.name} = ?", (value, )
        ).fetchone()[-1]

    def execute(self, sql: str, parameters: tuple | object = ...) -> sqlite3.Cursor:

        """
        Execute sql query. [ More details in `sqlite3.connect(...)` ]

        :param sql: Sql query
        :param parameters: Query parameters
        :return: SQLite database cursor
        """

        return self._database.execute(sql, parameters)

    def close(self) -> None:

        """
        Will close the session.

        :return: Nothing
        """

        self._database.close()

    def __enter__(self) -> "Session":
        return self

    def __exit__(self, _type: object, _value: object, _traceback: object) -> None:
        self.close()


def create_session(path: str, tables: list[type[Table]], **kwargs) -> Callable[[], Session]:

    """
    Creates all tables in the selected database.

    :param path: Path to the database
    :param tables: List of tables to be created during session initialization
    :param kwargs: Other options for opening a database [ More details in `sqlite3.connect(...)` ]
    :return: Local session with given parameters
    """

    with Session(path=path, tables=tables, **kwargs) as _:
        return lambda: Session(path, tables, **kwargs)
