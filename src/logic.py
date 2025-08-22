import sqlite3
import google.generativeai as genai
from database import (create_connection, add_topic, get_all_topics,
                    add_concept, get_concepts_for_topic, get_all_topics_with_mastery,
                    get_setting, set_setting)

class LearningAppLogic:
    def __init__(self, db_file):
        self.conn = create_connection(db_file)
        self.selected_topic = None

    def add_new_topic(self, topic_name):
        return add_topic(self.conn, topic_name)

    def get_all_topics(self):
        return get_all_topics(self.conn)

    def add_new_concept(self, topic_id, content):
        return add_concept(self.conn, topic_id, content)

    def get_concepts_for_topic(self, topic_id):
        return get_concepts_for_topic(self.conn, topic_id)

    def get_all_topics_with_mastery(self):
        return get_all_topics_with_mastery(self.conn)

    def save_api_key(self, api_key):
        set_setting(self.conn, "gemini_api_key", api_key)

    def get_api_key(self):
        return get_setting(self.conn, "gemini_api_key")

    def process_knowledge(self, knowledge_text, topic_id):
        api_key = self.get_api_key()
        if not api_key:
            raise ValueError("Gemini API Key not set.")

        if not knowledge_text:
            raise ValueError("Knowledge text is empty.")

        if not topic_id:
            raise ValueError("Topic not selected.")

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-pro')
            prompt = f"Extract the key concepts from the following text. Present them as a numbered list. Each concept should be a short, self-contained statement.\n\nText: \"{knowledge_text}\""
            response = model.generate_content(prompt)

            concepts = []
            for line in response.text.split('\n'):
                line = line.strip()
                if line and line[0].isdigit() and '.' in line:
                    concepts.append(line.split('.', 1)[1].strip())

            if not concepts:
                return []

            for concept_content in concepts:
                self.add_new_concept(topic_id, concept_content)

            return concepts

        except Exception as e:
            raise RuntimeError(f"An error occurred while processing the knowledge: {e}")

    def close_connection(self):
        if self.conn:
            self.conn.close()
