import pytest
import os
import sys
import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from fsrs import FSRS, default_params
from grading import rule_based_grade
from database import (
    create_connection,
    main as create_db,
    add_topic,
    add_concept,
    initialize_learning_data,
    update_learning_data,
    record_recall_session,
    get_next_concept_to_review
)

DB_FILE = "data/test_logic.db"

@pytest.fixture(scope="module")
def db_connection():
    # Set up: create the database and tables
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    conn = create_connection(DB_FILE)

    # Manually create tables
    from database import main
    main() # this will create the tables in the default db, not test one.

    # We need to create tables in our test db
    conn.close()
    # HACK: The main function from database.py uses a hardcoded path.
    # We will rename the db file to what main() expects, call main, then rename it back.
    if os.path.exists("data/learning_data.db"):
        os.remove("data/learning_data.db")
    os.rename(DB_FILE, "data/learning_data.db")
    main()
    os.rename("data/learning_data.db", DB_FILE)

    conn = create_connection(DB_FILE)
    yield conn

    # Tear down: close the connection and remove the database file
    conn.close()
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)


def test_fsrs_calculations():
    fsrs = FSRS(default_params)

    # Test initial stability
    assert fsrs.initial_stability(1) == default_params[0]
    assert fsrs.initial_stability(2) == default_params[1]
    assert fsrs.initial_stability(3) == default_params[2]
    assert fsrs.initial_stability(4) == default_params[3]

    # Test initial difficulty
    d0 = fsrs.initial_difficulty(3) # grade = good
    assert d0 == default_params[4] - (3-3) * default_params[5]

    # Test retrievability
    r = fsrs.retrievability(t=10, s=100)
    assert 0 < r < 1

    # Test new stability after recall
    s_good = fsrs.new_stability(d=5, s=10, r=0.9, g=3) # grade = good
    assert s_good > 10

    # Test new stability after forgetting
    s_again = fsrs.new_stability(d=5, s=10, r=0.8, g=1) # grade = again
    assert s_again < 10


def test_grading_mechanism():
    assert rule_based_grade("the cat sat", "the cat sat on the mat") == 3/5
    assert rule_based_grade("the cat sat on the mat", "the cat sat on the mat") == 1.0
    assert rule_based_grade("a completely different response", "the cat sat on the mat") == 0.0
    assert rule_based_grade("", "the cat sat on the mat") == 0.0
    assert rule_based_grade("the cat sat on the mat", "") == 0.0

def test_scheduling_engine_new_concept(db_connection):
    conn = db_connection
    # Clear tables
    conn.execute("DELETE FROM concepts")
    conn.execute("DELETE FROM topics")
    conn.execute("DELETE FROM learning_data")
    conn.commit()

    topic_id = add_topic(conn, "Test Topic")
    concept_id = add_concept(conn, topic_id, "New Concept")

    next_concept = get_next_concept_to_review(conn)
    assert next_concept is not None
    assert next_concept[0] == concept_id
    assert next_concept[2] == "New Concept"

def test_scheduling_engine_lowest_retrievability(db_connection):
    conn = db_connection
    # Clear tables
    conn.execute("DELETE FROM concepts")
    conn.execute("DELETE FROM topics")
    conn.execute("DELETE FROM learning_data")
    conn.execute("DELETE FROM recall_sessions")
    conn.commit()

    topic_id = add_topic(conn, "Test Topic")

    # Concept 1: reviewed recently
    c1_id = add_concept(conn, topic_id, "Concept 1")
    initialize_learning_data(conn, c1_id, 5, 10)
    record_recall_session(conn, c1_id, "response", 0.9)

    # Concept 2: reviewed a while ago, should have lower retrievability
    c2_id = add_concept(conn, topic_id, "Concept 2")
    initialize_learning_data(conn, c2_id, 5, 10)
    # Manually insert a recall session from 10 days ago
    ten_days_ago = (datetime.datetime.now() - datetime.timedelta(days=10)).isoformat()
    conn.execute("INSERT INTO recall_sessions(concept_id, timestamp, user_response, ai_grade) VALUES (?,?,?,?)",
                 (c2_id, ten_days_ago, "response", 0.9))
    conn.commit()

    next_concept = get_next_concept_to_review(conn)
    assert next_concept is not None
    assert next_concept[0] == c2_id
    assert next_concept[2] == "Concept 2"
