import sqlite3
import os
import sys
import pytest

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from database import create_connection, main as create_db, add_topic, get_all_topics, add_concept, get_concepts_for_topic

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

def test_add_topic(db_connection):
    topic_name = "Organic Chemistry"
    topic_id = add_topic(db_connection, topic_name)
    assert topic_id is not None

    # Verify the topic was added
    cursor = db_connection.cursor()
    cursor.execute("SELECT name FROM topics WHERE id = ?", (topic_id,))
    result = cursor.fetchone()
    assert result[0] == topic_name

def test_get_all_topics(db_connection):
    # Clear topics table
    cursor = db_connection.cursor()
    cursor.execute("DELETE FROM topics")
    db_connection.commit()

    # Add some topics
    topics = ["World War II", "Calculus", "Python Programming"]
    for topic in topics:
        add_topic(db_connection, topic)

    # Get all topics
    all_topics = get_all_topics(db_connection)
    assert len(all_topics) == len(topics)

    retrieved_topic_names = sorted([row[1] for row in all_topics])
    assert retrieved_topic_names == sorted(topics)

def test_add_concept(db_connection):
    # Add a topic first
    topic_name = "Biology"
    topic_id = add_topic(db_connection, topic_name)

    # Add a concept
    concept_content = "Cell is the basic unit of life"
    concept_id = add_concept(db_connection, topic_id, concept_content)
    assert concept_id is not None

    # Verify the concept was added
    cursor = db_connection.cursor()
    cursor.execute("SELECT topic_id, content FROM concepts WHERE id = ?", (concept_id,))
    result = cursor.fetchone()
    assert result[0] == topic_id
    assert result[1] == concept_content

def test_get_concepts_for_topic(db_connection):
    # Clear tables
    cursor = db_connection.cursor()
    cursor.execute("DELETE FROM concepts")
    cursor.execute("DELETE FROM topics")
    db_connection.commit()

    # Add a topic
    topic_id = add_topic(db_connection, "History")

    # Add concepts
    concepts = ["The Renaissance", "The Reformation", "The Age of Discovery"]
    for concept in concepts:
        add_concept(db_connection, topic_id, concept)

    # Get concepts for the topic
    retrieved_concepts = get_concepts_for_topic(db_connection, topic_id)
    assert len(retrieved_concepts) == len(concepts)

    retrieved_concept_contents = sorted([row[2] for row in retrieved_concepts])
    assert retrieved_concept_contents == sorted(concepts)
