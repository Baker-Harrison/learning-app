import sqlite3
import pytest
from src.database import create_table
from src.knowledge_base import allocate_technique, create_knowledge_tables

@pytest.fixture
def db_conn():
    """Fixture to set up an in-memory SQLite database for tests."""
    conn = sqlite3.connect(":memory:")

    # Create tables from the main schema
    sql_create_concepts_table = """CREATE TABLE IF NOT EXISTS concepts (
                                    id integer PRIMARY KEY,
                                    topic_id integer NOT NULL,
                                    content text NOT NULL
                                );"""
    sql_create_recall_sessions_table = """CREATE TABLE IF NOT EXISTS recall_sessions (
                                            id integer PRIMARY KEY,
                                            concept_id integer NOT NULL,
                                            timestamp text NOT NULL,
                                            user_response text,
                                            ai_grade real,
                                            FOREIGN KEY (concept_id) REFERENCES concepts (id)
                                        );"""
    create_table(conn, sql_create_concepts_table)
    create_table(conn, sql_create_recall_sessions_table)

    # Create tables from the knowledge base schema
    create_knowledge_tables(conn)

    # Add a dummy concept
    conn.execute("INSERT INTO concepts (id, topic_id, content) VALUES (1, 1, 'Test Concept')")
    conn.commit()

    yield conn
    conn.close()

def test_allocate_technique_no_history(db_conn):
    """Test that 'Recall' is allocated for a concept with no history."""
    technique = allocate_technique(db_conn, 1)
    assert technique == "Recall"

def test_allocate_technique_few_failures(db_conn):
    """Test that 'Recall' is allocated with 2 or fewer failures."""
    # Add 2 failure sessions
    db_conn.execute("INSERT INTO recall_sessions (concept_id, timestamp, ai_grade) VALUES (1, '2023-01-01', 1)")
    db_conn.execute("INSERT INTO recall_sessions (concept_id, timestamp, ai_grade) VALUES (1, '2023-01-02', 2)")
    db_conn.commit()

    technique = allocate_technique(db_conn, 1)
    assert technique == "Recall"

def test_allocate_technique_many_failures(db_conn):
    """Test that 'Elaboration' is allocated with more than 2 failures."""
    # Add 3 failure sessions
    db_conn.execute("INSERT INTO recall_sessions (concept_id, timestamp, ai_grade) VALUES (1, '2023-01-01', 1)")
    db_conn.execute("INSERT INTO recall_sessions (concept_id, timestamp, ai_grade) VALUES (1, '2023-01-02', 1)")
    db_conn.execute("INSERT INTO recall_sessions (concept_id, timestamp, ai_grade) VALUES (1, '2023-01-03', 2)")
    db_conn.commit()

    technique = allocate_technique(db_conn, 1)
    assert technique == "Elaboration"

def test_allocate_technique_mixed_history(db_conn):
    """Test that 'Elaboration' is allocated with a mixed history resulting in >2 failures."""
    # Add 3 failures and 2 successes
    db_conn.execute("INSERT INTO recall_sessions (concept_id, timestamp, ai_grade) VALUES (1, '2023-01-01', 1)") # Fail
    db_conn.execute("INSERT INTO recall_sessions (concept_id, timestamp, ai_grade) VALUES (1, '2023-01-02', 4)") # Success
    db_conn.execute("INSERT INTO recall_sessions (concept_id, timestamp, ai_grade) VALUES (1, '2023-01-03', 2)") # Fail
    db_conn.execute("INSERT INTO recall_sessions (concept_id, timestamp, ai_grade) VALUES (1, '2023-01-04', 3)") # Success
    db_conn.execute("INSERT INTO recall_sessions (concept_id, timestamp, ai_grade) VALUES (1, '2023-01-05', 1)") # Fail
    db_conn.commit()

    technique = allocate_technique(db_conn, 1)
    assert technique == "Elaboration"
