from psycopg2 import sql

def get_data(my_cur, choosen_table):
    my_query = sql.SQL(
        """
            SELECT * FROM {table}
        """
    ).format(
        table = sql.Identifier(choosen_table),
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