import sqlite3
import os

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        # ensure the directory exists
        os.makedirs(os.path.dirname(db_file), exist_ok=True)
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

def add_topic(conn, topic_name):
    """
    Add a new topic to the topics table
    :param conn:
    :param topic_name:
    :return: topic id
    """
    sql = ''' INSERT INTO topics(name)
              VALUES(?) '''
    cur = conn.cursor()
    cur.execute(sql, (topic_name,))
    conn.commit()
    return cur.lastrowid

def get_all_topics(conn):
    """
    Query all rows in the topics table
    :param conn: the Connection object
    :return:
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM topics")

    rows = cur.fetchall()

    return rows

def add_concept(conn, topic_id, content):
    """
    Add a new concept to the concepts table
    :param conn:
    :param topic_id:
    :param content:
    :return: concept id
    """
    sql = ''' INSERT INTO concepts(topic_id, content)
              VALUES(?,?) '''
    cur = conn.cursor()
    cur.execute(sql, (topic_id, content))
    conn.commit()
    return cur.lastrowid

def get_concepts_for_topic(conn, topic_id):
    """
    Query all concepts for a given topic
    :param conn: the Connection object
    :param topic_id:
    :return:
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM concepts WHERE topic_id=?", (topic_id,))

    rows = cur.fetchall()

    return rows

if __name__ == '__main__':
    main()
