import sqlite3

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        print(e)

    return conn

def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except sqlite3.Error as e:
        print(e)

def main():
    database = "data/learning_data.db"

    sql_create_topics_table = """ CREATE TABLE IF NOT EXISTS topics (
                                        id integer PRIMARY KEY,
                                        name text NOT NULL UNIQUE
                                    ); """

    sql_create_concepts_table = """CREATE TABLE IF NOT EXISTS concepts (
                                    id integer PRIMARY KEY,
                                    topic_id integer NOT NULL,
                                    content text NOT NULL,
                                    FOREIGN KEY (topic_id) REFERENCES topics (id)
                                );"""

    sql_create_recall_sessions_table = """CREATE TABLE IF NOT EXISTS recall_sessions (
                                            id integer PRIMARY KEY,
                                            concept_id integer NOT NULL,
                                            timestamp text NOT NULL,
                                            user_response text,
                                            ai_grade real,
                                            FOREIGN KEY (concept_id) REFERENCES concepts (id)
                                        );"""

    sql_create_learning_data_table = """CREATE TABLE IF NOT EXISTS learning_data (
                                            id integer PRIMARY KEY,
                                            concept_id integer NOT NULL UNIQUE,
                                            difficulty real NOT NULL,
                                            stability real NOT NULL,
                                            FOREIGN KEY (concept_id) REFERENCES concepts (id)
                                        );"""

    # create a database connection
    conn = create_connection(database)

    # create tables
    if conn is not None:
        # create topics table
        create_table(conn, sql_create_topics_table)

        # create concepts table
        create_table(conn, sql_create_concepts_table)

        # create recall_sessions table
        create_table(conn, sql_create_recall_sessions_table)

        # create learning_data table
        create_table(conn, sql_create_learning_data_table)

        conn.close()
    else:
        print("Error! cannot create the database connection.")

if __name__ == '__main__':
    main()
