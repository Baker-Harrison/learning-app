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

import datetime
from fsrs import FSRS, default_params

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

def initialize_learning_data(conn, concept_id, difficulty, stability):
    """
    Initialize learning data for a new concept.
    :param conn:
    :param concept_id:
    :param difficulty:
    :param stability:
    """
    sql = ''' INSERT INTO learning_data(concept_id, difficulty, stability)
              VALUES(?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, (concept_id, difficulty, stability))
    conn.commit()

def update_learning_data(conn, concept_id, difficulty, stability):
    """
    Update learning data for a concept.
    :param conn:
    :param concept_id:
    :param difficulty:
    :param stability:
    """
    sql = ''' UPDATE learning_data
              SET difficulty = ?,
                  stability = ?
              WHERE concept_id = ?'''
    cur = conn.cursor()
    cur.execute(sql, (difficulty, stability, concept_id))
    conn.commit()

def record_recall_session(conn, concept_id, user_response, ai_grade):
    """
    Record a recall session.
    :param conn:
    :param concept_id:
    :param user_response:
    :param ai_grade:
    """
    sql = ''' INSERT INTO recall_sessions(concept_id, timestamp, user_response, ai_grade)
              VALUES(?,?,?,?) '''
    cur = conn.cursor()
    timestamp = datetime.datetime.now().isoformat()
    cur.execute(sql, (concept_id, timestamp, user_response, ai_grade))
    conn.commit()

def get_next_concept_to_review(conn):
    """
    Get the next concept to review using the FSRS algorithm.

    This function first looks for new concepts (those not in learning_data).
    If there are no new concepts, it finds the concept with the lowest
    retrievability score.

    :param conn: the Connection object
    :return: The concept to review (id, topic_id, content) or None
    """
    cur = conn.cursor()

    # 1. Check for new concepts
    cur.execute("""
        SELECT c.id, c.topic_id, c.content
        FROM concepts c
        LEFT JOIN learning_data ld ON c.id = ld.concept_id
        WHERE ld.concept_id IS NULL
        ORDER BY c.id
        LIMIT 1
    """)
    new_concept = cur.fetchone()
    if new_concept:
        return new_concept

    # 2. If no new concepts, find the one with the lowest retrievability
    fsrs = FSRS(default_params)

    cur.execute("""
        SELECT
            ld.concept_id,
            ld.difficulty,
            ld.stability,
            (SELECT MAX(rs.timestamp) FROM recall_sessions rs WHERE rs.concept_id = ld.concept_id) as last_review
        FROM learning_data ld
    """)

    concepts_to_review = []
    for concept_id, difficulty, stability, last_review_str in cur.fetchall():
        if last_review_str:
            last_review_date = datetime.datetime.fromisoformat(last_review_str)
            days_since_review = (datetime.datetime.now() - last_review_date).days

            retrievability = fsrs.retrievability(days_since_review, stability)
            concepts_to_review.append((retrievability, concept_id))

    if not concepts_to_review:
        return None

    # Find the concept with the minimum retrievability
    min_retrievability_concept_id = min(concepts_to_review, key=lambda x: x[0])[1]

    # Get the full concept details
    cur.execute("SELECT id, topic_id, content FROM concepts WHERE id = ?", (min_retrievability_concept_id,))
    return cur.fetchone()


def get_topic_mastery(conn, topic_id):
    """
    Calculate the mastery of a topic as the average retrievability of its concepts.
    Concepts that have not been reviewed are excluded from the calculation.
    """
    fsrs = FSRS(default_params)
    cur = conn.cursor()

    cur.execute("""
        SELECT
            c.id,
            ld.stability
        FROM concepts c
        JOIN learning_data ld ON c.id = ld.concept_id
        WHERE c.topic_id = ?
    """, (topic_id,))

    rows = cur.fetchall()

    total_retrievability = 0
    reviewed_concepts_count = 0

    for concept_id, stability in rows:
        # Find the last review timestamp for this concept
        cur.execute("""
            SELECT MAX(timestamp)
            FROM recall_sessions
            WHERE concept_id = ?
        """, (concept_id,))
        last_review_str = cur.fetchone()[0]

        if last_review_str:
            last_review_date = datetime.datetime.fromisoformat(last_review_str)
            days_since_review = (datetime.datetime.now() - last_review_date).days
            retrievability = fsrs.retrievability(days_since_review, stability)
            total_retrievability += retrievability
            reviewed_concepts_count += 1

    if reviewed_concepts_count == 0:
        return 0.0

    return total_retrievability / reviewed_concepts_count


def get_all_topics_with_mastery(conn):
    """
    Get all topics with their calculated mastery score.
    """
    topics = get_all_topics(conn)
    topics_with_mastery = []
    for topic in topics:
        topic_id, topic_name = topic
        mastery = get_topic_mastery(conn, topic_id)
        topics_with_mastery.append((topic_id, topic_name, mastery))

    return topics_with_mastery


if __name__ == '__main__':
    main()
