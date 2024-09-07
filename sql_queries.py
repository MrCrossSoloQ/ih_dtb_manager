from psycopg2 import sql
from psycopg2.sql import Identifier, Literal

def update_data(my_con, my_cur, table_a, column_a, new_value, column_b, id_value):
    my_query = sql.SQL(
        """
            UPDATE {}
            SET {} = {}
            WHERE {}.{} = {}
        """
    ).format(
    sql.Identifier(table_a),
        sql.Identifier(column_a),
        sql.Literal(new_value),
        sql.Identifier(table_a),
        sql.Identifier(column_b),
        sql.Literal(id_value)
    )
    my_cur.execute(my_query)
    my_con.commit()

def get_data_join_condition_results(my_cur, table_a, table_b, column_t_a, column_t_b, column_t_b2,condition_column, value):
    my_query = sql.SQL(
        """
            SELECT {}.*, {}.{} FROM {}
            INNER JOIN {}
            ON {}.{} = {}.{}
            WHERE {}.{} = {}
        """
    ).format(
        sql.Identifier(table_a),
        sql.Identifier(table_b),
        sql.Identifier(column_t_b),
        sql.Identifier(table_a),
        sql.Identifier(table_b),
        sql.Identifier(table_a),
        sql.Identifier(column_t_a),
        sql.Identifier(table_b),
        sql.Identifier(column_t_b2),
        sql.Identifier(table_a),
        sql.Identifier(condition_column),
        sql.Literal(value)
    )

    my_cur.execute(my_query)
    recieved_data = my_cur.fetchall()
    return recieved_data

def get_data_simple(my_cur, choosen_table):
    my_query = sql.SQL(
        """
            SELECT * FROM {table}
        """
    ).format(
        table = sql.Identifier(choosen_table)
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