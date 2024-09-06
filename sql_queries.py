from psycopg2 import sql
from psycopg2.sql import Identifier, Literal


def get_data(my_cur, choosen_table, choosen_table2 = None, choosen_columns=None, value=None, value2=None):
    if choosen_columns is None:
        my_query = sql.SQL(
            """
                SELECT * FROM {table}
            """
        ).format(
            table = sql.Identifier(choosen_table)
        )
    else:
        my_query = sql.SQL(
            """
                SELECT {columns} FROM {table}
                INNER JOIN {table2}
                ON {value} = {value2}
            """
        ).format(
            columns = sql.SQL(",").join(map(Identifier, choosen_columns)),
            table = sql.Identifier(choosen_table),
            table2 = sql.Identifier(choosen_table2),
            value = sql.SQL(",").join(map(Literal, value)),
            value2 = sql.SQL(",").join(map(Literal, value2))
        )

    my_cur.execute(my_query)
    recieved_data = my_cur.fetchall()
    return recieved_data

def insert_data(my_con, my_cur, choosen_table, columns, values):
    my_query = sql.SQL(
        """
        INSERT INTO {table}({columns})
            VALUES({values})
        """
    ).format(
        table = sql.Identifier(choosen_table),
        columns = sql.SQL(",").join(map(sql.Identifier, columns)),
        values = sql.SQL(",").join(map(sql.Literal, values))
    )

    my_cur.execute(my_query)
    my_con.commit()