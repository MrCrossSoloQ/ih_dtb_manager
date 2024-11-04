import psycopg2
import psycopg2.extras
from psycopg2 import sql


class DtbDriver:
    def __init__(self, host, database, user, password):
        self.connection = None
        self.cursor = None
        self.host = host
        self.database = database
        self.user = user
        self.password = password

    def connection_maker(self):
        if self.connection is None:
            self.connection = psycopg2.connect(
                host = self.host,
                database = self.database,
                user = self.user,
                password = self.password
            )
            return self.connection

    def cursor_maker(self):
        if self.connection and self.cursor is None:
            self.cursor = self.connection.cursor(cursor_factory = psycopg2.extras.DictCursor)
            return self.cursor

    def dtb_disconnection(self):
        self.cursor.close()
        self.connection.close()

    def get_data_simple(self, choosen_table):
        my_query = sql.SQL(
            """
                SELECT * FROM {table}
            """
        ).format(
            table=sql.Identifier(choosen_table)
        )

        self.cursor.execute(my_query)
        recieved_data = self.cursor.fetchall()
        return recieved_data

    def insert_data(self, choosen_table, columns, values):
        my_query = sql.SQL(
            """
            INSERT INTO {table}({columns})
                VALUES({values})
            """
        ).format(
            table=sql.Identifier(choosen_table),
            columns=sql.SQL(",").join(map(sql.Identifier, columns)),
            values=sql.SQL(",").join(map(sql.Literal, values))
        )

        self.cursor.execute(my_query)
        self.connection.commit()