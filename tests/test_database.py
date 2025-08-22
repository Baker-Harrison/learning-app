import sqlite3
import os
import sys
import pytest

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from database import create_connection, main as create_db

DB_FILE = "data/learning_data.db"

@pytest.fixture(scope="module")
def db_connection():
    # Set up: create the database and tables
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    create_db()

    conn = create_connection(DB_FILE)
    yield conn

    # Tear down: close the connection and remove the database file
    conn.close()
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

def test_database_file_creation():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    create_db()
    assert os.path.exists(DB_FILE)
    os.remove(DB_FILE)

def test_database_connection(db_connection):
    assert db_connection is not None

def test_tables_creation(db_connection):
    cursor = db_connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = sorted([row[0] for row in cursor.fetchall()])

    expected_tables = sorted(['topics', 'concepts', 'recall_sessions', 'learning_data'])

    assert tables == expected_tables


def test_topics_schema(db_connection):
    cursor = db_connection.cursor()
    cursor.execute("PRAGMA table_info(topics);")
    columns = [row[1] for row in cursor.fetchall()]
    expected_columns = ['id', 'name']
    assert columns == expected_columns

def test_concepts_schema(db_connection):
    cursor = db_connection.cursor()
    cursor.execute("PRAGMA table_info(concepts);")
    columns = [row[1] for row in cursor.fetchall()]
    expected_columns = ['id', 'topic_id', 'content']
    assert columns == expected_columns

def test_recall_sessions_schema(db_connection):
    cursor = db_connection.cursor()
    cursor.execute("PRAGMA table_info(recall_sessions);")
    columns = [row[1] for row in cursor.fetchall()]
    expected_columns = ['id', 'concept_id', 'timestamp', 'user_response', 'ai_grade']
    assert columns == expected_columns

def test_learning_data_schema(db_connection):
    cursor = db_connection.cursor()
    cursor.execute("PRAGMA table_info(learning_data);")
    columns = [row[1] for row in cursor.fetchall()]
    expected_columns = ['id', 'concept_id', 'difficulty', 'stability']
    assert columns == expected_columns
