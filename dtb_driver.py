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

    def get_data_join_condition_results(self, table_a, table_b, column_t_a, column_t_b, column_t_b2, condition_column, value):
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
        self.cursor.execute(my_query)
        recieved_data = self.cursor.fetchall()
        return recieved_data

    def update_data(self, table_a, column_a, new_value, column_b, id_value):
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
        self.cursor.execute(my_query)
        self.connection.commit()

    def get_full_game_info_on_optional_date(self, choosen_date):
        my_query = sql.SQL(
            """
                SELECT ih_games.*, home_teams.team_name AS home_team_name, away_teams.team_name AS away_team_name FROM ih_games
                JOIN teams AS home_teams
                ON ih_games.home_team_id = home_teams.team_id
                JOIN teams AS away_teams
                ON  ih_games.away_team_id = away_teams.team_id
                WHERE match_date = {date_value}
            """
        ).format(
            date_value=sql.Literal(choosen_date)
        )

        self.cursor.execute(my_query)
        recieved_data = self.cursor.fetchall()
        return recieved_data

    def get_player_game_stats(self):
        my_query = sql.SQL(
            """
            
            """
        )