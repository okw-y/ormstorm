import sqlite3

from .orm.filters import MagicFilter
from .orm.column import Column, ColumnType
from .orm.constants import Types
from .orm.exceptions import SessionExecuteError
from .orm.table import Table, DynamicTable

from typing import Callable, Union, Type


class Typing(object):

    """
    Namespace with type hints.
    """

    AnyTable = Union[MagicFilter, DynamicTable, Table, Type[Table]]
    NamespaceTable = Union[DynamicTable, Type[Table]]
    AnyColumn = Union[Column, ColumnType]


class Session(object):
    def __init__(self, path: str, tables: list[Typing.NamespaceTable] = None, **kwargs) -> None:

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

    def create(self, table: Typing.NamespaceTable) -> None:

        """
        Creates a new table in the database.

        :param table: Table or dynamic table
        :return: Nothing
        """

        self._database.execute(f"CREATE TABLE IF NOT EXISTS {table.__tablename__} "
                               f"({', '.join([column.serialize() for column in table.columns().values()])})")
        self._database.commit()

    def clear(self, table: Typing.NamespaceTable) -> None:

        """
        Clears the selected table.

        :param table: Table or dynamic table
        :return: Nothing
        """

        self._database.execute(
            f"DELETE FROM {table.__tablename__}"
        )
        self._database.commit()

    def drop(self, table: Typing.NamespaceTable) -> None:

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

    def delete(self, data: Typing.AnyTable) -> None:

        """
        Removes all rows that match the specified conditions

        :param data: Any type of table or magic filter
        :return: Nothing
        """

        if not isinstance(data, (MagicFilter, DynamicTable, Table, type(Table))):
            raise SessionExecuteError("The data is not a successor of MagicFilterData or Table!")

        if isinstance(data, (DynamicTable, Table, type(Table))):
            self._database.execute(
                f"DELETE FROM {data.__tablename__}"
            )

        self._database.execute(
            f"DELETE FROM {data.parameters['table']} WHERE {data.query}", data.variables
        )

    def exists(self, data: Typing.AnyTable) -> bool:

        """
        Checks for the existence of rows satisfying given conditions.

        :param data: Any type of table or magic filter
        :return: Boolean
        """

        if not isinstance(data, (MagicFilter, DynamicTable, Table, type(Table))):
            raise SessionExecuteError("The data is not a successor of MagicFilterData or Table!")

        if isinstance(data, (DynamicTable, Table, type(Table))):
            return not not self._database.execute(
                f"SELECT EXISTS(SELECT * FROM {data.__tablename__})"
            ).fetchone()[-1]

        return not not self._database.execute(
            f"SELECT EXISTS(SELECT * FROM {data.parameters['table']} WHERE {data.query})", data.variables
        ).fetchone()[-1]

    def select(self, data: Typing.AnyTable, items: list[Typing.AnyColumn] = None) -> list[tuple]:

        """
        Selects certain data from a table that satisfies given conditions.

        :param data: Any type of table or magic filter
        :param items: Elements to select
        :return: List of tuples
        """

        if not isinstance(data, (MagicFilter, DynamicTable, Table, type(Table))):
            raise SessionExecuteError("The data is not a successor of MagicFilterData or Table!")

        select = "*" if not items else ", ".join(
            [f"{item.table}.{item.name}" for item in items]
        )

        if isinstance(data, (DynamicTable, Table, type(Table))):
            return self._database.execute(
                f"SELECT {select} FROM {data.__tablename__}"
            ).fetchall()

        return self._database.execute(
            f"SELECT {select} FROM {data.parameters['table']} WHERE {data.query}", data.variables
        ).fetchall()

    def count(self, data: Typing.AnyTable) -> int:

        """
        Counts the number of rows satisfying given conditions.

        :param data: Any type of table or magic filter
        :return: Integer
        """

        if not isinstance(data, (MagicFilter, DynamicTable, Table, type(Table))):
            raise SessionExecuteError("The data is not a successor of MagicFilterData or Table!")

        if isinstance(data, (DynamicTable, Table, type(Table))):
            return self._database.execute(
                f"SELECT COUNT(*) FROM {data.__tablename__}"
            ).fetchone()[-1]

        return self._database.execute(
            f"SELECT COUNT(*) FROM {data.parameters['table']} WHERE {data.query}", data.variables
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


def create_session(path: str, tables: list[Typing.NamespaceTable], **kwargs) -> Callable[[], Session]:

    """
    Creates all tables in the selected database.

    :param path: Path to the database
    :param tables: List of tables to be created during session initialization
    :param kwargs: Other options for opening a database [ More details in `sqlite3.connect(...)` ]
    :return: Local session with given parameters
    """

    with Session(path=path, tables=tables, **kwargs) as _:
        return lambda: Session(path, tables, **kwargs)
