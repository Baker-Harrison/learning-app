import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from logic import LearningAppLogic
from database import create_db_tables

DB_FILE = "data/test_logic.db"

@pytest.fixture
def logic_app():
    # Setup: create a clean database for each test
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    create_db_tables(DB_FILE)

    app = LearningAppLogic(DB_FILE)
    yield app

    # Teardown: close connection and remove db file
    app.close_connection()
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

def test_add_and_get_topic(logic_app):
    topic_name = "New Topic"
    topic_id = logic_app.add_new_topic(topic_name)
    assert topic_id is not None

    topics = logic_app.get_all_topics()
    assert any(topic[1] == topic_name for topic in topics)

def test_add_and_get_concept(logic_app):
    topic_id = logic_app.add_new_topic("A Topic")
    concept_content = "A new concept"
    concept_id = logic_app.add_new_concept(topic_id, concept_content)
    assert concept_id is not None

    concepts = logic_app.get_concepts_for_topic(topic_id)
    assert any(c[2] == concept_content for c in concepts)

def test_api_key_settings(logic_app):
    api_key = "my-secret-api-key"
    logic_app.save_api_key(api_key)
    retrieved_key = logic_app.get_api_key()
    assert retrieved_key == api_key

@patch('logic.genai')
def test_process_knowledge_success(mock_genai, logic_app):
    # Setup
    api_key = "fake-api-key"
    logic_app.save_api_key(api_key)
    topic_id = logic_app.add_new_topic("Test Topic")
    knowledge_text = "This is a test concept."

    # Mock the Gemini API response
    mock_model = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model
    mock_model.generate_content.return_value.text = "1. Test concept"

    # Run
    concepts = logic_app.process_knowledge(knowledge_text, topic_id)

    # Assert
    assert len(concepts) == 1
    assert concepts[0] == "Test concept"

    db_concepts = logic_app.get_concepts_for_topic(topic_id)
    assert any(c[2] == "Test concept" for c in db_concepts)

def test_process_knowledge_no_api_key(logic_app):
    with pytest.raises(ValueError, match="Gemini API Key not set."):
        logic_app.process_knowledge("Some text", 1)

def test_process_knowledge_no_text(logic_app):
    logic_app.save_api_key("fake-key")
    with pytest.raises(ValueError, match="Knowledge text is empty."):
        logic_app.process_knowledge("", 1)

def test_process_knowledge_no_topic(logic_app):
    logic_app.save_api_key("fake-key")
    with pytest.raises(ValueError, match="Topic not selected."):
        logic_app.process_knowledge("Some text", None)

@patch('logic.genai')
def test_process_knowledge_api_error(mock_genai, logic_app):
    logic_app.save_api_key("fake-key")
    topic_id = logic_app.add_new_topic("A Topic")
    mock_genai.GenerativeModel.side_effect = Exception("API Error")

    with pytest.raises(RuntimeError, match="An error occurred while processing the knowledge: API Error"):
        logic_app.process_knowledge("Some text", topic_id)
